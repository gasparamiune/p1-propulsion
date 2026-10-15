#!/usr/bin/env python3
"""Build interfaces/electronics.json v3 (Electronics, 06-electronics), 2026-10-13, firmware v2.10.

Supersedes electronics.json v2 (hub file at the time of the run, recorded by sha256/16 and archived by the publish step under
06-electronics/archive/v2.9/interfaces/electronics_v2.json). v1 (2026-10-11) stays archived as 06-electronics/results/electronics_v1.json.

REV-ELEC-1 RE-16 ("regenerate the file as v3 from a corrected generator, and add a self-check that every abort-matrix entry quotes the
config.h constants it describes"). Corrections against the v2 generator (make_interface_json_v2.py, kept for provenance):
  - v1 path is an ARGUMENT (--v1, default the archived v1): v2 read the hub file and required it to be v1, which is no longer true;
  - config.h is read through a small preprocessor (flight-build macros: none defined), so #ifdef variants (kBpc1Shown, the SIL W
    what-if, the lift-clamp sweep macros) resolve to the flight values; ternaries on build constants are evaluated;
  - gnc.json relight planning keys are read at requirements.ignition.relight_planning_value_s.* (v2 published "NOT in gnc.json v3");
  - abort-matrix triggers are TEMPLATES whose numbers come only from config.h placeholders; the self-check refuses a trigger with a
    stand-alone numeric literal, a placeholder that does not resolve, or a listed constant the text does not quote;
  - schematic revision read from the generator (REV) and checked against the KiCad files; pin map file named by the revision;
  - firmware version read from the config.h v2.10 stamp and checked against the Makefile;
  - a stale-string scan over the output (outside the history keys) fails the build on known v2 errors.
Single-source rule as in v2: numbers come from the files that own them; every file read is listed with sha256/16.
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
FWD = os.path.join(ROOT, 'firmware')
CORE = os.path.join(FWD, 'src', 'core')
KICAD = os.path.join(ROOT, 'hardware', 'kicad')
KGEN = os.path.join(ROOT, 'hardware', 'kicad_gen')
SIL = os.path.join(RES, 'sil_v2p10')
DATE = '2026-10-13'
READ = OrderedDict()   # every file read -> sha256/16


def rd(path: str, mode: str = 'r'):
    with open(path, 'rb') as f:
        b = f.read()
    READ[os.path.relpath(path, ROOT) if path.startswith(ROOT) else path] = hashlib.sha256(b).hexdigest()[:16]
    return b if mode == 'rb' else b.decode('utf-8')


def jload(path: str):
    return json.loads(re.sub(r'\bnan\b', 'null', rd(path)))


def tv(v, tag, **kw):
    d = OrderedDict([('v', v), ('tag', tag)])
    d.update(kw)
    return d


# ------------------------------------------------------------------------------------------------ config.h (flight build)
UNIT = [('_radps2', 'rad/s^2'), ('_radps', 'rad/s'), ('_rad', 'rad'), ('_Paps', 'Pa/s'), ('_Nps', 'N/s'), ('_mps', 'm/s'),
        ('_kgps', 'kg/s'), ('_Pa', 'Pa'), ('_Hz', 'Hz'), ('_ohm', 'ohm'), ('_us', 'us'), ('_dB', 'dB'), ('_ps', '1/s'), ('_s', 's'),
        ('_N', 'N'), ('_K', 'K'), ('_V', 'V'), ('_A', 'A'), ('_m', 'm')]


def unit_of(name: str) -> str:
    for suf, u in UNIT:
        if name.endswith(suf):
            return u
    return '-'


def preprocess(text: str, defined: set):
    """Minimal C preprocessor for the config headers: #ifdef/#ifndef/#if defined()/#else/#endif and object-like #define."""
    out, stack, macros = [], [], OrderedDict()
    def active():
        return all(stack)
    for line in text.split('\n'):
        s = line.strip()
        m = re.match(r'#\s*(ifdef|ifndef)\s+(\w+)', s)
        if m:
            d = m.group(2) in defined or m.group(2) in macros
            stack.append(d if m.group(1) == 'ifdef' else not d)
            out.append('')
            continue
        m = re.match(r'#\s*if\s+(.*)', s)
        if m:
            expr = re.sub(r'defined\s*\(\s*(\w+)\s*\)', lambda mm: 'True' if (mm.group(1) in defined or mm.group(1) in macros) else 'False',
                          m.group(1).split('//')[0])
            expr = expr.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ')
            stack.append(bool(eval(expr, {'__builtins__': {}}, {})))
            out.append('')
            continue
        if re.match(r'#\s*else', s):
            stack[-1] = not stack[-1]
            out.append('')
            continue
        if re.match(r'#\s*endif', s):
            stack.pop()
            out.append('')
            continue
        m = re.match(r'#\s*define\s+(\w+)\s+(.+)', s)
        if m:
            if active():
                macros[m.group(1)] = m.group(2).split('//')[0].strip()
            out.append('')
            continue
        if re.match(r'#\s*(error|pragma|include)', s):
            out.append('')
            continue
        out.append(line if active() else '')
    body = '\n'.join(out)
    for k, v in macros.items():
        body = re.sub(r'\b%s\b' % k, v, body)
    return body, macros


def parse_constexpr(text: str, ns: str):
    out = OrderedDict()
    for m in re.finditer(r'constexpr\s+(?:float|double|int|bool|uint16_t|uint8_t|uint32_t)\s+(\w+)\s*=\s*([^;]+);[ \t]*(?://[ \t]*(.*))?', text):
        name, expr, com = m.group(1), m.group(2).strip(), (m.group(3) or '').strip()
        tag = re.match(r'\[([^\]]*)\]', com)
        if name in out:
            raise SystemExit('config parse: %s::%s defined twice in the flight-build text' % (ns, name))
        out[name] = {'expr': expr, 'tag': tag.group(1) if tag else com[:120], 'ns': ns}
    return out


class Cfg:
    def __init__(self):
        self.d = OrderedDict()
        self.macros = OrderedDict()
        for fn, ns in (('engine_params.h', 'eng'), ('mech_params.h', 'mech'), ('config.h', 'cfg')):
            body, mac = preprocess(rd(os.path.join(CORE, fn)), defined=set())
            self.macros.update(mac)
            for k, v in parse_constexpr(body, ns).items():
                self.d[(ns, k)] = v
        self.val = {}
        for _ in range(8):   # resolve references iteratively
            for (ns, k), v in self.d.items():
                if (ns, k) in self.val:
                    continue
                e = v['expr']
                e = re.sub(r'\b(eng|mech|cfg)::(\w+)', lambda m: '__%s__%s' % (m.group(1), m.group(2)), e)
                e = re.sub(r'(\d)f\b', r'\1', e)
                if e in ('true', 'false'):
                    self.val[(ns, k)] = (e == 'true')
                    continue
                mt = re.fullmatch(r'\s*(\w+)\s*\?\s*([^:]+):\s*(.+)', e)   # ternary on a build constant
                if mt:
                    key = (ns, mt.group(1)) if (ns, mt.group(1)) in self.d else ('eng', mt.group(1))
                    if key not in self.val:
                        continue
                    e = mt.group(2).strip() if self.val[key] else mt.group(3).strip()
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
                if not ok or re.search(r'[a-jl-zA-Z_]\w*\s*\(', e):
                    continue
                try:
                    self.val[(ns, k)] = float(eval(e, {'__builtins__': {}}, env))
                except Exception:
                    pass

    def has(self, name, ns='cfg'):
        return (ns, name) in self.d

    def __call__(self, name: str, ns: str = 'cfg', digits: int = 6):
        key = (ns, name)
        if key not in self.d:
            raise KeyError('%s::%s not found' % (ns, name))
        v = self.val.get(key)
        if isinstance(v, float):
            v = float('%.*g' % (digits, v))
        return OrderedDict([('v', v), ('unit', unit_of(name)), ('tag', self.d[key]['tag']),
                            ('src', '%s %s' % ({'cfg': 'config.h', 'eng': 'engine_params.h', 'mech': 'mech_params.h'}[ns], name))])


def human(c):
    """Render a config constant for a sentence (display units; the JSON thresholds keep SI)."""
    v, u = c['v'], c['unit']
    if v is None:
        return '(%s, not evaluated)' % c['src'].split()[-1]
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if u == 'Pa':
        return '%.4g bar' % (v / 1e5)
    if u == 's':
        return ('%.4g ms' % (v * 1e3)) if abs(v) < 1.0 else ('%.4g s' % v)
    if u == 'rad':
        return '%.3g deg' % (v * 57.29577951308232)
    if u == 'K':
        return '%.2f K (%.1f C)' % (v, v - 273.15)
    if u in ('V', 'A', 'N', 'Hz', 'm'):
        return ('%.4g mm' % (v * 1e3)) if u == 'm' else '%.4g %s' % (v, u)
    if u in ('N/s', 'kg/s', 'us'):
        return ('%.4g g/s' % (v * 1e3)) if u == 'kg/s' else '%.4g %s' % (v, u)
    return '%.4g' % v


class Changelog:
    def __init__(self, path):
        self.lines = rd(path).split('\n')

    def cite(self, n: int, marker: str, chars: int = 220, before: int = 40):
        line = self.lines[n - 1]
        if marker not in line:
            raise SystemExit('CHANGELOG line %d does not contain %r' % (n, marker))
        parts = [p.strip() for p in line.split('|')]
        text = parts[3] if len(parts) > 3 else line
        i = text.find(marker)
        start = 0 if (i < 0 or i + len(marker) <= chars) else max(0, i - before)
        snip = text[start:start + chars]
        return 'CHANGELOG line %d (%s, %s): %s%s%s' % (n, parts[1], parts[0], '...' if start else '', snip,
                                                      '...' if start + chars < len(text) else '')


# ------------------------------------------------------------------------------------------------ abort matrix (templates)
# Numbers in a trigger come ONLY from {kName} / {eng:kName} placeholders. Self-check: no stand-alone numeric literal outside them.
AB = OrderedDict([
    ('CMD', ('FC ABORT frame 0x010 (magic 0xA5 0x5A, code, seq, CRC-8; no sequence check) or CMD_STATE ABORT: acted on at the next tick ahead '
             'of every other command; NC valve holding magnet released and pintle commanded closed on that tick; EVENT STATE with cause CMD '
             'sent three times; log abort_cause CMD. Works with the Pc channel invalid (test v210-15)', [])),
    ('HARD_START', ('IGNITION, or RUN within {kRunSettle_s} of entry: filtered absolute Pc above {kPcOverPressureAbs_Pa} abs for '
                    '{kPcOverPressureTime_s} (RE-20, filtered channel); in IGNITION a Pc transducer output at or above {kPcSensorMax_V} '
                    '(over-range taken as real pressure). The v2.9 late-light pressure-hold abort is DELETED (RE-01): a LIGHT_SPIKE record is logged '
                    'from {kLightSpikeLoAbs_Pa} abs (EVENT 0x20)', ['kRunSettle_s', 'kPcOverPressureAbs_Pa', 'kPcOverPressureTime_s',
                                                                  'kPcSensorMax_V', 'kLightSpikeLoAbs_Pa'])),
    ('NO_IGNITION', ('no light within W from the lift by the relative rule: filtered AND raw rise over P0 at least {kIgnRise_Pa} with '
                     'filtered AND raw Pc at least the floor {kIgnFloorAbs_Pa} abs for {kIgnConfirmRelN} consecutive ticks; W = '
                     '{kIgnWindowFirst_s} flight first start, {kIgnWindowRelightLong_s} flight relight, {kIgnWindowFirstStand_s} stand. '
                     'Also the fault bit of TORCH_FAULT and TORCH_LOST', ['kIgnRise_Pa', 'kIgnFloorAbs_Pa', 'kIgnConfirmRelN',
                                                                        'kIgnWindowFirst_s', 'kIgnWindowRelightLong_s', 'kIgnWindowFirstStand_s'])),
    ('FLAMEOUT', ('RUN, Pc valid: A3 ratio (Pc - P0)/(Pc_map_lo - P0) below {kFlameoutRel} for {kFlameoutTime_s} (Pc_map lagged by '
                  '{kFlameoutMapTau_s}). RUN, Pc invalid: FLAMEOUT_OPT, photodiode dark for {kPhotoFlameoutTime_s} once the main-chamber '
                  'view was proven ({kPhotoViewProveN} lit ticks after the torch closed). The legacy gauge rule ({kFlameoutPc_Pa}, '
                  '{kFlameoutFrac}) is not used', ['kFlameoutRel', 'kFlameoutTime_s', 'kFlameoutMapTau_s', 'kPhotoFlameoutTime_s',
                                                    'kPhotoViewProveN', 'kFlameoutPc_Pa', 'kFlameoutFrac'])),
    ('PC_BAND', ('RUN after {kRunSettle_s}: |Pc - Pc_ref| above {kPcBandFrac} of Pc_ref and above {kPcBandMin_Pa} for {kPcBandTime_s}',
                 ['kRunSettle_s', 'kPcBandFrac', 'kPcBandMin_Pa', 'kPcBandTime_s'])),
    ('OVER_TEMP', ('case TC above {kCaseOverTemp_K} or nozzle holder above {kNozzleHolderOverTemp_K} for {kOverTempTime_s} in a burn, '
                   'PREPRESS or PURGE; ARM refused unless BOTH case TCs are valid (RE-08); one TC lost: continue on the other; both lost: '
                   'stand treated hot, flight burn continues and the relight is refused (CASE_HOT). Servo-bracket NTC above '
                   '{kServoBracketOverTemp_K} only flags', ['kCaseOverTemp_K', 'kNozzleHolderOverTemp_K', 'kOverTempTime_s',
                                                           'kServoBracketOverTemp_K'])),
    ('TANK_OVERPRESSURE', ('P_tank above {kTankOverPressure_Pa} for {kTankOverPressureTime_s} in ARMED or PREPRESS (never aborts a burn)',
                           ['kTankOverPressure_Pa', 'kTankOverPressureTime_s'])),
    ('GIMBAL_FAULT', ('command-model vs encoder mismatch above {kGimbalFaultErr_rad} for {kGimbalFaultTime_s} while burning; the allowance '
                      'grows by {kGimbalFaultRateWin_s} times the model rate. Detection bound on the as-built linkage: see '
                      'sil_fail_dispositions (RE-24)', ['kGimbalFaultErr_rad', 'kGimbalFaultTime_s', 'kGimbalFaultRateWin_s'])),
    ('PINTLE_FAULT', ('pintle rail below {kPrailLost_V} for {kPrailLostTime_s} (LTC4365 trip or regulator failure); jam: no progress for '
                      '{kPintleStallTime_s} (time path) or {kPintleStallTimeI_s} (current path); encoder invalid at ARM; needle off seat '
                      'or encoder invalid during a purge on the stand', ['kPrailLost_V', 'kPrailLostTime_s', 'kPintleStallTime_s',
                                                                        'kPintleStallTimeI_s'])),
    ('LINK_LOST', ('no valid CMD_FAST: degraded after {kLinkDegraded_s}, lost after {kLinkLost_s}; SAFE/ARMED/PREPRESS -> SAFE, RUN -> '
                   'SHUTDOWN by default (link policy)', ['kLinkDegraded_s', 'kLinkLost_s'])),
    ('PREPRESS_FAIL', ('feed not primed (P_feed above {kFeedPrimedFrac} of P_tank) within {kPrepressTimeout_s}, or the NC valve OPEN '
                       'switch missing', ['kFeedPrimedFrac', 'kPrepressTimeout_s'])),
    ('PC_SENSOR', ('transducer output outside {kPcSensorMin_V} to {kPcSensorMax_V}: IGNITION abort (low side), stand RUN abort after '
                   '{kPcSensorLossStand_s}, flight RUN continues open loop; A7 plausibility band outside for {kA7Time_s} (HOLD band low edge '
                   'P0 minus {kA7HoldLow_Pa}; START high side blanked for {kA7StartHiBlank_s} after E2): IGNITION and stand abort, flight RUN '
                   'flag once per burn; RE-02 baseline above the auto-zero ambient by more than {kIgnBaseCheck_Pa} (BASE_HIGH): pad first '
                   'start and stand refuse the lift; ARM: |Pc| above {kPcArmZeroMax_Pa} before the auto-zero',
                   ['kPcSensorMin_V', 'kPcSensorMax_V', 'kPcSensorLossStand_s', 'kA7Time_s', 'kA7HoldLow_Pa', 'kA7StartHiBlank_s',
                    'kIgnBaseCheck_Pa', 'kPcArmZeroMax_Pa'])),
    ('BATT_LOW', ('VBAT below {kBattLow_V} for {kBattLowTime_s} in pad states before the first start (flag in flight); ARM refused below '
                  '{kBattArmMin_V} rest voltage', ['kBattLow_V', 'kBattLowTime_s', 'kBattArmMin_V'])),
    ('MV_FAULT', ('NC valve CLOSED switch missing at ARM, ladder OPEN+CLOSED or short (RE-19); direct relight OPEN switch missing by '
                  '{kMvOpenBy_s} from E0: stand abort, flight flag; CLOSED expected within {kMvCloseConfirm_s} of the latch drop (flag)',
                  ['kMvOpenBy_s', 'kMvCloseConfirm_s'])),
    ('ARM_LOST', ('arming plug removed, or ARM bus not on after the request', [])),
    ('WATCHDOG', ('hardware watchdog timeout {kHwWatchdog_s}: reboot lands in SAFE, MV and bleed closed, RUN never reported after the reset '
                  '(no in-flight recovery path, see decision); a lit-session marker becomes a relight lockout', ['kHwWatchdog_s'])),
    ('PC_OVERPRESSURE', ('outside the ignition phase: filtered absolute Pc above {kPcOverPressureAbs_Pa} for {kPcOverPressureTime_s}',
                         ['kPcOverPressureAbs_Pa', 'kPcOverPressureTime_s'])),
    ('HW_OVERPRESSURE', ('hardware comparator latch on the 070BG (OVP_OK low): ARM bus already off in hardware; firmware reports after '
                         '{kHwOvpTime_s}', ['kHwOvpTime_s'])),
    ('TVC_SUPPLY', ('pad only: predicted both-stall TVC plug voltage below {kTvcSupplyMin_V} for {kTvcSupplyTime_s}',
                    ['kTvcSupplyMin_V', 'kTvcSupplyTime_s'])),
    ('OVERCURRENT', ('firmware e-fuse before the first start: battery current above {kEfuse_A} for {kEfuseTime_s}', ['kEfuse_A', 'kEfuseTime_s'])),
    ('MAINT_JAM', ('ARM refused: a pintle jam recorded in NV memory and not cleared (CLEAR_JAM, bearing A rule)', [])),
    ('TORCH_FAULT', ('torch not confirmed by {kTorchGate_s} from E0: P_torch above {kTorchLitAbs_Pa} abs AND photodiode lit (2oo2, FA-1) '
                     'for {kTorchConfirmN} ticks with the main chamber below {kTorchGateMaxPcG_Pa} gauge; abort before the pintle step',
                     ['kTorchGate_s', 'kTorchLitAbs_Pa', 'kTorchConfirmN', 'kTorchGateMaxPcG_Pa'])),
    ('RELIGHT_LOCKOUT', ('ARM, IGNITE and RELIGHT refused after an abort following a lit burn or on a relight, until CLEAR_LOCKOUT (ground); '
                         'after a ground no-light CLEAR_LOCKOUT is refused for {kNoLightSafingMin_s} (safing hold, see decision)',
                         ['kNoLightSafingMin_s'])),
    ('OVER_THRUST', ('flight RUN: FC_THRUST above {kOverThrust_N} on {kOverThrustFrames} consecutive fresh valid frames (rate '
                     '{kFcThrustRate_Hz}, stale after {kFcThrustStale_s}); never on the stand', ['kOverThrust_N', 'kOverThrustFrames',
                                                                                                 'kFcThrustRate_Hz', 'kFcThrustStale_s'])),
    ('MODE_MISMATCH', ('ARM refused: mode strap invalid, or strap and load-cell reading disagree', [])),
    ('BAY_HOT', ('ARM refused: bay temperature above {kBayArmMax_K} or no valid reading', ['kBayArmMax_K'])),
    ('TANK_HOT', ('ARM refused: tank wall above {kTankIgnMaxWall_K} (limit {kTankIgnMax_K} minus the wall-channel uncertainty '
                  '{kTankWallUnc_K}), or Tsat(P_tank) above the limit with P_tank above {kTankIgnMaxP_Pa} abs uncalibrated / '
                  '{kTankIgnMaxPCal_Pa} abs after B-PT-1 (guard band, see decision), or no valid tank temperature',
                  ['kTankIgnMaxWall_K', 'kTankIgnMax_K', 'kTankWallUnc_K', 'kTankIgnMaxP_Pa', 'kTankIgnMaxPCal_Pa'])),
    ('BLEED_FAULT', ('head-end bleed: pad BIT step failed (any mode); STAND: closure not confirmed, purge path not proven, or P_mid high '
                     'with both valves commanded closed for {kHbleedLeakTime_s}. FLIGHT: an unconfirmed closure is a FLAG to the FC and '
                     'the relight proceeds (closure step bound {kHbleedCloseConfirm_s}; deadline {kTorchGate_s} from E0)',
                     ['kHbleedLeakTime_s', 'kHbleedCloseConfirm_s', 'kTorchGate_s'])),
    ('TORCH_LOST', ('torch confirmed (E1, 2oo2) but BOTH flame sensors dark for {kTorchLossTime_s} before E2: pintle and NC valve close',
                    ['kTorchLossTime_s'])),
    ('TANK_COLD', ('tank below {kTankIgnMin_K} or no valid tank temperature at ARM (pad first start, stand starts); a flight relight is '
                   'flagged only (RE-17)', ['kTankIgnMin_K'])),
])


# Lead decisions behind a cause: cited from the CHANGELOG line (marker checked), kept OUT of the trigger text so that the
# trigger holds only quoted constants.
AB_REF = OrderedDict([('WATCHDOG', (166, '(8) RE-28')), ('RELIGHT_LOCKOUT', (172, '(1) R2-02')), ('TANK_HOT', (172, '(4) R2-07')),
                      ('CMD', (181, '(4) Drogue release'))])


def render(template, C):
    def sub(m):
        ns, name = (m.group(1)[:-1] if m.group(1) else 'cfg'), m.group(2)
        return human(C(name, ns))
    return re.sub(r'\{(eng:|mech:)?(k\w+)\}', sub, template)


def template_check(cause, template, keys, C):
    errs = []
    ph = re.findall(r'\{(?:eng:|mech:)?(k\w+)\}', template)
    for k in ph:
        if not (C.has(k) or C.has(k, 'eng') or C.has(k, 'mech')):
            errs.append('%s: placeholder %s not in the config headers' % (cause, k))
    for k in keys:
        if k not in ph:
            errs.append('%s: listed constant %s not quoted in the trigger' % (cause, k))
    for k in ph:
        if k not in keys:
            errs.append('%s: quoted constant %s not listed in thresholds' % (cause, k))
    bare = re.sub(r'\{(?:eng:|mech:)?k\w+\}', ' ', template)
    for tok in re.findall(r'[A-Za-z0-9_.+-]*\d[A-Za-z0-9_.+-]*', bare):
        if not re.search(r'[A-Za-z]', tok):
            errs.append('%s: stand-alone number %r in the trigger text' % (cause, tok))
    return errs


STALE_STRINGS = ['FALLBACK only', 'NOT in gnc.json', 'OI-GNC-V3', 'F501": "3 A 1206 12 V boost', 'ECU v2.3 schematic',
                 'A5 8.0 bar abs for 5 ms', 'BLEED_FAULT at E0 + 0.15 s', 'sequence-integrated (RELIGHT)',
                 # v2.10 LEAD CHANGELOG 186: L* decided (1); TLM_RELIGHT d6 b6 = DROGUE (2); OI-37 hygiene (4)
                 '1.7 s interim, 1.3 s if', 'd6 & 0x7F', 'b0-b6 refuse reason', 'magic A5 5A', 'late-light hold A5', 'Burkert', '6027',
                 'pending the LEAD decision (OI-UNPURGED-RELIGHT)']
HISTORY_KEYS = ('change_summary_v2_to_v3', 'superseded_v2', 'oi37_interface_hygiene')   # excluded from the stale / A5 scans
A5_ALLOWED = 'Teensy analog pin A5'   # the only allowed stand-alone A5 token outside the history keys (a pin name, not the deleted monitor)




def hdr_status(r, gnc, gnc_sha):
    """v2.10: a gnc.json reference recorded 'current' by the manifest is re-checked against the hub file at this run."""
    if r['source'] == 'gnc.json' and r['status'].startswith('HISTORICAL (names'):
        return 'HISTORICAL (names %s; the hub file is now %s)' % (r.get('version_named'), gnc.get('version'))
    if r['source'] != 'gnc.json' or not r['status'].startswith('current') or r['sha_at_generation'] == gnc_sha:
        return r['status']
    chk = jload(os.path.join(RES, 'gnc_v31_read_keys_check_v2p10.json'))
    if chk['old']['sha256_16'] != r['sha_at_generation'] or chk['new']['sha256_16'] != gnc_sha:
        raise SystemExit('gnc.json changed again: re-run calc/v2p10/gnc_v31_read_keys_check.py for %s -> %s' % (r['sha_at_generation'], gnc_sha))
    n = sum(len(v['changed_numeric']) + len(v['removed']) for v in chk['by_subtree'].values())
    return ('HISTORICAL since CHANGELOG 192 (names %s; the hub file is now %s %s); %s numeric leaf changed or removed under the subtrees '
            'the generators read (results/gnc_v31_read_keys_check_v2p10.json, DERIVED)' % (r.get('version_named'), gnc.get('version'), gnc_sha,
                                                                                        'no' if n == 0 else str(n)))

def gnc_purge_request(gnc, bd):
    """v2.10 (gnc.json v3.1, CHANGELOG 192): GNC's purge bound names 2.5 s as the ECU duration cap; the ECU cap is longer."""
    pb = gnc.get('flight_software', {}).get('relight_sequence_placeholder', {}).get('v', {}).get('purge_bound', {})
    rows = OrderedDict((r['case'], r) for r in bd['purge_mass']['rows'])
    nom, cap, hw = rows['nominal 2.5 s flow'], rows['firmware cap (both open 2.61 s)'], rows['hardware window bound (both open t_max)']
    if 'ecu_cap_mass_kg_rev2' not in pb:
        return ('GNC: purge bound check skipped (gnc.json %s has no flight_software.relight_sequence_placeholder.v.purge_bound.'
                'ecu_cap_mass_kg_rev2)' % gnc.get('version'))
    return ('GNC (gnc.json %s): flight_software.relight_sequence_placeholder.v.purge_bound.ecu_cap_mass_kg_rev2 = %.3f kg is described as '
            'the mass "at the 2.5 s ECU duration cap"; 2.5 s is the scheduled FLOW (%.1f g vented, Combustion basis). The ECU both-open cap '
            'is kHbleedCap_s 2.61 s (%.1f g Combustion basis, %.1f g SIL basis: above 76 g, OI-PURGE-CAP) and the hardware window bounds '
            'about %.0f g. Use the flow for a nominal and the cap or the window for a bound'
            % (gnc.get('version'), pb['ecu_cap_mass_kg_rev2'], nom['mass_comb_basis_g'], cap['mass_comb_basis_g'], cap['mass_sil_basis_g'],
               hw['mass_comb_basis_g']))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/home/claude/work/shared-fallback/engine')
    ap.add_argument('--v1', default=os.path.join(RES, 'electronics_v1.json'), help='archived electronics.json v1 (base keys and v1 names)')
    ap.add_argument('--prev', default=None, help='electronics.json v2 being superseded (default: <engine-root>/interfaces/electronics.json)')
    ap.add_argument('--out', default=os.path.join(RES, 'electronics_v3.json'))
    a = ap.parse_args()
    ENG = a.engine_root
    C = Cfg()
    CL = Changelog(os.path.join(ENG, 'interfaces', 'CHANGELOG.md'))
    v1 = jload(a.v1)
    if v1.get('version') != 'v1':
        raise SystemExit('--v1 is not electronics.json v1 (%s)' % v1.get('version'))
    prev_path = a.prev or os.path.join(ENG, 'interfaces', 'electronics.json')
    prev = jload(prev_path)
    if prev.get('version') != 'v2':
        raise SystemExit('--prev is not electronics.json v2 (%s): v3 supersedes v2' % prev.get('version'))
    prev_sha = READ[os.path.relpath(prev_path, ROOT) if prev_path.startswith(ROOT) else prev_path]
    v1_sha = READ[os.path.relpath(a.v1, ROOT) if a.v1.startswith(ROOT) else a.v1]
    gnc_path = os.path.join(ENG, 'interfaces', 'gnc.json')
    gnc = jload(gnc_path)
    gnc_sha = READ[gnc_path]
    mech_path = os.path.join(ENG, 'interfaces', 'mechanical.json')
    mech = jload(mech_path)
    comb_path = os.path.join(ENG, 'interfaces', 'combustion.json')
    comb = jload(comb_path)
    # combustion v2.4a purge_commit_rule_v2p4a: unpurged branch REFUTED as written (finding + source file, hash cross-checked)
    pcr = comb.get('purge_commit_rule_v2p4a', {}).get('v', {})
    usc_path = os.path.join(ENG, '02-combustion', 'data', 'v2p4a', 'unpurged_start_check_v2p4a.json')
    usc = jload(usc_path)
    usc_sha = READ[os.path.relpath(usc_path, ROOT) if usc_path.startswith(ROOT) else usc_path]
    if usc_sha not in pcr.get('file', ''):
        raise SystemExit('combustion purge_commit_rule_v2p4a.file %r does not name unpurged_start_check_v2p4a.json %s' % (pcr.get('file'), usc_sha))
    m_rel = re.search(r'A3 abort after the release in (0\.\d+) of starts', pcr.get('finding', ''))
    if not (pcr.get('finding', '').startswith('REFUTED as written') and m_rel):
        raise SystemExit('combustion purge_commit_rule_v2p4a.finding changed - review OI-UNPURGED-RELIGHT text before publishing')
    unp = OrderedDict([('released_then_A3_unlined_LO_worst', float(m_rel.group(1))),
                       ('released_then_A3_lined_LO_worst', pcr.get('lined_LO_worst_P_released_then_A3')),
                       ('A3_ratio_max_in_gap', round(usc['partB_A3_ratio_in_gap']['A3_ratio_max'], 3)),
                       ('A3_threshold', usc['partB_A3_ratio_in_gap']['A3_threshold'])])
    ign = gnc['requirements']['ignition']
    rpv = ign['relight_planning_value_s']
    for k in ('option_c_unprimed_s', 'stale_or_missing_flag'):
        if k not in rpv:
            raise SystemExit('gnc.json requirements.ignition.relight_planning_value_s.%s missing' % k)

    # ---- versions (self-check: config.h stamp vs Makefile; schematic REV vs KiCad files)
    cfg_first = rd(os.path.join(CORE, 'config.h')).split('\n', 1)[0]
    m = re.match(r'// \[(v[0-9][0-9.]*) ', cfg_first)
    if not m:
        raise SystemExit('config.h first line carries no [vX.Y] stamp')
    fw_ver = m.group(1)
    mk_first = rd(os.path.join(FWD, 'Makefile')).split('\n', 1)[0]
    if (' %s ' % fw_ver) not in mk_first:
        raise SystemExit('Makefile header does not name %s' % fw_ver)
    rev = re.search(r"^REV = '(v[0-9.]+)'", rd(os.path.join(KGEN, 'make_ecu_kicad.py')), re.M).group(1)
    sch = rd(os.path.join(KICAD, 'argos_ecu.kicad_sch'))
    if ('rev "%s"' % rev) not in sch:
        raise SystemExit('KiCad root sheet rev is not %s' % rev)
    pin_map_name = 'pin_map_%s.csv' % rev.replace('.', 'p')
    pins = list(csv.DictReader(rd(os.path.join(KICAD, pin_map_name)).splitlines()))
    if any(p['ecu_rev'] != rev for p in pins):
        raise SystemExit('pin map rows carry another revision than %s' % rev)
    xc = rd(os.path.join(KICAD, 'erc', 'netlist_crosscheck.txt'))
    erc = rd(os.path.join(KICAD, 'erc', 'argos_ecu_erc.rpt'))
    xm = re.search(r'components (\d+), nets (\d+) .*pins (\d+) of (\d+) intended\s*\nerrors (\d+), warnings (\d+)', xc)
    em = re.search(r'ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)', erc)
    erc_time = re.search(r'ERC report \(([^,]+),', erc).group(1)
    sheets = re.findall(r'\*\*\*\*\* Sheet (\S+)', erc)

    # ---- firmware record (SIL v2.10)
    man = jload(os.path.join(SIL, 'MANIFEST_v1.json'))
    if man.get('firmware_version') != fw_ver:
        raise SystemExit('SIL manifest firmware_version %s != %s' % (man.get('firmware_version'), fw_ver))
    bins = man.get('binaries') or {}
    if not bins or not all(b.get('rebuild_of_current_tree', {}).get('identical') for b in bins.values()):
        raise SystemExit('SIL manifest lacks binaries or a binary does not match the rebuild of the current tree')
    s5 = jload(os.path.join(SIL, 'S5_mc.json'))
    s5_rows = list(csv.DictReader(rd(os.path.join(SIL, 'S5_mc.csv')).splitlines()))
    s6 = jload(os.path.join(SIL, 'S6_aborts.json'))
    s8 = jload(os.path.join(SIL, 'S8_priming.json'))
    s9 = jload(os.path.join(SIL, 'S9_pc_transducer.json'))
    s10 = jload(os.path.join(SIL, 'S10_relight_v2p8.json'))
    s12 = jload(os.path.join(SIL, 'S12_bleed.json'))
    s13 = jload(os.path.join(SIL, 'S13', 'S13_ignition_rule.json'))
    s13f = jload(os.path.join(SIL, 'S13', 'S13B_ext_bpc1_false.json'))
    s13t = jload(os.path.join(SIL, 'S13', 'S13B_ext_bpc1_true.json'))
    s14 = jload(os.path.join(SIL, 'S14', 'S14_v2p10.json'))
    s15 = jload(os.path.join(SIL, 'S15', 'S15_start_mc.json'))
    s16 = jload(os.path.join(SIL, 'S16', 'S16_coast206.json'))
    s17 = jload(os.path.join(SIL, 'S17', 'S17_r2hold.json'))   # v2.10 LEAD 186 (2) R2 command hold
    fa1 = jload(os.path.join(RES, 'fa1_overrange_v2p10.json'))   # LEAD 194 (7): 070BG over-range at the FA-1 relight peaks
    fa1_env_path = os.path.join(ENG, '02-combustion', 'data', 'v2p4a', 'fa1_envelope_v2p4a.json')
    rd(fa1_env_path, 'rb')
    if fa1['inputs']['fa1_envelope']['sha256_16'] != READ[fa1_env_path]:
        raise SystemExit('fa1_envelope_v2p4a.json changed since results/fa1_overrange_v2p10.json - re-run calc/v2p10/fa1_overrange.py')
    tc_log = rd(os.path.join(SIL, 'test_core_log.txt'))
    pf = jload(os.path.join(SIL, 'probeF', 'S5_probeF.json'))
    fp4 = jload(os.path.join(RES, 'fault_path_v4.json'))
    bd = jload(os.path.join(RES, 'bleed_driver_v1.json'))
    rg = jload(os.path.join(RES, 'gen_headers_regen_check_v2p10.json'))   # calc/v2p10/gen_headers_regen_check.py
    hbp = jload(os.path.join(RES, 'hbleed_provision_v1.json'))
    bom = jload(os.path.join(RES, 'bom_v2p2.json'))['summary']
    ot3 = jload(os.path.join(RES, 'over_thrust_v3.json'))
    rmap_path = os.path.join(RES, 'pintle_rate_map_v1.json')
    rmap = jload(rmap_path)
    eng03 = jload(os.path.join(RES, 'eng03_slew_check_v1.json'))
    rail = jload(os.path.join(RES, 'pintle_rail_v3.json'))
    ecuv = jload(os.path.join(RES, 'ecu_v2p3_values_v1.json'))
    pct = jload(os.path.join(RES, 'pc_transducer_v2.json'))
    latch = jload(os.path.join(RES, 'mv_latch_magnet_v1.json'))
    sup = jload(os.path.join(RES, 'tvc_supply_budget_v1.json'))
    servo = jload(os.path.join(RES, 'pintle_mini_servo_v1.json'))
    hv69 = [c for c in servo['candidates'] if c.get('id') == 'MKS HV69'][0]
    proto = rd(os.path.join(CORE, 'protocol.h'))
    types_h = rd(os.path.join(CORE, 'types.h'))

    ids = OrderedDict((mm.group(1), int(mm.group(2), 16)) for mm in re.finditer(r'ID_(\w+)\s*=\s*(0x[0-9A-Fa-f]+)', proto))
    ev_block = proto.split('namespace evt')[1].split('namespace tlmg')[0]
    events = OrderedDict((mm.group(1), mm.group(2)) for mm in re.finditer(r'constexpr uint8_t (\w+) = (0x[0-9A-Fa-f]+);', ev_block))
    tlmr = OrderedDict((mm.group(1), mm.group(2)) for mm in re.finditer(r'constexpr uint8_t (\w+) = (1u << \d|PRIMED);',
                                                                         proto.split('namespace tlmr {')[1].split('}')[0]))
    refuse = OrderedDict((mm.group(1), int(mm.group(2))) for mm in re.finditer(r'\b([A-Z_0-9]+) = (\d+)', types_h.split('namespace refuse')[1].split('}')[0]))
    abort_enum = OrderedDict((mm.group(1), int(mm.group(2))) for mm in re.finditer(r'\b([A-Z_]+) = (\d+)\b', types_h.split('enum class Abort')[1].split('};')[0]))
    s5_causes = OrderedDict()
    for r in s5_rows:
        s5_causes[r['abort']] = s5_causes.get(r['abort'], 0) + 1
    code2name = {v: k for k, v in abort_enum.items()}
    s5_causes_named = OrderedDict((code2name.get(int(k), k) if k.isdigit() else k, v) for k, v in s5_causes.items())

    # ================================================================================================ document
    doc = OrderedDict()
    doc['id'] = 'electronics'
    doc['version'] = 'v3'
    doc['date'] = DATE
    doc['owner'] = 'electronics (06-electronics)'
    doc['status'] = ('DESIGN + SIL + schematic. Firmware %s runs only in SIL (no HAL); the ECU %s schematic passes ERC and a netlist '
                     'cross-check (self-consistency only); no board has been built and nothing here is hardware-validated. Values carry '
                     'tags; open items are listed in open_issues and closed by the bench plan (06-electronics/docs/bench_plan_v3.md).'
                     % (fw_ver, rev))
    doc['units'] = v1['units']
    doc['supersedes'] = OrderedDict([('file', 'electronics.json v2 (2026-10-13, firmware v2.9)'), ('sha256_16', prev_sha),
                                     ('archive', '06-electronics/archive/v2.9/interfaces/electronics_v2.json'),
                                     ('v1', OrderedDict([('sha256_16', v1_sha), ('archive', '06-electronics/results/electronics_v1.json')]))])
    doc['scripts'] = ['06-electronics/calc/make_interface_json_v3.py (this file; v2 generator kept for provenance)',
                      '06-electronics/calc/bom_v2.py', '06-electronics/calc/bleed_driver_v1.py', '06-electronics/calc/fault_path_v4.py',
                      '06-electronics/calc/hbleed_provision_v1.py', '06-electronics/calc/ecu_v2p3_values_v1.py',
                      '06-electronics/calc/pintle_rail_v3.py', '06-electronics/calc/over_thrust_v3.py', '06-electronics/calc/pintle_rate_map_v1.py',
                      '06-electronics/firmware/tools/sil_manifest_v1.py (v1.3)', '06-electronics/calc/v2p10/gnc_v31_read_keys_check.py',
                      '06-electronics/calc/v2p10/fa1_overrange.py + fa1_overrange_chain.cpp', '06-electronics/hardware/kicad_gen/run_all.sh']
    doc['inputs'] = OrderedDict([
        ('gnc.json', '%s %s' % (gnc.get('version'), gnc_sha)), ('mechanical.json', '%s %s' % (mech.get('version'), READ[mech_path])),
        ('combustion.json', '%s %s' % (comb.get('version'), READ[comb_path])),
        ('firmware', '%s (SIL record %s, source tree %s)' % (fw_ver, man['record_sha256_16'], man['tree_sha256'][:16])),
        ('generated_headers', OrderedDict((k, [(r['source'], r.get('version_named') or '(not named in the header)', r['sha_at_generation'],
                                                hdr_status(r, gnc, gnc_sha))
                                               for r in v['refs']]) for k, v in man['generated_headers'].items())),
        ('generated_headers_note', 'status as recorded by the SIL manifest, except gnc.json references re-checked against the hub file at '
                                   'this run (gnc.json v3.1 was published after the SIL record, CHANGELOG 192)')])

    # ---------------------------------------------------------------------------------------------------- what changed
    doc['change_summary_v2_to_v3'] = [
        'firmware v2.9 -> %s (REV-ELEC-1 RE-01..RE-25 actions, LEAD CHANGELOG 164, 166, 168, 172, 175): A5 deleted (LIGHT_SPIKE log), '
        '30 bar abort on the filtered channel with 5 ms persistence, one-sided light-rule fallback (BASE_HIGH), b7 on the filtered channel, '
        'lift clamp (RE-04), bleed schedule on flow time with a closure step and cap, FA-1 photodiode 2oo2 + TORCH_LOST + FLAMEOUT_OPT, '
        'second re-zero, case-TC policy, tank 15 C lower bound, interlock guard band, ground safing hold, unpurged RELIGHT, PC_VALID bit, '
        'encoder lift in TLM_FAST' % fw_ver,
        'schematic v2.4 -> %s: hardware purge window (J512 PURGE_EN AND LTC6993-1 one-shot into both bleed drives), FA-1 photodiode on '
        'ADC2 CH3 (J902)' % rev,
        'BOM v2.1 -> v2.2 (bench equipment, bleed plumbing, O2-clean notes, item 208 replaced by a specification row, GSE anemometer)',
        'bench plan v2 -> v3 (criteria per test; B-PT-1, B-DPC-1, B-SAFE-1, CHK-PW, HAL-1, HIL-RST-1)',
        'abort matrix: 30 causes (v2: 28; + TORCH_LOST 29, TANK_COLD 30), triggers rendered from config.h with a self-check (RE-16)',
        'GNC N5: actuators.tvc_A/tvc_B carry the v1 fields dynamics_for_GNC, engine_side_at_n7_7V4 and hinge_moment_assumed_Nm again',
        'LEAD CHANGELOG 181 (REV-GNC-3) folded: R2 ADOPTED in design with pcf_tmax 0.5 s (pcf_tmax, threshold and baseline reference are FC '
        'parameters) and the ECU side of the R2 ABORT checked in test_core (v210-16); PURGE commit rule with L* (FC parameter; 181 (2) '
        'interim 1.7 s, replaced by 1.3 s in line 186 (1)); FC_THRUST not armed on A1 and the ECU detector structure stated for the RG-16 '
        'budget; A1 FMEA row (no over-thrust detector after an in-flight Pc loss); A1 pad go/no-go list (HARD wind rule, Pc VALID, bleed '
        'closure); purge masses labelled VENTED N2O (tank liquid depletion 81.6 g)',
        'LEAD CHANGELOG 186 folded: (1) L* = 1.3 s for both brackets; below L* no purge and no unpurged relight on that pass (FC rule; the '
        'ECU still accepts an unpurged RELIGHT, then kept for GNC\'s held-release alternative, withdrawn by 194 (3)); (2) R2 command hold implemented: Cmd::DROGUE (17) '
        'carries the FC drogue state, flight RUN with the drogue attached and Pc invalid holds the open-loop command at kR2HoldThrust_N, '
        'return at <= kStartRamp_Nps after the release; TLM_RELIGHT d6 b6 echo (refuse reason now b0-b5); log tlm_flags b0/b1; test_core '
        '(v210-17); SIL S17 with an in-loop FC stand-in (R2) and the Combustion v2.4a cold-flow bound; (4) OI-37 interface hygiene '
        '(oi37_interface_hygiene): A5 and the rejected bleed valve removed, the v2.9 2.0 s hold checked against the decided sequence',
        'LEAD CHANGELOG 194 folded (no firmware change): (3) the E2 + 0.22 s held-release alternative WITHDRAWN (a GNC comparator only; not '
        'admissible with Pc invalid): unpurged-relight texts and OI-UNPURGED-RELIGHT; (4) the R2 hold margin CONDITIONAL on Cd x A x G at '
        'the start lift, CF-3 start-lift point, heat TO-VERIFY moved to injector-body / feed soak-back: r2_command_hold, OI-38, requests, '
        'bench plan; (7) 070BG over-range at the FA-1 peaks and the stand dynamic channel >= 100 bar abs: pc_overrange_fa1 (new), '
        'OI-FA1-PC-OVERRANGE, sensors.stand_dynamic_pc, BOM 237 / 238 / 245; (1) FA-1 period domain: Pc port, sense line and bleed '
        'valves noted (pc_overrange_fa1.period_domain, BOM 218)']
    doc['superseded_v2'] = [
        OrderedDict([('key', 'relight_interface.fc_planning_from_gnc'), ('v2', 'option_c_unprimed_s / stale_or_missing_flag "NOT in gnc.json v3"'),
                     ('v3', 'read at gnc.json requirements.ignition.relight_planning_value_s.* (the v2 generator read one level too high; RE-16)')]),
        OrderedDict([('key', 'open_issues OI-GNC-V3'), ('v2', 'gnc.json v3 lacks the planning keys'), ('v3', 'WITHDRAWN: the keys exist (same generator error)')]),
        OrderedDict([('key', 'relight_interface.head_end_bleed'), ('v2', 'FALLBACK only, 0.75 A / 9 W budget line'),
                     ('v3', 'drawn provision (schematic v2.4) with the hardware purge window (v2.5); firmware v2.10 purge; see head_end_bleed_provision')]),
        OrderedDict([('key', 'abort_matrix HARD_START / FLAMEOUT / PC_SENSOR'), ('v2', '30 bar trip only / legacy 1.5 bar, 0.35 rule / voltage window only'),
                     ('v3', 'templates from config.h: HARD_START with the filtered 30 bar and over-range terms; FLAMEOUT = A3 + FLAMEOUT_OPT; '
                            'PC_SENSOR = window + A7 + BASE_HIGH lift refusal + ARM zero check')]),
        OrderedDict([('key', 'power_budget.fusing.F501'), ('v2', '3 A 1206 12 V boost'),
                     ('v3', '3 A 1206 VBAT vent-branch fuse (ecu_design.py F501); the 12 V boost sits on ARM_BUS behind F301')]),
        OrderedDict([('key', 'ecu.schematic.version'), ('v2', 'status text "ECU v2.3 schematic" while the delivery was v2.4'), ('v3', rev)]),
        OrderedDict([('key', 'start_monitors.A5'), ('v2', 'A5 8.0 bar abs, 5 ms, abort'),
                     ('v3', 'deleted as an abort; LIGHT_SPIKE record (RE-01) under start_monitors.light_spike_record (key renamed, LEAD 186 (4))')]),
        OrderedDict([('key', 'head_end_bleed_provision.coil.valve / OI-BLEED-COIL'), ('v2', 'bleed valve named (orifice 1.0 mm), 24 V coil issue'),
                     ('v3', 'no valve named: rejected (LEAD 160 (6), 186 (4)); specification row in the BOM, OI-BLEED-VALVE')]),
        OrderedDict([('key', 'head_end_bleed_provision.schedule.post_flow_hold_max'), ('v2', '2.0 s with the bleed valves OPEN (v2.9)'),
                     ('v3', '0.50 s with the bleed CLOSED, from the scheduled E0 (see oi37_interface_hygiene.hold_2s)')]),
        OrderedDict([('key', 'can_interface TLM_RELIGHT d6'), ('v2', 'refuse reason (whole byte)'),
                     ('v3', 'b0-b5 refuse reason, b6 DROGUE echo (LEAD 186 (2)), b7 PC_VALID (LEAD 175 (4)); decoders mask d6 & 0x3F '
                            '(an earlier v2.10 draft, not published, used b0-b6 and 0x7F)')]),
        OrderedDict([('key', 'light_rule BASE_AMB'), ('v2', '|P0| > check -> ambient'), ('v3', 'one-sided (LEAD 166 (1)): high side keeps P0 + BASE_HIGH; low side P0 := 0')]),
        OrderedDict([('key', 'drogue_release_support b5-b7'), ('v2', 'b7 from the filtered AND raw rise'), ('v3', 'b6/b7 from the VALID filtered channel only (RE-03); E2 keeps both')]),
        OrderedDict([('key', 'actuators.tvc_A/B v1 fields'), ('v2', 'removed as superseded'), ('v3', 'restored with the v1 names and values (GNC N5), status noted')]),
    ]

    # ---------------------------------------------------------------------------------------------------- firmware + SIL record
    s13_classes = lambda d: OrderedDict((c['class'], c['runs']) for c in d['classes'])
    doc['firmware'] = OrderedDict([
        ('version', fw_ver),
        ('target', 'PJRC Teensy 4.1 (i.MX RT1062). HAL NOT written (RE-06; LEAD 166 (9): Electronics open item, required before B-PC-1). '
                   'The core runs in SIL and test_core only'),
        ('record', OrderedDict([('manifest', '06-electronics/results/sil_v2p10/MANIFEST_v1.json'), ('record_sha256_16', man['record_sha256_16']),
                                ('tree_sha256_16', man['tree_sha256'][:16]), ('n_files', man['n_files']),
                                ('binaries', OrderedDict((k, OrderedDict([('sha256_16', b['sha256_16']),
                                                                          ('rebuild_of_current_tree_identical', b['rebuild_of_current_tree']['identical'])]))
                                                         for k, b in bins.items())),
                                ('scenarios', [OrderedDict([('id', s['id']), ('binary_sha256_16', s['binary_sha256_16']), ('files', s['n_files'])])
                                               for s in man.get('scenarios') or []]),
                                ('unmapped_results', len(man.get('results_unmapped') or []))])),
        ('unit_tests', man['test_core']['summary']),
        ('arm_build', 'make arm (arm-none-eabi-g++, Cortex-M7 FPU ABI) compiles the core: compile and size check only; 93 -Wdouble-promotion '
                      'warnings, all in engine_ecu.cpp (v2.9: 53); text engine_ecu.o 29614 B (control.o 5538, protocol.o 3528, sensor_scale.o 636)'),
        ('sil_record_v2p10', OrderedDict([
            ('S5_pad_mc', OrderedDict([('runs', s5['runs']), ('aborts', s5['aborts']), ('abort_causes', s5_causes_named),
                                       ('interlock_refused_at_arm', s5.get('interlock_refused_at_arm')),
                                       ('plant_Pc_max_bar_abs', round(s5['pc_max_abs_max_Pa'] / 1e5, 3)), ('pc_overpressure_aborts', s5['ovp_aborts']),
                                       ('eng03_req_150ms_frac_of_armed', s5.get('pass_eng03_req_150ms_frac_of_armed')),
                                       ('eng03_target_100ms_frac_of_armed', s5.get('pass_eng03_target_100ms_frac_of_armed')),
                                       ('up_rise_p50_p95_max_s', [s5['up_rise_p50_s'], s5['up_rise_p95_s'], s5['up_rise_max_s']]),
                                       ('eng03_clause_map', s5.get('eng03_clause_map'))])),
            ('probeF_RE04', OrderedDict([('runs', len(pf['runs'])), ('worst_plant_Pc_bar_abs', pf['worst_plant_Pc_bar_abs']),
                                         ('pc_overpressure_aborts', pf['pc_overpressure_aborts']), ('aborts', pf['aborts']),
                                         ('abort_causes', [r['abort'] for r in pf['runs'] if r['abort'] != 'none']), ('pass', pf['pass'])])),
            ('S6_abort_paths', '%d/%d' % (s6['passed'], s6['total'])), ('S8_priming', '%d/%d' % (s8['passed'], s8['total'])),
            ('S10_relight', '%d/%d' % (s10['passed'], s10['total'])),
            ('S12_bleed', '%d/%d (mass above 76 g in %d cases)' % (sum(1 for c in s12['cases'] if c['pass']), len(s12['cases']), s12['mass_over_limit_cases'])),
            ('S13_light_rule', OrderedDict([('B_residual_corners', '%d cases, %d fail' % (s13['B_cases'], s13['B_fail'])),
                                            ('B_extension_kBpc1Shown_false', OrderedDict([('runs', s13f['runs']), ('lead_criteria_fail', s13f['lead_criteria_fail']),
                                                                                          ('classes', s13_classes(s13f))])),
                                            ('B_extension_kBpc1Shown_true', OrderedDict([('runs', s13t['runs']), ('lead_criteria_fail', s13t['lead_criteria_fail']),
                                                                                         ('classes', s13_classes(s13t))]))])),
            ('S14_pool_and_pc_invalid', OrderedDict([('cases', len(s14['cases'])), ('fail_count', s14['fail_count'])])),
            ('S15_start_mc', OrderedDict([('flight', s15['flight']), ('stand', s15['stand'])])),
            ('S16_coast_drift', [OrderedDict([('drift_bar', c['drift_bar']), ('stand', c['stand']), ('relight_refused', c['relight_refused']),
                                              ('first_abort', c['first_abort']), ('rezero2', c['f2_rezero2']), ('rezero2_rejected', c['f2_rezero2_rejected'])])
                                 for c in s16['cases']]),
            ('S17_r2_command_hold', OrderedDict([('cases', len(s17['cases'])), ('not_as_expected', s17['not_as_expected_count']),
                                                 ('noise_runs', sum(x['runs'] for x in s17['noise_sweep_flameout_200N_calm_5N_rms'])),
                                                 ('detail', 'r2_command_hold.sil_S17')])),
            ('fail_count', man.get('sil_fail_count_v13', len(man['sil_fail_lines'] or []))),
            ('fail_lines', man.get('sil_fail_lines_v13') or {'sil_run_log.txt': man['sil_fail_lines']}),
            ('fail_lines_note', 'manifest tool v1.3 status-token rule over every scenario log; v1.0-v1.2 kept only lines ending in FAIL and '
                                'listed %d of them (the S12 bleed table prints FAIL in a column)' % len(man['sil_fail_lines'] or []))])),
        ('W_build_constant', OrderedDict([
            ('flight_relight_W', C('kIgnWindowRelightLong_s')), ('flight_first_start_W', C('kIgnWindowFirst_s')),
            ('stand_R1_W', C('kIgnWindowFirstStand_s')), ('stand_R2_W', C('kIgnWindowRelightStand_s')),
            ('rule', 'compile-time constant; the SIL what-if SIL_WHATIF_RELIGHT_W #errors without ECU_SIL_TEST_HOOKS')])),
    ])

    # ---------------------------------------------------------------------------------------------------- SIL fail dispositions (record)
    doc['sil_fail_dispositions'] = [
        OrderedDict([('id', 'S6 gimbal_jam_moving_cmd'), ('disposition', 'DISPOSITIONED (RE-24, lead to accept)'),
                     ('why_fails', 'per-axis mismatch at a 2 deg command stays below the %s threshold; detection bound >= 3 deg per axis / 2.12 deg '
                                   'along a servo line' % human(C('kGimbalFaultErr_rad'))),
                     ('closure', 'B-TVC-1 measures the bound on the as-built linkage; travel-ratio detector = research proposal (hypothesis: '
                                 'servo-frame travel ratio flags a jam below the angle threshold; comparator: current rule; refuted if the '
                                 'B-TVC-1 false-alarm rate at the GNC command spectrum exceeds the lead limit)')]),
        OrderedDict([('id', 'S6 throat_blocked_70pct_500N_24C_Cd0p8'), ('disposition', 'ACCEPTED-WITH-REASON (unchanged)'),
                     ('why_fails', 'hardware comparator first and plant Pc 53.4 bar abs > MEOP for 72 ms before any detection can act'),
                     ('closure', 'Combustion fault load case LC-TB70 / LC-TB-S; the assembled FEA closes it (LEAD 166 (10))')]),
        OrderedDict([('id', 'S6 throat_blocked_70pct_500N_24C_Cd0p8_ballvalve_v2p7_compare'), ('disposition', 'OBSOLETE (comparison evidence)')]),
        OrderedDict([('id', 'S9 unlit_spike_train_20bar_2ms_50Hz'), ('disposition', 'CONFLICT kept (RE-02)'),
                     ('why_fails', 'v2.10: the spike train raises P0 above the check -> BASE_HIGH -> PC_SENSOR refusal at E1 on the pad (the '
                                   'scenario expects TORCH_FAULT); fail-safe, same decision as the S13 B extension pad classes')]),
        OrderedDict([('id', 'S9 unlit_bias_plus_1p034bar_TEB, lit_bias_plus/minus_1p034bar_TEB'), ('disposition', 'OPEN (as v2.9; OI-TEB-FALSE-LIGHT)'),
                     ('closure', 'B-PC-1 residual <= 0.3 bar, then kBpc1Shown')]),
        OrderedDict([('id', 'S12 stuck_open_after_lift d0.6/0.8/1.0 mm stand, stuck_open_first_burn d1.0 mm'), ('disposition', 'OPEN (detection gap, evidence)'),
                     ('why_fails', 'on the decided path P_mid with V1 stuck open and V2 closed stays below the comparator band -> no leak '
                                   'flag on the stand; the flight first-burn case raises the leak flag 5.05 s after injection (criterion < 0.5 s; 104 g through '
                                   'the bleed) [SIM results/sil_v2p10/S12_bleed.json]'),
                     ('closure', 'B-BLEED-1 P_mid during the purge and leak-monitor tests; comparator band or path change by the lead')]),
        OrderedDict([('id', 'S14 starved_A1_relight_reference_flight (INFO case)'), ('disposition', 'EVIDENCE'),
                     ('why_fails', 'reference starved plateau (cap stand-in 2.6 bar abs, lift-independent) -> A3 FLAMEOUT at E2 + 54 ms; the '
                                   'stand-in is pessimistic; not a v2.10 change')]),
        OrderedDict([('id', 'S13 B extension lead criteria'), ('disposition', 'CONFLICT kept (RE-02)'),
                     ('why_fails', 'the lead pass "every lit start reaches RUN" cannot hold where the same decision refuses the lift '
                                   '(BASE_HIGH on pad/stand) or where the torch gate blocks confirmation (A1 offsets >= +1.05 bar); '
                                   'kBpc1Shown stays false')]),
    ]

    # ---------------------------------------------------------------------------------------------------- CAN
    doc['can_interface'] = OrderedDict([
        ('physical', v1['can_interface']['physical']), ('bus', v1['can_interface']['bus']),
        ('e2e', tv('8-bit rolling sequence per ID + CRC-8 (SAE J1850 poly 0x1D, init 0xFF, final XOR 0xFF) over the preceding payload bytes; '
                   'CMD_STATE key = 0xA500 | (cmd XOR 0x5A); ABORT magic 0xA5 0x5A (no sequence check on ABORT)', 'DESIGN protocol.h')),
        ('ids_parsed_from_protocol_h', OrderedDict(('0x%03X' % v, k) for k, v in ids.items())),
        ('frames', OrderedDict([
            ('0x010 FC->ECU ABORT (event, sent 3x)', 'len 5: [0xA5][0x5A][abort code][seq][crc8]'),
            ('0x020 FC->ECU CMD_FAST 500 Hz', 'len 8: [seq][thrust setpoint u16 0.1 N][gimbal a i16 0.001 deg][gimbal b i16 0.001 deg][crc8]'),
            ('0x024 FC->ECU FC_THRUST >= 100 Hz', 'len 5: [seq][thrust estimate u16 0.1 N][flags b0 valid][crc8]'),
            ('0x028 FC->ECU CMD_AUX >= 50 Hz while wanted', 'len 4: [seq][roll bits b0 CW b1 CCW][~roll bits][crc8]; dead-man 50 ms'),
            ('0x030 FC->ECU CMD_STATE event + 10 Hz', 'len 7: [seq][cmd][arg u16][key u16][crc8]; cmd = Cmd enum (types.h); PURGE, RELIGHT, '
                                                      'CLEAR_LOCKOUT and DROGUE (17, v2.10, LEAD 186 (2): arg 1 attached, 0 released) among them'),
            ('0x100 ECU->FC TLM_FAST 500 Hz', 'len 8: [seq][d1: state b0-b3 + tlmf b4-b7][Pc u16 kPa abs, 0xFFFF = invalid][pintle crank-encoder '
                                              'lift u16 um, 0xFFFF = encoder invalid (v2.10, LEAD 175 (3))][fault bits u16]'),
            ('0x101 ECU->FC TLM_GIMBAL 500 Hz', 'len 8: [seq][flags][gimbal a meas i16][gimbal b meas i16][thrust u16 0.1 N, 0xFFFF when Pc invalid]'),
            ('0x102 ECU->FC TLM_RELIGHT 50 Hz, every state', 'len 8: [seq][state][flags][relight worst u16 ms][P_feed/P_tank %, 0xFF invalid]'
                                                             '[d6: b0-b5 refuse reason, b6 DROGUE echo (v2.10, LEAD 186 (2)), b7 PC_VALID (v2.10, '
                                                             'LEAD 175 (4))][crc8]'),
            ('0x110 ECU->FC TLM_SLOW', 'NOT DEFINED (page layout TO-DEFINE with the HAL)'),
            ('0x120 ECU->FC EVENT', 'len 8: [code][state][t_ms u32][arg u16]; each event sent 3x 10 ms apart; STATE (code 0x01) carries the '
                                    'state entry time (E2 = RUN entry = t_E2 on the FC clock, copy index in arg b13-b15)')])),
        ('event_codes', events),
        ('tlm_relight_flags_d2', tlmr),
        ('tlm_relight_d6', OrderedDict([('b0_b5', 'refuse reason (refuse:: enum, below; codes <= %d, static_assert in protocol.h)' % max(refuse.values())),
                                        ('b6', 'DROGUE: drogue attached as last reported by the FC (Cmd::DROGUE echo, LEAD 186 (2))'),
                                        ('b7', 'PC_VALID')])),
        ('refuse_reasons', refuse),
        ('pc_valid_bit', tv('TLM_RELIGHT d6 b7 = Pc channel valid this tick AND no latched PC_SENSOR fault AND no latched PC_SENSOR abort; '
                            'for the FC launch commit (LEAD CHANGELOG 175 (4)); decoders mask d6 & 0x3F for the refuse reason (b6 = DROGUE)',
                            'DESIGN protocol.h / engine_ecu.cpp')),
        ('cmd_drogue', tv('CMD_STATE cmd 17 DROGUE: arg 1 = drogue attached (FC, at the deployment), 0 = released (FC, at the release); other '
                          'values ignored; accepted in every state; reset to not attached at power-up and at an accepted ARM; echo TLM_RELIGHT '
                          'd6 b6. Effect: r2_command_hold', 'DESIGN types.h / engine_ecu.cpp; LEAD CHANGELOG 186 (2); test_core (v210-17)')),
        ('rg15_pc_invalid', 'TLM_FAST d2-d3 = 0xFFFF and TLM_GIMBAL d6-d7 = 0xFFFF while the Pc channel is invalid; RUN state, b4 (E2) and the '
                            'EVENT STATE t_E2 do not depend on Pc validity; b5-b7 need the valid filtered channel'),
        ('abort_path', OrderedDict([
            ('frame', 'ABORT 0x010 or CMD_STATE ABORT'),
            ('latency', tv('acted on at the next 1 kHz tick ahead of other commands', 'DESIGN engine_ecu.cpp; test v210-15')),
            ('effect_sil', tv('same tick: state ABORT, NC valve holding magnet released; pintle command 0 at +4 ms; valve closed +39 ms; needle '
                              'seated (<= 20 um) +66 ms; oxidiser flow < 1 % +68 ms; ARM bus off +82 ms; EVENT STATE (ABORT, cause CMD) x3; '
                              'log abort_cause CMD', 'SIL S6 fc_abort_command (plant times ASSUMED/SIM)')),
            ('fc_rule_r2_line175', 'HISTORY (its pcf_tmax 0.8 s was a proposal; line 181 (4) keeps 0.5 s): ' + CL.cite(175, 'R2', 260)),
            ('fc_rule_r2_status', CL.cite(181, '(4) Drogue release', 300)),
            ('r2_drogue_hold_abort', tv('Pc lost in flight RUN, R2 not met -> FC ABORT at t_E2 + pcf_tmax: the ECU stays in RUN until the frame (no '
                                 'ECU-initiated transition; flight Pc loss is flagged, not aborted), then ABORT/CMD on that tick, MV magnet '
                                 'released, pintle command 0 at +4 ms; loss onsets E2 + 5 / 10 ms and pcf_tmax 0.5 / 0.8 s all pass (the ECU path '
                                 'does not depend on the FC value)', 'SIL test_core (v210-16), ideal lit plant; plant effect times as effect_sil'))])),
        ('bus_load', v1['can_interface']['bus_load']),
        ('flight_computer_side', v1['can_interface']['flight_computer_side'])])

    # ---------------------------------------------------------------------------------------------------- relight interface
    doc['relight_interface'] = OrderedDict([
        ('sequence_v2p10', 'RELIGHT at the planned T_fire: direct path when the line is PRIMED (NC valve latch + opener ramp and torch at E0, '
                           'lift at E1 on 2oo2 torch confirmation, gate %s, W %s from the lift; worst E0 -> Pc-confirm %s); prep path when '
                           'UNPRIMED/UNKNOWN (PREPRESS first)' % (human(C('kTorchGate_s')), human(C('kIgnWindowRelightLong_s')),
                                                                 human(OrderedDict([('v', C('kTorchGate_s')['v'] + C('kIgnWindowRelightLong_s')['v']), ('unit', 's')])))),
        ('unpurged_relight', tv('a RELIGHT with no preceding PURGE is an UNPURGED relight: the ECU accepts it, never refuses or delays it for '
                                'lack of a purge; path from the line state as above. The v2.9 sequence-integrated purge (RELIGHT in COAST -> '
                                'PURGE + 2.90 s) is DELETED. Since LEAD 186 (1) the FC sends no unpurged RELIGHT below L* (FC rule, see '
                                'purge_commit). LEAD 194 (3) WITHDREW the E2 + 0.22 s held-release alternative (never baseline): GNC flies the '
                                'unpurged branch only as a comparator (H >= 0.30 s with the ramp to 200 N, >= 0.19 s with the ramp to 500 N, '
                                'no admissible hold with flow held at the start lift; not admissible with Pc invalid because of the 186 (2) '
                                'hold). No flight use of an unpurged RELIGHT remains; the ECU still accepts one (an ECU refusal is offered, '
                                'NOT implemented: OI-UNPURGED-RELIGHT)', 'LEAD CHANGELOG 175 (3), 186 (1), 194 (3)')),
        ('unpurged_relight_contest', tv('Combustion %s finds the unpurged branch REFUTED as written: in the LO worst line state a light inside '
                                        'the first liquid slug is followed by a vapour gap after E2; the drogue-release term is already true and '
                                        'A3 trips after the release (%.3f of starts unlined, %.4f lined; A3 ratio in the gap <= %.2f against %.2f). '
                                        'LEAD 186 (1) decided on it: below L* no unpurged relight on that pass. The 186 (1) alternative (drogue '
                                        'release held to >= E2 + 0.22 s) is WITHDRAWN by LEAD 194 (3) after REV-COMB-3 R3-01; it is a GNC '
                                        'comparator only. The SIL plant models one vapour plug ahead of the liquid (v2.7 C7), not '
                                        'slug/void alternation, and cannot show the gap'
                                        % (comb.get('version'), unp['released_then_A3_unlined_LO_worst'], unp['released_then_A3_lined_LO_worst'],
                                           unp['A3_ratio_max_in_gap'], unp['A3_threshold']),
                                        'combustion.json %s purge_commit_rule_v2p4a (SIM on ASSUMED delays + DERIVED line states; not physical); '
                                        'unpurged_start_check_v2p4a.json %s' % (comb.get('version'), usc_sha))),
        ('purge_commit', tv('the FC alone decides a purge: PURGE commits iff the lead to the plain relight trigger is >= L*; below L* there is '
                            'no purge AND no unpurged relight on that pass (drogue descent). L* = 1.3 s for both brackets, an FC parameter '
                            '(LEAD 186 (1); the 181 (2) interim value is replaced). Cmd::PURGE at E0 - %s; a RELIGHT during the purge ignites '
                            'once the flow has ended %s before E0. PURGE is refused (PURGE_PATH) unless the direct path applies; a following '
                            'RELIGHT then takes the prep path. The ECU does not know the plain trigger and does not check L*'
                            % (human(C('kPurgeRelight_s')), human(C('kPurgeFlowEndLead_s'))),
                            'LEAD CHANGELOG 164 / 175 / 181 (2) / 186 (1); SIL S11 drained_prep_seg_bleed_fitted')),
        ('purge_commit_decision', CL.cite(186, 'L* = 1.3 s is ADOPTED', 420)),
        ('purge_commit_decision_note_194_3', 'the held-release alternative quoted above (release held to >= E2 + 0.22 s) is WITHDRAWN by LEAD '
                                             '194 (3); the baseline of 186 (1) is unchanged: ' + CL.cite(194, '(3) R3-01', 300, 0)),
        ('purge_commit_history_181', 'HISTORY (interim L* replaced by line 186 (1)): ' + CL.cite(181, 'The rule is restated', 300, 0)),
        ('relight_worst_ms', tv('TLM_RELIGHT d4-d5 worst valve-command -> Pc-confirm time: 810 ms on the direct path (the integrated 3310 ms value '
                                'is gone with the integrated purge)', 'DESIGN protocol.h / engine_ecu.cpp')),
        ('torch_gate', C('kTorchGate_s')), ('W_flight_relight', C('kIgnWindowRelightLong_s')),
        ('primed_flag', 'PRIMED = DIRECT PATH (protocol.h alias tlmr::DIRECT_PATH); not a liquid or vapour detector (lead line 113 (1))'),
        ('states', 'NONE (VALID 0), PRIMED, UNPRIMED, UNKNOWN (P_feed or P_tank invalid, or a coast pintle anomaly, RG-08); POST_ABORT b6'),
        ('rate', tv('50 Hz in every state (>= 10 Hz required in COAST)', 'DESIGN protocol.h')),
        ('fc_planning_from_gnc', OrderedDict([
            ('relight_planning_value_s', tv(rpv['v'], 'gnc.json: ' + rpv.get('tag', 'untagged'))),
            ('option_c_unprimed_s', tv(rpv['option_c_unprimed_s']['v'], 'gnc.json: ' + rpv['option_c_unprimed_s'].get('tag', 'untagged'))
             if isinstance(rpv['option_c_unprimed_s'], dict) else rpv['option_c_unprimed_s']),
            ('stale_or_missing_flag', tv(rpv['stale_or_missing_flag']['v'], 'gnc.json: ' + rpv['stale_or_missing_flag'].get('tag', 'untagged'))
             if isinstance(rpv['stale_or_missing_flag'], dict) else rpv['stale_or_missing_flag']),
            ('source', 'gnc.json %s requirements.ignition.relight_planning_value_s (%s)' % (gnc.get('version'), gnc_sha)),
            ('scope', CL.cite(181, 'scoped to the predictor path', 200))])),
        ('head_end_bleed', 'drawn provision with the hardware purge window; see head_end_bleed_provision'),
        ('a1_apogee_m', tv(285, 'LEAD CHANGELOG 175 (5), record only')),
    ])

    # ---------------------------------------------------------------------------------------------------- abort matrix + self-check
    errs = []
    matrix = []
    for name, code in abort_enum.items():
        if name == 'NONE':
            continue
        if name not in AB:
            errs.append('%s: no template' % name)
            continue
        tpl, keys = AB[name]
        errs += template_check(name, tpl, keys, C)
        th = OrderedDict()
        for k in keys:
            th[k] = C(k) if C.has(k) else C(k, 'eng')
            if th[k]['v'] is None:
                errs.append('%s: %s did not evaluate' % (name, k))
        row = OrderedDict([('code', code), ('cause', name), ('trigger', render(tpl, C)), ('thresholds', th)])
        if name in AB_REF:
            row['decision'] = CL.cite(AB_REF[name][0], AB_REF[name][1], 260)
        matrix.append(row)
    for name in AB_REF:
        if name not in AB:
            errs.append('%s: decision reference for a cause without a template' % name)
    for name in AB:
        if name not in abort_enum:
            errs.append('%s: template for a cause that is not in types.h' % name)
    if errs:
        raise SystemExit('abort-matrix self-check FAILED:\n  ' + '\n  '.join(errs))
    doc['abort_matrix'] = OrderedDict([
        ('actions', 'every abort de-energises the NC valve at once and commands the pintle closed in parallel; no in-flight relight retry '
                    'after a no-light; normal shutdown: pintle first, MV on seat confirmation or the timeout'),
        ('mv_seat_timeout', C('kMvSeatTimeout_s')),
        ('causes', matrix)])

    # ---------------------------------------------------------------------------------------------------- start monitors / light rule / drogue
    doc['light_rule'] = OrderedDict([
        ('rule', tv('P0 = mean of filtered/raw gauge Pc over [E1 - 20 ms, E1]. One-sided check against the auto-zero ambient (LEAD CHANGELOG 166 (1)): '
                    'P0 above +check -> P0 kept, BASE_HIGH flagged to the FC, the pad first start and the stand refuse the lift (PC_SENSOR), '
                    'the A1 relight proceeds on the measured P0; P0 below -check -> P0 := 0 (BASE_AMB). Light (E2) = filtered AND raw rise over '
                    'P0 >= kIgnRise_Pa with filtered AND raw Pc >= the floor, kIgnConfirmRelN consecutive ticks', 'LEAD/COMB')),
        ('kIgnRise_Pa', C('kIgnRise_Pa')), ('kIgnConfirmRelN', C('kIgnConfirmRelN')), ('kIgnPreN', C('kIgnPreN')),
        ('kBpc1Shown', C('kBpc1Shown')), ('kIgnResidual_Pa', C('kIgnResidual_Pa')), ('kIgnBaseCheck_Pa', C('kIgnBaseCheck_Pa')),
        ('kIgnFloorAbs_Pa', C('kIgnFloorAbs_Pa')),
        ('note', 'kBpc1Shown stays false until B-PC-1 shows residual <= 0.3 bar AND RE-02 closes (S13 B extension fails the lead criteria in both builds)')])
    doc['start_monitors'] = OrderedDict([
        ('A3', tv('(Pc - P0)/(Pc_map_lo - P0) < %s for %s in RUN; denominator >= 0.5 bar' % (human(C('kFlameoutRel')), human(C('kFlameoutTime_s'))), 'LEAD/COMB + DESIGN')),
        ('light_spike_record', tv('no late-light abort (the v2.9 pressure-hold abort is deleted, RE-01, LEAD CHANGELOG 160): LIGHT_SPIKE record '
                                  'from %s abs (raw and filtered peak, time above %s and above the 30 bar limit, time from light) in the log '
                                  'and EVENT 0x20' % (human(C('kLightSpikeLoAbs_Pa')), human(C('kLightSpikeLoAbs_Pa'))), 'LEAD')),
        ('light_spike_lower_bound', tv('the flight LIGHT_SPIKE comes from the 1 kHz record of the 50 Hz filtered and the raw channel: a LOWER BOUND '
                                       'of the real chamber event; the stand dynamic channel B-DPC-1 measures it', 'LEAD CHANGELOG 172 (5)')),
        ('A7', tv('HOLD band from E1 (low edge P0 - %s), START band E2 -> E3, RUN_MAP after E3; %s; IGNITION / stand -> PC_SENSOR abort, flight '
                  'RUN -> flag once per burn; high side blanked from E2 to E2 + %s in every phase (RE-12)'
                  % (human(C('kA7HoldLow_Pa')), human(C('kA7Time_s')), human(C('kA7StartHiBlank_s'))), 'LEAD/COMB + DESIGN')),
        ('E3', tv('first RUN tick with the ramp done and Pc >= P0 + 0.9 (setpoint - P0), or E2 + %s' % human(C('kE3Max_s')), 'DESIGN')),
        ('fa1', tv('E1 = torch confirmed by P_torch AND photodiode (2oo2) AND the bleed closure step ended (confirmed, or the deadline reached); '
                   'both dark for %s between E1 and E2 -> TORCH_LOST; FLAMEOUT_OPT in RUN with Pc invalid' % human(C('kTorchLossTime_s')),
                   'LEAD CHANGELOG 164 (8), 166 (3); REV-GNC-2 (2)')),
        ('photodiode', OrderedDict([('valid_min', C('kPhotoMin_V')), ('valid_max', C('kPhotoMax_V')), ('lit_rise', C('kPhotoLitRise_V')),
                                    ('dark_tau', C('kPhotoDarkTau_s')), ('note', 'thresholds are placeholders set by IGN-1')])),
        ('cf3_lift_table', tv('17 rows 0.1928-0.2520 mm vs T_tank (A1 row 286.7 K 0.2178 mm); warm rows reach 37.4 g/s, +0.8 % over 37.1 g/s', 'CF-3 pending / DERIVED')),
    ])
    doc['drogue_release_support'] = OrderedDict([
        ('predicate_owner', CL.cite(168, 'RELEASE iff RUN AND b4', 300)),
        ('fc_rule_r2_line175', 'HISTORY (its pcf_tmax 0.8 s was a proposal; line 181 (4) keeps 0.5 s): ' + CL.cite(175, 'R2', 300)),
        ('fc_rule_r2_status', CL.cite(181, '(4) Drogue release', 420)),
        ('fc_parameters', tv('pcf_tmax 0.5 s (0.8 s NOT adopted) until GNC flies R2 v2; release threshold 37.16 N for 3 frames at 100 Hz; '
                             'baseline reference at E0 for now (E2 or drag-compensated may follow). All three are FC parameters set by the '
                             'lead; the ECU supplies RUN, t_E2 and the ABORT path', 'LEAD CHANGELOG 181 (4)')),
        ('ecu_publishes', [tv('TLM_FAST d1: b0-b3 state (decoders mask d1 & 0x0F), b4 E2 of this start, b5 rise now, b6 rise held since E2, '
                              'b7 rise held to E2 + %s (latched); b5-b7 from the VALID filtered channel only (RE-03); E2 itself on filtered AND raw'
                              % human(C('kDrogueRiseHold_s')), 'DESIGN protocol.h (tlmf::)'),
                           tv('t_E2 = EVENT 0x120 STATE (RUN entry) t_ms; usable with the Pc channel invalid', 'DESIGN'),
                           tv('PC_VALID = TLM_RELIGHT d6 b7 (launch commit)', 'DESIGN'),
                           tv('DROGUE = TLM_RELIGHT d6 b6: the FC drogue state held by the ECU (Cmd::DROGUE echo, r2_command_hold)',
                              'DESIGN protocol.h; LEAD CHANGELOG 186 (2)')]),
        ('kDrogueRiseHold_s', C('kDrogueRiseHold_s')),
        ('tests', 'test_core (25)-(26), (v210-4..8) predicate timing with Pc invalid before E2 / at E2 + 20 ms / after E2 + 150 ms, '
                  '(v210-15) Pc invalid in flight RUN: RUN + E2 kept, b7 clear, 0xFFFF, ABORT frame same tick; (v210-16) drogue held, ABORT '
                  'frame at t_E2 + 0.5 / 0.8 s after a loss at E2 + 5 / 10 ms; (v210-17) R2 command hold (r2_command_hold)'),
        ('sil', OrderedDict([('S5_rise_held_runs', s5.get('drogue_rise_held_to_E2_0p10_runs')),
                             ('S14', 'Pc invalid at E2 + 20 ms: RUN open loop, no A7, b7 never; scored against the line-168 interim FC rule (release '
                                     'E2 + 101 ms, branch 3), which R2 replaced in design (LEAD 175 / 181 (4)): the S14 ECU result stands, its FC '
                                     'release time is historical; stand PC_SENSOR +5 ms'),
                             ('S17', 'in-loop FC stand-in with R2 (3 frames >= 37.16 N at 100 Hz, ABORT at t_E2 + 0.5 s) and the R2 command '
                                     'hold: r2_command_hold.sil_S17. R2 itself stays GNC\'s FC-side design and test')])),
    ])

    # ---------------------------------------------------------------------------------------------------- R2 command hold (v2.10, LEAD 186 (2))
    if s17.get('not_as_expected_count') != 0:
        raise SystemExit('S17: %s cases not as expected - review r2_command_hold before publishing' % s17.get('not_as_expected_count'))
    s17c = OrderedDict((c['case'], c) for c in s17['cases'])
    s17sw = OrderedDict(('hold' if x['drogue_report'] else 'no_hold', x) for x in s17['noise_sweep_flameout_200N_calm_5N_rms'])
    lit17, litn17 = s17c['lit_starved_pc_lost_hold_200N'], s17c['lit_starved_pc_lost_NOREPORT_200N']
    w6, w6b, aw17 = s17c['flameout_hold_200N_W6'], s17c['flameout_hold_200N_W6_onset10ms'], s17c['flameout_hold_200N_allwinds']
    nrc, nr6, nr5 = s17c['flameout_NOREPORT_200N_calm'], s17c['flameout_NOREPORT_200N_W6'], s17c['flameout_NOREPORT_500N_calm']
    tr17 = list(csv.DictReader([l for l in rd(os.path.join(SIL, 'S17', 'S17_lit_starved_pc_lost_hold_200N_trace.csv')).splitlines()
                                if not l.startswith('#')]))
    hold17 = [r for r in tr17 if r['r2_hold'] == '1']
    f_lit_hold, pc_lit_hold = float(hold17[-1]['F_plant_N']), float(hold17[-1]['Pc_plant_bar_abs'])
    m17 = re.search(r'hold level reached after (\d+) ms \(slew bound (\d+), ramp (\d+) ms\), held ([\d.]+) N; release max step ([\d.]+) N/ms, '
                    r'200 N after (\d+) ms', tc_log)
    if not m17:
        raise SystemExit('test_core log lacks the (v210-17) result line')
    R2_THR = 37.16   # [LEAD CHANGELOG 175 (5) / 181 (4)] FC R2 threshold, an FC parameter (used here only to state margins)
    w6_margin = R2_THR - w6['d_app_N'] - w6['dead_F_cold_mean_N']
    case17 = lambda c: OrderedDict([('case', c['case']), ('outcome', c['outcome']), ('expected', c['expected_outcome']), ('as_expected', c['as_expected']),
                                    ('fc_release_from_E2_ms', c['fc_release_from_E2_ms']), ('fc_abort_frame_from_E2_ms', c['fc_abort_frame_from_E2_ms']),
                                    ('F_meas_max_R2_window_N', c['F_meas_max_R2_window_N']),
                                    ('frames_in_a_row_at_or_above_threshold', c['R2_max_consecutive_frames_at_or_above_threshold']),
                                    ('r2_hold_ticks', c['r2_hold_ticks'])])
    _cfgtxt = rd(os.path.join(CORE, 'config.h'))

    def _arr(name):
        m_ = re.search(r'constexpr\s+float\s+%s\[\w+\]\s*=\s*\{([^}]*)\}' % name, _cfgtxt)
        if not m_:
            raise SystemExit('config.h: array %s not found' % name)
        return [float(x.strip().rstrip('f')) for x in m_.group(1).split(',') if x.strip()]
    _lt, _lv = _arr('kIgnLiftT_K'), _arr('kIgnLiftTab_m')
    if 286.70 not in [round(x, 2) for x in _lt]:
        raise SystemExit('kIgnLiftT_K has no 286.70 K row - review the r2_command_hold lift basis text')
    ign_lift_a1_mm = _lv[[round(x, 2) for x in _lt].index(286.70)] * 1e3
    doc['r2_command_hold'] = OrderedDict([
        ('decision', CL.cite(186, '(2) OI-38 R2 command hold ADOPTED', 600)),
        ('decision_194_4', CL.cite(194, '(4) R3-05/R3-14', 700)),
        ('rule', tv('flight (not stand) AND state RUN AND drogue attached (Cmd::DROGUE) AND Pc channel invalid this tick -> the open-loop '
                    'thrust command is min(FC command, %s), applied at once (the Pc setpoint slew of %.0f bar/s still applies); it ends at the '
                    'FC release report (Cmd::DROGUE 0) or when the Pc channel is valid again, and the command then returns at <= %s. With Pc '
                    'valid nothing changes (closed loop, A3 active). The ECU takes no drogue decision'
                    % (human(C('kR2HoldThrust_N')), C('kPcSpRateLimit_Paps')['v'] / 1e5, human(C('kStartRamp_Nps'))),
                    'DESIGN config.h / engine_ecu.cpp; LEAD CHANGELOG 186 (2)')),
        ('kR2HoldThrust_N', C('kR2HoldThrust_N')),
        ('interface', OrderedDict([('fc_to_ecu', 'CMD_STATE cmd 17 DROGUE (can_interface.cmd_drogue)'),
                                   ('ecu_to_fc', 'TLM_RELIGHT d6 b6 echo; the FC checks it before a RELIGHT'),
                                   ('log', 'v11 tlm_flags b0 = hold active this tick, b1 = drogue attached (log only; TLM_FAST d1 carries b4-b7)')])),
        ('fc_side', 'FC owner (GNC): DROGUE 1 at the deployment, DROGUE 0 at the release; R2 (threshold, persistence, pcf_tmax, baseline) '
                    'unchanged. Not implemented by its owner yet; Electronics modelled it only as the S17 stand-in'),
        ('flameout_opt_coverage', 'FLAMEOUT_OPT needs the main-chamber view proven (%d lit ticks in RUN after the torch closes); a flame-out in '
                                  'the first ms after E2 is not covered, which is the case the hold addresses' % int(C('kPhotoViewProveN')['v'])),
        ('unit_test', tv('test_core (v210-17), 2 checks: flight RUN at 200 N, drogue attached, Pc invalid -> hold on every tick; the setpoint '
                         'reaches the 62.5 N level in %s ms (setpoint-slew bound %s ms; the start ramp would take %s ms), held %s N; DROGUE 0 -> '
                         'off on that tick, back to 200 N at <= %s N/ms in %s ms; hold also ends when Pc is valid again; no hold without the '
                         'report, on the stand (PC_SENSOR abort) or with Pc valid; args other than 0/1 ignored, ARM resets, CMD_STATE round trip'
                         % m17.groups(), 'SIM (ideal Rig9 plant); results/sil_v2p10/test_core_log.txt')),
        ('sil_S17', OrderedDict([
            ('file', 'results/sil_v2p10/S17/S17_r2hold.json (+ 3 traces)'),
            ('model', 'A1 relight (flight), in-loop FC stand-in R2Fc: DROGUE 1 at 2.90 s, release on Pc >= 3 bar valid or b7, with Pc invalid R2 '
                      '(F_meas >= 37.16 N on 3 consecutive 100 Hz frames) else ABORT at t_E2 + 0.5 s; F_meas = 20 ms low-pass of the plant thrust, '
                      'after the flame-out the Combustion cold-flow thrust at the plant lift, + a constant dead-vehicle bound d_app; starved-plateau '
                      'stand-in (2.6 bar abs for 0.40 s) on the R2-path cases; Pc lost at E2 + 5 ms, flame-out at E2 + 6 ms'),
            ('cold_flow_source', s17['cold_flow_source']), ('d_app_source', s17['d_app_source']),
            ('cases', [case17(c) for c in s17['cases']]),
            ('noise_sweep_flameout_200N_calm_5N_rms', s17sw),
            ('not_as_expected', s17['not_as_expected_count'])])),
        ('findings', [
            tv('undetected flame-out with the hold: open-loop lift %.4f mm, F_cold bound %.2f N; R2 never met at d_app 0 and at the W10 < 6 m/s '
               'bound %.2f N, 200 and 500 N commands -> ABORT frame at t_E2 + %.0f ms, drogue kept (no released dead vehicle)'
               % (w6['dead_lift_mean_mm'], w6['dead_F_cold_mean_N'], w6['d_app_N'], w6['fc_abort_frame_from_E2_ms']), 'SIM + DERIVED (S17)'),
            tv('steady margin at the W10 < 6 m/s bound: %.2f - %.2f - %.2f = %.2f N. LEAD 194 (4): the 16.31 N margin is CONDITIONAL on '
               'Cd x A x G at the start lift; CF-3 start-lift point (mdot and load-cell F, encoder lift recorded), acceptance F <= 16.31 N '
               'minus the heat allowance or mdot <= 52.6-56.3 g/s; a failure returns the hold level and the W10 rule to the LEAD. The heat '
               'TO-VERIFY is the injector-body and feed soak-back temperature at the relight (heat at tank pressure, threshold 2.8-3.7 kW)'
               % (R2_THR, w6['d_app_N'], w6['dead_F_cold_mean_N'], w6_margin), 'DERIVED from the S17 lift + Combustion bound'),
            tv('lift basis, three values not reconciled: the ECU commands %.4f mm in the hold (S17, open-loop map at the A1 state), the ECU '
               'ignition-lift row at 286.70 K is %.4f mm (kIgnLiftTab_m), and LEAD 194 (4) cites the grain_q1d start level 0.2039 mm. CF-3 '
               'measures at the lift the ECU commands in the hold and records it' % (w6['dead_lift_mean_mm'], ign_lift_a1_mm),
               'SIM (S17) + DESIGN (config.h) + LEAD CHANGELOG 194 (4)'),
            tv('estimator carry-over: at the W10 < 6 m/s bound %d frame(s) in a row read >= 37.16 N (max %.2f N) with the loss at E2 + 5 ms and %d '
               '(max %.2f N) with the loss at E2 + 10 ms, from the lit plateau through the 20 ms low-pass; the 3-frame persistence alone kept '
               'the drogue (one frame short). When R2 starts counting and the estimator lag are FC parameters (request to GNC)'
               % (w6['R2_max_consecutive_frames_at_or_above_threshold'], w6['F_meas_max_R2_window_N'],
                  w6b['R2_max_consecutive_frames_at_or_above_threshold'], w6b['F_meas_max_R2_window_N']), 'SIM (S17; constant d_app, stand-in FC)'),
            tv('all-winds bound (d_app %.2f N) with the hold: dead vehicle %s at E2 + %.0f ms, as LEAD 186 (2) predicts; the hold protects only '
               'inside the A1 HARD wind rule' % (aw17['d_app_N'], aw17['outcome'], aw17['fc_release_from_E2_ms']), 'SIM (S17)'),
            tv('without the hold (no DROGUE report): 200 N open-loop lift %.4f mm, F_cold %.2f N; calm noise-free max %.2f N, no release; W10 < 6 '
               'm/s bound -> %s at E2 + %.0f ms; 500 N calm -> %s at E2 + %.0f ms (F_cold %.1f N). 5 N rms noise, calm, 200 N: %d/%d dead '
               'released without the hold, %d/%d with it'
               % (nrc['dead_lift_mean_mm'], nrc['dead_F_cold_mean_N'], nrc['F_meas_max_R2_window_N'], nr6['outcome'], nr6['fc_release_from_E2_ms'], nr5['outcome'], nr5['fc_release_from_E2_ms'],
                  nr5['dead_F_cold_mean_N'], s17sw['no_hold']['dead_released'], s17sw['no_hold']['runs'], s17sw['hold']['dead_released'],
                  s17sw['hold']['runs']), 'SIM (S17)'),
            tv('lit relight with Pc lost under the starved-plateau stand-in (2.6 bar abs, about 26 N < 37.16 N): R2 release at E2 + %.0f ms with '
               'the hold (E2 + %.0f ms without), %.0f ms before pcf_tmax; a longer plateau reaches the ABORT of a lit engine (not run)'
               % (lit17['fc_release_from_E2_ms'], litn17['fc_release_from_E2_ms'], 500.0 - lit17['fc_release_from_E2_ms']), 'SIM (S17; plateau stand-in)'),
            tv('lit thrust in the hold: SIL plant %.1f N at %.2f bar abs at the last hold tick against the 62.5 N target (open-loop map from the '
               'v2.3 tables at the A1 tank state); the lit-engine R2 margin in the SIL plant is %.1f N, not 25.3 N'
               % (f_lit_hold, pc_lit_hold, f_lit_hold - R2_THR), 'SIM (S17 trace)'),
            tv('after the release the command returns at %.3f N/ms: 200 N reached %.0f ms after the release'
               % (lit17['ramp_max_after_release_N_per_ms'], lit17['to_command_after_release_ms']), 'SIM (S17)')]),
        ('limits', 'd_app is a constant bound over the window (GNC maxima, not a gust history); the FC model is an Electronics stand-in; the '
                   'starved plateau is a shape stand-in; the cold-flow thrust is the adiabatic bound without heat pick-up; SIL plant on '
                   'ASSUMED/COMB inputs; nothing here is hardware or flight-software evidence'),
        ('owner_actions', ['GNC (LEAD 194 (4)): R2 v2 with F_cold plus the grain_q1d start-level lit history (fuel-starved 0.1-0.4 s at '
                           '0.2039 mm), not 62.5 N x pcf_k; the hold command profile (sim6 V); state the R2 counting start',
                           'FC owner: DROGUE reports and the d6 b6 echo check in the FSW record; B-FC-1 / HIL with the FC',
                           'Combustion (LEAD 194 (4)): injector-body and feed soak-back temperature at the relight (heat at tank pressure, '
                           'threshold 2.8-3.7 kW) for the start-level bound; CF-3 start-lift point with a load cell'])])

    # ---------------------------------------------------------------------------------------------------- 070BG over-range at FA-1 (LEAD 194 (7))
    def fsum(node, line, tau, vsat, fam='all'):
        for s_ in fa1['summary']:
            if (s_['node'], s_['sense_line'], s_['tau_x_ms'], s_['v_sat_V'], s_['family']) == (node, line, tau, vsat, fam):
                return s_
        raise SystemExit('fa1_overrange_v2p10: configuration %r missing' % ((node, line, tau, vsat, fam),))
    fnl, ffa, fln = fsum('head', 'off', '0.9', '4.95'), fsum('head', 'off', '0.1', '4.95'), fsum('head', 'on', '0.9', '4.95')
    fln474, fln450 = fsum('head', 'on', '0.9', '4.74'), fsum('head', 'on', '0.9', '4.50')
    ffa474, ffa450 = fsum('head', 'off', '0.1', '4.74'), fsum('head', 'off', '0.1', '4.50')
    fnlvo, fnlaw = fsum('head', 'off', '0.9', '4.95', 'vapour_once'), fsum('head', 'off', '0.9', '4.95', 'as_written')
    fall = [s_ for s_ in fa1['summary'] if s_['family'] == 'all']
    n_fa1 = fnl['n_cases']
    v_hi = C('kPcSensorMax_V')['v']
    proof_abs = 140.0 + 1.01325
    fp = lambda f: '; '.join('%s %d' % (k if k != 'none' else 'no abort path', v)
                             for k, v in sorted(f['first_abort_path_counts'].items(), key=lambda kv: -kv[1]))
    doc['pc_overrange_fa1'] = OrderedDict([
        ('request', CL.cite(194, '(7) R3-10', 420)),
        ('relay', 'coordinator relay of line 194: state the 070BG over-range behaviour from the datasheet (saturation level, recovery time, '
                  'damage / proof) and its effect on the 30 bar abort and comparator, the Pc-valid flag and the logged FA-1 peak; a proof '
                  'rating below about 90 bar abs is a design-change item'),
        ('transducer_datasheet', OrderedDict([
            ('part', 'TE M3234-000005-070BG (M3200), 0-70 bar g, 0.5-4.5 V ratiometric at 5 +/- 0.25 V'),
            ('source', 'TE M3200 datasheet 08/2018 (farnell.com/datasheets/3007269.pdf)'),
            ('proof', tv('2 x rated = 140 bar g = %.1f bar abs at sea level' % proof_abs, 'DATASHEET')),
            ('burst', tv('5 x rated (<= 20 kpsi) = 350 bar g', 'DATASHEET')),
            ('rise_time_10_90', tv('< 2 ms', 'DATASHEET (a bound only; the SIL tau 0.9 ms gives 2.0 ms, the slowest response it allows)')),
            ('total_error_band', tv('+/- 1.5 % FS', 'DATASHEET')),
            ('output_above_full_scale', tv(None, 'MISSING: the datasheet does not state the output above 4.5 V (the saturation level)')),
            ('recovery_after_over_range', tv(None, 'MISSING: not stated')),
            ('over_range_damage', 'no damage is stated below the proof rating; above it the datasheet gives no performance guarantee (zero or '
                                  'span shift possible); the burst rating is far above the FA-1 levels, so N2O containment at the port is not '
                                  'at issue'),
            ('ninety_bar_test', 'proof %.1f bar abs > 90 bar abs: NOT a design-change item by the proof rating at the head pressure; at the '
                                'transducer port behind the sense line see period_domain' % proof_abs)])),
        ('ecu_chain', OrderedDict([
            ('adc_range', tv('PC_SIG readable to about 4.99 V (1.2 V full scale / 0.2404 divider 12.7k-4.02k; 5.04 V with the 330 kOhm '
                             'input): above the 4.75 V check, so the transducer saturation, not the ADC, limits the reading',
                             'DERIVED from DESIGN resistor values and DATASHEET ADS131M04 full scale')),
            ('over_range_check', tv('cfg::kPcSensorMax_V %s V = %.1f bar g (%.1f bar abs at sea level) on the 1 kHz reading (4 ADC frames '
                                    'averaged)' % (v_hi, (v_hi - 0.5) / 4.0 * 70.0, (v_hi - 0.5) / 4.0 * 70.0 + 1.01325), 'DESIGN config.h')),
            ('sil_simplification', 'sil/sim.cpp limits the 1 kHz average at 4.95 V, not the transducer output; above full scale this over-reads. '
                                   'The FA-1 harness limits each sample (transducer, then ADC); the ADS131M04 sinc3 response is not modelled '
                                   'in either')])),
        ('firmware_behaviour', OrderedDict([
            ('reading_at_or_above_4p75V', tv('pc_sensor_ok_ false on that tick -> fault::PC_SENSOR set; faults_ is sticky (cleared only by DISARM '
                                             'in SAFE) -> PC_VALID (pc_commit_valid, TLM_RELIGHT d6 b7) = 0 for the rest of the power cycle; '
                                             'in IGNITION the same tick aborts HARD_START with fault::PC_OVERP (v2.6 OI-6 rule: a high '
                                             'over-range is taken as real pressure); in RUN no immediate abort, Pc invalid from then on',
                                             'DESIGN engine_ecu.cpp (sensors block, IGNITION case, out.pc_commit_valid)')),
            ('reading_between_4p5_and_4p75V', 'above the 70 bar g full scale but below the check: used as a real reading, no flag, PC_VALID '
                                              'unaffected'),
            ('firmware_30bar_abort', tv('LowPass2 50 Hz of the 1 kHz reading, absolute above %s for %s: HARD_START in IGNITION or RUN within '
                                        '%s, else PC_OVERPRESSURE; every state but SAFE; not gated by PC_VALID. The persistence runs on the '
                                        'FILTERED channel (LEAD RE-20); the relay wording "5 ms raw persistence" does not match v2.10'
                                        % (human(C('kPcOverPressureAbs_Pa')), human(C('kPcOverPressureTime_s')), human(C('kRunSettle_s'))),
                                        'DESIGN config.h / engine_ecu.cpp monitors()')),
            ('hardware_comparator', tv('PC_SIG (transducer output, before the ADC) -> tap RC 5.283 ms -> LMV331 trip 2.298 V (31.47 bar g) '
                                       'nominal, 2.208 V at the low band edge; U331 latch forces the ARM bus off; firmware HW_OVERPRESSURE '
                                       'after OVP_OK low for 2 ms. A saturated transducer limits PC_SIG at its saturation level, so the '
                                       'comparator sees at most that level', 'DESIGN ecu_design.py / ovp_hw_params.h')),
            ('light_spike_record', 'LIGHT_SPIKE (E1 to E2 + 0.45 s or the exit tick, which is sampled; EVENT 0x20): raw and filtered peaks of '
                                   'the 1 kHz channel (a saturated reading is logged at its clipped value); overrange bit set only for a '
                                   'reading >= 4.75 V')])),
        ('sim', OrderedDict([
            ('method', 'calc/v2p10/fa1_overrange.py + fa1_overrange_chain.cpp: the %d FA-1 head histories (fa1_envelope_v2p4a %s, COMB SIM) '
                       'through the SIL Pc chain with the transducer output limited at v_sat (4.95 / 4.74 / 4.50 V / none), worst of 4 ADC '
                       'phases, E2 emulated; cross-checked against the published spike_chain.cpp on one case (identical)'
                       % (n_fa1, fa1['inputs']['fa1_envelope']['sha256_16'])),
            ('file', 'results/fa1_overrange_v2p10.json (+ _cases.csv, _run_log.txt, _traces/)'),
            ('counts_note', 'counts are over Combustion\'s parametric grid, not probabilities'),
            ('no_line_tau_0p9ms', tv('transducer port = head <= %.2f bar abs; reading max %.3f V (%.2f bar abs, the LIGHT_SPIKE raw peak) '
                                     'for a %.2f bar abs head peak: no reading >= %s V, no flag, PC_VALID not latched; firmware 30 bar / 5 ms '
                                     'trips in %d of %d (vapour_once %d, as_written %d); comparator %d nominal / %d low band; any abort path '
                                     '%d; first path: %s; E2 at %.1f-%.1f ms after the light'
                                     % (fnl['port_peak_bar_abs_max'], 0.5 + 4.0 * (fnl['logged_raw_peak_bar_abs_max'] - 1.01325) / 70.0,
                                        fnl['logged_raw_peak_bar_abs_max'], fnl['logged_raw_peak_case_true_head_peak_bar'], v_hi,
                                        fnl['cases_fw_30bar_5ms_trip'], n_fa1,
                                        fnlvo['cases_fw_30bar_5ms_trip'], fnlaw['cases_fw_30bar_5ms_trip'], fnl['cases_comparator_trip_nominal'],
                                        fnl['cases_comparator_trip_low_band'], fnl['cases_any_abort_path_nominal'], fp(fnl),
                                        fnl['E2_ms_from_light_range'][0], fnl['E2_ms_from_light_range'][1]), 'SIM')),
            ('no_line_tau_0p1ms', tv('faster transducer (the datasheet gives only the < 2 ms bound): %d readings >= %s V at %.2f ms after '
                                     'the light at the earliest (all before E2: HARD_START), %d at or above full scale without the flag '
                                     '(%d with v_sat 4.74 V, %d with 4.50 V); logged max %.2f bar abs; firmware 30 bar %d, comparator %d '
                                     'nominal; any %d'
                                     % (ffa['cases_reading_ge_4p75V'], v_hi, ffa['first_reading_ge_4p75V_ms_from_light_min'],
                                        ffa['cases_logged_at_or_above_full_scale_without_flag'],
                                        ffa474['cases_logged_at_or_above_full_scale_without_flag'],
                                        ffa450['cases_logged_at_or_above_full_scale_without_flag'], ffa['logged_raw_peak_bar_abs_max'],
                                        ffa['cases_fw_30bar_5ms_trip'], ffa['cases_comparator_trip_nominal'], ffa['cases_any_abort_path_nominal']),
                                     'SIM')),
            ('with_sil_sense_line', tv('SIL line (0.30 m, 1.59 mm ID, ASSUMED; linear acoustics, documented as outside its range for strong '
                                       'waves): %d of %d cases swing to the model\'s 1 kPa floor (non-physical), port up to %.1f bar abs; '
                                       '%d readings >= %s V (first %.2f ms, before E2: HARD_START) with v_sat 4.95 V, none with v_sat 4.74 / '
                                       '4.50 V, where %d / %d cases log at or above full scale without the flag; any abort path %d. A '
                                       'sensitivity, not evidence'
                                       % (fln['cases_port_at_line_model_floor'], n_fa1, fln['port_peak_bar_abs_max'],
                                          fln['cases_reading_ge_4p75V'], v_hi, fln['first_reading_ge_4p75V_ms_from_light_min'],
                                          fln474['cases_logged_at_or_above_full_scale_without_flag'],
                                          fln450['cases_logged_at_or_above_full_scale_without_flag'], fln['cases_any_abort_path_nominal']),
                                       'SIM (model outside its validity)')),
            ('sensitivities_not_proposals', tv('largest trip count over all configurations: comparator RC 10 or 20 ms at the low band edge %d; '
                                               'filtered persistence 15 ms %d; persistence 10 ms %d-%d. The effect of such changes on a real '
                                               'sustained over-pressure (S6 blocked nozzle, runaway) is NOT evaluated'
                                               % (max(max(f['sens_comparator_trip_low_band_rc10ms'], f['sens_comparator_trip_low_band_rc20ms']) for f in fall),
                                                  max(f['sens_fw_30bar_trip_persist15ms'] for f in fall),
                                                  min(f['sens_fw_30bar_trip_persist10ms'] for f in fall),
                                                  max(f['sens_fw_30bar_trip_persist10ms'] for f in fall)), 'SIM'))])),
        ('effects', OrderedDict([
            ('abort_paths', tv('an FA-1 event of the envelope\'s severity at the A1 relight is aborted by v2.10 in a large part of the grid '
                               '(%d-%d of %d over the configurations run), mainly by the firmware filtered 30 bar / 5 ms check (HARD_START) '
                               'and the hardware comparator (ARM bus off). These two paths act on the pressure above 30 bar for several ms, '
                               'not on the over-range, and act with or without saturation. The over-range path adds HARD_START only when '
                               'a 1 kHz reading reaches %s V (fast transducer or line amplification). Whether the relight should abort or '
                               'ride through an FA-1 spike is a LEAD decision (OI-FA1-PC-OVERRANGE)'
                               % (min(f['cases_any_abort_path_nominal'] for f in fall), max(f['cases_any_abort_path_nominal'] for f in fall),
                                  n_fa1, v_hi), 'SIM + DESIGN')),
            ('pc_valid_flag', tv('requirement "an FA-1 spike must not latch Pc invalid": met only while every 1 kHz reading stays below %s V. '
                                 'With no line amplification and the slow transducer no FA-1 case reaches it; with a faster unit %d cases '
                                 'do, with the SIL line %d. Any such reading latches PC_SENSOR (PC_VALID 0 for the power cycle) and, '
                                 'before E2, aborts. NOT guaranteed by the v2.10 design' % (v_hi, ffa['cases_reading_ge_4p75V'],
                                                                                            fln['cases_reading_ge_4p75V']), 'DESIGN + SIM')),
            ('logged_fa1_peak', tv('the 1 kHz record under-reads the FA-1 peak: %.2f bar abs logged for a %.2f bar abs head peak with no line; '
                                   'a saturated reading is logged at its clipped value (4.95 V = 78.9 bar abs in SIL, real level MISSING); '
                                   'readings between 4.5 V (71.0 bar abs) and 4.75 V are above full scale with no flag; if the real '
                                   'saturation is below 4.75 V an over-range is never flagged. Requirement "not logged as a real 70 bar '
                                   'reading without an over-range flag": NOT met by v2.10 in those cases. The stand dynamic channel is the '
                                   'evidence for peaks' % (fnl['logged_raw_peak_bar_abs_max'], fnl['logged_raw_peak_case_true_head_peak_bar']),
                                   'DESIGN + SIM')),
            ('recovery', tv(None, 'MISSING: if the output recovers slowly or undershoots below 0.25 V after saturation, the light rule, the 30 bar '
                                  'check and the LOW sensor-fault check act on wrong readings for that time; B-PC-1 over-range row')),
        ])),
        ('period_domain', OrderedDict([
            ('lead', CL.cite(194, 'Candidates to list first', 360)),
            ('pc_port_and_line', tv('the 070BG sees the sense-line response, not the head pressure. The SIL line rings with a period of about '
                                    '6 ms (peaks 6.0 ms apart in results/fa1_overrange_v2p10_traces/trace_743_head_on_4.95_0.9.csv), so its '
                                    'governing period is > 1 ms, where 194 (1) sets the spectrum value at that period (Combustion v2.4b; '
                                    'reviewer DERIVED up to 146.4 bar abs at 3 ms) or FA1S (about 151 bar abs, above the 070BG proof %.1f '
                                    'bar abs). The SIL line model gives %.1f bar abs at the port (outside its validity). Under 194 (1) the '
                                    '070BG on the 0.3 m line is a DESIGN CHANGE candidate unless the line response is shown below the proof '
                                    '(Mechanical period / B-DPC-1 line-end sensor)' % (proof_abs, fln['port_peak_bar_abs_max']),
                                    'DERIVED (SIL line model, ASSUMED geometry) + DATASHEET + LEAD CHANGELOG 194 (1)')),
            ('bleed_valves', 'J509/J510 are listing candidates: at selection the body proof and the closed-seat rating are checked against the '
                             'FA-1 period domain (BOM 218 note); no valve is selected yet'),
            ('options_not_decided', ['a higher-range M3200 code (the 170BG already on the BOM, proof 340 bar g): costs light-rule resolution, '
                                     'TEB in bar and the comparator scaling; ENG-09 (>= 70 bar) still met',
                                     'line damping (orifice / snubber at the transducer end): slows the comparator path and the light rule',
                                     'flush or shorter port: moves the transducer to the gimballed side or the head (vibration, temperature, '
                                     'harness across the gimbal)'])])),
        ('design_change_items', [
            'FA-1 at the A1 relight: abort (v2.10 as built) or ride-through; a ride-through needs the filtered 30 bar persistence, the 4.75 V '
            'IGNITION rule and the hardware comparator RC changed and S6 re-run (LEAD)',
            'PC_VALID: a high over-range latches PC_SENSOR for the power cycle; offered: a separate non-sticky over-range bit, PC_VALID 0 '
            'only while it lasts (v2.11 with a re-record; LEAD)',
            'logging: flag readings at or above full scale (4.5 V plus the TEB) in LIGHT_SPIKE and the 1 kHz log; meaningful only once B-PC-1 '
            'gives the saturation level (v2.11; LEAD)',
            'transducer port pressure vs proof under the 194 (1) period domain (see period_domain; LEAD / Mechanical)']),
        ('stand_dynamic_channel', OrderedDict([
            ('sensor', tv('PCB Piezotronics 113B22: 5 kpsi = 344.75 bar at +/-5 V; maximum pressure 15 kpsi = 1034 bar (no-damage rating); '
                          '1.0 mV/psi +/-10 %; resonance >= 500 kHz; rise <= 1 us; LF (-5 %) 0.001 Hz; DTC >= 500 s; -73..+135 C; flash '
                          '1649 C; 10-32 coax', 'DATASHEET pcb.com 113B22 product page, read 2026-10-13')),
            ('conditioner', tv('NI 9234: +/-5 V, IEPE 2.0 mA min, compliance 19 V max, AC coupling -3 dB 0.5 Hz (-0.1 dB 4.6 Hz max), '
                               'alias-free 0.45 fs = 23.04 kHz at 51.2 kS/s, stopband 100 dB from 0.55 fs',
                               'DATASHEET NI 9234 specifications 377849B-01 (Feb 2025); 374238A-02 (Oct 2015)')),
            ('fit', tv('range 344.75 bar >= 100 bar abs; 1.45 V at 100 bar; bias 8-14 V + 1.45 V <= 15.5 V < 19 V compliance; PCB lists '
                       '20-30 V excitation (TO-VERIFY with PCB/NI); AC coupled, so a flat pulse of T reads about T / 0.32 s low at its end '
                       '(0.3 % at 1 ms, 3 % at 10 ms) and static levels come from the 070BG chain', 'DERIVED')),
            ('placement', 'two in use: head flush, and the transducer end of a flight-like 0.3 m line next to the 070BG; one spare (BOM 237 qty 3)'),
            ('replaces', '113B24 (1 kpsi = 69 bar), which fails the >= 100 bar abs requirement'),
            ('price', 'TO-QUOTE, delivered to Soenderborg, DK-6400 (BOM 237 / 238); founder instrumentation purchase')])),
        ('bench', ['B-PC-1 over-range row on the spare 070BG (70-100 bar g, below proof): saturation level, zero shift, recovery',
                   'B-DPC-1 head + line end at IGN-1 and the T series; the 070BG logged in parallel',
                   'TE inquiry (founders / Electronics): output above full scale, recovery time, over-range zero shift for M3234-000005-070BG']),
        ('limits', 'COMB SIM histories (lumped three-node construct); SIL chain on ASSUMED line and transducer dynamics; saturation level '
                   'swept, not known; open-loop histories (a trip does not change them); nothing here is hardware evidence')])

    # ---------------------------------------------------------------------------------------------------- over-thrust, ENG-03, pintle rail (as v2)
    b = ot3['rg19_end_to_end_budget']
    doc['over_thrust'] = OrderedDict([
        ('rule', 'flight RUN, FC_THRUST > %s on %d consecutive fresh valid frames; stale > %s or b0 = 0 -> flag only; never on the stand'
         % (human(C('kOverThrust_N')), int(C('kOverThrustFrames')['v']), human(C('kFcThrustStale_s')))),
        ('threshold', C('kOverThrust_N')), ('frames', C('kOverThrustFrames')), ('rate', C('kFcThrustRate_Hz')), ('stale', C('kFcThrustStale_s')),
        ('rg19_budget_known_terms_s', b['step_onset_to_mv_seated_known_terms_s']),
        ('rg19_terms', [OrderedDict((k, t.get(k)) for k in ('id', 'term', 'mean_s', 'max_s', 'tag', 'owner', 'verify')) for t in b['terms']]),
        ('imu', tv('ADIS16470 filter / decimation delay UNKNOWN', 'UNKNOWN')),
        ('source', 'results/over_thrust_v3.json'),
        ('detector_structure', tv('consecutive-count form, no window and no hold: a counter of fresh valid FC_THRUST frames above %s, counted '
                                  'at frame receipt; the trip needs %d consecutive frames (a %s span at %s); a frame at or below the threshold, '
                                  'an invalid frame (valid flag clear), a gap above %s, leaving RUN or stand mode resets it to 0; checked every '
                                  '1 ms tick; the trip latches ABORT OVER_THRUST (NC valve released at once). Latency from the first exceeding '
                                  'frame = %d frame periods + <= 1 tick, plus the FC estimate (first-order tau 20 ms) and the IMU filter delay '
                                  '(UNKNOWN)' % (human(C('kOverThrust_N')), int(C('kOverThrustFrames')['v']), human(C('kOverThrustTime_s')),
                                                 human(C('kFcThrustRate_Hz')), human(C('kFcThrustStale_s')), int(C('kOverThrustFrames')['v']) - 1),
                                  'DESIGN engine_ecu.cpp / config.h')),
        ('rg16_allowance', CL.cite(181, '(3) RG-16', 520)),
        ('rg16_note', 'The ECU detector is NOT the windowed form behind the PROVISIONAL 0.5 s allowance: on a noisy 670 N plateau every frame '
                      'at or below 650 N restarts the count, so its latency there follows from the frame noise and is GNC\'s to budget. A '
                      'windowed form would be an ECU firmware change (monitor + config.h), not made in v2.10'),
        ('mission_arming', tv('FC_THRUST NOT armed on A1: the ECU has no mission input; the FC keeps the FC_THRUST valid flag clear (or sends '
                              'no frames) on A1, so the counter never runs. Arming on any mission needs GNC\'s RG-16 budget', 'LEAD CHANGELOG 181 (3)'))])
    doc['eng03_pintle_rate'] = OrderedDict([
        ('requirement', CL.cite(121, 'ENG-03 AMENDED', 260)),
        ('rate_map', OrderedDict([('file', '06-electronics/results/pintle_rate_map_v1.json'), ('sha256_16', READ[os.path.relpath(rmap_path, ROOT)]),
                                  ('summary', rmap['summary']), ('reduced_model_for_gnc', rmap['reduced_model_for_gnc'])])),
        ('quasi_static_check', eng03['verdict']['A_quasi_static']),
        ('start_ramp', C('kStartRamp_Nps', 'eng')),
        ('lift_clamp_RE04', tv('while the reference travels (or the pintle has not arrived), the lift command is clamped to the map lift at the '
                               'active setpoint + %s; integrator held during pintle travel. SIL: S5 plant Pc max %.2f bar abs, 0 PC_OVERPRESSURE in '
                               '300; probe F worst %.2f bar abs, 0 PC_OVERPRESSURE' % (human(C('kLiftClampMarginPc_Pa')), s5['pc_max_abs_max_Pa'] / 1e5,
                                                                                       pf['worst_plant_Pc_bar_abs']), 'DESIGN, SIL-tuned')),
        ('RE23_clause_map', s5.get('eng03_clause_map')),
        ('b_pnt_1', 'HV69 torque-speed under load at 7.335 and 7.49 V; closed-loop t10-90 <= 100 ms under load (S5 up-step does not meet it in SIL)')])
    tps, fets, ltc = ecuv['tps552882'], ecuv['external_fets'], ecuv['ltc4365']
    doc['pintle_rail'] = OrderedDict([
        ('adopted', CL.cite(62, 'PINTLE RAIL', 240)), ('publish_v3', rail['publish']),
        ('schematic_values', OrderedDict([('tps552882', tps), ('external_fets', fets), ('ltc4365', ltc)])),
        ('to_confirm', ['LTC4365 UV threshold = OV threshold ASSUMED', 'Q803 enhancement at the LTC4365 gate drive',
                        'TPS552882 compensation equations and phase margin at B-PWR-1', 'RPM0026A land pattern (placeholder footprint)'])])

    # ---------------------------------------------------------------------------------------------------- ECU hardware (v1 'ecu' key)
    ecu = OrderedDict(v1['ecu'])
    ecu['schematic'] = OrderedDict([
        ('version', '%s (KiCad 7.0.11, generated from hardware/kicad_gen/ecu_design.py)' % rev),
        ('erc', tv('%s errors, %s warnings, %d sheets (%s)' % (em.group(2), em.group(3), len(sheets), erc_time), 'KiCad eeschema ERC (GUI on Xvfb); self-consistency only (RE-15)')),
        ('netlist_crosscheck', tv('components %s, nets %s, pins %s of %s intended, errors %s, warnings %s' % xm.groups(), 'check_netlist.py v1')),
        ('negative_control', 'v2.3: PREG PWR_FLAG removed -> 1 error power_pin_not_driven U802 pin 1 (erc/negative_control_v2p3); not repeated for v2.5'),
        ('files', '06-electronics/hardware/kicad (README.md lists them)'),
        ('re15_before_fabrication', 'signed pin-function check of each custom symbol, real footprints, layout + DRC, derating table, ERC + '
                                    'cross-check on the final design: NOT DONE (no layout)'),
        ('placeholders', ['TI_RPM0026A_PLACEHOLDER (NOT FOR FABRICATION)', 'Pololu_U3V70_WireAttach (wire pads only)', 'Teensy41_Socket (verify vs PJRC drawing)'])])
    # LEAD CHANGELOG 186 (4): the CSV labels analog inputs by their Teensy pin names (A0..A9); written out so that 'A5' / 'A7' cannot be
    # read as the deleted A5 monitor or the A7 band monitor (the CSV itself is unchanged)
    pinfn = lambda f: re.sub(r'^(A\d+) ', r'Teensy analog pin \1: ', f)
    ecu['pin_map'] = [OrderedDict([('pin', p['teensy_pin']), ('net', p['net']), ('dir', p['direction']), ('function', pinfn(p['function']))]) for p in pins]
    ecu['pin_map_file'] = '06-electronics/hardware/kicad/%s' % pin_map_name
    hw = bd['hardware_window']
    ecu['purge_window'] = OrderedDict([
        ('circuit', 'J512 FC discrete PURGE_EN (1k series, 100k pull-down, ESD, 74LVC1G17) -> LTC6993-1 non-retriggerable one-shot (U572) ; '
                    'PURGE_WIN = PURGE_EN AND one-shot (U573); V1 = pin 15 AND PURGE_WIN (U574), V2 = pin 24 AND PURGE_WIN (U575)'),
        ('one_shot_s', tv(OrderedDict([('nominal', hw['t_nom_s']), ('min', hw['t_min_s']), ('max', hw['t_max_s'])]),
                          'DATASHEET LTC6993 Rev F (3.0 % grade) + RSET 0.1 %; DERIVED calc/bleed_driver_v1.py')),
        ('powered_span_needed_s', tv(hw['powered_span_needed_s'], 'DERIVED config.h (kHbleedHwPoweredMax_s)')),
        ('cap_relation', 'the window bounds the scheduled POWERED span, not the %s both-open firmware cap (a cap-length one-shot would cut '
                         'the scheduled flow)' % human(C('kHbleedCap_s'))),
        ('ecu_visibility', 'the ECU cannot read PURGE_WIN (no free pin); a stuck-high window chain is latent -> CHK-PW and a proposed '
                           'pre-flight check with PURGE_EN low (not in firmware %s)' % fw_ver),
        ('fc_icd', tv('PURGE_EN raised <= %s before Cmd::PURGE, dropped at E0; raised for the pad BIT; drive level 3.3 or 5 V TO-VERIFY'
                      % human(C('kFcPurgeEnLead_s')), 'ASSUMED, ICD item for the FC owner'))])
    ecu['photodiode_channel'] = 'ADC2 CH3 PHOTO_AIN from J902 (+5V_SNS, PHOTO_SIG, GND): 12.7k/4.02k 0.1 % divider (0.240), 22 nF C0G, ESD, 100k open-head pull-down'
    ecu['cs_decoder'] = ecuv['cs_decoder']
    ecu['mode_strap'] = ecuv['mode_strap']
    ecu['adc2'] = ecuv['adc2']
    ecu['heater_interlock'] = ecuv['heater_interlock']
    ecu['superseded_v1'] = ['pcb_outline_mm / mount_holes / enclosure_envelope_mm / connector_edges stay DESIGN reservations from v1: no layout yet',
                            'mass_kg 0.16 ASSUMED (v1) not re-estimated: re-weigh after the board is built']
    doc['ecu'] = ecu

    # ---------------------------------------------------------------------------------------------------- actuators (v1 key; GNC N5)
    act = OrderedDict()
    for k in ('tvc_A', 'tvc_B'):
        blk = OrderedDict((kk, vv) for kk, vv in v1['actuators'][k].items()
                          if kk not in ('linkage_proposal', 'margins_7V4', 'stiffness', 'resolution_deg_engine', 'backlash_deg_engine'))
        blk['v1_fields_for_gnc_status'] = ('dynamics_for_GNC, engine_side_at_n7_7V4 and hinge_moment_assumed_Nm keep their v1 names and values '
                                           '(GNC N5). dynamics_for_GNC (omega_n 94.2 rad/s ASSUMED, zeta 0.7, 4.5 ms) is the current Electronics '
                                           'position: no new servo data; B-TVC-1 FRF replaces it. engine_side_at_n7_7V4 is for the v1 n = 7 '
                                           'linkage; the as-built linkage is n = %s (mechanical.json %s gear_ratio_n, LEAD-DECISION): engine-side '
                                           'values at that ratio are NOT re-derived here (Mechanical/GNC own the kinematics). '
                                           'hinge_moment_assumed_Nm is the v1 ASSUMED sum; mechanical.json carries the current terms'
                                           % (mech['tvc']['linkage']['gear_ratio_n']['v'] if 'tvc' in mech and 'linkage' in mech['tvc'] and 'gear_ratio_n' in mech['tvc']['linkage']
                                              else 'see mechanical.json', mech.get('version')))
        blk['superseded_v1'] = 'linkage proposal, margins, stiffness and engine-side resolution/backlash of v1 are superseded by mechanical.json (as-built 135/225 deg linkage)'
        blk['supply'] = OrderedDict([('switch', 'Q401 + Q403 AOD4185 on VBAT, watchdog-gated (F401 removed)'), ('budget', sup['verdict']),
                                     ('pad_rule', C('kTvcSupplyMin_V')), ('arm_rule', C('kBattArmMin_V'))])
        act[k] = blk
    act['pintle_throttle'] = OrderedDict([
        ('model', 'MKS HV69 (%s)' % hv69['pn']), ('rail', 'PRAIL 7.49 V typ (TPS552882 + LTC4365)'),
        ('datasheet_class', OrderedDict((k, hv69.get(k)) for k in ('dims_mm', 'mass_g', 'V_range', 'T_kgcm', 's60', 'stall_A', 'T_op_C', 'deadband_us', 'spline'))),
        ('tags', 'DATASHEET via retailer copies of MKS data (TO-CONFIRM with MKS)'),
        ('jam', OrderedDict([('detection', rail['publish']['jam_detection']), ('design_load', CL.cite(62, 'JAM DESIGN LOAD', 120))])),
        ('pulse', OrderedDict([('centre', C('kPintleCenter_us')), ('us_per_deg', C('kPintleUsPerDeg')), ('min', C('kPintleMin_us')), ('max', C('kPintleMax_us'))])),
        ('position_telemetry', 'crank-encoder lift in TLM_FAST d4-d5 at 500 Hz (0xFFFF = encoder invalid)')])
    act['main_valve'] = OrderedDict([
        ('concept', CL.cite(91, 'MV-P balanced poppet ADOPTED', 200)),
        ('opener', 'Savox SB-2292SG on ARM_BUS (J404), cam; ramp %s, cock hold %s' % (human(C('kMvOpenRampSlow_s')), human(C('kMvCockHold_s')))),
        ('latch_magnet', OrderedDict([('design', latch['selected']), ('open', latch['open'])])),
        ('hardware_gate', 'MV_LATCH_G = MV_LATCH_GB AND PRAIL_OK (U306)'),
        ('position', 'OPEN/CLOSED microswitches J508 through the pin 23 ladder (RE-19 decode: OPEN+CLOSED and short = invalid)')])
    act['bleed_valves'] = OrderedDict([
        ('status', 'NOT SELECTED: no candidate meets all four LEAD criteria (12 V NC; seat >= 2 mm or Kv >= %.3f m3/h verified at 55 bar; medium '
                   'class covering flashing N2O; <= 0.15 kg each)' % bd['valve_kv']['kv_valve_min_m3h_4x']),
        ('kv_requirement', tv(bd['valve_kv']['kv_valve_min_m3h_4x'], 'DERIVED (4 x the 1.0 mm restriction, Cd 0.7 ASSUMED)')),
        ('seat_force_2mm_55bar_N', tv(bd['valve_kv']['seat_force_2mm_55bar_N'], 'DERIVED')),
        ('timing_used_by_firmware', OrderedDict([('open', C('kHbleedOpenTime_s')), ('close', C('kHbleedCloseTime_s'))])),
        ('driver', 'low-side DMN6075S on +12V_ARM with SS14 + SMAJ24A fast-release clamp (V_DS peak %s V < 60 V); peak-and-hold NOT drawn '
                   '(coil data unknown)' % bd['fast_release_clamp']['vds_peak_V'])])
    doc['actuators'] = act

    # ---------------------------------------------------------------------------------------------------- igniter, sensors
    doc['igniter'] = OrderedDict([
        ('type', 'torch: spark coil (IGBT, hardware-limited dwell) + SOL1 N2O and SOL2 propane solenoids (12 V, ARM-gated); flame confirmation '
                 'P_torch AND photodiode (2oo2)'),
        ('torch_gate', C('kTorchGate_s')), ('torch_lit', C('kTorchLitAbs_Pa')), ('torch_confirm_ticks', C('kTorchConfirmN')),
        ('torch_arm_zero_max', C('kTorchArmZeroMax_Pa')), ('chamber_vented_for_spark', C('kPcVentedMax_Pa')),
        ('torch_loss', C('kTorchLossTime_s')), ('spark_dwell', C('kSparkDwell_s')),
        ('timing_only_ground_start', 'SET_TORCH_GATE with the key, stand only, first start of the arming session')])
    dec = pct['A_ranges']['decision']['v'] if 'decision' in pct['A_ranges'] else pct['D_summary']
    sens = OrderedDict()
    sens['pressure_transducers'] = OrderedDict([
        ('selection', tv(dec, 'DESIGN pc_transducer_v2; lead line 73 (3)')),
        ('connectors', 'Pc J601, P_feed J602 (FS-01 block), P_tank J603, P_torch J901, P_mid J511'),
        ('hw_ovp', tv('31.47 bar g on the 070BG; band 30.90-34.06 bar abs; firmware abort %s abs filtered' % human(C('kPcOverPressureAbs_Pa')), 'DERIVED pc_transducer_v2')),
        ('fault_window', OrderedDict([('min', C('kPcSensorMin_V')), ('max', C('kPcSensorMax_V'))])),
        ('coast_rezero', OrderedDict([('span', C('kPcRezeroSpan_Pa')), ('max', C('kPcRezeroMax_Pa')), ('second_rezero_max_age', C('kPcRezero2MaxAge_s')),
                                      ('rule', 'second re-zero ending before PURGE/RELIGHT (RE-07); flight NOT_VENTED = flag, stand = refusal')]))])
    sens['thermocouples'] = OrderedDict([
        ('channels', ['TC1 type K case az 90 (U604)', 'TC2 type K case az 270 (U605)', 'TC3 type K nozzle holder (U606)',
                      'TC4 type K bore top (U904)', 'TC5 type T MSS-1 (U905)', 'TC6 type T MSS-2 (U906)']),
        ('case_abort', C('kCaseOverTemp_K')), ('relight_refusal', C('kCaseRelightMax_K')),
        ('case_tc_policy', 'RE-08 (LEAD 166 (6)): both valid at ARM; one lost -> continue on the other (f2 CASE_TC_DEGRADED); both lost -> stand abort, flight relight refused')])
    sens['photodiode'] = 'FA-1 head on J902 (Si photodiode + log TIA, 0-5 V), part TO-SELECT (BOM row); valid %s to %s' % (human(C('kPhotoMin_V')), human(C('kPhotoMax_V')))
    sens['temperature_other'] = ['DS18B20 x2 tank wall + #3 bay on 1-Wire (J608/J614)', 'NTC 10k pintle-servo bracket (J609)']
    sens['encoders'] = 'AS5048A x3 (gimbal A/B J610/J611, pintle crank J612), SPI1 1 MHz'
    sens['load_cell'] = v1['sensors']['load_cell_test_stand']
    sens['stand_dynamic_pc'] = tv('B-DPC-1: PCB 113B22 (5 kpsi = 344.75 bar at +/-5 V; maximum pressure 15 kpsi = 1034 bar) + NI 9234 at '
                                  '51.2 kS/s (AC coupled, -3 dB 0.5 Hz), flat to >= 10 kHz incl. the mount; head flush + end of a flight-like '
                                  'sense line (stand only, IGN-1 and the T series); see pc_overrange_fa1.stand_dynamic_channel',
                                  'LEAD CHANGELOG 172 (5), 194 (7); DATASHEET pcb.com 113B22, NI 377849B-01')
    doc['sensors'] = sens

    # ---------------------------------------------------------------------------------------------------- interlocks, safing
    doc['interlocks'] = OrderedDict([
        ('tank_hot', OrderedDict([('limit', C('kTankIgnMax_K')), ('wall_threshold', C('kTankIgnMaxWall_K')), ('wall_uncertainty', C('kTankWallUnc_K')),
                                  ('ptank_threshold_uncalibrated', C('kTankIgnMaxP_Pa')), ('ptank_threshold_calibrated', C('kTankIgnMaxPCal_Pa')),
                                  ('ptank_uncertainty_uncalibrated', C('kTankPUncUncal_Pa')), ('ptank_uncertainty_calibrated', C('kTankPUncCal_Pa')),
                                  ('calibration_flag', 'EngineEcu::ptank_cal_ok (runtime, from the B-PT-1 NV record via the HAL; boot default false)'),
                                  ('consequence', 'until B-PT-1 passes, a pad or stand start needs the tank at or below ~19.8 C by pressure'),
                                  ('missing', 'wall-vs-bulk offset and drift of the DS18B20 mounting (MISSING)'),
                                  ('source', CL.cite(172, 'guard band', 200))])),
        ('tank_cold', C('kTankIgnMin_K')),
        ('bay_hot', C('kBayArmMax_K')),
        ('wind_launch_commit', tv('W10 < 6 m/s AND sigma_u(3 m) <= 1.0 m/s over the 10 min before ARM (GSE anemometer, BOM v2.2)', 'LEAD line 161 (6), PROVISIONAL'))])
    doc['safing'] = OrderedDict([
        ('rule', CL.cite(172, 'safing rule', 260)),
        ('ecu', tv('ground no-light (stand any start, pad first start; abort in IGNITION or NO_IGNITION/TORCH_FAULT/TORCH_LOST/FLAMEOUT) -> '
                   'lockout + safing hold: CLEAR_LOCKOUT refused (refuse SAFING_HOLD) until %s after the abort; NV b4 restarts the hold at a '
                   'boot; EVENT SAFING_HOLD 0x23. The ECU cannot see the N2 flow: its timer is a lower bound only' % human(C('kNoLightSafingMin_s')), 'DESIGN')),
        ('n2_purge_min', C('kNoLightPurgeMin_s')), ('n2_flow_min', C('kNoLightPurgeFlowMin_kgps')), ('hold_total', C('kNoLightSafingMin_s'))])

    # ---------------------------------------------------------------------------------------------------- power, rates, link, fail-safe, harness
    pb = OrderedDict(v1['power_budget'])
    pb['rails'] = OrderedDict(v1['power_budget']['rails'])
    pb['rails']['PRAIL'] = 'pintle servo rail 7.49 V typ (TPS552882 on ARM_BUS) behind the LTC4365 OV disconnect'
    pb['rails']['VBAT_SERVO'] = 'TVC servos A/B on VBAT through the watchdog-gated Q401 + Q403'
    pb['rails']['+12V_ARM'] = 'Pololu U3V70F12 boost on ARM_BUS (behind F301): spark coil, torch and roll solenoids, bleed valves V1/V2'
    pb['fusing'] = OrderedDict([('F101', '25 A ATM main'), ('F102', '2 A 1206 logic'), ('F301', '15 A ATM ARM bus (feeds the 12 V boost)'),
                                ('F501', '3 A 1206 VBAT vent-branch fuse')])
    pb['re09_status'] = tv('EXCEEDS (REV-ELEC-1 R17/R18, DERIVED): +12V_ARM input 4.4-7.5 A in the purge with both coils, up to 12.1-15.7 A at E0 '
                           'with the spark peak vs the U3V70F12 6 A / 7 A / 10 A limits; ARM bus 14.5-22.8 A at PURGE entry vs F301 15 A. '
                           'Time-resolved budget at 6.6 V, load sequencing (LEAD 166 (8): remove the E0 brown-out) and peak-and-hold: NOT DONE. '
                           'Bleed coil data unknown (valve not selected)', 'OPEN')
    pb['heater_interlock'] = 'J616 GSE heater permit: <= 28 V, <= 1 A; hardware cut by ARM plug or ARM bus'
    pb['superseded_v1'] = 'v1 fusing (logic 1 A, IGN 5 A, SOL 3 A)'
    doc['power_budget'] = pb
    lr = OrderedDict(v1['loop_rates_and_latency'])
    lr['tick'] = C('kDt_s')
    lr['fc_command_period'] = C('kFcCmdPeriod_s')
    lr['hw_watchdog'] = C('kHwWatchdog_s')
    lr['tlm_fast_Hz'] = tv(500, 'DESIGN protocol.h')
    lr['tlm_relight_Hz'] = tv(50, 'DESIGN protocol.h')
    lr['fc_thrust_Hz'] = C('kFcThrustRate_Hz')
    doc['loop_rates_and_latency'] = lr
    doc['link_loss'] = OrderedDict([('degraded_after', C('kLinkDegraded_s')), ('lost_after', C('kLinkLost_s')),
                                    ('action_on_lost', v1['link_loss']['action_on_lost'])])
    fs = OrderedDict(v1['fail_safe_states'])
    fs['ECU power loss'] = 'MV latch drops -> MV-P spring + pressure bias close it; the pintle spring closes the unpowered HV69; NC bleed valves close; igniter dead'
    fs['ECU reset in flight'] = 'reboot to SAFE, MV and bleed closed, RUN never reported after the reset, the drogue is not released; no in-flight recovery path (LEAD 166 (8)); HIL-RST-1 proves it'
    fs['pintle rail fail-high'] = 'LTC4365 OV disconnect 8.06-8.34 V: servo unpowered, spring closes; PRAIL_OK low drops the MV latch in hardware (U306)'
    fs['Pc over-pressure'] = 'hardware comparator latch 31.47 bar g removes the ARM bus independent of firmware; firmware abort %s abs filtered for %s' % (
        human(C('kPcOverPressureAbs_Pa')), human(C('kPcOverPressureTime_s')))
    fs['purge window'] = 'FC PURGE_EN low or the one-shot expired: both bleed drives forced off in hardware'
    fs['superseded_v1'] = 'v1 "latch drops -> spring closes main valve (ball valve)"'
    doc['fail_safe_states'] = fs
    doc['fmea_rows_a1'] = [OrderedDict([
        ('id', 'FMEA-A1-PCLOSS-OT'),
        ('mode', 'Pc channel lost in flight RUN on A1 (transducer, supply, wiring or ADC path)'),
        ('effect', 'no over-thrust detector: PC_OVERPRESSURE (%s) and HARD_START need the Pc channel valid; the hardware comparator '
                   '(HW_OVERPRESSURE) reads the same PC_SIG and is blind when the transducer, its supply or its wiring fails (it still trips '
                   'if only the ECU ADC path is lost: DESIGN, not tested on hardware); OVER_THRUST needs FC_THRUST, which is not armed on A1'
                   % human(C('kPcOverPressureAbs_Pa'))),
        ('detection', 'TLM_FAST d2-d3 = 0xFFFF, PC_VALID (TLM_RELIGHT d6 b7) clear, fault PC_SENSOR; RUN continues open loop'),
        ('mitigation', 'none for over-thrust on A1: recorded by the lead (RV3-12). R2 and the FC ABORT at t_E2 + pcf_tmax cover the no-thrust '
                       'side only (drogue held)'),
        ('source', CL.cite(181, 'A1 FMEA records', 260)),
        ('tag', 'DESIGN / LEAD; SIL v210-15, v210-16, S14')]),
        OrderedDict([
            ('id', 'FMEA-A1-FLAMEOUT-PCLOSS-DROGUE'),
            ('mode', 'undetected flame-out right after E2 with the Pc channel invalid, drogue attached (FLAMEOUT_OPT not yet armed, A3 suspended)'),
            ('effect', 'cold N2O flow gives apparent thrust that R2 can read as a light: without the hold F_cold %.1f N at the 200 N open-loop '
                       'lift (bound), released by R2 at the W10 < 6 m/s bound in S17 (dead vehicle released)' % nrc['dead_F_cold_mean_N']),
            ('detection', 'none in the ECU (Pc invalid); FC R2 on the accelerometer thrust'),
            ('mitigation', 'R2 command hold (LEAD 186 (2)): F_cold %.1f N at the hold lift, steady margin %.2f N at the W10 < 6 m/s bound; R2 '
                           'not met -> ABORT at t_E2 + 0.5 s, drogue descent (vehicle loss in the FMEA, no released dead vehicle). Not covered: '
                           'all-winds conditions (A1 HARD wind rule) and large chamber heat pick-up (TO-VERIFY)' % (w6['dead_F_cold_mean_N'], w6_margin)),
            ('source', CL.cite(186, 'cold-flow apparent thrust after an undetected flame-out', 300)),
            ('tag', 'DESIGN / LEAD; SIM test_core v210-17, S17; DERIVED Combustion v2.4a cold-flow bound')]),
        OrderedDict([
            ('id', 'FMEA-A1-LIT-PCLOSS-HOLD'),
            ('mode', 'lit relight with the Pc channel lost after E2 while the drogue is attached'),
            ('effect', 'thrust held at the start level until R2 releases (SIL plant %.1f N, not 62.5 N); a starved start below 37.16 N delays '
                       'R2 (S17 stand-in: release at E2 + %.0f ms, %.0f ms before pcf_tmax); a longer plateau ends in ABORT of a lit engine '
                       '(drogue descent)' % (f_lit_hold, lit17['fc_release_from_E2_ms'], 500.0 - lit17['fc_release_from_E2_ms'])),
            ('detection', 'TLM_FAST d2-d3 = 0xFFFF, PC_VALID clear; log tlm_flags b0 (hold active)'),
            ('mitigation', 'after the release the command returns at <= 2500 N/s; impulse lost during the hold and the ramp is GNC\'s trade'),
            ('source', 'LEAD CHANGELOG 186 (2); S17 lit_starved_pc_lost_hold_200N'),
            ('tag', 'SIM (S17); plateau stand-in')])]
    doc['pad_go_no_go_a1'] = OrderedDict([
        ('rule', 'every item GO before the A1 launch commit; one NO-GO stops the count. The ECU items are SIL evidence (v2.10) until B-ECU-1, '
                 'B-BLEED-1 and B-FC-1 pass on hardware'),
        ('items', [
            OrderedDict([('item', 'wind'), ('go', 'W10 < 6 m/s AND sigma_u(3 m) <= 1.0 m/s over the 10 min before ARM (anemometer at 3 m, BOM 250); '
                                                  'ground procedure, no ECU input'), ('source', CL.cite(181, 'HARD rule for A1', 200))]),
            OrderedDict([('item', 'Pc VALID'), ('go', 'TLM_RELIGHT d6 b7 = 1 (Pc channel valid AND no latched PC_SENSOR fault or abort)'),
                         ('source', 'LEAD CHANGELOG 175 (4); ECU v2.10 (test v210-15)')]),
            OrderedDict([('item', 'bleed closure'), ('go', 'before IGNITE: V1 and V2 commanded closed with the drivers inhibited, P_mid low, no EVENT '
                                                           'HBLEED leak/fault and no MV fault bit in TLM_FAST d6-d7. In the sequence: the pad BIT '
                                                           'S0-S4 runs in PREPRESS and aborts BLEED_FAULT before IGNITION if a step fails (its result '
                                                           'is not available at the launch commit)'),
                         ('source', 'combustion.json %s igniter.sequence.arm_preconditions; ECU v2.10 pad BIT' % comb.get('version'))]),
            OrderedDict([('item', 'ECU armed'), ('go', 'TLM_FAST state = ARMED; a refused ARM stays in SAFE with the inhibit cause latched as the '
                                                       'abort cause (DISARM clears it). TLM_RELIGHT d6 & 0x3F reads NOT_COAST (10) on the pad by '
                                                       'design'), ('source', 'ECU v2.10 armChecksOk')]),
            OrderedDict([('item', 'drogue echo'), ('go', 'TLM_RELIGHT d6 b6 = 0 after ARM (the accepted ARM resets the drogue state; the FC reports '
                                                         'the deployment in flight with Cmd::DROGUE 1)'),
                         ('source', 'LEAD CHANGELOG 186 (2); ECU v2.10 (test v210-17)')]),
            OrderedDict([('item', 'purge window'), ('go', 'CHK-PW passed on this board; PURGE_EN low at the pad (a stuck-high window chain is '
                                                          'latent to the ECU)'), ('source', 'LEAD CHANGELOG 166 (3); bench plan v3 CHK-PW')])]),
        ('bench_plan', '06-electronics/docs/bench_plan_v3.md, A1 pad go/no-go list')])
    h = OrderedDict(v1['harness_across_gimbal'])
    h['bundle'] = ('Pc (3 + shield), pintle servo HV69 (3 x AWG20 on PRAIL), pintle encoder (4 + shield), case TCs x2 + nozzle holder TC (K), '
                   'bore-top TC (stand), servo-bracket NTC (2), photodiode head lead (3, shielded) if the head sits on the engine side; V1 bleed '
                   'line -2 across the gimbal (Mechanical)')
    h['lengths'] = 'TO-DEFINE on the CAD solids'
    doc['harness_across_gimbal'] = h

    # ---------------------------------------------------------------------------------------------------- head-end bleed provision (v2.10)
    pm = bd['purge_mass']
    doc['head_end_bleed_provision'] = OrderedDict([
        ('architecture', tv('2 NC valves in series (V1 engine side of the decided path, V2), restrictors 2 x 0.707 mm upstream of V1 (1.0 mm '
                            'equivalent), P_mid 170BG between them on the LMV331 comparator into the pin 23 ladder; V1 = pin 15 AND PURGE_WIN, '
                            'V2 = pin 24 AND PURGE_WIN, low-side on +12V_ARM', 'DESIGN / LEAD 164, 166 (3)')),
        ('fitted', tv('build constant kHbleedFitted = %s; A1 build true unless CF-4 clears it; B1/B2 not fitted (J512 not fitted)' % human(C('kHbleedFitted')), 'LEAD')),
        ('schedule', OrderedDict([('purge_to_E0', C('kPurgeRelight_s')), ('flow_start', C('kPurgeFlowStart_s')), ('flow', C('kPurgeFlow_s')),
                                  ('flow_min_fc_planning', C('kPurgeFlowMin_s')), ('flow_end_lead', C('kPurgeFlowEndLead_s')),
                                  ('path_proof_extra_wait', C('kHbleedPathBy_s')), ('cap_both_open', C('kHbleedCap_s')),
                                  ('post_flow_hold_max', C('kPurgeHoldMax_s')),
                                  ('text', 'PURGE: MV open, pintle seated; fill step V1 only (path proof on P_mid); V2 opens; FLOW %s; V1 close command '
                                           '%s before E0 + its closing time; closure step: vent (P_mid low %d ticks) then hold test (%s); IGNITION '
                                           'never truncates the flow' % (human(C('kPurgeFlow_s')), human(C('kPurgeFlowEndLead_s')),
                                                                         int(C('kHbleedConfirmN')['v']), human(C('kHbleedHoldTest_s'))))])),
        ('closure_rule', tv('E1 = 2oo2 torch AND [closure confirmed OR deadline %s from E0]; flight: not confirmed -> BLEED_FAULT flag to the FC, '
                            'V2 commanded closed, relight proceeds; stand: abort' % human(C('kTorchGate_s')), 'LEAD CHANGELOG 166 (3)')),
        ('achieved_flow_report', 'EVENT PURGE_FLOW 0x21 arg = flow time [ms] DERIVED from the valve commands (a valve that failed closed still '
                                 'reports the commanded time: P_mid cannot see it on the decided path)'),
        ('mass', OrderedDict([('limit_g', tv(76, 'LEAD')), ('rows', pm['rows']), ('flow_for_76g_comb_s', pm['flow_for_76g_comb_s']),
                              ('basis', pm['basis']), ('quantity', pm['quantity']),
                              ('finding', 'CONTRADICTION kept: the firmware cap (both open 2.61 s, flow ~2.66 s) allows 77.7 g on the Combustion '
                                          'basis and 83.6 g on the SIL basis, above 76 g; the hardware window bounds ~96 g (Combustion basis). '
                                          'The cap would have to be <= 2.553 s to hold 76 g on the Combustion basis: lead decision, not changed')])),
        ('hardware_window', OrderedDict((k, hw[k]) for k in ('t_nom_s', 't_min_s', 't_max_s', 'powered_span_needed_s', 'margin_min_s', 'covers',
                                                              'cap_equal_window_would_cut_flow'))),
        ('pad_bit', 'PREPRESS steps S0-S4 (valve pattern vs P_mid); any failure -> BLEED_FAULT; a missing purge window fails S2 (V1 not opening)'),
        ('leak_monitor', tv('both commanded closed: P_mid high for %s -> flight flag + EVENT, stand BLEED_FAULT' % human(C('kHbleedLeakTime_s')), 'DESIGN')),
        ('ladder', hbp['ladder']), ('pmid_comparator', hbp['pmid_comparator']),
        ('sil_s12', OrderedDict([('cases', len(s12['cases'])), ('pass', sum(1 for c in s12['cases'] if c['pass'])),
                                 ('mass_over_limit_cases', s12['mass_over_limit_cases']), ('mass_note', s12.get('mass_note'))])),
        ('sil_s11_fault_path_v4', [OrderedDict([('run', r['tag']), ('unreached_cm3', r['unreached_cm3']),
                                                ('cases', [OrderedDict([('case', c['case']), ('V_cm3', c['V_cm3']), ('first_abort', c['first_abort']),
                                                                        ('cmd_to_E2_s', c['cmd_to_E2_s'])]) for c in r['cases']])]) for r in fp4['runs']]),
        ('naming_note', 'SIL case names "purge_integrated" are kept for continuity; since LEAD 175 they send FC PURGE then RELIGHT 1 ms later'),
    ])
    doc['log_v11'] = tv('LogRecord v11 = 179 bytes at 1 kHz (v10 + LIGHT_SPIKE record, bleed hb2/flow ms, fa1, photodiode mV, dark mV, fault2, '
                        'safing_left_s; t_us wraps byte, TC invalid marker)', 'DESIGN protocol.h')

    # ---------------------------------------------------------------------------------------------------- GSE, BOM, bench plan
    doc['gse_interface'] = OrderedDict([
        ('arming_plug', 'J301 XT30, remove-before-flight shorting link; removes the ARM bus in hardware'),
        ('mode_strap', 'J620 [MODE_A, MODE_B, GND]: FLIGHT or STAND plug; open or both = invalid -> ARM refused'),
        ('heater_permit', 'J616 [HTR_ILK_SW, GND]: low-side permit for the GSE tank heater, <= 28 V and <= 1 A; SAFE only'),
        ('can', 'J201 to the FC (flight) or the test-stand box'),
        ('purge_enable', 'J512 [PURGE_EN_IN, GND] from the FC (flight) or the stand box: hardware purge window'),
        ('stand_arm_loop', 'burst-disc break-wire in series with the stand ARM loop'),
        ('anemometer', 'GSE anemometer at 3 m (launch commit wind rule, BOM v2.2 section I)'),
        ('umbilical', v1['power_budget'].get('ground_power'))])
    doc['bom'] = OrderedDict([('file', '06-electronics/results/bom_v2p2.csv (v2.2)'), ('summary', bom)])
    doc['bench_plan'] = OrderedDict([
        ('file', '06-electronics/docs/bench_plan_v3.md'),
        ('tests', ['RE-15 checks', 'HAL-1', 'B-PWR-1', 'B-PWR-2', 'B-ECU-1', 'B-PT-1', 'B-PC-1', 'B-DPC-1', 'B-MV-1', 'B-PNT-1', 'B-TVC-1',
                   'CHK-PW', 'B-BLEED-1', 'B-IGN-1', 'B-FC-1', 'B-SAFE-1', 'HIL-OT-1', 'HIL-TR-1', 'HIL-RST-1', 'LEAK-1', 'CF-3', 'CF-4',
                   'IGN-1', 'T1-T4 F_acc'])])

    # ---------------------------------------------------------------------------------------------------- open issues
    def oi(i, sev, issue, owner, closure=None):
        d = OrderedDict([('id', i), ('severity', sev), ('issue', issue), ('owner', owner)])
        if closure:
            d['closure'] = closure
        return d
    gt = rg['generators']['gen_tables.py']
    gm = rg['generators']['gen_mech_params.py']
    if gt['regenerated']:
        raise SystemExit('gen_headers_regen_check: gen_tables regenerated - review OI-GEN-TABLES text before publishing')
    ck = rg['combustion_read_keys']['by_key']
    num_same = [k for k, v in ck.items() if not (v['changed_numeric'] or v['added_numeric'])]
    num_diff = ['%s (%d numeric leaves changed, %d added, %d removed leaves)' % (k, len(v['changed_numeric']), len(v['added_numeric']), v['removed'])
                for k, v in ck.items() if k not in num_same]
    txt_only = [k for k in num_same if ck[k]['changed_text'] or ck[k]['added'] or ck[k]['removed']]
    mech_code = sum(h['changed_code_lines'] for h in gm['headers'].values())
    gen_tables_issue = ('gen_tables.py v3.3 cannot parse combustion.json %s (%s); engine_params.h / plant_tables.h / gnc_tables.h / '
                        'valve_map_table.h stay generated from combustion.json v2.3 (manifest HISTORICAL). Keys the generator reads, v2.3 vs %s: '
                        'numeric leaves identical in %s (text/tag changes only in %s); %s [DERIVED results/gen_headers_regen_check_v2p10.json]. '
                        'The v2.4 epoch values in use were entered by '
                        'hand in config.h with tags (torch gate, W, E2 rule, LIGHT_SPIKE). Values in use with NO source text in combustion.json %s: start ramp '
                        '%s, spark train %s, propane-off Pc backstop %s abs, timing-only lift time %s -> Combustion to confirm or replace. '
                        'mechanical.json %s regeneration: %d code lines differ (comment lines only)'
                        % (rg['combustion_read_keys']['now']['version'], gt['stderr_tail'][0] if gt['stderr_tail'] else 'generator failed',
                           rg['combustion_read_keys']['now']['version'], ', '.join(num_same), ', '.join(txt_only) or 'none', '; '.join(num_diff),
                           rg['combustion_read_keys']['now']['version'], human(C('kStartRamp_Nps')), human(C('kSparkTrain_s', 'eng')), human(C('kPropaneOffPcAbs_Pa', 'eng')),
                           human(C('kTimingOnlyLiftAt_s')), mech.get('version'), mech_code))
    # ---------------------------------------------------------------------------------------------------- OI-37 hygiene (LEAD 186 (4))
    flow_end = -C('kPurgeRelight_s')['v'] + C('kPurgeFlowStart_s')['v'] + C('kPurgeFlow_s')['v']
    doc['oi37_interface_hygiene'] = OrderedDict([
        ('decision', CL.cite(186, '(4) OI-37 interface configuration', 520)),
        ('A5', OrderedDict([
            ('status', 'removed: no A5 monitor, abort or key outside the history keys (change_summary_v2_to_v3, superseded_v2, this record); '
                       'the late-light record is start_monitors.light_spike_record (LIGHT_SPIKE, log and EVENT 0x20, no abort)'),
            ('remaining_tokens', 'the ABORT frame magic byte 0xA5 (protocol constant, unrelated) and the Teensy analog pin names in ecu.pin_map, '
                                 'written as "Teensy analog pin A<n>" (pin 19 = A5, V5SNS_SENSE); the hardware CSV keeps the bare pin label'),
            ('check', 'self_check.a5_token_scan')])),
        ('rejected_bleed_valve', OrderedDict([
            ('status', 'no bleed valve is named in v3; the v2 coil entry and OI-BLEED-COIL are superseded (superseded_v2)'),
            ('bom', 'bom_v2p2 J509/J510 is a specification row; the Burkert 6027 family is recorded as screened and NOT qualifying (1.5 mm: Kv '
                    '0.07 < 0.11 m3/h; the 6027 HP 1.0 mm was rejected in LEAD 160 (6)); no qualifying candidate yet (OI-BLEED-VALVE)')])),
        ('hold_2s', OrderedDict([
            ('v2', 'kPurgeHoldMax_s 2.0 s: post-flow hold with the bleed valves OPEN, up to 4.5 s after PURGE (firmware v2.9 config.h; the v2 '
                   'interface text did not state the value: REV-ELEC-1 R19 and REVIEW-COMBUSTION-R2 R2-13 read it from the firmware)'),
            ('v3', tv('%s with the bleed CLOSED, counted from the scheduled E0; no RELIGHT by then -> purge expired, COAST'
                      % human(C('kPurgeHoldMax_s')), 'DESIGN config.h kPurgeHoldMax_s')),
            ('decided_sequence', 'Cmd::PURGE at E0 - %s; flow from PURGE + %s for %s; the flow ends %.0f ms before E0 (computed from these '
                                 'three constants; flow_end_lead %s); a RELIGHT during the purge ignites at E0; both-open cap %s'
                                 % (human(C('kPurgeRelight_s')), human(C('kPurgeFlowStart_s')), human(C('kPurgeFlow_s')), -flow_end * 1e3,
                                    human(C('kPurgeFlowEndLead_s')), human(C('kHbleedCap_s')))),
            ('schedule_consistent', abs(flow_end + C('kPurgeFlowEndLead_s')['v']) < 1e-6),
            ('schedule_consistent_note', 'true by construction: config.h derives kPurgeFlowStart_s = kPurgeRelight_s - kPurgeFlowEndLead_s - '
                                         'kPurgeFlow_s; the check catches an edit that breaks the derivation and is not an independent '
                                         'confirmation of the sequence'),
            ('check', 'in the decided sequence the valves are never held open after the flow; the post-flow hold is only the ECU tolerance for a '
                      'RELIGHT later than E0. Combustion\'s tolerance of a later E0 (static soak after the flow) is UNKNOWN (requests: Combustion, '
                      'kPurgeHoldMax_s basis)')])),
        ('scope', 'interface text hygiene only; not a design review')])
    doc['open_issues'] = [
        oi('OI-HAL', 'HIGH', 'Teensy HAL not written (RE-06); TLM_SLOW undefined; 93 ARM double-promotion warnings', 'Electronics', 'HAL-1, B-ECU-1'),
        oi('OI-POWER', 'HIGH', 'RE-09: +12V_ARM and ARM bus over rating in purge and E0 overlaps; time-resolved budget, sequencing and peak-and-hold not done', 'Electronics', 'B-PWR-2'),
        oi('OI-BLEED-VALVE', 'HIGH', 'bleed valve not selected; peak-and-hold not drawn; valve times ASSUMED (30/80 ms)', 'Electronics / Mechanical', 'B-BLEED-1'),
        oi('OI-PURGE-CAP', 'HIGH', 'firmware cap allows 77.7 g (COMB basis) / 83.6 g (SIL basis) VENTED N2O > 76 g; hardware window bound ~96 g '
           'vented; tank liquid depletion is larger (81.6 g at 73.0 g vented, LEAD 181 (10))', 'LEAD', 'decision on the cap; B-BLEED-1 mass'),
        oi('OI-WINDOW-LATENT', 'MEDIUM', 'stuck-high purge-window chain invisible to the ECU; pre-flight check with PURGE_EN low not implemented', 'Electronics / FC owner', 'CHK-PW; firmware BIT step'),
        oi('OI-BLEED-DETECT', 'MEDIUM', 'S12 (SIM): V1 stuck open with V2 closed not detected on the stand and flagged 5.05 s after injection in the flight first burn '
           '(P_mid below the comparator band on the decided path); flow time reported from commands', 'Electronics / LEAD', 'B-BLEED-1'),
        oi('OI-RE02-CRITERIA', 'MEDIUM', 'S13 B extension: lead criteria fail 32/164 (kBpc1Shown false) and 64/164 (true): BASE_HIGH refusals and torch-gate blocking are by design', 'LEAD', 'criteria restated per class'),
        oi('OI-TEB-FALSE-LIGHT', 'MEDIUM', 'S9 +/-1.034 bar TEB cases fail as in v2.9', 'LEAD / Electronics', 'B-PC-1 <= 0.3 bar'),
        oi('OI-GUARD-BAND', 'MEDIUM', 'uncalibrated P_tank interlock needs the tank <= ~19.8 C; wall-vs-bulk offset MISSING. Cold edge (SIM): S5/S15 runs '
           '125 and 127 (T_tank0 15.06 / 15.03 C) pass ARM and are refused TANK_COLD at IGNITE (ECU holds PREPRESS until SHUTDOWN); the S5/S15 '
           'summaries did not classify them (results/sil_v2p10_probe_s5_unclassified_runs.txt); countdown margin above 15 C MISSING',
           'Electronics / Mechanical', 'B-PT-1; SIL summary classification of start refusals'),
        oi('OI-E2-LATENCY', 'LOW', 'E2 - light 14-15 ms in S5/S15, 16-18 ms at the A1 relight (SIL)', 'Combustion / Electronics', 'IGN-1'),
        oi('OI-RE15', 'HIGH', 'no layout; pin-function check, footprints, derating table not done', 'Electronics', 'RE-15 checks before fabrication'),
        oi('OI-GIMBAL-JAM', 'MEDIUM', 'S6 gimbal_jam_moving_cmd: small-amplitude jam undetected (RE-24 dispositioned)', 'Electronics + GNC', 'B-TVC-1'),
        oi('OI-TB-MEOP', 'ACCEPTED', 'S6 throat block Pc 53.4 bar abs > MEOP for 72 ms', 'Mechanical FEA', 'LC-TB70 / LC-TB-S'),
        oi('OI-FC', 'HIGH', 'FC: PURGE_EN discrete, R2 drogue rule with pcf_tmax / threshold / baseline as parameters, PURGE commit L* parameter '
           '(1.3 s, LEAD 186 (1)) with no unpurged RELIGHT below it, Cmd::DROGUE reports and the TLM_RELIGHT d6 b6 echo check (LEAD 186 (2)), '
           'FC_THRUST valid flag clear on A1, PC_VALID launch commit, IMU filter delay', 'FC owner + GNC', 'B-FC-1, HIL-OT-1'),
        oi('OI-38-R2-COMMAND-HOLD', 'HIGH', 'R2 command hold (LEAD 186 (2)) implemented in the ECU and shown in SIL only (test_core v210-17, S17 '
           'with an Electronics FC stand-in). Open: the FC side (DROGUE reports, echo check); GNC R2 v2 with F_cold plus the grain_q1d '
           'start-level lit history (LEAD 194 (4)); steady margin %.2f N at the W10 < 6 m/s bound, the 16.31 N margin CONDITIONAL on '
           'Cd x A x G at the start lift (CF-3 start-lift point; heat TO-VERIFY = injector-body / feed soak-back); hold lift 0.2154 mm '
           '(S17) vs start level 0.2039 mm (194 (4)) not reconciled; 1-2 R2 frames above the threshold from the lit plateau '
           'through the estimator lag (3-frame persistence holds); lit hold thrust %.1f N in the SIL plant (map at the A1 state)'
           % (w6_margin, f_lit_hold), 'GNC (FC) / Combustion / Electronics',
           'GNC R2 v2 (sim6 V); B-FC-1 DROGUE echo and hold on hardware; CF-3 start-lift point (acceptance per LEAD 194 (4))'),
        oi('OI-FA1-PC-OVERRANGE', 'HIGH', 'FA-1 at the A1 relight (LEAD 194 (7), pc_overrange_fa1): v2.10 aborts it in %d-%d of %d grid cases '
           '(firmware filtered 30 bar / 5 ms HARD_START, hardware comparator; the 4.75 V over-range HARD_START with a fast transducer or line '
           'amplification); a reading >= 4.75 V latches PC_VALID 0 for the power cycle; the 1 kHz log under-reads the peak and does not '
           'flag readings above full scale below 4.75 V; 070BG saturation level and recovery MISSING; port pressure behind the 0.3 m line '
           'vs the 141.0 bar abs proof not shown (194 (1) design-change candidate)'
           % (min(f['cases_any_abort_path_nominal'] for f in fall), max(f['cases_any_abort_path_nominal'] for f in fall), n_fa1),
           'LEAD (abort or ride-through) / Electronics / Mechanical (line period) / founders (B-PC-1, B-DPC-1, TE inquiry)',
           'LEAD decision; B-PC-1 over-range row; B-DPC-1 head + line end at IGN-1 / T series; v2.11 firmware items if adopted'),
        oi('OI-A1-PCLOSS-OVERTHRUST', 'ACCEPTED (FMEA record)', 'A1: no over-thrust detector after an in-flight Pc loss (see fmea_rows_a1)',
           'LEAD / GNC', 'none on A1; RG-16 budget before FC_THRUST is armed on any mission'),
        oi('OI-STAND-LATE-LIGHT', 'LOW', 'S15 stand: 4 of 239 lit plants end NO_IGNITION (light later than the stand W); fail-safe by design', 'Combustion / LEAD', 'IGN-1'),
        oi('OI-UNPURGED-RELIGHT', 'MEDIUM', 'Combustion %s purge_commit_rule_v2p4a finds the unpurged branch REFUTED as written (A3 after the drogue '
           'release in %.3f of LO worst starts); LEAD 186 (1) decided: below L* = 1.3 s no unpurged relight on that pass (FC rule). ECU v2.10 '
           'still accepts an unpurged RELIGHT; its stated reason (GNC\'s E2 + 0.22 s held-release alternative) is WITHDRAWN by LEAD 194 '
           '(3): the alternative is a GNC comparator only and is not admissible with Pc invalid. Open: (a) an ECU guard that refuses an '
           'unpurged RELIGHT unless keyed is offered, NOT implemented, and no flight use now opposes it; (b) a ride-through (torch kept on, A3 adapted through the gap) is NOT implemented (kTorchHoldAfterLight_s is 0); '
           '(c) Combustion\'s latency model takes E2 as Pc > 3 bar abs (withdrawn, LEAD 134) while the ECU flight E2 is the relative rule: '
           'its timing against the gap is checked by neither side' % (comb.get('version'), unp['released_then_A3_unlined_LO_worst']),
           'LEAD / Combustion / GNC (FC)', 'FC rule in the FSW record (B-FC-1); LEAD on the ECU guard; GNC comparator (194 (3)); CF-4 O-3, IGN-1'),
        oi('OI-GEN-TABLES', 'MEDIUM', gen_tables_issue, 'Electronics (parser) + Combustion (values)',
           'gen_tables v3.4 parser for the epoch sequence, regenerate, diff, re-run the SIL record'),
    ]
    doc['requests'] = [
        'FC owner: PURGE_EN discrete on J512 (timing per ecu.purge_window.fc_icd), R2 drogue rule and ABORT use, PC_VALID launch commit',
        'FC owner (LEAD 181, 186 (1)): pcf_tmax (0.5 s), the R2 threshold (37.16 N) and the baseline reference as parameters in the FSW '
        'record; the PURGE commit lead L* (1.3 s) as a parameter, with no unpurged RELIGHT below it; FC_THRUST valid flag clear on A1',
        'FC owner (LEAD 186 (2)): CMD_STATE DROGUE (17) arg 1 at the deployment and arg 0 at the release; check TLM_RELIGHT d6 b6 before a '
        'RELIGHT; state when R2 starts counting after a Pc loss',
        'GNC (LEAD 186 (2), 194 (4)): R2 v2 with F_cold plus the grain_q1d start-level lit history (0.2039 mm) and the hold command '
        'profile (start level until the release, then <= 2500 N/s); note that the ECU commands %.4f mm in the hold (S17, bound %.2f N); report '
        'the frames above 37.16 N carried from the lit phase through the estimator lag (S17: up to %d in a row at the W10 < 6 m/s bound)'
        % (w6['dead_lift_mean_mm'], w6['dead_F_cold_mean_N'],
                                                                         max(w6['R2_max_consecutive_frames_at_or_above_threshold'],
                                                                             w6b['R2_max_consecutive_frames_at_or_above_threshold'])),
        gnc_purge_request(gnc, bd),
        'Mechanical: transducer temperature MECO -> RELIGHT for the drift budget (RE-07); bleed valve mass and mounting once selected',
        'Combustion: bleed flow on the decided path for B-BLEED-1 pass/fail; tolerance of a later E0 after the flow (kPurgeHoldMax_s basis)',
        'Combustion: confirm or replace the four sequence values without source text in combustion.json %s (OI-GEN-TABLES); keep the epoch '
        'sequence machine-readable (one field per value) so the table generator can read it' % comb.get('version'),
        'Combustion (%s): the closure deadline attributed to Electronics as E0 + 0.15 s in igniter.sequence start[0], abort_matrix_v2p4 A14 and '
        'cf4_gate pass_criteria[5] is stale; ECU v2.10 uses the torch gate, E0 + %s (kTorchGate_s); drogue_release_hold.line175_5_note_v2p4a '
        'still gives the drogue-hold abort at t_E2 + 0.8 s (LEAD 181 (4): pcf_tmax 0.5 s, an FC parameter); restate igniter.sequence start[0].'
        'action and purge_commit_rule_v2p4a.rule_LEAD_175_3 per LEAD 186 (1): both still give the interim 1.7 s and an unpurged relight with '
        'no commit; now L* = 1.3 s, below it no purge and no unpurged relight on that pass, and the withdrawn T_fire-delay basis removed' % (comb.get('version'), human(C('kTorchGate_s'))),
        'Combustion (LEAD 194 (4)): injector-body and feed soak-back temperature at the relight (heat at tank pressure, threshold '
        '2.8-3.7 kW) for the start-level cold-flow bound (S17 steady margin %.2f N at the W10 < 6 m/s bound); the cold_flow setting text '
        'should name FLAMEOUT_OPT (photodiode, armed after the view is proven) next to A3' % w6_margin,
        'Combustion (LEAD 194 (1), (7)): the v2.4b head spectrum at the sense-line period (SIL line about 6 ms, ASSUMED geometry) for the '
        '070BG port; FA-1 histories beyond 25 ms (the over-range run holds P_at_25ms)',
        'Mechanical (LEAD 194 (1)): list the Pc port and sense line with their period and basis (geometry: length, ID, end volume, routing); '
        'until then the 070BG port is at FA1S, above its proof',
        'LEAD: purge cap vs 76 g; S13 B-extension criteria per class; RE-12 flight extension of the A7 blank; RE-24 bound acceptance; '
        'the ECU guard for an unpurged RELIGHT (OI-UNPURGED-RELIGHT (a): offered, not implemented; with 194 (3) no flight use of an '
        'unpurged RELIGHT remains, so Electronics recommends the guard for v2.11: flight build refuses a RELIGHT with no PURGE since the '
        'last burn unless keyed, stand unchanged)',
        'LEAD (194 (7), OI-FA1-PC-OVERRANGE): FA-1 at the A1 relight - abort as built or ride-through; the PC_VALID latch and the '
        'above-full-scale flag (v2.11 items offered); the 070BG port vs proof under 194 (1)',
        'Founders: bench instruments owned (scope, e-load, PSU, DAQ) so BOM section H can drop those lines; B-DPC-1 113B22 x 3 + NI 9234 '
        'and the hydraulic pump (BOM 237 / 238 / 245) TO-QUOTE delivered to Soenderborg DK-6400; TE inquiry on the 070BG over-range']
    doc['rev_elec_1_author_status'] = OrderedDict([
        ('note', 'Electronics statement for the reviewer; acceptance is the reviewer\'s'),
        ('CLOSED_in_SIL_or_document', ['RE-01', 'RE-03', 'RE-04', 'RE-08', 'RE-11', 'RE-12', 'RE-13', 'RE-14', 'RE-16', 'RE-17', 'RE-18', 'RE-19', 'RE-20',
                                       'RE-21', 'RE-22', 'RE-23', 'RE-25']),
        ('OPEN', ['RE-02 (partly done: rule implemented and unit-tested; S13 B criteria conflict with the rule, LEAD)',
                  'RE-05 (partly done: firmware + hardware purge window; no qualifying valve, peak-and-hold not designed, cap vs 76 g open)',
                  'RE-06 (not done: Teensy HAL not written)',
                  'RE-07 (partly done: firmware + SIL coast drift cases; B-PC-1 drift measurement open)',
                  'RE-09 (not done: time-resolved power budget, sequencing, peak-and-hold)',
                  'RE-10 (partly done: P_mid level and closure from ASSUMED valve times; final path timing open until B-BLEED-1)',
                  'RE-15 (not done: no layout; pin-function check, footprints, derating table)',
                  'RE-28 (not done on hardware: HIL-RST-1 written in bench plan v3; no in-flight recovery path by LEAD decision)']),
        ('DISPOSITIONED', ['RE-24 (S6 small-amplitude jam undetected below the SIL command bound; B-TVC-1 measures the bound; LEAD to accept)',
                           'RE-26 (no A7 rate criterion; the review accepted the stated reason; unchanged)',
                           'RE-27 (TLM_FAST has CAN CRC-15 only, no application CRC; b4 persists to the next IGNITION, harmless under the RUN-state '
                           'gate if the FC implements it; checked in HIL)',
                           'RE-29 (stale entries owned by other disciplines: sent as requests to their owners and the LEAD)'])])

    # ---------------------------------------------------------------------------------------------------- self-check record + stale scan
    scan = json.dumps(OrderedDict((k, v) for k, v in doc.items() if k not in HISTORY_KEYS), ensure_ascii=False)
    stale_found = [s for s in STALE_STRINGS if s in scan]
    if stale_found:
        raise SystemExit('stale strings in v3 outside the history keys: %s' % stale_found)
    n_a5, n_a5_ok = len(re.findall(r'\bA5\b', scan)), scan.count(A5_ALLOWED)
    if n_a5 != n_a5_ok:   # LEAD CHANGELOG 186 (4): A5 removed (deleted, line 160); hex 0xA5 does not match \bA5\b
        raise SystemExit('A5 token outside the history keys: %d found, %d allowed (%s)' % (n_a5, n_a5_ok, A5_ALLOWED))
    doc['self_check'] = OrderedDict([
        ('abort_matrix', OrderedDict([('causes', len(matrix)), ('enum_causes', len(abort_enum) - 1),
                                      ('constants_quoted', sum(len(c['thresholds']) for c in matrix)),
                                      ('rule', 'trigger numbers only from config.h placeholders; every listed constant quoted; none unresolved'),
                                      ('result', 'PASS')])),
        ('firmware_version', '%s (config.h stamp = Makefile header)' % fw_ver),
        ('schematic_version', '%s (generator REV = KiCad root rev = pin map rows)' % rev),
        ('relight_keys', 'read at gnc.json requirements.ignition.relight_planning_value_s'),
        ('sil_manifest', 'firmware_version matches; every binary identical to a rebuild of the current tree'),
        ('stale_strings_absent', STALE_STRINGS),
        ('a5_token_scan', 'stand-alone A5 tokens outside %s: %d, all of them "%s" (LEAD CHANGELOG 186 (4))' % (', '.join(HISTORY_KEYS), n_a5, A5_ALLOWED)),
        ('scope', 'consistency of this file with its sources only; not a check of the design or of hardware')])
    doc['inputs']['files_read_sha256_16'] = READ
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('electronics.json v3 -> %s (%d top-level keys, %d abort causes, %d constants quoted, %d pins, %d open issues; firmware %s, schematic %s)'
          % (a.out, len(doc), len(matrix), sum(len(c['thresholds']) for c in matrix), len(pins), len(doc['open_issues']), fw_ver, rev))


if __name__ == '__main__':
    main()
