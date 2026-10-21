#!/usr/bin/env python3
"""Build electronics.json v4 (Electronics, 06-electronics), firmware v2.11, for STAGING (LEAD brief 2026-10-20, item B7).

Supersedes electronics.json v3 (hub interfaces/electronics.json, 38bf149f368c1d4c, firmware v2.10). The hub file stays as it is: this
script writes results/electronics_v4.json, which is staged under 06-electronics/staging_v2.11/; the lead verifies and promotes.

Base: the v3 hub file is read and asserted (version v3, sha256/16); sections whose content changed in v2.11 are rebuilt here from the
files that own the numbers (config.h through the v3 generator's preprocessor / constexpr evaluator, the SIL v2.11 record, the v2.11 calc
results, the interfaces and the CHANGELOG); unchanged sections are carried from v3 with the stale leaves listed in
change_summary_v3_to_v4 corrected. The v3 history keys (change_summary_v2_to_v3, superseded_v2, oi37_interface_hygiene) are not carried
(they stay readable in v3); the v4 history keys are change_summary_v3_to_v4, superseded_v3 and changelog_folding.

Reuses calc/make_interface_json_v3.py (imported as G3): rd / READ (every file read is recorded with sha256/16), Cfg (flight build:
no macro defined), human, Changelog.cite (the marker must be present on the cited line), render and template_check (abort-matrix
triggers hold numbers only through config.h placeholders).

Self-check (fails the build): abort matrix = types.h enum (31 causes) with every template passing template_check; config.h stamp =
Makefile header; SIL manifest firmware_version = the stamp and every binary identical to a rebuild of the current tree; stale-string
scan outside the history keys (v3 list + v4 list, with context allowances for values that are quoted as history); the stand-alone A5
token rule of LEAD 186 (4); structural checks (Pc transducer = C1, case-TC abort = 423.15 K, cap 2.55 s, R2 window 0.8 s).
Nothing here is hardware validation: SIL, calculation and schematic checks only.

Usage: PYTHONDONTWRITEBYTECODE=1 python3 calc/v2p11/make_interface_json_v4.py [--engine-root ...] [--out results/electronics_v4.json]
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..')))
import make_interface_json_v3 as G3   # noqa: E402  (v3 generator helpers; its main() is not run)

ROOT = G3.ROOT
RES = G3.RES
FWD = G3.FWD
CORE = G3.CORE
SIL = os.path.join(RES, 'sil_v2p11')
READ = G3.READ
tv = G3.tv
_human_v3 = G3.human


def human(c):
    """v3 rendering, except a kelvin DIFFERENCE (|v| < 100 K: no absolute temperature in these headers is that low) is shown in K only
    (v3 rendered e.g. kTankWallUnc_K 0.56 K as '0.56 K (-272.6 C)')."""
    if c.get('unit') == 'K' and isinstance(c.get('v'), float) and abs(c['v']) < 100.0:
        return '%.2f K' % c['v']
    return _human_v3(c)


G3.human = human   # G3.render resolves human at call time: the abort-matrix templates use the same rule
G3.UNIT.append(('_kg', 'kg'))   # v2.11 constants in kg (kPurgeVentLimit_kg); appended after _kgps so that suffix wins


def rel(p):
    return os.path.relpath(p, ROOT) if p.startswith(ROOT) else p


def rd(path, mode='r'):
    return G3.rd(path, mode)


def jload(path):
    t = rd(path)
    t = re.sub(r'-?\binf(inity)?\b', 'null', re.sub(r'\bnan\b', 'null', t, flags=re.I), flags=re.I)
    return json.loads(t, object_pairs_hook=OrderedDict)


def sha(path):
    if rel(path) not in READ:
        rd(path, 'rb')   # a cited file is read here if no earlier step read it (the hash is of the file as read at generation)
    return READ[rel(path)]


def shr(path):
    rd(path, 'rb')   # read (records the hash in READ), then cite
    return sha(path)


def r(x, n=3):
    return None if x is None else round(float(x), n)


def bar(pa, n=2):
    return round(pa / 1e5, n)


# ------------------------------------------------------------------------------------------------ abort matrix v4 (templates)
# Numbers in a trigger come ONLY from {kName} / {eng:kName} placeholders (G3.template_check). Lead decisions are cited in 'decision'.
AB4 = copy.deepcopy(G3.AB)
AB4['HARD_START'] = (
    'IGNITION, or RUN within {kRunSettle_s} of entry: filtered absolute Pc above {kPcOverPressureAbs_Pa} abs for {kPcOverPressureTime_s} '
    '(RE-20, filtered channel); in IGNITION a Pc transducer output at or above {kPcSensorMax_V} (a high over-range is taken as real '
    'pressure; flight: the over-range bit is non-sticky and PC_SENSOR is not latched, stand as built). Ride-through BUILD OPTION '
    '(kRideThroughBuild = {kRideThroughBuild} in the flight build: OFF; flight relight only, from E1 to E2 + {kRideWinPostE2_s}): the '
    'filtered persistence becomes {kRideOvpTime_s}, the IGNITION over-range rule needs {kRideOverrangeN} consecutive over-range readings, '
    'and a raw reading above the MEOP {kPcMeopLeadAbs_Pa} abs held for {kRideT45_s} aborts at once (T45 guard); the hardware comparator '
    'RC of that BOM variant is FIXED at {kRideCmpTauNom_s} nominal. No late-light abort (the v2.9 pressure hold is deleted, RE-01): a '
    'LIGHT_SPIKE record is logged from {kLightSpikeLoAbs_Pa} abs (EVENT 0x20) with the above-full-scale flag at {kPcAboveFs_V}',
    ['kRunSettle_s', 'kPcOverPressureAbs_Pa', 'kPcOverPressureTime_s', 'kPcSensorMax_V', 'kRideThroughBuild', 'kRideWinPostE2_s',
     'kRideOvpTime_s', 'kRideOverrangeN', 'kPcMeopLeadAbs_Pa', 'kRideT45_s', 'kRideCmpTauNom_s', 'kLightSpikeLoAbs_Pa', 'kPcAboveFs_V'])
AB4['OVER_TEMP'] = (
    'case TC (TC1 / TC2) above {kCaseOverTemp_K} or nozzle holder (TC3) above {kNozzleHolderOverTemp_K} for {kOverTempTime_s} in a burn, '
    'PREPRESS or PURGE (the persistence spans two to three MAX31856 conversions); ARM refused with this cause when TC1 or TC2 reads above '
    'the start limit {kCaseRelightMax_K} or TC3 above {kNozzleHolderOverTemp_K}, and unless BOTH case TCs are valid (RE-08); a start '
    'command (IGNITE / RELIGHT) in COAST above {kCaseRelightMax_K} is refused CASE_HOT; one TC lost: continue on the other; both lost: '
    'stand treated hot, flight burn continues and the relight is refused (CASE_HOT). Servo-bracket NTC above {kServoBracketOverTemp_K} '
    'only flags',
    ['kCaseOverTemp_K', 'kNozzleHolderOverTemp_K', 'kOverTempTime_s', 'kCaseRelightMax_K', 'kServoBracketOverTemp_K'])
AB4['PC_SENSOR'] = (
    'transducer output outside {kPcSensorMin_V} to {kPcSensorMax_V}: IGNITION abort (low side), stand RUN abort after '
    '{kPcSensorLossStand_s}, flight RUN continues open loop; flight high over-range is non-sticky (kPcOverrangeNonSticky = '
    '{kPcOverrangeNonSticky}: PC_VALID cleared on the over-range readings only, no PC_SENSOR latch), stand as built (latched); A7 plausibility '
    'band outside for {kA7Time_s} (HOLD band low edge P0 minus {kA7HoldLow_Pa}; START high side blanked from E2 for {kA7StartHiBlank_s} on '
    'the stand and in flight): IGNITION and stand abort, flight RUN flag once per burn; RE-02 baseline per location: on the pad first '
    'start and on the stand the lift is refused when P0 is above the auto-zero ambient by more than {kIgnBaseCheck_Pa} (BASE_HIGH) or '
    'below it by more than that (BASE_AMB); the A1 relight keeps the measured P0 on BASE_HIGH and sets P0 to zero on BASE_AMB; ARM: '
    '|Pc| above {kPcArmZeroMax_Pa} before the auto-zero',
    ['kPcSensorMin_V', 'kPcSensorMax_V', 'kPcSensorLossStand_s', 'kPcOverrangeNonSticky', 'kA7Time_s', 'kA7HoldLow_Pa',
     'kA7StartHiBlank_s', 'kIgnBaseCheck_Pa', 'kPcArmZeroMax_Pa'])
AB4['HW_OVERPRESSURE'] = (
    'hardware comparator U330 on the C1 Pc chain (INA333 output before the ADC; tap RC, trip and band in thresholds_hardware) sets the '
    'U331 latch: ARM bus off in hardware, independent of the firmware; the firmware reports HW_OVERPRESSURE after OVP_OK low for '
    '{kHwOvpTime_s} (OVP_OK ignored for {kHwOvpArmSettle_s} after ARM_REQ rises)',
    ['kHwOvpTime_s', 'kHwOvpArmSettle_s'])
AB4['TANK_COLD'] = (
    'ARM refused when no valid tank temperature exists or the coldest tank estimate (lower of the wall DS18B20 readings and Tsat(P_tank)) '
    'is below {kTankIgnMin_K} plus the ARM margin {kTankColdArmMargin_K} (sized from the PREPRESS Tsat drop {kTankColdPrepressDrop_K} '
    'with a factor and the repeatability {kTankColdRepeat_K}); IGNITE in PREPRESS refused below {kTankIgnMin_K} on the pad first start '
    'and on the stand, with the safe exit: back to ARMED on the refusal tick, MV latch dropped, pintle seated, CLOSED switch expected '
    'within {kMvCloseConfirm_s}; a flight relight is flagged only (RE-17)',
    ['kTankIgnMin_K', 'kTankColdArmMargin_K', 'kTankColdPrepressDrop_K', 'kTankColdRepeat_K', 'kMvCloseConfirm_s'])
AB4['CASE_WARM_STAND'] = (
    'stand mode only: ARM refused when TC1 or TC2 reads above {kCaseStandArmMax_K} (stand T0 rule; a backstop for gross cases, the '
    'founder pre-fire checklist row is the control); flight has no T0 rule',
    ['kCaseStandArmMax_K'])
AB4['RELIGHT_LOCKOUT'] = (
    'ARM, IGNITE and RELIGHT refused after an abort following a lit burn or on a relight, until CLEAR_LOCKOUT (ground); after a ground '
    'no-light CLEAR_LOCKOUT is refused for {kNoLightSafingMin_s} (safing hold, see decision)', ['kNoLightSafingMin_s'])
AB4['GIMBAL_FAULT'] = (
    'command-model vs encoder mismatch above {kGimbalFaultErr_rad} for {kGimbalFaultTime_s} while burning; the allowance grows by '
    '{kGimbalFaultRateWin_s} times the model rate; NOT inhibited near touchdown (see decision). Detection bound on the as-built '
    'linkage: see sil_fail_dispositions (RE-24)', ['kGimbalFaultErr_rad', 'kGimbalFaultTime_s', 'kGimbalFaultRateWin_s'])

AB4_REF = OrderedDict([
    ('WATCHDOG', (166, '(8) RE-28')), ('RELIGHT_LOCKOUT', (172, '(1) R2-02')), ('TANK_HOT', (172, '(4) R2-07')),
    ('CMD', (181, '(4) Drogue release')), ('OVER_TEMP', (243, '(3) ABORT VALUE')), ('GIMBAL_FAULT', (227, '(7) RE-24')),
    ('PC_SENSOR', (216, '(4) R2-04')), ('TANK_COLD', (216, '(7) R2-11')), ('HARD_START', (216, '(3) R2-03'))])
# v2.11 rulings (LEAD 2026-10-20T21:46:49Z / 21:51:07Z), recorded by the lead as CHANGELOG line 249: cited with the marker checked
AB4_RULING = OrderedDict([
    ('OVER_TEMP', [(249, '(1) CASE-TC ABORT CHANNEL', 520), (249, '(4) RELIGHT AND TRANSDUCER', 420)]),
    ('CASE_WARM_STAND', [(249, '(2) STAND T0 RULE', 560)])])

# ------------------------------------------------------------------------------------------------ stale scan v4
HISTORY_KEYS_V4 = ('change_summary_v3_to_v4', 'superseded_v3', 'changelog_folding', 'lead_rulings_v2p11')
STALE_V4 = ['log v11', 'LogRecord v11 = 179', 'never refuses', 'offered, NOT implemented', 'LEAD line 161 (6), PROVISIONAL',
            '0.8 s NOT adopted', 'bench_plan_v3.md', 'ECU v2.10 still accepts', 'on the 070BG (OVP_OK low)', '31.47 bar g on the 070BG',
            'not in firmware v2.10', 'not made in v2.10', 'bom_v2p2.csv', 'pcf_tmax 0.5 s (0.8 s',
            'for 72 ms', 'MEOP for 72 ms', 'hold lift 0.2154 mm', 'Pc invalid from then on', 'P_mid 170BG between them', '77.7 g',
            '83.6 g', 'rise 9.86', 'P_mid with V1 stuck open and V2 closed']
# a value that is history in v4 may appear only next to one of its context words (checked per JSON string leaf)
CONTEXT_ALLOWED = OrderedDict([
    ('448.15', ('Z1', 'LC-TB70', 'v2.10', 'superseded', 'label', 'old', 'replac', 'was ')),
    ('433.15', ('v2.10', 'superseded', 'was ', 'old', 'replac')),
    ('2.61 s', ('v2.10', 'superseded', 'was ', 'old')),
    ('31.47', ('v2.10', 'superseded', 'was ', '070BG chain', 'old')),
    ('0.2154', ('v2.10', 'superseded', 'was ', 'S17 v2.10', 'old')),
    ('pc_transducer_v2.py', ('070BG', 'P_torch', 'P_TORCH', 'v2.10', 'Makefile', 'history')),
    ('V1 stuck open with V2 closed', ('label', 'wrong', 'corrected'))])
STALE_V4 += ['codes <= 15', 'ABORT at t_E2 + 0.5 s', 'kHbleedCap_s 2.61', 'R2 v2 not yet run against the ECU', 'b0-b5 refuse reason (codes <= 15']


# ------------------------------------------------------------------------------------------------ helpers (v4)
def refresh_cfg(obj, C, changes, path=''):
    """Carried v3 leaves: every embedded config constant {v, unit, tag, src '<header> kName'} is re-read from the v2.11 headers;
    a value or tag that changed is listed (change_summary_v3_to_v4 / self_check)."""
    if isinstance(obj, dict):
        if {'v', 'unit', 'tag', 'src'} <= set(obj.keys()) and isinstance(obj.get('src'), str):
            m = re.match(r'(config\.h|engine_params\.h|mech_params\.h) (k\w+)$', obj['src'])
            if m:
                ns = {'config.h': 'cfg', 'engine_params.h': 'eng', 'mech_params.h': 'mech'}[m.group(1)]
                new = C(m.group(2), ns)
                if new['v'] != obj['v'] or new['tag'] != obj['tag']:
                    changes.append(OrderedDict([('path', path), ('src', obj['src']), ('v3', [obj['v'], obj['tag']]),
                                                ('v4', [new['v'], new['tag']])]))
                return new
        return OrderedDict((k, refresh_cfg(v, C, changes, path + '/' + k)) for k, v in obj.items())
    if isinstance(obj, list):
        return [refresh_cfg(v, C, changes, '%s[%d]' % (path, i)) for i, v in enumerate(obj)]
    return obj


def complete_tags(C):
    """The v3 parser keeps the first 120 characters of a comment whose [tag] bracket closes on a later line; v4 reads such a tag to its
    closing bracket over the // continuation lines (only for a constant defined once in its header). Returns the names completed."""
    done = []
    for fn, ns in (('engine_params.h', 'eng'), ('mech_params.h', 'mech'), ('config.h', 'cfg')):
        lines = rd(os.path.join(CORE, fn)).split('\n')
        for (ns_, name), ent in C.d.items():
            if ns_ != ns or not ent['tag'].startswith('['):
                continue
            hits = [i for i, ln in enumerate(lines) if re.match(r'\s*(?:static\s+)?constexpr\s+\w+\s+%s\s*=' % name, ln)]
            if len(hits) != 1:
                continue
            t = lines[hits[0]].split('//', 1)[1].strip()
            j = hits[0] + 1
            while ']' not in t and j < len(lines) and j <= hits[0] + 6 and re.match(r'\s*//', lines[j]):
                t += ' ' + re.sub(r'^\s*//\s*', '', lines[j]).strip()
                j += 1
            if t.startswith('[') and ']' in t:
                ent['tag'] = re.sub(r'\s+', ' ', t[1:t.index(']')]).strip()
                done.append('%s::%s' % (ns, name))
    return done


def string_leaves(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from string_leaves(v, path + '/' + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from string_leaves(v, '%s[%d]' % (path, i))
    elif isinstance(obj, str):
        yield path, obj


def stale_scan(doc):
    """v3 STALE_STRINGS + STALE_V4 anywhere outside the history keys; CONTEXT_ALLOWED values only next to a context word.
    Leaves that quote the CHANGELOG ('CHANGELOG line N (...)') are quotations of the lead and are skipped."""
    found = []
    for path, s in string_leaves(OrderedDict((k, v) for k, v in doc.items() if k not in HISTORY_KEYS_V4)):
        if s.startswith('CHANGELOG line ') or s.startswith('HISTORY'):
            continue
        for t in G3.STALE_STRINGS + STALE_V4:
            if t in s:
                found.append('%s: stale %r' % (path, t))
        for val, ctx in CONTEXT_ALLOWED.items():
            for m in re.finditer(r'(?<![\d.])%s(?!\d)' % re.escape(val), s):
                win = s[max(0, m.start() - 160): m.end() + 160]
                if not any(c in win for c in ctx):
                    found.append('%s: %s without a history context: ...%s...' % (path, val, s[max(0, m.start() - 60): m.end() + 40]))
    return found


def grp(S17, **f):
    """S17 v2 sweep: sum the outcome counts over the groups matching every filter (both commands unless F_rl_N is given)."""
    rows = [g for g in S17['groups'] if all(g.get(k) == v for k, v in f.items())]
    if not rows:
        raise SystemExit('S17v2: no group for %s' % f)
    out = OrderedDict([('groups', len(rows)), ('evaluations', sum(g['evaluations'] for g in rows))])
    for k in ('LIT_RELEASED', 'DEAD_RELEASED', 'LIT_ABORT', 'DEAD_ABORT', 'ECU_LEFT_RUN', 'NO_R2_WINDOW'):
        out[k] = sum(g[k] for g in rows)
    mm = [g['margin_min_N'] for g in rows if g['margin_min_N'] is not None]
    sm = [g['stat_max_N'] for g in rows if g['stat_max_N'] is not None]
    out['margin_min_N'] = min(mm) if mm else None
    out['stat_max_N'] = max(sm) if sm else None
    rel = [g['release_from_E2_ms_min_med_max'] for g in rows if g['release_from_E2_ms_min_med_max'] and g['release_from_E2_ms_min_med_max'][0] is not None]
    out['release_from_E2_ms_min_max'] = [min(x[0] for x in rel), max(x[2] for x in rel)] if rel else None
    return out


def s17_row(S17, label, **f):
    a = grp(S17, window_s=0.5, **f)
    b = grp(S17, window_s=0.8, **f)
    keep = ('evaluations', 'LIT_RELEASED', 'DEAD_RELEASED', 'LIT_ABORT', 'DEAD_ABORT', 'ECU_LEFT_RUN', 'margin_min_N', 'stat_max_N',
            'release_from_E2_ms_min_max')
    return OrderedDict([('row', label), ('filter', OrderedDict(f)),
                        ('W_0p5_s', OrderedDict((k, a[k]) for k in keep)), ('W_0p8_s', OrderedDict((k, b[k]) for k in keep))])


def tc_line(log, pattern):
    """One PASS line of the test_core log (the line text is quoted as evidence; a missing or failing line fails the build)."""
    for ln in log.split('\n'):
        if re.search(pattern, ln):
            if not ln.startswith('PASS '):
                raise SystemExit('test_core line does not PASS: %s' % ln)
            return ln.strip()
    raise SystemExit('test_core log: no line matches %r' % pattern)


# ================================================================================================ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--engine-root', default='/home/claude/work/shared-fallback/engine')
    ap.add_argument('--prev', default=None, help='electronics.json v3 being superseded (default: <engine-root>/interfaces/electronics.json)')
    ap.add_argument('--out', default=os.path.join(RES, 'electronics_v4.json'))
    ap.add_argument('--stamp', default=None, help='generation time, UTC from date -u (default: the clock at the run)')
    a = ap.parse_args()
    ENG = a.engine_root
    stamp = a.stamp or datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    C = G3.Cfg()
    tags_completed = complete_tags(C)
    cl_path = os.path.join(ENG, 'interfaces', 'CHANGELOG.md')
    CL = G3.Changelog(cl_path)
    n_cl = rd(cl_path).count('\n')   # line count as wc -l (the count the lead asserts), header and blank lines included

    def cite(n, marker, chars=260, before=40):
        return CL.cite(n, marker, chars, before)

    def cv(name, ns='cfg'):
        c = C(name, ns)
        if c['v'] is None:
            raise SystemExit('%s::%s did not evaluate' % (ns, name))
        return c['v']

    # ---- base: the v3 hub file (asserted) and its local copy
    prev_path = a.prev or os.path.join(ENG, 'interfaces', 'electronics.json')
    v3 = jload(prev_path)
    if v3.get('version') != 'v3' or sha(prev_path) != '38bf149f368c1d4c':
        raise SystemExit('--prev is not the hub electronics.json v3 38bf149f368c1d4c (%s %s)' % (v3.get('version'), sha(prev_path)))
    v3_local = os.path.join(RES, 'electronics_v3.json')
    rd(v3_local, 'rb')
    if sha(v3_local) != sha(prev_path):
        raise SystemExit('results/electronics_v3.json differs from the hub v3 file')

    # ---- interfaces and reviews
    gnc_path = os.path.join(ENG, 'interfaces', 'gnc.json')
    mech_path = os.path.join(ENG, 'interfaces', 'mechanical.json')
    comb_path = os.path.join(ENG, 'interfaces', 'combustion.json')
    lctb_path = os.path.join(ENG, '04-fea', 'v352', 'lc_tb70_envelope_v1.json')
    rev2_path = os.path.join(ENG, 'reviews', 'REVIEW-ELECTRONICS-R2.md')
    gnc, mech, comb, lctb = jload(gnc_path), jload(mech_path), jload(comb_path), jload(lctb_path)
    rev2 = rd(rev2_path)
    expect = OrderedDict([(gnc_path, ('v3.1', '4f3209323b0e0ed4')), (mech_path, ('v2.2', 'f790d31b5ca7d954')),
                          (comb_path, ('v2.4b', 'fd3a7da6d27c7c66'))])
    for p, (ver, s) in expect.items():
        d = {gnc_path: gnc, mech_path: mech, comb_path: comb}[p]
        if d.get('version') != ver or sha(p) != s:
            raise SystemExit('%s is %s %s, the brief names %s %s' % (p, d.get('version'), sha(p), ver, s))
    if sha(lctb_path) != '6f710726e4787134' or sha(rev2_path) != 'c7dee8d6c73c9920':
        raise SystemExit('LC-TB70 envelope or REVIEW-ELECTRONICS-R2 changed since the brief')
    mech_req = [r for r in mech.get('requests_v352', []) if 'Electronics' in str(r)]
    mtrig = mech['gimballed_mass_properties_v352']['delta_vs_v3.5.1']['gnc_trigger']
    r2_ids = sorted(set(re.findall(r'\b(R2-\d\d)\b', rev2)))
    if r2_ids != ['R2-%02d' % i for i in range(1, 24)]:
        raise SystemExit('REVIEW-ELECTRONICS-R2 item list is not R2-01..R2-23: %s' % r2_ids)
    # CHANGELOG: the brief was written on 248 lines (addde6a1263549fc); the lead recorded the Part A rulings as line 249 since
    if n_cl < 249 or '(1) CASE-TC ABORT CHANNEL' not in CL.lines[248] or '(4) RELIGHT AND TRANSDUCER' not in CL.lines[248]:
        raise SystemExit('CHANGELOG line 249 (lead record of the Part A rulings) not found as expected')

    # ---- versions (config.h stamp = Makefile header; schematic REV = KiCad files)
    cfg_first = rd(os.path.join(CORE, 'config.h')).split('\n', 1)[0]
    m = re.match(r'// \[(v[0-9][0-9.]*) ', cfg_first)
    if not m:
        raise SystemExit('config.h first line carries no [vX.Y] stamp')
    fw_ver = m.group(1)
    if fw_ver != 'v2.11':
        raise SystemExit('config.h stamp is %s, not v2.11' % fw_ver)
    mk_first = rd(os.path.join(FWD, 'Makefile')).split('\n', 1)[0]
    if (' %s ' % fw_ver) not in mk_first:
        raise SystemExit('Makefile header does not name %s' % fw_ver)
    KICAD, KGEN = G3.KICAD, G3.KGEN
    rev = re.search(r"^REV = '(v[0-9.]+)'", rd(os.path.join(KGEN, 'make_ecu_kicad.py')), re.M).group(1)
    if ('rev "%s"' % rev) not in rd(os.path.join(KICAD, 'argos_ecu.kicad_sch')):
        raise SystemExit('KiCad root sheet rev is not %s' % rev)
    pins = list(csv.DictReader(rd(os.path.join(KICAD, 'pin_map_%s.csv' % rev.replace('.', 'p'))).splitlines()))
    if any(p['ecu_rev'] != rev for p in pins):
        raise SystemExit('pin map rows carry another revision than %s' % rev)
    xc = rd(os.path.join(KICAD, 'erc', 'netlist_crosscheck.txt'))
    erc = rd(os.path.join(KICAD, 'erc', 'argos_ecu_erc.rpt'))
    xm = re.search(r'components (\d+), nets (\d+) .*pins (\d+) of (\d+) intended\s*\nerrors (\d+), warnings (\d+)', xc)
    em = re.search(r'ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)', erc)
    if not (xm and em) or int(xm.group(5)) or int(em.group(2)):
        raise SystemExit('ERC / netlist cross-check not clean')

    # ---- SIL record v2.11
    man = jload(os.path.join(SIL, 'MANIFEST_v1.json'))
    if man.get('firmware_version') != fw_ver:
        raise SystemExit('SIL manifest firmware_version %s != %s' % (man.get('firmware_version'), fw_ver))
    bins = man.get('binaries') or {}
    if set(bins) != {'sil', 'sil_bpc1', 'test_core', 'test_core_nohooks'} or \
            not all(b.get('rebuild_of_current_tree', {}).get('identical') for b in bins.values()):
        raise SystemExit('SIL manifest: binaries missing or not identical to the rebuild of the current tree')
    if man['test_core']['all_logs'] != OrderedDict([('test_core_log.txt', '326 passed, 0 failed'), ('test_core_nohooks_log.txt', '325 passed, 0 failed')]):
        raise SystemExit('test_core summaries changed: %s' % man['test_core']['all_logs'])
    J = lambda *p: jload(os.path.join(SIL, *p))
    s5, s6, s6r, s6c, s8, s9 = J('S5_mc.json'), J('S6_aborts.json'), J('S6R_in_window_overpressure.json'), J('S6C_rc_cost.json'), \
        J('S8_priming.json'), J('S9_pc_transducer.json')
    s10, s10c, s12 = J('S10_relight_v2p8.json'), J('S10v211_cold_rule.json'), J('S12_bleed.json')
    s13, s13f, s13t = J('S13', 'S13_ignition_rule.json'), J('S13', 'S13B_ext_bpc1_false.json'), J('S13', 'S13B_ext_bpc1_true.json')
    s14, s15, s16, s17 = J('S14', 'S14_v2p10.json'), J('S15', 'S15_start_mc.json'), J('S16', 'S16_coast206.json'), J('S17', 'S17_r2hold.json')
    s17v2, pf, cmpj = J('S17v2_r2v2_sweep.json'), J('probeF', 'S5_probeF.json'), J('compare_v2p10_v2p11.json')
    s5_rows = list(csv.DictReader(rd(os.path.join(SIL, 'S5_mc.csv')).splitlines()))
    tc_log = rd(os.path.join(SIL, 'test_core_log.txt'))
    tc_nh = rd(os.path.join(SIL, 'test_core_nohooks_log.txt'))
    runmap_path = os.path.join(RES, 'sil_v2p11_runmap.json')
    rd(runmap_path, 'rb')
    sf = man.get('scenarios_file') or {}
    if sf.get('path') != 'results/sil_v2p11_runmap.json' or sf.get('sha256_16') != sha(runmap_path):
        raise SystemExit('manifest scenarios_file is not results/sil_v2p11_runmap.json at its current hash')
    rd(os.path.join(SIL, 'compare_v2p10_v2p11.txt'), 'rb')

    # ---- v2.11 calculation results and carried v3 inputs
    R = lambda f: jload(os.path.join(RES, f))
    pct3, fa1c, bom3, ctc, tf1 = R('pc_transducer_v3.json'), R('fa1_chain_v2p11.json'), R('bom_v2p3.json'), R('case_tc_channel_v1.json'), \
        R('tf1_rate_v1.json')
    leafd, regen, gnc_rk = R('gen_tables_v2p4b_leafdiff_v1.json'), R('gen_headers_regen_check_v2p11.json'), R('gnc_v31_read_keys_check_v2p10.json')
    if not regen['generators']['gen_mech_params.py']['regenerated'] or any(h_['changed_code_lines'] for h_ in regen['generators']['gen_mech_params.py']['headers'].values()):
        raise SystemExit('gen_headers_regen_check_v2p11: the mechanical headers do not regenerate with 0 code-line changes')
    if gnc_rk['new']['sha256_16'] != sha(gnc_path):
        raise SystemExit('gnc.json changed since results/gnc_v31_read_keys_check_v2p10.json')
    if regen['combustion_read_keys']['now']['sha256_16'] != sha(comb_path) or regen.get('firmware') != 'v2.11':
        raise SystemExit('combustion.json changed since results/gen_headers_regen_check_v2p11.json (or the check is not the v2.11 one)')
    if leafd['b'][1] != sha(comb_path):
        raise SystemExit('combustion.json changed since results/gen_tables_v2p4b_leafdiff_v1.json')
    carried = ['fault_path_v4.json', 'bleed_driver_v1.json', 'hbleed_provision_v1.json', 'over_thrust_v3.json', 'pintle_rate_map_v1.json',
               'eng03_slew_check_v1.json', 'pintle_rail_v3.json', 'ecu_v2p3_values_v1.json', 'mv_latch_magnet_v1.json',
               'tvc_supply_budget_v1.json', 'pintle_mini_servo_v1.json']
    carried_check = OrderedDict()
    for f in carried:
        rd(os.path.join(RES, f), 'rb')
        was = v3['inputs']['files_read_sha256_16'].get('results/' + f)
        carried_check[f] = 'unchanged since v3 (%s)' % was if was == sha(os.path.join(RES, f)) else 'CHANGED %s -> %s' % (was, sha(os.path.join(RES, f)))
        if not carried_check[f].startswith('unchanged'):
            raise SystemExit('carried v3 input changed: %s %s' % (f, carried_check[f]))
    bench_path = os.path.join(ROOT, 'docs', 'bench_plan_v4.md')
    bench = rd(bench_path)
    proto = rd(os.path.join(CORE, 'protocol.h'))
    types_h = rd(os.path.join(CORE, 'types.h'))
    ids = OrderedDict((mm.group(1), int(mm.group(2), 16)) for mm in re.finditer(r'ID_(\w+)\s*=\s*(0x[0-9A-Fa-f]+)', proto))
    events = OrderedDict((mm.group(1), mm.group(2)) for mm in re.finditer(r'constexpr uint8_t (\w+) = (0x[0-9A-Fa-f]+);',
                                                                         proto.split('namespace evt')[1].split('namespace tlmg')[0]))
    tlmr = OrderedDict((mm.group(1), mm.group(2)) for mm in re.finditer(r'constexpr uint8_t (\w+) = (1u << \d|PRIMED);',
                                                                         proto.split('namespace tlmr {')[1].split('}')[0]))
    refuse = OrderedDict((mm.group(1), int(mm.group(2))) for mm in re.finditer(r'\b([A-Z_0-9]+) = (\d+)', types_h.split('namespace refuse')[1].split('}')[0]))
    abort_enum = OrderedDict((mm.group(1), int(mm.group(2))) for mm in re.finditer(r'\b([A-Z_]+) = (\d+)\b', types_h.split('enum class Abort')[1].split('};')[0]))
    if abort_enum.get('CASE_WARM_STAND') != 31 or refuse.get('UNPURGED') != 16 or events.get('R2_BACKSTOP') != '0x24':
        raise SystemExit('v2.11 enums not as expected (CASE_WARM_STAND 31, refuse UNPURGED 16, EVENT R2_BACKSTOP 0x24)')
    code2name = {v: k for k, v in abort_enum.items()}
    log_ver = int(re.search(r'constexpr uint8_t kLogVersion = (\d+);', proto).group(1))
    log_size = int(re.search(r'static_assert\(sizeof\(LogRecord\) == (\d+)', proto).group(1))

    # ---- structural checks on the v2.11 constants
    struct = OrderedDict([
        ('Pc transducer selection kPcXdcrSel = 1 (C1 Kulite XTL-190SM-2000A)', cv('kPcXdcrSel') == 1),
        ('case-TC abort kCaseOverTemp_K = 423.15 K (LEAD 243 (3))', abs(cv('kCaseOverTemp_K') - 423.15) < 1e-6),
        ('start / relight limit kCaseRelightMax_K = 403.15 K (LEAD 249 (4); the 21:46:49Z message item 5)', abs(cv('kCaseRelightMax_K') - 403.15) < 1e-6),
        ('stand ARM limit kCaseStandArmMax_K = 297.15 K (LEAD 249 (2); the 21:46:49Z message item 3)', abs(cv('kCaseStandArmMax_K') - 297.15) < 1e-6),
        ('purge both-open cap kHbleedCap_s = 2.55 s (kept, LEAD 230 (3))', abs(cv('kHbleedCap_s') - 2.55) < 1e-9),
        ('R2 window kR2WindowMax_s = 0.8 s (LEAD 227 (5))', abs(cv('kR2WindowMax_s') - 0.8) < 1e-9),
        ('R2 hold lift kR2HoldLift_m = 0.21776 mm (LEAD 230 (4))', abs(cv('kR2HoldLift_m') - 0.21776e-3) < 1e-12),
        ('R2 backstop = window + 2 FC frames + link latency', abs(cv('kR2HoldBackstop_s') - (cv('kR2WindowMax_s') + 2 * cv('kFcFramePeriod_s') + cv('kFcLinkLatency_s'))) < 1e-9),
        ('ride-through build option OFF in the flight build', cv('kRideThroughBuild') == 0),
        ('LogRecord v12 = 180 bytes', log_ver == 12 and log_size == 180)])
    if not all(struct.values()):
        raise SystemExit('structural check failed: %s' % [k for k, v in struct.items() if not v])

    # ================================================================================================ shared evidence
    T = lambda pat: tc_line(tc_log, pat)          # a PASS line of the hooks build log (quoted as evidence)
    TN = lambda pat: tc_line(tc_nh, pat)          # a PASS line of the no-hooks build log (R2-08)
    s5_causes = Counter(r_['abort'] for r_ in s5_rows)
    s5_causes_named = OrderedDict(sorted(((code2name.get(int(k), k) if k.isdigit() else k), v) for k, v in s5_causes.items()))
    # v2.10 hub tree (frozen) through the same evaluator: the config diff is computed, not typed
    hub_core = os.path.join(ENG, '06-electronics', 'firmware', 'src', 'core')
    _core = G3.CORE
    G3.CORE = hub_core
    try:
        C10 = G3.Cfg()
    finally:
        G3.CORE = _core
    for fn in ('engine_params.h', 'mech_params.h'):
        if READ[rel(os.path.join(CORE, fn))] != READ[os.path.join(hub_core, fn)]:
            raise SystemExit('%s differs between the hub v2.10 tree and the v2.11 tree: the config diff below would be incomplete' % fn)
    cfg_order = [k for (ns, k) in C.d if ns == 'cfg']
    cfg10 = {k for (ns, k) in C10.d if ns == 'cfg'}
    cdiff_changed, cdiff_unevaluated = [], []
    for k in cfg_order:
        if k not in cfg10:
            continue
        a_, b_ = C10.val.get(('cfg', k)), C.val.get(('cfg', k))
        if a_ is None or b_ is None:
            cdiff_unevaluated.append(k)
        elif isinstance(a_, bool) or isinstance(b_, bool):
            if a_ != b_:
                cdiff_changed.append(k)
        elif abs(a_ - b_) > 1e-9 * max(1.0, abs(a_), abs(b_)):
            cdiff_changed.append(k)
    cdiff_added = [k for k in cfg_order if k not in cfg10]
    cdiff_removed = [k for (ns, k) in C10.d if ns == 'cfg' and k not in set(cfg_order)]
    if set(cdiff_changed) != {'kCaseOverTemp_K', 'kCaseRelightMax_K', 'kHbleedCap_s'} or cdiff_removed:
        raise SystemExit('config diff v2.10 -> v2.11 not as recorded: changed %s, removed %s' % (cdiff_changed, cdiff_removed))
    config_diff = OrderedDict([
        ('basis', 'hub 06-electronics/firmware/src/core/config.h (v2.10, frozen) vs the v2.11 tree, both through the generator\'s constexpr '
                  'evaluator (flight build, no macro defined); engine_params.h and mech_params.h are byte-identical in both trees'),
        ('changed', [OrderedDict([('name', k), ('v2p10', C10(k)['v']), ('v2p11', C(k)['v']),
                                  ('unit', C(k)['unit']), ('tag_v2p11', C(k)['tag'])]) for k in cdiff_changed]),
        ('added', [OrderedDict([('name', k), ('v', C(k)['v']), ('unit', C(k)['unit']), ('tag', C(k)['tag'])]) for k in cdiff_added]),
        ('removed', cdiff_removed),
        ('not_evaluated_in_either_tree', cdiff_unevaluated),
        ('tag', 'DERIVED (file comparison)')])

    # ================================================================================================ document
    doc = OrderedDict()
    doc['id'] = 'electronics'
    doc['version'] = 'v4'
    doc['date'] = stamp[:10]
    doc['generated_utc'] = stamp
    doc['owner'] = 'electronics (06-electronics)'
    doc['status'] = ('DESIGN + SIL + schematic, STAGED for the lead (06-electronics/staging_v2.11/; interfaces/electronics.json v3 stays the '
                     'published file until the lead promotes this one). Firmware %s runs only in SIL (no Teensy HAL); the ECU %s schematic '
                     'passes ERC and a netlist cross-check (self-consistency only) and does NOT show the v2.11 board items (schematic v2.6 '
                     'NOT drawn: C1 bridge amplifiers, U330 / U570 values, the ride-through C330 variant, the both-open timer U576-U579); no '
                     'board has been built and nothing here is hardware-validated or physical approval. Values carry tags; open items are '
                     'in open_issues and are closed by the bench plan (06-electronics/docs/bench_plan_v4.md).' % (fw_ver, rev))
    doc['units'] = v3['units']
    doc['supersedes'] = OrderedDict([
        ('file', 'electronics.json v3 (2026-10-13, firmware v2.10)'), ('sha256_16', sha(prev_path)),
        ('hub_path', 'interfaces/electronics.json (unchanged by this staging)'), ('local_copy', 'results/electronics_v3.json (identical)'),
        ('earlier', OrderedDict([('v2', OrderedDict([('sha256_16', v3['supersedes']['sha256_16']), ('archive', v3['supersedes']['archive'])])),
                                 ('v1', v3['supersedes']['v1'])]))])
    doc['scripts'] = [
        '06-electronics/calc/v2p11/make_interface_json_v4.py (this file; imports calc/make_interface_json_v3.py for its evaluator and checks)',
        '06-electronics/calc/v2p11/pc_transducer_v3.py (C1 Pc / P_feed / P_mid selection, conditioning, U330 / U570, sil/ovp_hw_params.h)',
        '06-electronics/calc/v2p11/fa1_chain_v2p11.cpp + fa1_chain_summary.py (FA-1 grid through the v2.10 and C1 chains; ride-through sizing)',
        '06-electronics/calc/v2p11/fa1_replay_select.py (sil/fa1_replay_cases.h for S6R / S9R)',
        '06-electronics/calc/v2p11/case_tc_channel_v1.py (Part A case-TC channel budget)',
        '06-electronics/calc/v2p11/tf1_rate_v1.py (T-F1 basis rate rule)',
        '06-electronics/calc/v2p11/bom_v2p3.py (BOM v2.3)',
        '06-electronics/calc/v2p11/sil_compare_v1.py (v2.11 SIL record case by case against v2.10)',
        '06-electronics/calc/v2p11/gen_tables_v2p4b_leafdiff_v1.py, gen_headers_regen_check_v2p11.py (generated headers vs combustion v2.4b)',
        '06-electronics/firmware/tools/sil_manifest_v1.py (v1.4)',
        '06-electronics/firmware/sil/sc_v211.inc, sc_v211_r2.inc, test_v211.inc, test_v211b.inc (v2.11 scenarios and unit tests)',
        'carried from v3 unchanged (inputs hash-checked, carried_inputs): calc/bleed_driver_v1.py, fault_path_v4.py, hbleed_provision_v1.py, '
        'ecu_v2p3_values_v1.py, pintle_rail_v3.py, over_thrust_v3.py, pintle_rate_map_v1.py; hardware/kicad_gen/run_all.sh (schematic v2.5)']
    doc['inputs'] = OrderedDict([
        ('gnc.json', '%s %s' % (gnc.get('version'), sha(gnc_path))), ('mechanical.json', '%s %s' % (mech.get('version'), sha(mech_path))),
        ('combustion.json', '%s %s' % (comb.get('version'), sha(comb_path))),
        ('lc_tb70_envelope', '04-fea/v352/lc_tb70_envelope_v1.json %s' % sha(lctb_path)),
        ('review', 'reviews/REVIEW-ELECTRONICS-R2.md %s (REV-ELEC-2; R2-01..R2-23)' % sha(rev2_path)),
        ('changelog', 'interfaces/CHANGELOG.md, %d lines at generation, %s (the brief was written on 248 lines addde6a1263549fc; lead line '
                      '249 records the Part A rulings; line 250 assigns Electronics no item)' % (n_cl, sha(cl_path))),
        ('firmware', '%s (SIL record %s, source tree %s, %d files; manifest %s)' % (fw_ver, man['record_sha256_16'], man['tree_sha256'][:16],
                                                                                   man['n_files'], sha(os.path.join(SIL, 'MANIFEST_v1.json')))),
        ('generated_headers', OrderedDict((k, [(r_['source'], r_.get('version_named') or '(not named in the header)', r_['sha_at_generation'],
                                                r_['status']) for r_ in v['refs']]) for k, v in man['generated_headers'].items())),
        ('generated_headers_note', 'status as recorded by the v2.11 SIL manifest. engine_params.h / plant_tables.h / gnc_tables.h / '
                                   'valve_map_table.h stay generated from combustion.json v2.3 and gnc.json v3 (HISTORICAL): gen_tables.py v3.3 '
                                   'cannot parse the v2.4b igniter sequence (results/gen_headers_regen_check_v2p11.json); the v2.3 -> v2.4b '
                                   'leaf diff of the keys the generator reads finds %d numeric changes outside the igniter sequence and %d '
                                   'inside it (results/gen_tables_v2p4b_leafdiff_v1.json %s); gnc.json v3 -> v3.1: no numeric leaf changed '
                                   'under the subtrees the generators read (results/gnc_v31_read_keys_check_v2p10.json %s); mech_params.h / '
                                   'mech_tables.h name mechanical.json v2: gen_mech_params.py regenerated them from v2.2 and only the source '
                                   'comment line differs (%s code lines changed; results/gen_headers_regen_check_v2p11.json %s; the tree keeps '
                                   'the v2 comment, no binary effect)'
                                   % (leafd['summary']['numeric_changes_outside_igniter_sequence'], leafd['summary']['igniter_sequence_numeric_changes'],
                                      sha(os.path.join(RES, 'gen_tables_v2p4b_leafdiff_v1.json')), sha(os.path.join(RES, 'gnc_v31_read_keys_check_v2p10.json')),
                                      ' / '.join(str(h_['changed_code_lines']) for h_ in regen['generators']['gen_mech_params.py']['headers'].values()),
                                      sha(os.path.join(RES, 'gen_headers_regen_check_v2p11.json')))),
        ('carried_inputs', carried_check)])

    # ================================================================================================ history keys (v3 -> v4)
    doc['change_summary_v3_to_v4'] = None      # filled at the end (it counts the carried constants refreshed below)
    v3s, v3r = v3['sensors'], v3['relight_interface']
    def sup(key, old, new):
        return OrderedDict([('key', key), ('v3', old), ('v4', new)])
    doc['superseded_v3'] = [
        sup('sensors.thermocouples.case_abort (kCaseOverTemp_K)', '%s K, tag %r' % (v3s['thermocouples']['case_abort']['v'], v3s['thermocouples']['case_abort']['tag']),
            '%s K (LEAD 243 (3), ACCEPTED with the channel budget by CHANGELOG 249 (1)); 0.20 s persistence unchanged' % cv('kCaseOverTemp_K')),
        sup('sensors.thermocouples.relight_refusal (kCaseRelightMax_K)', '%s K' % v3s['thermocouples']['relight_refusal']['v'],
            '%s K (CHANGELOG 249 (4)); now also the ARM refusal limit on TC1 / TC2 (OVER_TEMP)' % cv('kCaseRelightMax_K')),
        sup('ecu.purge_window.cap_relation / kHbleedCap_s', '2.61 s both-open firmware cap (v2.10)',
            '%s s (LEAD 203 (3); kept by 230 (3) because a 2.39 s cap would cut the scheduled flow) plus the hardware both-open timer (DESIGN, not drawn)' % cv('kHbleedCap_s')),
        sup('sensors.pressure_transducers.selection', json.dumps(v3s['pressure_transducers']['selection']['v']),
            'Pc, P_feed, P_mid: Kulite XTL-190SM-2000A (C1, LEAD 205 / 206 (3)); P_torch and the B-PC-1 static reference: TE M3234-000005-070BG; P_tank: M3234-000005-170BG'),
        sup('sensors.pressure_transducers.hw_ovp', v3s['pressure_transducers']['hw_ovp']['v'],
            'U330 on the C1 chain: trip %.2f bar abs, band %.2f-%.2f bar abs (DERIVED pc_transducer_v3); firmware abort %.0f bar abs filtered'
            % (pct3['F_hw_comparator_U330']['trip_nominal_Pa_abs']['v'] / 1e5, pct3['F_hw_comparator_U330']['trip_range_abs_Pa']['v'][0] / 1e5,
               pct3['F_hw_comparator_U330']['trip_range_abs_Pa']['v'][1] / 1e5, cv('kPcOverPressureAbs_Pa') / 1e5)),
        sup('sensors.pressure_transducers.fault_window.max meaning', v3s['pressure_transducers']['fault_window']['max']['tag'],
            '%s V = 146.5 bar abs on the C1 chain (test_core v2.11 LEAD 205 C1 scaling)' % cv('kPcSensorMax_V')),
        sup('r2_command_hold.rule', 'thrust-commanded hold at kR2HoldThrust_N 62.5 N through the open-loop map (S17: 0.2154 mm at the A1 state)',
            'lift-commanded hold at kR2HoldLift_m %.5f mm (Combustion v2.4b start-level lift, LEAD 216 (9) / 230 (4)); FC-command ceiling 62.5 N kept; ECU backstop at E2 + %.2f s (LEAD 216 (2))'
            % (cv('kR2HoldLift_m') * 1e3, cv('kR2HoldBackstop_s'))),
        sup('drogue_release_support.fc_parameters', v3['drogue_release_support']['fc_parameters']['v'],
            'R2 v2 (GNC): 0.8 s window ADOPTED for the W10 < 6 m/s envelope (LEAD 227 (5)); S17 v2.11 confirms it with conditions (drogue_release_support.r2v2_sweep)'),
        sup('relight_interface.unpurged_relight', 'accepted by the ECU (no refusal)',
            'flight build with the bleed fitted: refused UNPURGED (refuse code %d), LEAD 203 (7); stand build keeps the start' % refuse['UNPURGED']),
        sup('relight_interface.relight_worst_ms', v3r['relight_worst_ms']['v'], '810 ms direct, 1370 ms prep path, 3710 ms flight with the bleed fitted (PURGE + 2.90 s + gate + W)'),
        sup('relight_interface.a1_apogee_m', '%s m (%s)' % (v3r['a1_apogee_m']['v'], v3r['a1_apogee_m']['tag']), '210 m (LEAD 214; ACCEPTED 227 (1))'),
        sup('can_interface.tlm_relight_d6.b0_b5', v3['can_interface']['tlm_relight_d6']['b0_b5'], 'refuse reason codes 0-%d (UNPURGED %d added)' % (max(refuse.values()), refuse['UNPURGED'])),
        sup('pc_overrange_fa1.firmware_behaviour (PC_VALID)', 'a reading at or above 4.75 V latched PC_SENSOR and PC_VALID 0 for the power cycle',
            'flight: over-range bit non-sticky (PC_VALID 0 on the over-range ticks only), above-full-scale flag at %s V; stand as built (LEAD 203 (1)(a))' % cv('kPcAboveFs_V')),
        sup('light_rule BASE_AMB', 'P0 below -check -> P0 := 0 at every location', 'per location (LEAD 216 (4)): pad / stand refuse the lift (PC_SENSOR); A1 relight P0 := 0'),
        sup('interlocks.tank_cold', 'limit only (no ARM margin; an IGNITE refused in PREPRESS held PREPRESS with the MV open)',
            'ARM margin %s K and the PREPRESS safe exit (LEAD 216 (7))' % cv('kTankColdArmMargin_K')),
        sup('interlocks.wind_launch_commit tag', v3['interlocks']['wind_launch_commit']['tag'], 'HARD for A1 (LEAD 181 (6))'),
        sup('log_v11', v3['log_v11']['v'], 'log_v12: LogRecord v%d = %d bytes' % (log_ver, log_size)),
        sup('bench_plan', v3['bench_plan']['file'], '06-electronics/docs/bench_plan_v4.md'),
        sup('bom', v3['bom']['file'], '06-electronics/results/bom_v2p3.csv (v2.3)'),
        sup('relight_interface keys removed', 'unpurged_relight_contest, purge_commit_decision_note_194_3, purge_commit_history_181',
            'not carried (history; readable in v3); the unpurged relight is refused in flight (above)'),
        sup('oi37_interface_hygiene', 'v3 record of LEAD 186 (4)', 'not carried (history; readable in v3); the A5 token scan stays in self_check'),
        sup('pc_overrange_fa1 basis', '070BG chain with the ASSUMED 0.30 m sense line (fa1_overrange_v2p10)', 'C1 seat-mounted chain (fa1_chain_v2p11): 0 of 896 FA-1 cases reach the over-range'),
        sup('start_monitors.A7 flight high-side blank', 'proposed (RE-12)', 'ACCEPTED as DESIGN with four conditions (LEAD 216 (8)); start_monitors.A7_flight_blank'),
        sup('open_issues OI-PURGE-CAP numbers', 'cap 2.61 s: 77.7 g (Combustion basis) / 83.6 g (SIL basis)',
            'cap 2.55 s on the one basis 29.25 g/s: 76.05 g; warm end 31.06 g/s: 80.76 g (DERIVED, LEAD 230 (3))'),
        sup('abort_matrix causes', '30 causes', '%d causes (CASE_WARM_STAND %d added)' % (len(abort_enum) - 1, abort_enum['CASE_WARM_STAND']))]

    FOLD = [
        # (line, marker, item, status, where)
        (203, '(1) OI-FA1-PC-OVERRANGE', '203 (1)(a) non-sticky over-range bit and above-full-scale flag (flight)', 'DONE (SIL)', 'pc_overrange_fa1.firmware_behaviour; can_interface.pc_valid_bit'),
        (203, '(b) CANDIDATE: ride-through', '203 (1)(b) ride-through candidate (restated by 216 (3))', 'BUILT as a build option, default OFF; S6R / S6C evidence; adoption is the lead\'s', 'ride_through'),
        (203, '(2) 070BG port', '203 (2) 070BG port in the T > 1 ms domain', 'SUPERSEDED by 205 (flight Pc reselected: C1); 070BG behaviour MISSING -> F-7 TE inquiry, F-12 spare-070BG row', 'sensors.pressure_transducers; bench_plan'),
        (203, '(3) OI-PURGE-CAP', '203 (3) cap <= 2.55 s', 'DONE: kHbleedCap_s 2.55 s; the "not truncated" statement is withdrawn (216 (5)); 230 (3) decision below', 'head_end_bleed_provision'),
        (203, '(4) S12 OI-BLEED-DETECT', '203 (4) S12 stuck-open bleed (labelled "V1 stuck open with V2 closed"; the S12 cases have BOTH valves stuck open, label corrected): detection <= 0.5 s or an FMEA residual', 'OPEN: no detection design in v2.11; residual vented masses stated for GNC / FMEA (FMEA-A1-BLEED-BOTH-OPEN)', 'head_end_bleed_provision.oi_bleed_detect; open_issues OI-BLEED-DETECT'),
        (203, '(5) RE-02 / S13 B criteria', '203 (5) S13 B criteria per class (restated by 216 (4))', 'DONE (SIL): per location, 0 failures; occurrence on the A1 population stated', 'light_rule.base_check_per_location'),
        (203, '(6) RE-24 accepted as test-based', '203 (6) RE-24 test-based; RE-12 waits for REV-ELEC-2', 'NOTED (B-TVC-1); RE-12 ruled by 216 (8)', 'sil_fail_dispositions; start_monitors.A7_flight_blank'),
        (203, '(7) Unpurged RELIGHT guard in the ECU ADOPTED', '203 (7) unpurged RELIGHT guard', 'DONE (SIL): refuse UNPURGED (16) in the flight build with the bleed fitted', 'relight_interface.unpurged_relight'),
        (203, 'Start/hold lift', '203 (7) start / hold lift = Combustion v2.4b start level', 'DONE (SIL): kR2HoldLift_m 0.21776 mm (230 (4)); CF-3 measures at the commanded lift', 'r2_command_hold'),
        (203, 'gen_tables is re-run on v2.4b', '203 (7) gen_tables re-run on v2.4b', 'NOT DONE: gen_tables.py v3.3 cannot parse the v2.4b igniter sequence; leaf diff of the read keys: 0 numeric changes outside the igniter sequence', 'open_issues OI-GEN-TABLES'),
        (203, '113B22 excitation (20-30 V) vs NI 9234 compliance (19 V) is TO-VERIFY', '203 (7) 113B22 excitation; fallback IEPE conditioner', 'DONE (document): fallback conditioner BOM 265; F-8 / F-9 inquiries', 'pc_overrange_fa1.stand_dynamic_channel'),
        (205, 'DECISION: the flight Pc transducer is RESELECTED by Electronics', '205 flight Pc transducer reselection', 'DONE (DATASHEET + CALC): C1 Kulite XTL-190SM-2000A; proof requirement restated to >= 166 bar abs by 249 (4): C1 206.8 bar abs', 'sensors.pressure_transducers; pc_overrange_fa1'),
        (206, '(3) Miniature P_mid/P_feed transducers', '206 (3) miniature P_mid / P_feed', 'DONE: C1 family; mass delta stated', 'sensors.pressure_transducers; mass_statement'),
        (208, 'an ~80 g purge (203 (3))', '208 (1) ~80 g purge sensitivity arm (GNC)', 'NOTED: v2.11 purge masses for GNC stated on the one basis and at the warm end', 'head_end_bleed_provision.masses'),
        (208, '(5) RV5-05, RV5-09, RV5-10 recorded', '208 (5) R2 v2 carries both windows', 'DONE (SIL): S17 v2 at 0.5 and 0.8 s', 'drogue_release_support.r2v2_sweep'),
        (214, 'A1 APOGEE TARGET = 210 m', '214 A1 apogee 210 m', 'DONE (record)', 'relight_interface.a1_apogee_m'),
        (215, 'REV-ELEC-2 independent delta re-review', '215 REV-ELEC-2 record', 'ANSWERED item by item', 'rev_elec_2_author_status'),
        (216, '(1) R2-01', '216 (1) S17 sweep against R2 v2 at 0.5 / 0.8 s', 'DONE (SIL)', 'drogue_release_support.r2v2_sweep'),
        (216, '(2) R2-02 ADOPTED in full', '216 (2) lost DROGUE 0: FC re-send rule, ECU backstop, B-FC-1 row, test_core case', 'DONE (SIL + bench plan); the FC rule is the FC owner\'s', 'r2_command_hold.lost_drogue0'),
        (216, '(3) R2-03, 203 (1)(b) RESTATED', '216 (3) ride-through sizing, fixed RC, S6 in-window cases', 'DONE (SIL): S6R 105/105 inside LC-TB70; S6C whole-burn cost; still a CANDIDATE (lead)', 'ride_through'),
        (216, '(4) R2-04, 203 (5) RESTATED per location', '216 (4) BASE_HIGH / BASE_AMB per location', 'DONE (SIL); A1 BASE_AMB outcome stated for the lead', 'light_rule.base_check_per_location'),
        (216, '(5) R2-05, 203 (3) RESTATED', '216 (5) purge: one basis, provisional cap, hardware both-open timer', 'DONE (DESIGN, not drawn); 230 (3) answered: 2.55 s kept', 'head_end_bleed_provision'),
        (216, '(6) R2-06', '216 (6) founder-executable block', 'DONE (bench plan v4 F-1..F-14)', 'bench_plan.founder_block'),
        (216, '(7) R2-11 OI-GUARD-BAND', '216 (7) cold-rule ARM margin and PREPRESS safe exit', 'DONE (SIL)', 'interlocks.tank_cold'),
        (216, '(8) RE-12', '216 (8) A7 high-side flight blank, four conditions', 'DONE for 3 of 4 (config.h, this file, test v210-2 on d6 b7); condition 3 is the FC owner\'s', 'start_monitors.A7_flight_blank'),
        (216, '(9) R2-22', '216 (9) lift-commanded hold; R2-23', 'DONE (SIL)', 'r2_command_hold'),
        (216, '(10) Text and record items', '216 (10) text and record items', 'DONE (see rev_elec_2_author_status)', 'rev_elec_2_author_status'),
        (227, '(5) R2 starve window', '227 (5) 0.8 s window: confirm or return', 'CONFIRMED inside the W10 < 6 m/s envelope, with conditions (SIM)', 'drogue_release_support.r2v2_sweep.verdict_227_5'),
        (227, '(6) Mode-3 estimator', '227 (6) mode-3 re-initialisation at the Pc-invalid onset; FC frame-noise budget', 'DONE in the S17 R2 v2 evaluator (the FC implementation is GNC\'s); budget stated', 'drogue_release_support.r2v2_sweep.noise_budget_227_6'),
        (227, '(7) RE-24, lead safety decision', '227 (7) GIMBAL_FAULT not inhibited near touchdown', 'NOTED: firmware unchanged (no inhibit)', 'abort_matrix GIMBAL_FAULT'),
        (229, '(3) Purge: ONE basis 29.25 g/s', '229 (3) Combustion purge basis 29.25 g/s', 'USED (config.h kPurgeMdotBasis_kgps)', 'head_end_bleed_provision.masses'),
        (229, '(4) Start-level lift 0.21776 mm', '229 (4) start-level lift 0.21776 mm', 'USED (kR2HoldLift_m)', 'r2_command_hold'),
        (229, '(5) P4c lit side', '229 (5) lit side F >= 33.14 N', 'CARRIED as an S17 open item (230 (5))', 'drogue_release_support.r2v2_sweep.lit_side_230_5'),
        (230, '(2) Line 194 (1) band values are RESTATED', '230 (2) restated FA-1 band values', 'USED for the face-peak statement (routed to REV-COMB-4 by 249 (15))', 'pc_overrange_fa1.period_domain'),
        (230, '(3) Purge (OI-42; line 216 (5))', '230 (3) cap 2.39 s if the scheduled flow fits, else keep 2.55 s and state the warm-end mass', 'ANSWERED: does not fit; 2.55 s kept; warm-end mass stated; lead decides', 'head_end_bleed_provision.cap_decision_230_3'),
        (230, '(4) The start-level lift 0.21776 mm', '230 (4) ECU hold-lift row (OI-43)', 'DONE (SIL)', 'r2_command_hold'),
        (230, '(5) P4c lit side', '230 (5) F_min 33.14 N as an S17 open item', 'CARRIED (S17 sensitivity run)', 'drogue_release_support.r2v2_sweep.lit_side_230_5'),
        (233, 'an Electronics / GNC decision', '233 lever rod-force alternative', 'NOTED: not chosen; no Electronics action', None),
        (236, 'The lead then sets the abort value and tells Electronics, Combustion and GNC', '236 (5) abort value', 'DONE: 423.15 K (243 (3))', 'limits_v2p11'),
        (242, 'Electronics to confirm its channel tolerance inside 12.3 K', '242 case-TC channel tolerance', 'DONE (Part A; ACCEPTED 249 (1))', 'case_tc_channel'),
        (243, '(3) ABORT VALUE', '243 (3) A = 150 C with conditions (a) / (b)', 'DONE: (a) 7.78 K worst case inside +12.3 K; (b) tol_lo = 9.05 + 0.630 r K', 'case_tc_channel'),
        (247, 'requests (Electronics 243 (3)', '247 Mechanical v3.5.2 request to Electronics', 'ANSWERED', 'requests_answered'),
        (248, 'FOUNDER RULE', '248 founder rule: J-FWD counts as used after a case-TC or TB-state abort', 'DONE (bench plan v4 F-14)', 'bench_plan.founder_block'),
        (249, '(1) CASE-TC ABORT CHANNEL', '249 (1)-(4) lead rulings on Part A', 'IMPLEMENTED (firmware v2.11, bench plan v4, this file)', 'lead_rulings_v2p11; limits_v2p11'),
        (249, '(13) RUNS', '249 (13) record cited by the lead (MANIFEST 620b3d566fe0c8b9)', 'SUPERSEDED by two re-records after comment-only / Makefile edits, binaries identical (firmware.record)', 'firmware.record.re_records_after_line_249_13'),
        (249, '(15) OPEN after this line', '249 (15) open items naming Electronics', 'Part B = this handback; S6R input finding routed to REV-COMB-4', 'pc_overrange_fa1.period_domain; ride_through'),
        (250, '(11) STATE at 05:23Z', '250 lead record after line 249 (FEA3D-2 results, agent order, state): assigns Electronics no item; '
                                      'REV-ELEC-3 follows this handback ((7))', 'NOTED (no Electronics item)', '-')]
    doc['changelog_folding'] = [OrderedDict([('line', n), ('item', it), ('status', st), ('where', wh), ('quote', cite(n, mk, 200, 30))])
                                for (n, mk, it, st, wh) in FOLD]
    doc['lead_rulings_v2p11'] = OrderedDict([
        ('record', 'LEAD 2026-10-20T21:46:49Z and 21:51:07Z rulings on the v2.11 Part A, recorded by the lead as CHANGELOG line 249 (1)-(4)'),
        ('case_tc_abort_channel', cite(249, '(1) CASE-TC ABORT CHANNEL', 1150)),
        ('stand_T0_rule', cite(249, '(2) STAND T0 RULE', 760)),
        ('T_F1_basis', cite(249, '(3) T-F1 EXPOSURE BASIS', 1250)),
        ('relight_and_transducer', cite(249, '(4) RELIGHT AND TRANSDUCER', 900)),
        ('disk', cite(249, '(12) DISK', 420)),
        ('runs', cite(249, 'Electronics v2.11\'s final test record 2 is done', 300)),
        ('runs_note', 'the MANIFEST cited in 249 (13) is superseded by two re-records with byte-identical binaries (comment-only batch, Makefile '
                      'ovp target fix): firmware.record.re_records_after_line_249_13'),
        ('open', cite(249, "Electronics' S6R input finding", 330))])

    # ================================================================================================ firmware + SIL record v2.11
    s13_classes = lambda d_: OrderedDict((c_['class'], c_['runs']) for c_ in d_['classes'])
    s6cases = OrderedDict((c_['case'], c_) for c_ in s6['cases'])
    s6_case_tc = OrderedDict((k, OrderedDict([('cause', s6cases[k]['cause_name']), ('inj_to_abort_s', s6cases[k]['inj_to_abort_s'])]))
                             for k in ('case_over_temp_430K', 'case_415K_in_RUN_no_abort'))
    if s6_case_tc['case_over_temp_430K']['cause'] != 'OVER_TEMP' or s6_case_tc['case_415K_in_RUN_no_abort']['cause'] != 'NONE':
        raise SystemExit('S6 case-TC cases not as recorded: %s' % s6_case_tc)
    s6r_req = [c_ for c_ in s6r['cases'] if c_['class'] == 'PASS_aborted_inside']
    s6r_ctrl = [c_ for c_ in s6r['cases'] if c_['class'] == 'CONTROL_inside']
    s6r_in_out = [c_ for c_ in s6r['cases'] if c_['class'] == 'INPUT_outside_envelope']
    if len(s6r_req) != s6r['required_cases'] or s6r['required_passed'] != s6r['required_cases'] or s6r['runs_outside_envelope_ecu'] != 0 \
            or len(s6r_in_out) != s6r['runs_input_outside_envelope'] or len(s6r_req) + len(s6r_ctrl) + len(s6r_in_out) != s6r['runs']:
        raise SystemExit('S6R record counts not consistent')
    s6r_fam = OrderedDict()
    for c_ in s6r['cases']:
        f_ = s6r_fam.setdefault(c_['family'], Counter())
        f_[c_['class']] += 1
    s6c_rows = [OrderedDict([('case', c_['case']), ('comparator_tau_ms', c_['comparator_tau_ms']), ('cause', c_['cause']),
                             ('inj_to_abort_ms', c_['inj_to_abort_ms']), ('inj_to_hw_comparator_trip_ms', c_['inj_to_hw_comparator_trip_ms']),
                             ('peak_head_bar_abs', c_['peak_head_bar_abs']), ('zone_max', c_['zone_max']), ('inside_LC_TB70', c_['inside_LC_TB70']),
                             ('jfwd_rule_triggered', c_['jfwd_rule_triggered'])]) for c_ in s6c['cases']]
    if not all(c_['inside_LC_TB70'] for c_ in s6c['cases']) or any(c_['jfwd_rule_triggered'] for c_ in s6c['cases']):
        raise SystemExit('S6C: a case outside LC-TB70 or with the J-FWD rule - review ride_through before publishing')
    abort_value_note = (
        'every S6 / S6R / S6C case runs the v2.11 build with kCaseOverTemp_K %s K (A = 150 C, LEAD 243 (3), CHANGELOG 249 (1)); only the S6 '
        'cases case_over_temp_430K (-> %s at +%.2f s) and case_415K_in_RUN_no_abort (%s) exercise the case-TC abort; the over-pressure cases '
        'never reach it. LC-TB70 Z1 is labelled "case at the 448.15 K abort" by Mechanical: that label is its TB thermal field (the old '
        'abort value), a state hotter than any the 423.15 K abort admits, so the S6 / S6R / S6C checks against Z1 hold for the abort in '
        'force' % (cv('kCaseOverTemp_K'), s6_case_tc['case_over_temp_430K']['cause'], s6_case_tc['case_over_temp_430K']['inj_to_abort_s'],
                   s6_case_tc['case_415K_in_RUN_no_abort']['cause']))
    cmp_files = cmpj['files']

    def cmp_line(f):
        e = cmp_files[f]
        if 'status' in e:
            return e['status']
        if 'cases_identical' in e:
            t_ = 'cases identical %d, changed %d' % (e['cases_identical'], e['cases_changed'])
            for k in ('passed', 'total', 'fail'):
                if k in e:
                    t_ += ', %s %s -> %s' % (k, e[k][0], e[k][1])
            return t_
        if 'leaves_v2p10' in e:
            return 'leaves %d / %d, %d changed' % (e['leaves_v2p10'], e['leaves_v2p11'], e['n_changed_leaves'])
        return 'runs %s -> %s, fail %s -> %s (%s)' % (e['runs'][0], e['runs'][1], e['fail'][0], e['fail'][1], e['fail_basis'])
    doc['firmware'] = OrderedDict([
        ('version', fw_ver),
        ('target', 'PJRC Teensy 4.1 (i.MX RT1062). HAL NOT written (RE-06; LEAD 166 (9): Electronics open item, required before B-PC-1). '
                   'The core runs in SIL and test_core only'),
        ('record', OrderedDict([
            ('manifest', '06-electronics/results/sil_v2p11/MANIFEST_v1.json'), ('manifest_sha256_16', sha(os.path.join(SIL, 'MANIFEST_v1.json'))),
            ('record_sha256_16', man['record_sha256_16']), ('record_utc', man['record_utc']), ('tool', '%s %s' % (man['tool'], man['tool_revision'])),
            ('tree_sha256_16', man['tree_sha256'][:16]), ('n_files', man['n_files']), ('n_results', len(man['results'])),
            ('binaries', OrderedDict((k, OrderedDict([('sha256_16', b['sha256_16']),
                                                      ('rebuild_of_current_tree_identical', b['rebuild_of_current_tree']['identical'])]))
                                     for k, b in bins.items())),
            ('scenarios', [OrderedDict([('id', s_['id']), ('binary_sha256_16', s_['binary_sha256_16']), ('files', s_['n_files'])])
                           for s_ in man.get('scenarios') or []]),
            ('scenarios_file', 'results/sil_v2p11_runmap.json %s' % sha(runmap_path)),
            ('unmapped_results', len(man.get('results_unmapped') or [])),
            ('sources_edited_after_newest_result', man.get('sources_edited_after_newest_result')),
            ('sources_edited_note', 'comment-only edits (config.h, protocol.h, types.h, engine_ecu.cpp), the Makefile ovp target and the '
                                    'manifest tool after the last result; every binary rebuilt from the current tree is byte-identical to the '
                                    'one that produced the results (rebuild_of_current_tree_identical); the rebuild paths in the manifest point '
                                    'to an Electronics scratch folder removed at the close-out (the hashes are the evidence)'),
            ('date_field_note', 'the manifest "date" field (%s) is the tool default; record_utc is the record time' % man.get('date')),
            ('re_records_after_line_249_13', [
                'MANIFEST 620b3d566fe0c8b9 (record d3812c6332350d20, record_utc 2026-10-21T02:15:54Z): the record cited by CHANGELOG 249 (13)',
                'MANIFEST 4a611ee9fdacb88f (record 87c94300d897d4f4, 2026-10-21T02:29:53Z): after a TLM_RELIGHT relight-worst comment batch '
                '(protocol.h, types.h, engine_ecu.cpp; comments only), binaries identical',
                'MANIFEST %s (record %s, %s): after the Makefile "ovp" target fix (it ran calc/pc_transducer_v2.py; now '
                'calc/v2p11/pc_transducer_v3.py, whose re-run gives sil/ovp_hw_params.h byte-identical), binaries identical: THIS record'
                % (sha(os.path.join(SIL, 'MANIFEST_v1.json')), man['record_sha256_16'], man['record_utc'])])])),
        ('unit_tests', OrderedDict([
            ('hooks_build', man['test_core']['all_logs']['test_core_log.txt'] + ' (results/sil_v2p11/test_core_log.txt %s)' % sha(os.path.join(SIL, 'test_core_log.txt'))),
            ('no_hooks_build', man['test_core']['all_logs']['test_core_nohooks_log.txt'] + ' (results/sil_v2p11/test_core_nohooks_log.txt %s; '
                               'R2-08: the core built without ECU_SIL_TEST_HOOKS, the one hook-only case skipped)' % sha(os.path.join(SIL, 'test_core_nohooks_log.txt'))),
            ('v2p11_cases', [T(r'LogRecord v12 is 180 bytes'), T(r'v2\.11 203 \(1\)\(a\): over-range HIGH'), T(r'v2\.11 case A - 3 K'),
                             T(r'v2\.11 case in COAST'), T(r'unpurged RELIGHT guard'), T(r'216 \(8\) condition 4'), T(r'hard cap \(v2\.11 value'),
                             T(r'above-FS flag'), T(r'non-sticky over-range'), T(r'203 \(1\)\(b\) ride-through \(flight relight\)'),
                             T(r'ride-through never applies'), T(r'ride-through is a build option'), T(r'over-range N = 2'),
                             T(r'LEAD 203 \(3\) cap 2\.55 s'), T(r'LEAD 205 C1 scaling'), T(r'items 3/5: stand ARM refused'),
                             T(r'lost DROGUE 0'), T(r'R2 backstop is per burn'), T(r'lift-commanded R2 hold'), T(r'cold ARM margin'),
                             T(r'PREPRESS safe exit'), T(r'hardware both-open timer'), T(r'216 \(4\) BASE_AMB per location'),
                             T(r'light rule baseline \(LEAD RE-02\) \+ v2\.11')])])),
        ('arm_build', OrderedDict([
            ('v', 'make arm (arm-none-eabi-g++ 13.2.1 -Os, Cortex-M7 fpv5-d16 hard-float): the four core objects compile, 0 errors; objects '
                  'only (not linked, no HAL); text control.o 5838, engine_ecu.o 30922, protocol.o 3528, sensor_scale.o 796 = 41084 B (v2.10 '
                  '39316 B, +1768 B); 96 -Wdouble-promotion warnings (v2.10: 93; the 3 new ones compare float constants with double time / a '
                  'double sum); objects identical to the 01:50Z build of the record tree'),
            ('log', 'results/arm_build_v2p11_log.txt %s' % shr(os.path.join(RES, 'arm_build_v2p11_log.txt'))),
            ('tag', 'DERIVED (compile and size check only; no target execution)')])),
        ('config_diff_v2p10', config_diff),
        ('sil_record_v2p11', OrderedDict([
            ('comparison', 'results/sil_v2p11/compare_v2p10_v2p11.json %s (+ .txt), calc/v2p11/sil_compare_v1.py: every v2.10 result file '
                           'case by case or leaf by leaf; per file below' % sha(os.path.join(SIL, 'compare_v2p10_v2p11.json'))),
            ('per_file_vs_v2p10', OrderedDict((f, cmp_line(f)) for f in cmp_files)),
            ('S5_pad_mc', OrderedDict([
                ('runs', s5['runs']), ('armed_runs', s5['armed_runs']), ('flying_runs', s5['flying_runs']), ('aborts', s5['aborts']),
                ('abort_causes', s5_causes_named), ('interlock_refused_at_arm', s5.get('interlock_refused_at_arm')),
                ('non_flying_by_first_cause', s5['non_flying_by_first_cause']),
                ('plant_Pc_max_bar_abs', round(s5['pc_max_abs_max_Pa'] / 1e5, 3)), ('pc_overpressure_aborts', s5['ovp_aborts']),
                ('hw_comparator_trips', s5['hw_comparator_trips']),
                ('flying_eng03_clause_a_frac', s5['flying_pass_eng03_clause_a_frac']), ('flying_eng03_req_150ms_frac', s5['flying_pass_eng03_req_150ms_frac']),
                ('flying_eng03_target_100ms_frac', s5['flying_pass_eng03_target_100ms_frac']),
                ('flying_up_rise_p50_p95_max_s', [s5['flying_up_rise_p50_s'], s5['flying_up_rise_p95_s'], s5['flying_up_rise_max_s']]),
                ('flying_up_overshoot_p50_p95_max_pct', [s5['flying_up_overshoot_p50_pct'], s5['flying_up_overshoot_p95_pct'], s5['flying_up_overshoot_max_pct']]),
                ('denominators', s5['denominators']), ('prepress_safe_exit_runs', s5['prepress_safe_exit_runs']),
                ('note', 'R2-10: the ENG-03 statistics are stated over the flying runs (the runs that reach the pintle steps); the all-runs '
                         'fractions stay in the file')])),
            ('probeF_RE04', OrderedDict([('runs', len(pf['runs'])), ('worst_plant_Pc_bar_abs', pf['worst_plant_Pc_bar_abs']),
                                         ('pc_overpressure_aborts', pf['pc_overpressure_aborts']), ('aborts', pf['aborts']),
                                         ('abort_causes', [r_['abort'] for r_ in pf['runs'] if r_['abort'] != 'none']), ('pass', pf['pass'])])),
            ('S6_abort_paths', OrderedDict([('passed', '%d/%d' % (s6['passed'], s6['total'])),
                                            ('case_tc_cases', s6_case_tc), ('abort_value', abort_value_note)])),
            ('S6R_in_window_overpressure', OrderedDict([
                ('file', 'results/sil_v2p11/S6R_in_window_overpressure.json %s' % sha(os.path.join(SIL, 'S6R_in_window_overpressure.json'))),
                ('runs', s6r['runs']), ('required', s6r['required_cases']), ('required_passed_aborted_inside_LC_TB70', s6r['required_passed']),
                ('controls_inside', len(s6r_ctrl)), ('input_outside_LC_TB70', len(s6r_in_out)), ('ECU_outside_LC_TB70', s6r['runs_outside_envelope_ecu']),
                ('builds', [b_['build'] for b_ in s6r['builds']]), ('families', OrderedDict((k, OrderedDict(v)) for k, v in s6r_fam.items())),
                ('required_causes', OrderedDict(Counter(c_['cause'] for c_ in s6r_req))),
                ('required_zone_max_counts', OrderedDict(sorted(Counter(c_['zone_max'] for c_ in s6r_req).items()))),
                ('required_peak_head_max_bar_abs', max(c_['peak_head_bar_abs'] for c_ in s6r_req)),
                ('required_jfwd_rule_triggered', sum(1 for c_ in s6r_req if c_['jfwd_rule_triggered'])),
                ('abort_value', abort_value_note), ('envelope_label', s6r['envelope'])])),
            ('S6C_fixed_rc_cost', OrderedDict([('file', 'results/sil_v2p11/S6C_rc_cost.json %s' % sha(os.path.join(SIL, 'S6C_rc_cost.json'))),
                                               ('cases', len(s6c['cases'])), ('all_inside_LC_TB70', True), ('jfwd_rule_triggered', 0),
                                               ('abort_value', abort_value_note)])),
            ('S8_priming', '%d/%d' % (s8['passed'], s8['total'])),
            ('S9_pc_transducer', OrderedDict([('fail_lines', 4), ('note', 'the scenario text and the +/-1.034 bar bias cases (the 070BG TEB) are v2.6 '
                                                                      'labels; the v2.11 run uses the default C1 chain (sil/sim.h pc_chain 1) with '
                                                                      'the same injected biases: the 4 fails are the v2.10 ones (sil_fail_dispositions)')])),
            ('S10_relight', '%d/%d' % (s10['passed'], s10['total'])),
            ('S10v211_cold_rule', OrderedDict([('cases', len(s10c['cases'])), ('fail', s10c['fail']), ('arm_margin_K', s10c['arm_margin_K']),
                                               ('prepress_drop_max_K', s10c['prepress_drop_max_K']), ('margin_check', s10c['margin_check']),
                                               ('estimate_minus_plant_K_range', s10c['estimate_minus_plant_K_range'])])),
            ('S12_bleed', '%d/%d (fail %d: the 4 v2.10 detection-gap cases; mass above 76 g in %d cases on the SIL plant basis; 3 new '
                          'hardware-timer EVIDENCE cases)' % (sum(1 for c_ in s12['cases'] if c_['pass']), len(s12['cases']), s12['fail'],
                                                               s12['mass_over_limit_cases'])),
            ('S13_light_rule', OrderedDict([('B_residual_corners', '%d cases, %d fail' % (s13['B_cases'], s13['B_fail'])),
                                            ('B_extension_kBpc1Shown_false', OrderedDict([('runs', s13f['runs']), ('fail_v2p11_criteria', s13f['fail_v2p11_criteria']),
                                                                                          ('classes', s13_classes(s13f))])),
                                            ('B_extension_kBpc1Shown_true', OrderedDict([('runs', s13t['runs']), ('fail_v2p11_criteria', s13t['fail_v2p11_criteria']),
                                                                                         ('classes', s13_classes(s13t))])),
                                            ('criteria_v2p11', s13f['criteria_v2p11'])])),
            ('S14_pool_and_pc_invalid', OrderedDict([('cases', len(s14['cases'])), ('fail_count', s14['fail_count'])])),
            ('S15_start_mc', OrderedDict([('flight', s15['flight']), ('stand', s15['stand'])])),
            ('S16_coast_drift', [OrderedDict([('drift_bar', c_['drift_bar']), ('stand', c_['stand']), ('relight_refused', c_['relight_refused']),
                                              ('first_abort', c_['first_abort']), ('rezero2', c_['f2_rezero2']), ('rezero2_rejected', c_['f2_rezero2_rejected'])])
                                 for c_ in s16['cases']]),
            ('S17_r2_command_hold_v2p10_stand_in', OrderedDict([('cases', len(s17['cases'])), ('not_as_expected', s17['not_as_expected_count']),
                                                               ('note', 'v2.10 stand-in scenario kept for continuity; the v2.11 evidence is S17v2')])),
            ('S17v2_r2v2_sweep', OrderedDict([('file', 'results/sil_v2p11/S17v2_r2v2_sweep.json %s' % sha(os.path.join(SIL, 'S17v2_r2v2_sweep.json'))),
                                              ('groups', len(s17v2['groups'])), ('detail', 'drogue_release_support.r2v2_sweep')])),
            ('label_note', 'S14_v2p10.json, S15, S16, S17_r2hold.json and probeF carry their v2.10 scenario id / version labels: they are the '
                           'v2.11 runs of unchanged scenarios (manifest record above)'),
            ('fail_count', man.get('sil_fail_count_v13')),
            ('fail_lines', man.get('sil_fail_lines_v13')),
            ('fail_lines_note', 'manifest tool status-token rule over every scenario log: S6 3, S9 4, S12 4 (the v2.10 set; dispositions below)')])),
        ('W_build_constant', OrderedDict([
            ('flight_relight_W', C('kIgnWindowRelightLong_s')), ('flight_first_start_W', C('kIgnWindowFirst_s')),
            ('stand_R1_W', C('kIgnWindowFirstStand_s')), ('stand_R2_W', C('kIgnWindowRelightStand_s')),
            ('rule', 'compile-time constant; the SIL what-if SIL_WHATIF_RELIGHT_W #errors without ECU_SIL_TEST_HOOKS')])),
    ])

    # ================================================================================================ SIL fail dispositions (v2.11)
    tb70 = [c_ for c_ in s6['cases'] if c_['case'] == 'throat_blocked_70pct_500N_24C_Cd0p8'][0]
    tb70c = [c_ for c_ in s6c['cases'] if c_['case'] == 'throat_blocked_70pct_500N_24C_Cd0p8_fw_on' and c_['tau'].startswith('as_built')][0]
    s12fb = [c_ for c_ in s12['cases'] if c_['case'] == 'stuck_open_first_burn_d1.0mm'][0]
    doc['sil_fail_dispositions'] = [
        OrderedDict([('id', 'S6 gimbal_jam_moving_cmd'), ('disposition', 'DISPOSITIONED (RE-24; test-based, LEAD 203 (6)); abort NOT inhibited near touchdown (LEAD 227 (7))'),
                     ('why_fails', 'per-axis mismatch at a 2 deg command stays below the %s threshold; detection bound >= 3 deg per axis / 2.12 deg '
                                   'along a servo line' % human(C('kGimbalFaultErr_rad'))),
                     ('closure', 'B-TVC-1 measures the bound on the as-built linkage; travel-ratio detector = research proposal (not in v2.11)')]),
        OrderedDict([('id', 'S6 throat_blocked_70pct_500N_24C_Cd0p8'), ('disposition', 'ACCEPTED-WITH-REASON; now checked against LC-TB70: INSIDE'),
                     ('why_fails', 'the hardware comparator acts first (HW_OVERPRESSURE, scenario expects PC_OVERPRESSURE); plant Pc %.1f bar abs > '
                                   'MEOP; S6C on the same fault: head peak %.2f bar abs, zone %d, inside LC-TB70, J-FWD rule not triggered '
                                   '(R2-15: %.0f ms above MEOP is restated from the LC-TB70 pressure-time form, not 72 ms)'
                                   % (tb70['Pc_max_abs_Pa'] / 1e5, tb70c['peak_head_bar_abs'], tb70c['zone_max'], tb70['t_Pc_above_MEOP_s'] * 1e3)),
                     ('closure', 'Mechanical LC-TB70 (04-fea/v352/lc_tb70_envelope_v1.json %s) covers it; the fault itself stays a Combustion / '
                                 'Mechanical load case' % sha(lctb_path))]),
        OrderedDict([('id', 'S6 throat_blocked_70pct_500N_24C_Cd0p8_ballvalve_v2p7_compare'), ('disposition', 'OBSOLETE (comparison evidence)')]),
        OrderedDict([('id', 'S9 unlit_spike_train_20bar_2ms_50Hz'), ('disposition', 'CONFLICT kept (RE-02)'),
                     ('why_fails', 'the spike train raises P0 above the check -> BASE_HIGH -> PC_SENSOR refusal at E1 on the pad (the scenario '
                                   'expects TORCH_FAULT); fail-safe, the LEAD 216 (4) pad target (refusal before the lift)')]),
        OrderedDict([('id', 'S9 unlit_bias_plus_1p034bar_TEB, lit_bias_plus/minus_1p034bar_TEB'), ('disposition', 'OPEN (OI-TEB-FALSE-LIGHT)'),
                     ('closure', 'B-PC-1 residual <= 0.3 bar, then kBpc1Shown')]),
        OrderedDict([('id', 'S12 stuck_open_after_lift d0.6/0.8/1.0 mm stand, stuck_open_first_burn d1.0 mm'), ('disposition', 'OPEN (OI-BLEED-DETECT; LEAD 203 (4))'),
                     ('why_fails', 'the S12 cases inject BOTH bleed valves stuck open (the 203 (4) label "V1 stuck open with V2 closed" is corrected '
                                   'in head_end_bleed_provision.oi_bleed_detect): on the decided path P_mid then stays below the U570 band -> no leak '
                                   'flag on the stand; the flight first-burn case raises the leak flag %.2f s after injection (criterion < 0.5 s; %.1f g '
                                   'through the bleed) [SIM results/sil_v2p11/S12_bleed.json]' % (s12fb['leak_flag_after_injection_s'], s12fb['purge_mass_g'])),
                     ('closure', 'no detection design in v2.11 (candidate low U570 threshold near 2 bar abs NOT adopted: separation not shown, '
                                 'pc_transducer_v3 G); residual vented masses go to GNC / FMEA (head_end_bleed_provision.oi_bleed_detect)')]),
        OrderedDict([('id', 'S14 starved_A1_relight_reference_flight (INFO case)'), ('disposition', 'EVIDENCE'),
                     ('why_fails', 'reference starved plateau (cap stand-in 2.6 bar abs, lift-independent) -> A3 FLAMEOUT after E2; the stand-in is '
                                   'pessimistic; not a v2.11 change')]),
        OrderedDict([('id', 'S13 B extension'), ('disposition', 'CLOSED under the LEAD 216 (4) per-location criteria (0 fails in both builds)'),
                     ('note', 'the v2.10 lead-criteria fails (%d / %d) are history; A1 BASE_AMB outcome (P0 := 0, lift, A7 HOLD PC_SENSOR, no light) '
                              'stated for the lead in light_rule.base_check_per_location' % (s13f['lead_criteria_fail_v2p10'], s13t['lead_criteria_fail_v2p10']))]),
    ]

    # ================================================================================================ CAN interface (v3 carried + v2.11 items)
    can = copy.deepcopy(v3['can_interface'])
    can['ids_parsed_from_protocol_h'] = OrderedDict(('0x%03X' % v, k) for k, v in ids.items())
    can['frames']['0x102 ECU->FC TLM_RELIGHT 50 Hz, every state'] = (
        'len 8: [seq][state][flags][relight worst u16 ms][P_feed/P_tank %%, 0xFF invalid][d6: b0-b5 refuse reason (codes 0-%d, UNPURGED %d '
        'added in v2.11), b6 DROGUE echo (LEAD 186 (2)), b7 PC_VALID (LEAD 175 (4))][crc8]' % (max(refuse.values()), refuse['UNPURGED']))
    can['event_codes'] = events
    can['tlm_relight_flags_d2'] = tlmr
    can['tlm_relight_d6'] = OrderedDict([
        ('b0_b5', 'refuse reason (refuse:: enum, below; codes 0-%d, UNPURGED = %d is the highest; static_assert(refuse::UNPURGED <= '
                  'BLOCK_MASK) in protocol.h)' % (max(refuse.values()), refuse['UNPURGED'])),
        ('b6', 'DROGUE: drogue attached as last reported by the FC (Cmd::DROGUE echo, LEAD 186 (2))'),
        ('b7', 'PC_VALID')])
    can['refuse_reasons'] = refuse
    can['pc_valid_bit'] = tv('TLM_RELIGHT d6 b7 = Pc channel valid this tick AND no latched PC_SENSOR fault AND no latched PC_SENSOR abort '
                             '(engine_ecu.cpp out.pc_commit_valid). v2.11 flight (kPcOverrangeNonSticky = true, LEAD 203 (1)(a)): a HIGH '
                             'over-range reading sets PC_VALID 0 on that tick only and does not latch fault::PC_SENSOR; a LOW reading still '
                             'latches; the stand keeps the v2.10 latch. For the FC launch commit (LEAD 175 (4)); decoders mask d6 & 0x3F for '
                             'the refuse reason (b6 = DROGUE)', 'DESIGN protocol.h / engine_ecu.cpp; test_core "non-sticky over-range"')
    can['cmd_drogue'] = tv('CMD_STATE cmd 17 DROGUE: arg 1 = drogue attached (FC, at the deployment), 0 = released (FC, at the release); other '
                           'values ignored; accepted in every state; reset to not attached at power-up and at an accepted ARM; echo TLM_RELIGHT '
                           'd6 b6. FC re-send rule (LEAD 216 (2)(a), FC owner): after its DROGUE 0 the FC re-sends DROGUE 0 with a new sequence '
                           'number on every TLM_RELIGHT frame (50 Hz) that still shows d6 b6 = 1, from the second such frame, at most 10 times '
                           '(0.2 s), then logs DROGUE_ECHO (bench plan v4 B-FC-1). ECU backstop (216 (2)(b)): the R2 hold ends at E2 + %s '
                           '(r2_command_hold.lost_drogue0) whatever the report. Effect: r2_command_hold' % human(C('kR2HoldBackstop_s')),
                           'DESIGN types.h / engine_ecu.cpp; LEAD CHANGELOG 186 (2), 216 (2); test_core v210-17, "lost DROGUE 0"')
    can['abort_path'] = OrderedDict([
        ('frame', 'ABORT 0x010 or CMD_STATE ABORT'),
        ('latency', v3['can_interface']['abort_path']['latency']),
        ('effect_sil', v3['can_interface']['abort_path']['effect_sil']),
        ('fc_rule_r2_v2', cite(227, '(5) R2 starve window', 420)),
        ('fc_rule_r2_v2_estimator', cite(227, '(6) Mode-3 estimator', 360)),
        ('r2_drogue_hold_abort', tv('Pc lost in flight RUN, R2 not met -> FC ABORT at t_E2 + W (W = 0.8 s ADOPTED for the W10 < 6 m/s envelope, '
                                    'LEAD 227 (5); 0.5 s kept as the comparator): the ECU stays in RUN until the frame (flight Pc loss is flagged, '
                                    'not aborted), then ABORT/CMD on that tick, MV magnet released, pintle command 0 at +4 ms; the ECU R2 hold '
                                    'ends at E2 + %s at the latest (backstop, an EVENT, not an abort)' % human(C('kR2HoldBackstop_s')),
                                    'SIL test_core (v210-16; "lost DROGUE 0"), ideal lit plant; plant effect times as effect_sil'))])
    doc['can_interface'] = can

    # ================================================================================================ relight interface
    rl = OrderedDict()
    rl['sequence_v2p11'] = ('RELIGHT at the planned T_fire: direct path when the line is PRIMED (NC valve latch + opener ramp and torch at E0, lift '
                            'at E1 on 2oo2 torch confirmation, gate %s, W %s from the lift); prep path when UNPRIMED / UNKNOWN (PREPRESS first). '
                            'Flight build with the bleed fitted (A1): a RELIGHT is accepted only during PURGE (E0 at PURGE + %s); in COAST it is '
                            'refused UNPURGED (LEAD 203 (7))' % (human(C('kTorchGate_s')), human(C('kIgnWindowRelightLong_s')), human(C('kPurgeRelight_s'))))
    rl['unpurged_relight'] = tv('flight build with the head-end bleed fitted: a RELIGHT (or IGNITE) in COAST with no purge running is REFUSED with '
                                'refuse code UNPURGED (%d): no valve moves, TLM_RELIGHT relight_block UNPURGED with READY 0 (the FC reads it as '
                                '"PURGE first"); PURGE is accepted when the direct path applies (else PURGE_PATH) and the RELIGHT received during '
                                'PURGE is the accepted flight relight. Stand build: the unpurged start is kept (CF-4 / T4 measure it). A build '
                                'without the bleed fitted keeps the v2.10 relight paths. This is ECU command behaviour, not evidence that an '
                                'unpurged start is safe' % refuse['UNPURGED'],
                                'LEAD CHANGELOG 203 (7) (guard ADOPTED), 186 (1), 194 (3); test_core "unpurged RELIGHT guard"; S12 '
                                'relight_no_purge_flight_refused_UNPURGED_LEAD203_7')
    rl['unpurged_relight_decision'] = cite(203, '(7) Unpurged RELIGHT guard in the ECU ADOPTED', 300)
    rl['purge_commit'] = v3['relight_interface']['purge_commit']
    rl['purge_commit_decision'] = v3['relight_interface']['purge_commit_decision']
    rl['relight_worst_ms'] = tv('TLM_RELIGHT d3-d4 worst valve-command -> Pc-confirm time of a RELIGHT sent now: 810 ms flight direct (gate + W), '
                                '1370 ms flight prep path, 3710 ms in COAST in the flight build with the bleed fitted (PURGE lead %s + gate + W: '
                                'the purge comes first)' % human(C('kPurgeRelight_s')), 'DESIGN protocol.h / engine_ecu.cpp; test_core (worst 3710 ms)')
    for k in ('torch_gate', 'W_flight_relight', 'primed_flag', 'states', 'rate', 'fc_planning_from_gnc', 'head_end_bleed'):
        rl[k] = copy.deepcopy(v3['relight_interface'][k])
    rl['torch_gate'], rl['W_flight_relight'] = C('kTorchGate_s'), C('kIgnWindowRelightLong_s')
    rl['case_tc_start_limit'] = OrderedDict([
        ('limit', C('kCaseRelightMax_K')),
        ('rule', 'a start command (IGNITE / RELIGHT) in ARMED, COAST or PREPRESS with TC1 or TC2 above the limit is refused CASE_HOT; ARM is '
                 'refused OVER_TEMP above it (both modes); the abort A is %s K' % cv('kCaseOverTemp_K')),
        ('basis', 'A1 merged purge-to-end-of-relight rise 11.9 K + a 1 s longer relight 3.0 K + 1 K relative channel error: 130 C + 15.9 K = '
                  '145.9 C <= A 150 C; A1 nominal start reading <= 99.5 C < 130 C (DERIVED results/case_tc_channel_v1.json %s A2_relight_refusal)'
                  % sha(os.path.join(RES, 'case_tc_channel_v1.json'))),
        ('decision', cite(249, '(4) RELIGHT AND TRANSDUCER', 330)),
        ('test', T(r'v2\.11 case in COAST'))])
    rl['a1_apogee_m'] = tv(210, 'LEAD CHANGELOG 214 (A1 APOGEE TARGET = 210 m), record only')
    doc['relight_interface'] = rl

    # ================================================================================================ abort matrix v4 + self-check
    errs = []
    matrix = []
    for name, code in abort_enum.items():
        if name == 'NONE':
            continue
        if name not in AB4:
            errs.append('%s: no template' % name)
            continue
        tpl, keys = AB4[name]
        errs += G3.template_check(name, tpl, keys, C)
        th = OrderedDict()
        for k in keys:
            th[k] = C(k) if C.has(k) else C(k, 'eng')
            if th[k]['v'] is None:
                errs.append('%s: %s did not evaluate' % (name, k))
        row = OrderedDict([('code', code), ('cause', name), ('trigger', G3.render(tpl, C)), ('thresholds', th)])
        if name in AB4_REF:
            row['decision'] = cite(AB4_REF[name][0], AB4_REF[name][1], 260)
        if name in AB4_RULING:
            row['decision_v2p11'] = [cite(n_, mk_, ch_) for (n_, mk_, ch_) in AB4_RULING[name]]
        matrix.append(row)
    for name in list(AB4_REF) + list(AB4_RULING):
        if name not in AB4:
            errs.append('%s: decision reference for a cause without a template' % name)
    for name in AB4:
        if name not in abort_enum:
            errs.append('%s: template for a cause that is not in types.h' % name)
    if errs:
        raise SystemExit('abort-matrix self-check FAILED:\n  ' + '\n  '.join(errs))
    doc['abort_matrix'] = OrderedDict([
        ('actions', v3['abort_matrix']['actions']),
        ('mv_seat_timeout', C('kMvSeatTimeout_s')),
        ('causes', matrix)])

    # ================================================================================================ light rule (+ RE-02 per location)
    loc = lambda d_: OrderedDict((l_['where'], OrderedDict((k, l_[k]) for k in ('runs', 'unlit_runs', 'unlit_false_E2', 'torch_fault', 'base_high_runs',
                                                                               'base_amb_runs', 'aborted_before_lift', 'aborted_after_lift',
                                                                               'mv_open_after_abort', 'fail_v2p11', 'base_amb_outcomes',
                                                                               'base_high_outcomes'))) for l_ in d_['locations'])
    amc = s13['A_mc'][0]
    a1t = [l_ for l_ in s13t['locations'] if l_['where'] == 'a1'][0]
    a1f = [l_ for l_ in s13f['locations'] if l_['where'] == 'a1'][0]
    if any('PC_SENSOR' not in k_ for k_ in a1f['base_amb_outcomes']) or a1f['unlit_false_E2'] or a1t['unlit_false_E2']:
        raise SystemExit('S13 B extension A1 BASE_AMB outcome changed - review light_rule.base_check_per_location')
    lr_ = OrderedDict()
    lr_['rule'] = tv('P0 = mean of filtered / raw gauge Pc over [E1 - 20 ms, E1]. Check against the auto-zero ambient, per location (LEAD CHANGELOG '
                     '166 (1), 216 (4)): pad first start and stand: P0 above +check (BASE_HIGH) or below -check (BASE_AMB) -> the lift is '
                     'refused (PC_SENSOR abort before any pintle command, MV closed by the abort); A1 relight: BASE_HIGH -> P0 kept, flagged '
                     'to the FC, RUN on the measured P0; BASE_AMB -> P0 := 0. Light (E2) = filtered AND raw rise over P0 >= kIgnRise_Pa with '
                     'filtered AND raw Pc >= the floor, kIgnConfirmRelN consecutive ticks', 'LEAD/COMB; test_core "216 (4) BASE_AMB per location"')
    for k in ('kIgnRise_Pa', 'kIgnConfirmRelN', 'kIgnPreN', 'kBpc1Shown', 'kIgnResidual_Pa', 'kIgnBaseCheck_Pa', 'kIgnFloorAbs_Pa'):
        lr_[k] = C(k)
    lr_['base_check_per_location'] = OrderedDict([
        ('criteria', s13f['criteria_v2p11']),
        ('kBpc1Shown_false_build', loc(s13f)), ('kBpc1Shown_true_build', loc(s13t)),
        ('a1_base_amb_outcome', tv('flight build: P0 := 0, the lift is commanded, the A7 HOLD band (low edge P0 - %s) is then violated by the '
                                   'below-ambient reading and PC_SENSOR aborts %s after the lift, before any light (lit and unlit plants alike); '
                                   'MV closed by the abort; the relight is lost, no false E2. kBpc1Shown true build (check %.1f bar): of %d A1 '
                                   'BASE_AMB runs %d end PC_SENSOR, the others: %s'
                                   % (human(C('kA7HoldLow_Pa')), human(C('kA7Time_s')), s13t['kIgnBaseCheck_Pa'] / 1e5, a1t['base_amb_runs'],
                                      sum(v_ for k_, v_ in a1t['base_amb_outcomes'].items() if 'PC_SENSOR' in k_),
                                      ', '.join('%s %d' % (k_, v_) for k_, v_ in a1t['base_amb_outcomes'].items() if 'PC_SENSOR' not in k_)),
                                   'SIM S13 B extension v2.11; test_core "216 (4) BASE_AMB per location" (A1: PC_SENSOR 50.0 ms after the lift)')),
        ('a1_population_occurrence', tv('S13 A Monte Carlo at the A1 relight state (relative rule): BASE_AMB %s, BASE_HIGH %s runs (lit, unlit) '
                                        'of %d lit + %d unlit' % (amc['base_amb_runs_lit_unlit'], amc['base_high_runs_lit_unlit'], amc['runs_lit'],
                                                                  amc['runs_unlit']), 'SIM (dispersed SIL population; not a probability for hardware)')),
        ('lead_item', 'the lead set no target for A1 BASE_AMB (216 (4)): Electronics states the outcome above (relight lost, fail-safe, 0 of 500 '
                      'in the A1 population); the alternative (keep the measured P0 below ambient so the HOLD band is not violated) is not '
                      'implemented and would need a lead ruling')])
    lr_['note'] = 'kBpc1Shown stays false until B-PC-1 shows residual <= 0.3 bar (OI-TEB-FALSE-LIGHT)'
    doc['light_rule'] = lr_

    # ================================================================================================ start monitors (+ A7 flight blank)
    sm = copy.deepcopy(v3['start_monitors'])
    sm['A3'] = tv('(Pc - P0)/(Pc_map_lo - P0) < %s for %s in RUN; denominator >= 0.5 bar' % (human(C('kFlameoutRel')), human(C('kFlameoutTime_s'))), 'LEAD/COMB + DESIGN')
    sm['light_spike_record'] = tv('no late-light abort (the v2.9 pressure-hold abort is deleted, RE-01, LEAD CHANGELOG 160): LIGHT_SPIKE record from '
                                  '%s abs (raw and filtered peak, time above %s and above the 30 bar limit, time from light) in the log and EVENT '
                                  '0x20; v2.11 (LEAD 203 (1)(a)): a sample at or above %s (above the C1 full scale) sets the above-full-scale flag '
                                  '(LIGHT_SPIKE ls_flags b7, log v12 ovr_flags) with PC_VALID untouched' % (human(C('kLightSpikeLoAbs_Pa')),
                                                                                                          human(C('kLightSpikeLoAbs_Pa')),
                                                                                                          human(C('kPcAboveFs_V'))),
                                  'LEAD; test_core "above-FS flag"')
    sm['A7'] = tv('HOLD band from E1 (low edge P0 - %s), START band E2 -> E3, RUN_MAP after E3; %s; IGNITION / stand -> PC_SENSOR abort, flight '
                  'RUN -> flag once per burn; HIGH side blanked from E2 to E2 + %s on the stand and in flight (RE-12; flight extension ACCEPTED '
                  'as DESIGN, LEAD 216 (8))' % (human(C('kA7HoldLow_Pa')), human(C('kA7Time_s')), human(C('kA7StartHiBlank_s'))), 'LEAD/COMB + DESIGN')
    cfg_lines = rd(os.path.join(CORE, 'config.h')).split('\n')
    cl_a = [i + 1 for i, ln in enumerate(cfg_lines) if 'CORRECTION (LEAD 216 (8), REV-ELEC-2 R2-12' in ln]
    cl_b = [i + 1 for i, ln in enumerate(cfg_lines) if 'FC condition (LEAD 216 (8))' in ln]
    if len(cl_a) != 1 or len(cl_b) != 1:
        raise SystemExit('config.h: the 216 (8) correction comment block not found once')
    sm['A7_flight_blank'] = OrderedDict([
        ('decision', cite(216, '(8) RE-12', 420)),
        ('blind_window', tv('E2 .. E2 + %s, A7 HIGH side only (stand and flight). Still ARMED in it: the filtered 30 bar abort (%s; ride-through '
                            'build %s to E2 + %s), the hardware comparator U330, A3 (flame-out, low side) and the A7 LOW side'
                            % (human(C('kA7StartHiBlank_s')), human(C('kPcOverPressureTime_s')), human(C('kRideOvpTime_s')), human(C('kRideWinPostE2_s'))),
                            'DESIGN config.h l.%d-%d' % (cl_a[0], cl_b[0]))),
        ('conditions', [
            OrderedDict([('n', 1), ('condition', 'config.h comment corrected (REV-ELEC-2 cited v2.10 l.369-372)'),
                         ('status', 'DONE: config.h l.%d-%d (v2.11 numbering)' % (cl_a[0], cl_b[0]))]),
            OrderedDict([('n', 2), ('condition', 'electronics.json states the blind window and what stays armed'),
                         ('status', 'DONE: blind_window above')]),
            OrderedDict([('n', 3), ('condition', 'the FC owner confirms no decision uses the A7 high flag (d6 b7 via PC_SENSOR) before E2 + 0.45 s'),
                         ('status', 'OPEN: FC owner (requests)')]),
            OrderedDict([('n', 4), ('condition', 'test v210-2 extended on d6 b7'), ('status', 'DONE: ' + T(r'216 \(8\) condition 4'))])])])
    _lt, _lv = [float(x.strip().rstrip('f')) for x in re.search(r'kIgnLiftT_K\[\w+\]\s*=\s*\{([^}]*)\}', rd(os.path.join(CORE, 'config.h'))).group(1).split(',') if x.strip()], \
        [float(x.strip().rstrip('f')) for x in re.search(r'kIgnLiftTab_m\[\w+\]\s*=\s*\{([^}]*)\}', rd(os.path.join(CORE, 'config.h'))).group(1).split(',') if x.strip()]
    if len(_lt) != len(_lv) or 286.70 not in [round(x, 2) for x in _lt]:
        raise SystemExit('config.h ignition-lift table not as expected')
    a1_row = _lv[[round(x, 2) for x in _lt].index(286.70)]
    if abs(a1_row - cv('kR2HoldLift_m')) > 1e-9:
        raise SystemExit('kIgnLiftTab_m A1 row (%.6g) != kR2HoldLift_m (%.6g)' % (a1_row, cv('kR2HoldLift_m')))
    sm['cf3_lift_table'] = tv('%d rows %.4f-%.4f mm vs T_tank (A1 row 286.70 K %.5f mm = kR2HoldLift_m, the Combustion v2.4b start level, LEAD '
                              '230 (4)); CF-3 measures at the commanded lift with the encoder recorded' % (len(_lt), min(_lv) * 1e3, max(_lv) * 1e3, a1_row * 1e3),
                              'DESIGN config.h kIgnLiftTab_m; CF-3 pending')
    doc['start_monitors'] = sm

    # ================================================================================================ drogue release support + S17 v2 sweep
    S = s17v2
    if abs(S['threshold_N'] - 37.159) > 1e-9 or abs(S['tau_s'] - 0.02) > 1e-12 or S['quick_smoke_test'] or S['e2_differs_from_reference_runs']:
        raise SystemExit('S17v2 header not as recorded (threshold / tau / smoke test / E2 reference)')
    D6 = dict(kind='dead', d_basis='W10<6 fo_none', sensitivity='none')
    DAW = dict(kind='dead', d_basis='all-winds fo_none', sensitivity='none')
    DCF = dict(kind='dead', d_basis='W10<6 fo_none', sensitivity='cold_flow_x1.3')
    L0 = dict(kind='lit', d_basis='lit 0', sensitivity='none')
    LCAP = dict(kind='lit', d_basis='lit 0', sensitivity='lit_cap_33.14N')
    LM12 = dict(kind='lit', d_basis='lit -12 (W2 withdrawn arm, sensitivity)', sensitivity='none')
    FAM = [('normal', False), ('starved040', True), ('normal_noopt', False), ('starved040_noopt', True)]
    REFS = ['none_GNC_sim6', 'LP_at_ECU_E2', 'LP_at_plant_light']

    def s17c(label, **f):
        """compact S17v2 row: counts per 1000 evaluations at the 0.5 / 0.8 s windows (both commands summed)"""
        out = OrderedDict([('row', label)])
        for w in (0.5, 0.8):
            g = grp(S, window_s=w, **f)
            out['W%.1f' % w] = OrderedDict([('n', g['evaluations']), ('dead_released', g['DEAD_RELEASED']), ('lit_released', g['LIT_RELEASED']),
                                            ('dead_abort', g['DEAD_ABORT']), ('lit_abort', g['LIT_ABORT']), ('ecu_left_RUN', g['ECU_LEFT_RUN']),
                                            ('margin_min_N', g['margin_min_N']), ('release_from_E2_ms', g['release_from_E2_ms_min_max'])])
        return out

    def lbl(fam, hold, fl, ref):
        return '%s | hold %s | flush %s | ref %s' % (fam, 'on' if hold else 'off', 'on' if fl else 'off', ref)
    rows_dead = []
    for fam, br in FAM:
        for hold in ((True, False) if not fam.endswith('_noopt') else (True,)):
            for fl in (False, True):
                for ref in (REFS if hold else REFS[:1]):
                    rows_dead.append(s17c(lbl(fam, hold, fl, ref), family=fam, fc_pc_branch=br, drogue_report_hold=hold, flush=fl, ref=ref, **D6))
    rows_allw = [s17c(lbl(fam, True, True, ref), family=fam, fc_pc_branch=br, drogue_report_hold=True, flush=True, ref=ref, **DAW)
                 for fam, br in FAM for ref in REFS]
    rows_cold = [s17c(lbl(fam, True, True, ref), family=fam, fc_pc_branch=br, drogue_report_hold=True, flush=True, ref=ref, **DCF)
                 for fam, br in FAM for ref in REFS]
    rows_lit = [s17c(lbl(fam, hold, fl, ref), family=fam, fc_pc_branch=br, drogue_report_hold=hold, flush=fl, ref=ref, **L0)
                for fam, br in FAM[:2] for hold in (True, False) for fl in (False, True) for ref in (REFS if hold else REFS[:1])]
    rows_litcap = [s17c(lbl(fam, True, fl, ref), family=fam, fc_pc_branch=br, drogue_report_hold=True, flush=fl, ref=ref, **LCAP)
                   for fam, br in FAM[:2] for fl in (False, True) for ref in REFS]
    rows_litm12 = [s17c(lbl(fam, True, True, ref), family=fam, fc_pc_branch=br, drogue_report_hold=True, flush=True, ref=ref, **LM12)
                   for fam, br in FAM[:2] for ref in REFS]
    br_dead = s17c('normal | FC Pc branch ON | hold on | flush on | ref none_GNC_sim6 (dead runs)', family='normal', fc_pc_branch=True,
                   drogue_report_hold=True, flush=True, ref='none_GNC_sim6', **D6)
    br_lit = s17c('normal | FC Pc branch ON | hold on | flush on | ref none_GNC_sim6 (lit runs)', family='normal', fc_pc_branch=True,
                  drogue_report_hold=True, flush=True, ref='none_GNC_sim6', **L0)
    for rr in (br_dead, br_lit):
        if rr['W0.5']['lit_released'] != rr['W0.5']['n'] or rr['W0.5']['release_from_E2_ms'] != [0.0, 0.0]:
            raise SystemExit('S17v2: the FC Pc branch no longer releases every normal run at the E2 frame - review the finding text')

    def R_(rows, label):
        for rr in rows:
            if rr['row'] == label:
                return rr
        raise SystemExit('S17v2 row %r not built' % label)
    dn = lambda fam, hold, fl, ref: R_(rows_dead, lbl(fam, hold, fl, ref))
    # the four design numbers the verdict rests on (checked, so the text below cannot drift from the record)
    v_hold_flush = [dn(f_, True, True, 'none_GNC_sim6') for f_ in ('normal', 'starved040')]
    v_noflush = [dn(f_, True, False, 'none_GNC_sim6') for f_ in ('normal', 'starved040')]
    v_nohold = [dn(f_, False, True, 'none_GNC_sim6') for f_ in ('normal', 'starved040')]
    v_noopt = [dn(f_, True, True, 'none_GNC_sim6') for f_ in ('normal_noopt', 'starved040_noopt')]
    v_noopt_lp = [dn(f_, True, True, r_) for f_ in ('normal_noopt', 'starved040_noopt') for r_ in REFS[1:]]
    if any(rr[w]['dead_released'] for rr in v_hold_flush + v_noopt_lp for w in ('W0.5', 'W0.8')) or \
            not all(rr[w]['dead_released'] for rr in v_noflush + v_nohold + v_noopt for w in ('W0.5', 'W0.8')):
        raise SystemExit('S17v2 dead-side pattern changed - review verdict_227_5')
    aw = R_(rows_allw, lbl('normal', True, True, 'none_GNC_sim6'))
    st_rows = OrderedDict()
    for r_ in S['starve_threshold']:
        k_ = (r_['window_s'], r_['flush'], r_['ref'])
        v_ = r_['plateau_released_at_all_10_phases_max_s']
        if k_ in st_rows and st_rows[k_] != v_:
            raise SystemExit('S17v2 starve threshold differs between 200 and 500 N: %s' % (k_,))
        st_rows[k_] = v_
    st_tab = [OrderedDict([('window_s', k_[0]), ('flush', k_[1]), ('ref', k_[2]), ('lit_released_at_every_phase_up_to_plateau_s', v_)])
              for k_, v_ in st_rows.items()]
    gnc_top = 0.4
    st_none = (st_rows[(0.5, True, 'none_GNC_sim6')], st_rows[(0.8, True, 'none_GNC_sim6')])
    nb = OrderedDict(((r_['case'], r_['window_s']), r_) for r_ in S['noise_budget_dead_W10lt6'])
    df5, df8 = nb[('design_flush', 0.5)]['per_family'], nb[('design_flush', 0.8)]['per_family']
    rl5, rl8 = nb[('flush_ref_at_light', 0.5)]['per_family'], nb[('flush_ref_at_light', 0.8)]['per_family']
    gmc = OrderedDict((r_['window_s'], r_) for r_ in S['gnc_margin_constant_check'])
    nb_tab = []
    for case_ in ('design_noflush', 'design_flush', 'nohold_noflush', 'nohold_flush', 'flush_ref_at_light', 'flush_cold_x1.3'):
        for w in (0.5, 0.8):
            r_ = nb[(case_, w)]
            nb_tab.append(OrderedDict([('case', case_), ('window_s', w), ('ref', r_['ref']), ('cold_scale', r_['cold_scale']),
                                       ('per_family', OrderedDict((f_, OrderedDict([('margin_min_N', v_['margin_min_N']),
                                                                                    ('iid_sigma_for_P_1e-3_N', v_['iid_sigma_for_Pmax_1e-3_N']),
                                                                                    ('iid_P_at_5N_rms', v_['iid_Pmax_at_5N_rms']),
                                                                                    ('ar1_sigma_for_P_1e-3_N', v_['mc_ar1_sigma_for_P_1e-3_bounding_run_N']),
                                                                                    ('bounding_run', v_['bounding_run_at_5N'])]))
                                                                  for f_, v_ in r_['per_family'].items()))]))
    pf_lit = [p_ for p_ in S['plant_facts'] if p_['drogue_report_hold'] and p_['kind'] == 'lit']
    pf_dead = [p_ for p_ in S['plant_facts'] if p_['drogue_report_hold'] and p_['kind'] == 'dead']
    hold_lift_rng = [min(p_['hold_lift_steady_mean_mm'] for p_ in pf_lit + pf_dead), max(p_['hold_lift_steady_mean_mm'] for p_ in pf_lit + pf_dead)]
    flit_rng = [min(p_['F_lit_in_hold_steady_mean_N'] for p_ in pf_lit), max(p_['F_lit_in_hold_steady_mean_N'] for p_ in pf_lit)]
    fcold_rng = [min(p_['F_cold_in_hold_steady_mean_N'] for p_ in pf_dead), max(p_['F_cold_in_hold_steady_mean_N'] for p_ in pf_dead)]
    bs_ms = sorted(set(x for p_ in pf_lit + pf_dead for x in p_['backstop_from_E2_ms'] if x is not None))
    if bs_ms != [round(cv('kR2HoldBackstop_s') * 1e3, 1)]:
        raise SystemExit('S17v2: backstop time not E2 + kR2HoldBackstop_s in every hold run: %s' % bs_ms)
    gl = S['r2_23_overrange_glitch']
    gl_early = [g_ for g_ in gl if g_['family'] == 'normal' and g_['glitch_from_E2_ms'] < 100]
    gl_late = [g_ for g_ in gl if g_['family'] == 'normal' and g_['glitch_from_E2_ms'] > 100]
    if any(g_['r2_hold_ticks_in_30ms'] != 1 for g_ in gl) or any(g_['ecu_abort'] != 'NONE' for g_ in gl_early):
        raise SystemExit('S17v2 R2-23 glitch runs: hold ticks or early-glitch outcome changed')
    gl_late_tab = [OrderedDict([('build', 'ride-through' if g_['ride_through'] else 'as built'), ('comparator_tau_ms', g_['comparator_tau_ms']),
                                ('F_rl_N', g_['F_rl_N']), ('Pc_before_bar_abs', g_['Pc_before_bar_abs']),
                                ('Pc_filtered_max_bar_abs', g_['Pc_filtered_max_30ms_bar_abs']), ('ecu_abort', g_['ecu_abort']),
                                ('ecu_left_RUN_from_glitch_ms', g_['ecu_left_RUN_from_glitch_ms'])]) for g_ in gl_late]
    nf8 = df8['normal']
    nf5 = df5['normal']
    verdict = OrderedDict([
        ('question', cite(227, '(5) R2 starve window', 470)),
        ('verdict', 'CONFIRMED for the W10 < 6 m/s launch-commit envelope, with conditions (SIM; not returned to the lead)'),
        ('dead_side', tv('with the ECU hold and the mode-3 flush at the Pc-invalid onset, 0 of %d dead evaluations are released at either window '
                         '(normal and starved040 families, main-chamber photodiode view, reference none = the dead-side bound); minimum margin '
                         '%+.3f N at 0.5 s and %+.3f N at 0.8 s (the 0.8 s window costs %.3f N)'
                         % (sum(rr['W0.8']['n'] for rr in v_hold_flush), min(rr['W0.5']['margin_min_N'] for rr in v_hold_flush),
                            min(rr['W0.8']['margin_min_N'] for rr in v_hold_flush),
                            min(rr['W0.5']['margin_min_N'] for rr in v_hold_flush) - min(rr['W0.8']['margin_min_N'] for rr in v_hold_flush)),
                         'SIM S17v2 (W10 < 6 m/s dead bound d = %s N)' % S['d_dead_W10lt6_N'])),
        ('lit_side', tv('a starved plateau is released at every frame phase up to %.2f s at 0.8 s against %.2f s at 0.5 s (reference none, flush): '
                        'margin over GNC\'s %.1f s starve top %.2f s at 0.8 s against %.2f s at 0.5 s (R2-16). With the reference at the ECU E2 the '
                        '0.5 s window never releases a starved plateau (%s) and the 0.8 s window does up to %.2f s'
                        % (st_none[1], st_none[0], gnc_top, st_none[1] - gnc_top, st_none[0] - gnc_top,
                           'lit abort in every starved040 run' if st_rows[(0.5, True, 'LP_at_ECU_E2')] is None else st_rows[(0.5, True, 'LP_at_ECU_E2')],
                           st_rows[(0.8, True, 'LP_at_ECU_E2')]), 'SIM S17v2 starve_threshold')),
        ('conditions', [
            'the ECU R2 hold with the FC DROGUE report: without it %d / %d of 1000 normal-family dead runs are released (flush on, reference none)'
            % (v_nohold[0]['W0.5']['dead_released'], v_nohold[0]['W0.8']['dead_released']),
            'the mode-3 estimator re-initialised at the Pc-invalid onset (LEAD 227 (6)): without the flush %d / %d (normal) and %d / %d (starved040) '
            'of 1000 dead runs are released at 0.5 / 0.8 s (the lit plateau carried through the 20 ms filter)'
            % (v_noflush[0]['W0.5']['dead_released'], v_noflush[0]['W0.8']['dead_released'], v_noflush[1]['W0.5']['dead_released'],
               v_noflush[1]['W0.8']['dead_released']),
            'the main-chamber photodiode view proven (FLAMEOUT_OPT armed), or the reference re-taken at the ECU E2 or at the light: photodiode-blind '
            'families with the flush and reference none release %d / %d (normal_noopt) and %d / %d (starved040_noopt) of 1000 dead runs at 0.5 / '
            '0.8 s; with either re-taken reference none'
            % (v_noopt[0]['W0.5']['dead_released'], v_noopt[0]['W0.8']['dead_released'], v_noopt[1]['W0.5']['dead_released'],
               v_noopt[1]['W0.8']['dead_released']),
            'FC frame noise inside the 227 (6) budget (noise_budget_227_6)',
            'inside the W10 < 6 m/s envelope only: at the all-winds bound the flush + hold design releases %d of 1000 normal dead runs at 0.8 s '
            '(%d at 0.5 s); 227 (5) scopes the window to W10 < 6' % (aw['W0.8']['dead_released'], aw['W0.5']['dead_released'])]),
        ('fc_pc_branch_finding', tv('with the FC Pc branch (release on a frame with Pc valid and filtered Pc >= 3.0 bar abs) every normal-family '
                                    'run, lit or about to flame out, is released at the E2 frame (release 0 ms after E2 in %d of %d evaluations): '
                                    'Pc_f at E2 is 3.04 bar abs, 0.04 bar above the branch threshold, so R2 never decides those runs, and a '
                                    'flame-out after that release is outside R2 (no drogue held). The dead-side numbers above are taken with the '
                                    'branch OFF for the normal family (mode 3 decides). GNC / FC owner to state the branch margin or move it'
                                    % (br_dead['W0.5']['lit_released'], br_dead['W0.5']['n']),
                                    'SIM S17v2 (fc_pc_branch true groups; sc_v211_r2.inc header)')),
        ('limits', 'SIL closed-loop plant (ASSUMED / COMB SIM inputs) with GNC R2 v2 evaluated offline on the recorded histories; dead bound d '
                   'from GNC r2v2_eval (fo_none) applied to every frame; cold flow = Combustion v2.4a adiabatic bound at the plant lift; '
                   'starved plateau = a shape stand-in; frame phase TO-VERIFY (all 10 run). Not flight-software or hardware evidence')])
    noise = OrderedDict([
        ('question', cite(227, '(6) Mode-3 estimator', 420)),
        ('implemented', 'in the S17 R2 v2 evaluator (sc_v211_r2.inc: flush = the mode-3 filter state set to the reference at the counting start, '
                        'estimate 0); the flight implementation is the FC owner\'s (GNC re-runs R2 with the flush)'),
        ('budget', tv('P(dead release) <= 1e-3 in the bounding run needs an FC frame noise <= %.2f N rms iid (<= %.2f N rms AR(1), rho %.2f) at '
                      'the 0.8 s window and <= %.2f N rms iid (<= %.2f N AR(1)) at 0.5 s (normal family, flush, reference none, margin %+.3f / '
                      '%+.3f N). 5 N rms is NOT admissible: P = %.1f %% (0.5 s) and %.1f %% (0.8 s) iid in the bounding run. With the reference '
                      'taken at the light the 0.8 s budget is %.2f N rms iid (%.2f N AR(1))'
                      % (nf8['iid_sigma_for_Pmax_1e-3_N'], nf8['mc_ar1_sigma_for_P_1e-3_bounding_run_N'], nb[('design_flush', 0.8)]['ar1_rho'],
                         nf5['iid_sigma_for_Pmax_1e-3_N'], nf5['mc_ar1_sigma_for_P_1e-3_bounding_run_N'], nf5['margin_min_N'], nf8['margin_min_N'],
                         100 * nf5['iid_Pmax_at_5N_rms'], 100 * nf8['iid_Pmax_at_5N_rms'], rl8['normal']['iid_sigma_for_Pmax_1e-3_N'],
                         rl8['normal']['mc_ar1_sigma_for_P_1e-3_bounding_run_N']),
                   'SIM + DERIVED (S17v2 noise_budget_dead_W10lt6: exact forward recursion over the frames, iid ASSUMED as RV6-07; AR(1) by '
                   'seeded Monte Carlo)')),
        ('gnc_constant_margin_check', tv('GNC\'s design maxima (%.3f / %.3f N) give margins %.3f / %.3f N and P(5 N rms iid) %.2f %% / %.2f %% at '
                                         '0.5 / 0.8 s: the 6.5-18.4 %% of RV6-07 reproduced; sigma for 1e-3: %.2f / %.2f N iid'
                                         % (gmc[0.5]['gnc_fo_cb_design_max_N'], gmc[0.8]['gnc_fo_cb_design_max_N'], gmc[0.5]['margin_N'],
                                            gmc[0.8]['margin_N'], 100 * gmc[0.5]['iid_P_at_5N'], 100 * gmc[0.8]['iid_P_at_5N'],
                                            gmc[0.5]['iid_sigma_for_P_1e-3_N'], gmc[0.8]['iid_sigma_for_P_1e-3_N']), 'DERIVED (S17v2 gnc_margin_constant_check)')),
        ('photodiode_blind', 'the photodiode-blind families have a negative noise-free margin with reference none (%+.3f / %+.3f N at 0.8 s): no '
                             'noise budget exists for them without a re-taken reference (with the reference at the light: %.2f N rms iid at 0.8 s)'
                             % (df8['normal_noopt']['margin_min_N'], df8['starved040_noopt']['margin_min_N'],
                                rl8['starved040_noopt']['iid_sigma_for_Pmax_1e-3_N'])),
        ('table', nb_tab)])
    lit_cap = OrderedDict([
        ('question', cite(230, '(5) P4c lit side', 300)),
        ('status', 'CARRIED as an S17 open item (OI-FMIN-LIT; GNC R2 v2 re-run and the lead)'),
        ('result', tv('with the lit thrust in the hold capped at F_min %.2f N (the 3 of 72 Combustion corners at 0.21776 mm), the flush and the hold, '
                      'no lit run is released at either window and every reference (lit abort at E2 + W: the relight is lost, the drogue is kept); '
                      'without the flush, reference none: %d of 1000 normal-family lit runs released (the unflushed lit plateau, the same carry-over '
                      'that releases dead runs)'
                      % (33.14, R_(rows_litcap, lbl('normal', True, False, 'none_GNC_sim6'))['W0.8']['lit_released']),
                   'SIM S17v2 (sensitivity lit_cap_33.14N)')),
        ('trade', 'the hold lift sets both sides: a higher lift raises the lit F_min and the dead cold flow (dead-side margin with the flush %+.3f N '
                  'at 0.8 s); a lower threshold costs the dead side one for one. Not an Electronics choice' % nf8['margin_min_N']),
        ('rows', rows_litcap)])
    drs = OrderedDict()
    drs['predicate_owner'] = v3['drogue_release_support']['predicate_owner']
    drs['fc_rule_r2_line175'] = v3['drogue_release_support']['fc_rule_r2_line175']
    drs['fc_rule_r2_status'] = 'HISTORY (line 181 (4) kept 0.5 s; 227 (5) adopted 0.8 s for the W10 < 6 m/s envelope): ' + v3['drogue_release_support']['fc_rule_r2_status']
    drs['fc_rule_r2_v2'] = cite(227, '(5) R2 starve window', 470)
    drs['fc_rule_r2_v2_estimator'] = cite(227, '(6) Mode-3 estimator', 300)
    drs['fc_parameters'] = tv('GNC R2 v2 (FC parameters set by the lead): window W 0.8 s for the W10 < 6 m/s envelope (LEAD 227 (5); 0.5 s kept as '
                              'the comparator); release on 3 consecutive 100 Hz frames with the mode-3 estimate (20 ms low-pass of the accelerometer '
                              'thrust minus the reference) >= %.3f N, counting from the first frame with E2 and Pc invalid; the mode-3 filter '
                              're-initialised at the Pc-invalid onset (227 (6)); else ABORT at t_E2 + W. Reference content: GNC sim6 takes none; '
                              'the SIL sweep also runs the reference at the ECU E2 and at the light (r2v2_sweep). The ECU supplies RUN, t_E2, '
                              'PC_VALID, the DROGUE echo and the ABORT path' % S['threshold_N'],
                              'LEAD CHANGELOG 227 (5) / (6); GNC rev4 (S17v2 gnc_inputs)')
    drs['ecu_publishes'] = v3['drogue_release_support']['ecu_publishes']
    drs['kDrogueRiseHold_s'] = C('kDrogueRiseHold_s')
    drs['tests'] = [v3['drogue_release_support']['tests'], T(r'lost DROGUE 0'), T(r'R2 backstop is per burn'), T(r'lift-commanded R2 hold')]
    drs['tests_note'] = ('the v210-16 line text says "0.5 s adopted, 0.8 s checked" (its v2.10 label): the test checks the ABORT frame at both '
                         'windows; 0.8 s is the adopted window since LEAD 227 (5)')
    drs['sil'] = OrderedDict([('S5_rise_held_runs', s5.get('drogue_rise_held_to_E2_0p10_runs')),
                              ('S14', v3['drogue_release_support']['sil']['S14']),
                              ('S17', 'v2.11: S17 v2 sweep against GNC R2 v2 (r2v2_sweep); the v2.10 stand-in scenario S17_r2hold.json is kept for '
                                      'continuity only')])
    drs['r2v2_sweep'] = OrderedDict([
        ('file', 'results/sil_v2p11/S17v2_r2v2_sweep.json %s (+ S17v2_log.txt, S17v2_r2v2_evals_mode3.csv.gz)' % sha(os.path.join(SIL, 'S17v2_r2v2_sweep.json'))),
        ('decision', cite(216, '(1) R2-01', 560)),
        ('method', 'firmware/sil/sc_v211_r2.inc header: one closed-loop SIL run (ECU firmware + plant, flight A1 relight at 200 / 500 N) per '
                   'family, command, drogue report, lit / dead and Pc-loss onset (1-50 ms after E2); GNC R2 v2 evaluated offline on the recorded '
                   '1 ms history for every frame phase (10), window (0.5 / 0.8 s), flush option, reference option and noise level (causal: '
                   'decisions only at or after the counting start). Families: normal, starved040 (0.40 s starved plateau), and the dead runs '
                   'with the photodiode NOT viewing the main chamber (*_noopt: FLAMEOUT_OPT never arms). FC Pc branch on / off for the normal '
                   'family. ' + S['method']),
        ('gnc_inputs', S['gnc_inputs']),
        ('threshold_N', S['threshold_N']), ('tau_s', S['tau_s']), ('d_dead_W10lt6_N', S['d_dead_W10lt6_N']),
        ('d_dead_allwinds_N', S['d_dead_allwinds_N']), ('gnc_fo_cb_design_max_W10lt6_N', S['gnc_fo_cb_design_max_W10lt6_N']),
        ('references', S['references']), ('groups', len(S['groups'])), ('evaluations', sum(g_['evaluations'] for g_ in S['groups'])),
        ('row_key', 'per window: n evaluations (onsets x phases x commands), dead / lit released, dead / lit aborted by the FC at E2 + W, ECU left '
                    'RUN before the FC decided (optical flame-out FLAMEOUT_OPT), minimum noise-free margin (threshold - statistic; < 0 = a '
                    'release), release time from E2 (min, max)'),
        ('dead_W10lt6', rows_dead), ('dead_allwinds_hold_flush', rows_allw), ('dead_cold_flow_x1p3_hold_flush', rows_cold),
        ('lit', rows_lit), ('lit_minus12N_sensitivity_hold_flush', rows_litm12), ('fc_pc_branch_rows', [br_dead, br_lit]),
        ('starve_threshold_R2_16', OrderedDict([('rows', st_tab), ('same_at_200_and_500_N', True),
                                                ('gnc_starve_top_s', gnc_top),
                                                ('note', 'R2-16 asked for the threshold at both R2 v2 windows (216 (10)): longest starved plateau '
                                                         'still released at all 10 frame phases (0.05 s grid)')])),
        ('plant_facts', OrderedDict([
            ('hold_lift_plant_mm', tv(hold_lift_rng, 'SIM: plant pintle position in the steady hold (command kR2HoldLift_m %.5f mm; the SIL servo '
                                                   'under the feed-pressure load sits %.1f-%.1f %% below it); CF-3 records the encoder lift'
                                      % (cv('kR2HoldLift_m') * 1e3, 100 * (1 - hold_lift_rng[1] / (cv('kR2HoldLift_m') * 1e3)),
                                         100 * (1 - hold_lift_rng[0] / (cv('kR2HoldLift_m') * 1e3))))),
            ('F_lit_in_hold_N', tv(flit_rng, 'SIM (starved040 / normal)')),
            ('F_cold_in_hold_N', tv(fcold_rng, 'SIM (Combustion v2.4a cold-flow bound at the plant lift)')),
            ('backstop_from_E2_ms', tv(bs_ms, 'SIM: every hold run that reaches it (kR2HoldBackstop_s)')),
            ('ecu_left_RUN_before_E2_plus_0p8', 'dead runs with the photodiode view: FLAMEOUT_OPT aborts the onsets it sees (34 of 50 per command) '
                                               'before the FC decides; *_noopt: none')])),
        ('verdict_227_5', verdict),
        ('noise_budget_227_6', noise),
        ('lit_side_230_5', lit_cap)])
    doc['drogue_release_support'] = drs

    # ================================================================================================ R2 command hold (lift-commanded, backstop)
    rh = OrderedDict()
    rh['decision'] = v3['r2_command_hold']['decision']
    rh['decision_194_4'] = v3['r2_command_hold']['decision_194_4']
    rh['decision_216_9'] = cite(216, '(9) R2-22', 330)
    rh['decision_230_4'] = cite(230, '(4) The start-level lift', 200)
    rh['decision_216_2'] = cite(216, '(2) R2-02 ADOPTED in full', 330)
    rh['rule'] = tv('flight (not stand) AND RUN AND drogue attached (Cmd::DROGUE 1) AND the Pc channel invalid this tick AND the backstop not '
                    'reached -> the pintle is commanded to kR2HoldLift_m %.5f mm (lift-commanded, servo rate limit only, no learned trim; the '
                    'Combustion v2.4b start-level lift at the A1 relight state, LEAD 216 (9) / 230 (4)); the open-loop thrust command is '
                    'min(FC command, %s) and an FC command below it keeps the thrust path. The hold ends at the FC release (DROGUE 0), when the '
                    'Pc channel is valid again, or at E2 + %s (ECU backstop, latched for the start, EVENT R2_BACKSTOP 0x24, log tlm_flags b2); '
                    'the command then returns at <= %s. With Pc valid nothing changes (closed loop, A3 active). The ECU takes no drogue decision'
                    % (cv('kR2HoldLift_m') * 1e3, human(C('kR2HoldThrust_N')), human(C('kR2HoldBackstop_s')), human(C('kStartRamp_Nps'))),
                    'DESIGN config.h / engine_ecu.cpp; LEAD CHANGELOG 186 (2), 216 (2)(b), 216 (9), 230 (4)')
    rh['kR2HoldLift_m'] = C('kR2HoldLift_m')
    rh['kR2HoldThrust_N'] = C('kR2HoldThrust_N')
    rh['kR2HoldBackstop_s'] = C('kR2HoldBackstop_s')
    rh['backstop_margin'] = tv('E2 + %s = the longer R2 v2 window %s + 2 FC frames (%s, the TLM_RELIGHT period that carries the DROGUE echo) + '
                               'link latency %s (ASSUMED); the FC ABORT of a dead engine at E2 + 0.8 s arrives first'
                               % (human(C('kR2HoldBackstop_s')), human(C('kR2WindowMax_s')), human(C('kFcFramePeriod_s')), human(C('kFcLinkLatency_s'))),
                               'DESIGN config.h static_assert (LEAD 216 (2)(b))')
    rh['lost_drogue0'] = OrderedDict([
        ('fc_rule', tv('after its DROGUE 0 the FC re-sends DROGUE 0 with a NEW sequence number (protocol.cpp rejects a pure retransmission) on '
                       'every TLM_RELIGHT frame (50 Hz) that still shows d6 b6 = 1, from the second such frame after the first send, at most %d '
                       'times (bound 0.2 s); b6 still 1 after that -> the FC logs DROGUE_ECHO. The FC rule is the FC owner\'s (GNC); stated here '
                       'for the interface' % cv('kFcDrogueResendMax'), 'DESIGN config.h kFcDrogueResendMax; LEAD 216 (2)(a)')),
        ('ecu_backstop', 'the hold ends at E2 + %s whatever the report (above)' % human(C('kR2HoldBackstop_s'))),
        ('bench', 'bench plan v4 B-FC-1 row LOST DROGUE 0 (216 (2)(c)): drop the FC DROGUE 0 frame and its re-sends on the bus; pass = the ECU ends '
                  'the hold at E2 + 0.85 s (+- 1 ms), one EVENT R2_BACKSTOP, command back at <= 2.5 N/ms; and the FC re-send count and '
                  'DROGUE_ECHO log on a single dropped frame'),
        ('tests', [T(r'lost DROGUE 0'), T(r'R2 backstop is per burn')])])
    rh['interface'] = OrderedDict([('fc_to_ecu', v3['r2_command_hold']['interface']['fc_to_ecu']),
                                   ('ecu_to_fc', v3['r2_command_hold']['interface']['ecu_to_fc']),
                                   ('log', 'log v12 tlm_flags b0 = hold active this tick, b1 = drogue attached, b2 = R2 backstop reached (log only; '
                                           'TLM_FAST d1 carries b4-b7); EVENT R2_BACKSTOP 0x24 (arg = hold ticks)')])
    rh['fc_side'] = ('FC owner (GNC): DROGUE 1 at the deployment, DROGUE 0 at the release with the re-send rule above; R2 v2 parameters per '
                     'drogue_release_support.fc_parameters; the mode-3 flush (227 (6)); not implemented by its owner yet')
    rh['flameout_opt_coverage'] = v3['r2_command_hold']['flameout_opt_coverage']
    rh['unit_test'] = tv([T(r'lift-commanded R2 hold'), T(r'LEAD 186 \(2\) R2 command hold')],
                         'SIM (ideal plant); results/sil_v2p11/test_core_log.txt %s' % sha(os.path.join(SIL, 'test_core_log.txt')))
    rh['r2_23'] = OrderedDict([
        ('question', 'R2-23 (LEAD 216 (9)): state, with S6 / S17 evidence, whether HIGH over-range ticks after E2 engage the hold'),
        ('answer', tv('YES, for exactly those ticks: a HIGH over-range reading makes the Pc channel invalid on that tick only (flight, non-sticky, '
                      'LEAD 203 (1)(a); the FC sees TLM 0xFFFF / PC_VALID 0 too), so the hold engages for that tick (1 hold tick in every glitch '
                      'run) and the command returns at the start ramp. Early in the burn (E2 + 20 ms, Pc %.2f bar abs) a 1 ms rail glitch costs '
                      '%.2f-%.2f N s over 280 ms and no abort'
                      % (gl_early[0]['Pc_before_bar_abs'], min(g_['thrust_deficit_Ns_over_280ms'] for g_ in gl_early),
                         max(g_['thrust_deficit_Ns_over_280ms'] for g_ in gl_early)),
                      'SIM S17v2 r2_23_overrange_glitch; test_core "lift-commanded R2 hold" (over-range tick: hold 1 -> 0)')),
        ('later_glitch', tv('at E2 + 350 ms (Pc %.1f-%.1f bar abs) the rail reading is also taken as real pressure by the filtered channel and the '
                            'U330 tap (filtered peak %.1f-%.1f bar abs): as built the comparator trips (HW_OVERPRESSURE) at every command; the '
                            'ride-through build (fixed RC %.3f ms) aborts PC_OVERPRESSURE at 300 / 400 N and HW_OVERPRESSURE at 500 N, none at '
                            '200 N. Fail-safe, the relight is lost; the real glitch rate is MISSING (B-PC-1 / HIL-TR-1)'
                            % (min(g_['Pc_before_bar_abs'] for g_ in gl_late), max(g_['Pc_before_bar_abs'] for g_ in gl_late),
                               min(g_['Pc_filtered_max_30ms_bar_abs'] for g_ in gl_late), max(g_['Pc_filtered_max_30ms_bar_abs'] for g_ in gl_late),
                               cv('kRideCmpTauNom_s') * 1e3), 'SIM S17v2 r2_23_overrange_glitch')),
        ('rows_late', gl_late_tab),
        ('S6', 'S6 / S6R over-pressure cases never engage the hold (no drogue report in those scenarios: the over-range there is an over-pressure '
               'path, see ride_through)')])
    rh['findings'] = [
        tv('dead side: with the hold and the flush no dead vehicle is released at either window (W10 < 6 m/s, photodiode view); without the hold or '
           'without the flush dead vehicles are released (verdict_227_5)', 'SIM S17v2'),
        tv('hold lift in the SIL plant %.4f-%.4f mm against the %.5f mm command (servo under load); cold flow in the hold %.2f-%.2f N; lit thrust '
           'in the hold %.2f-%.2f N' % (hold_lift_rng[0], hold_lift_rng[1], cv('kR2HoldLift_m') * 1e3, fcold_rng[0], fcold_rng[1], flit_rng[0], flit_rng[1]),
           'SIM S17v2 plant_facts'),
        tv('lift basis reconciled: the ECU commands the Combustion v2.4b start-level lift 0.21776 mm, the same value as the kIgnLiftTab_m A1 row '
           '(the S17 v2.10 thrust-commanded 0.2154 mm and the 194 (4) grain_q1d 0.2039 mm are superseded); CF-3 measures at the commanded lift',
           'DESIGN config.h; LEAD 216 (9), 230 (4)'),
        tv('after the release (or the backstop) the command returns at 2.500 N/ms: 200 N reached 54-55 ms later', 'SIM test_core')]
    rh['limits'] = ('SIL plant on ASSUMED / COMB inputs; the R2 v2 rule evaluated offline by Electronics from GNC\'s text; cold flow = the adiabatic '
                    'bound without heat pick-up; nothing here is hardware or flight-software evidence')
    rh['owner_actions'] = [
        'GNC: R2 v2 re-run with the flush and the reference choice (none / E2 / light), the frame-noise budget, the FC Pc-branch margin at E2 and the '
        'lit F_min 33.14 N corners (230 (5)); the counting start',
        'FC owner: DROGUE reports with the re-send rule and DROGUE_ECHO log; the d6 b6 echo check before a RELIGHT; B-FC-1 LOST DROGUE 0 row',
        'Combustion (LEAD 194 (4)): injector-body and feed soak-back temperature at the relight for the start-level cold-flow bound; CF-3 '
        'start-lift point with a load cell at 0.21776 mm']
    doc['r2_command_hold'] = rh

    # ================================================================================================ Pc over-range / FA-1 (C1 chain, v2.11)
    c1ds = pct3['B_candidates_datasheet']['C1']
    c1ck = [c_ for c_ in pct3['C_checks'] if c_['id'] == 'C1'][0]
    econd, u330 = pct3['E_conditioning'], pct3['F_hw_comparator_U330']
    ebud = pct3['E_error_budget']['v']['levels']
    fs_pa = econd['transfer']['v']['FS_Pa_abs']

    def v2p(v_):
        """C1 chain transfer (DESIGN pc_transducer_v3 E): V_SIG = 5 V x (0.10 + 0.80 p_abs / FS) -> p_abs [Pa]"""
        return (v_ / 5.0 - econd['transfer']['v']['zero_frac']) / econd['transfer']['v']['span_frac'] * fs_pa
    p475, p456 = v2p(cv('kPcSensorMax_V')), v2p(cv('kPcAboveFs_V'))
    proof_c1_bar = 1.5 * 2000.0 * 6894.757 / 1e5
    proof_req_bar = 1.1 * 151.04
    if abs(p475 / 1e5 - 146.5) > 0.06 or abs(p456 / 1e5 - 139.96) > 0.06 or proof_c1_bar < proof_req_bar or abs(proof_c1_bar - 206.8) > 0.05:
        raise SystemExit('C1 scaling / proof not as recorded (4.75 V %.2f, 4.56 V %.2f, proof %.2f vs %.2f bar abs)'
                         % (p475 / 1e5, p456 / 1e5, proof_c1_bar, proof_req_bar))
    ch = fa1c['chains']
    c1n = [k for k in ch if k.startswith('c1_')]
    rngc = lambda key, sub=None: [min((ch[k][sub][key] if sub else ch[k][key]) for k in c1n), max((ch[k][sub][key] if sub else ch[k][key]) for k in c1n)]
    if any(ch[k]['overrange_475_in_IGNITION'] or ch[k]['above_fs_456_in_IGNITION'] for k in c1n) or \
            any(fa1c['ride_through_outcome_grid']['per_chain'][k]['aborts_low_band'] for k in c1n):
        raise SystemExit('fa1_chain_v2p11: a C1 chain reaches the over-range / above-FS level or aborts with the ride-through grid')
    face_pk = OrderedDict((k, ch[k]['max']['face_pk_bar']) for k in c1n)
    po = OrderedDict()
    po['request'] = v3['pc_overrange_fa1']['request']
    po['request_v2p11'] = [cite(203, '(1) OI-FA1-PC-OVERRANGE', 420), cite(205, 'DECISION: the flight Pc transducer is RESELECTED by Electronics', 600),
                           cite(249, '(4) RELIGHT AND TRANSDUCER', 900, 10)]
    po['transducer_datasheet'] = OrderedDict([
        ('part', 'Kulite %s (C1; %s)' % (c1ds['part_proposed'], c1ds['family'])),
        ('source', c1ds['source']),
        ('range', tv('%.1f bar abs full scale (2000 psia, absolute)' % (fs_pa / 1e5), 'DATASHEET (range code 2000 psi)')),
        ('proof', tv('1.5 x rated above 500 psi = 3000 psi = %.1f bar abs (rule: %s)' % (proof_c1_bar, c1ds['proof_rule']), 'DATASHEET')),
        ('proof_requirement', tv('>= %.1f bar abs (1.1 x FA1S 151.04 bar abs, CHANGELOG 230 (2)) by LEAD 249 (4), replacing the line-205 '
                                 '112 bar abs (1.1 x 102): C1 %.1f bar abs meets it with %.1f bar' % (proof_req_bar, proof_c1_bar, proof_c1_bar - proof_req_bar),
                                 'LEAD 249 (4) + DATASHEET')),
        ('proof_requirement_note', 'results/pc_transducer_v3.json (161982ca107d83a7) still records the pre-ruling check "proof >= 112.2 bar abs" '
                                   'and its input combustion.json v2.4a 5237d4584bad38c4: the part choice is unchanged by 249 (4) (206.8 >= 166.1), '
                                   'the file is kept as the BOM v2.3 record (its re-run against v2.4b changes only the recorded input hashes)'),
        ('burst', tv('%.1f bar (3 x rated capped at 5000 psi)' % c1ck['checks']['burst_bar']['v'], 'DATASHEET')),
        ('natural_frequency', tv('%d kHz typical without a screen (rise 10-90 %% %.2f us DERIVED); with the B screen MISSING'
                                 % (c1ck['checks']['natural_frequency']['v']['kHz_no_screen_typ'], c1ck['checks']['natural_frequency']['v']['rise_10_90_us_DERIVED']),
                                 'DATASHEET (range mapping by order, TO-VERIFY)')),
        ('accuracy', tv('non-linearity + hysteresis + repeatability %.2f %% FSO max = %.2f bar; thermal zero %.1f %% FS / 100 F typ, thermal '
                        'sensitivity %.1f %% / 100 F typ (max MISSING); compensated %s C (order 20-120 C, TO-QUOTE)'
                        % (c1ds['nonlin_hyst_rep_pctFSO']['max'], c1ck['checks']['accuracy']['v']['nonlin_hyst_rep_max_bar'],
                           c1ds['thermal_zero_pctFS_per_100F_typ'], c1ds['thermal_sens_pct_per_100F_typ'], '-'.join('%g' % x for x in c1ds['compensated_C'])),
                        'DATASHEET')),
        ('operating_temperature', tv('%g..%g C; margin %.1f C over the B1 soak 118.3 C SIM (held for the MISSING diaphragm gas-side transient)'
                                     % (c1ds['operating_C'][0], c1ds['operating_C'][1], econd['margin_statement']['v']['margin_C']), 'DATASHEET + DERIVED')),
        ('vibration_shock', tv('%s; shock MISSING in the sheet' % c1ds['vibration'], 'DATASHEET')),
        ('media', tv('%s; oxygen cleaning and the N2O statement TO-VERIFY with Kulite (F-10); the supplied silicone O-ring is replaced (FKM or a metal '
                     'seal)' % c1ds['wetted'], 'DATASHEET + TO-VERIFY')),
        ('output_above_full_scale', tv(None, 'MISSING: the bridge output above 140 bar is not stated (linear to the proof by construction is ASSUMED, '
                                             'not shown); F-10 inquiry')),
        ('recovery_after_over_range', tv(None, 'MISSING: not stated (F-10 inquiry)')),
        ('envelope', tv('hex 3/8 in (11.00 mm across corners) inside dia 12 mm; height inside 30 mm TO-VERIFY (cable dia MISSING, %s)'
                        % c1ck['checks']['envelope_height30']['basis'][:60], 'DATASHEET + DERIVED')),
        ('price', 'TO-QUOTE delivered to Soenderborg DK-6400 (BOM v2.3 line 251; F-6 RFQ)'),
        ('kept_070BG', 'TE M3234-000005-070BG stays for P_torch (J901) and as the B-PC-1 static reference (BOM 199); its over-range row is F-12 '
                       'on the spare unit')])
    po['ecu_chain'] = OrderedDict([
        ('topology', tv(econd['topology']['v'], 'DESIGN (calc/v2p11/pc_transducer_v3.py E; schematic v2.6 NOT drawn)')),
        ('transfer', tv('V_SIG = 5 V x (0.10 + 0.80 p_abs / %.1f bar) after the select-on-test trims; INA333 G %.2f (RG %.0f ohm E96), '
                        'bandwidth %.0f Hz, anti-alias %.0f Hz; noise %.4f bar rms (EMI on the 50 mV cable not modelled; SIL 3450 Pa rms ASSUMED)'
                        % (fs_pa / 1e5, econd['gain']['v']['G_E96'], econd['gain']['v']['RG_E96_ohm'], econd['bandwidth_Hz']['v'],
                           econd['anti_alias_Hz']['v'], econd['noise']['v']['bar_rms']), 'DESIGN + DERIVED')),
        ('over_range_level', tv('kPcSensorMax_V %s = %.1f bar abs; above-full-scale flag kPcAboveFs_V %s = %.2f bar abs'
                                % (human(C('kPcSensorMax_V')), p475 / 1e5, human(C('kPcAboveFs_V')), p456 / 1e5), 'DESIGN config.h + DERIVED transfer')),
        ('error_budget_bar_rss', tv(OrderedDict((k, ebud[k]['rss_bar']) for k in ebud),
                                    'DERIVED pc_transducer_v3 E (DATASHEET typ thermal terms, max MISSING; A1 trim-to-relight dT 13.8 K)')),
        ('open_wire', tv(econd['open_wire']['v'], 'DERIVED / MISSING (B-PC-1 open-wire row)')),
        ('sil_model', 'sil/sim.h pc_chain 1 (default): seat passage (1-D lumped, ASSUMED), INA333 + anti-alias, per-sample clamp at the rails; the '
                      'v2.10 070BG sense-line chain stays selectable (pc_chain 0)')])
    po['firmware_behaviour'] = OrderedDict([
        ('over_range_high_flight', tv('kPcOverrangeNonSticky %s (LEAD 203 (1)(a)): a reading at or above %s makes PC_VALID 0 on that tick only '
                                      '(Outputs::pc_overrange, log v12 ovr_flags b0); fault::PC_SENSOR is NOT latched; a LOW reading still latches; '
                                      'the stand keeps the latch. In IGNITION a HIGH over-range aborts HARD_START (kept)'
                                      % (human(C('kPcOverrangeNonSticky')), human(C('kPcSensorMax_V'))),
                                      'DESIGN engine_ecu.cpp; test_core "non-sticky over-range", "v2.11 203 (1)(a): over-range HIGH"')),
        ('above_full_scale_flag', tv('a sample at or above %s (above the C1 full scale) sets LIGHT_SPIKE ls_flags b7 and log ovr_flags b1; PC_VALID '
                                     'untouched; above FS the datasheet gives no accuracy (a lower-quality reading)' % human(C('kPcAboveFs_V')),
                                     'DESIGN; test_core "above-FS flag"')),
        ('firmware_30bar_abort', tv('filtered absolute Pc above %s for %s (HARD_START in IGNITION / RUN settle, else PC_OVERPRESSURE); not gated by '
                                    'PC_VALID' % (human(C('kPcOverPressureAbs_Pa')), human(C('kPcOverPressureTime_s'))), 'DESIGN config.h / engine_ecu.cpp')),
        ('hardware_comparator', tv('U330 on the INA333 output (PC_SIG before the ADC): tap %.3f (R330 / R331 %.1fk), tau %.3f ms (C330 220 nF), trip '
                                   '%.2f bar abs nominal, band %.2f-%.2f bar abs (replaces the v2.10 trip on the 070BG chain); U331 latch '
                                   'drops the ARM bus; HW_OVERPRESSURE after OVP_OK low for %s'
                                   % (u330['tap_ratio']['v'], u330['values']['v']['R330'] / 1e3, u330['tau_s']['v'] * 1e3,
                                      u330['trip_nominal_Pa_abs']['v'] / 1e5, u330['trip_range_abs_Pa']['v'][0] / 1e5,
                                      u330['trip_range_abs_Pa']['v'][1] / 1e5, human(C('kHwOvpTime_s'))),
                                   'DESIGN + DERIVED pc_transducer_v3 F; sil/ovp_hw_params.h %s' % pct3['I_header']['sha256_16'])),
        ('ride_through_option', 'see ride_through (build option, default OFF)')])
    po['sim'] = OrderedDict([
        ('method', 'calc/v2p11/fa1_chain_v2p11.cpp + fa1_chain_summary.py: the 896 FA-1 head histories (%s) through the v2.10 070BG chains '
                   '(with / without the 0.3 m line) and four C1 seat-passage variants (CC-1 at c 222 / 400 m/s, 6 / 20 mm3 front volume; CC-2 at '
                   'c 222 m/s), worst ADC phase, E2 emulated' % fa1c['inputs']['fa1_envelope']),
        ('file', 'results/fa1_chain_v2p11.json %s (+ _cases.csv %s, 5376 rows)' % (sha(os.path.join(RES, 'fa1_chain_v2p11.json')),
                                                                                     fa1c['inputs']['cases_csv']['sha256_16'])),
        ('c1_chains', tv(OrderedDict([
            ('chains', c1n), ('overrange_475V_in_IGNITION', 0), ('above_fs_456V_in_IGNITION', 0),
            ('as_built_aborts_of_896', rngc('as_built_aborts_nominal')), ('firmware_30bar_5ms_trips', rngc('fw30_trips_persist_5ms')),
            ('comparator_trips_nominal', rngc('cmp_trips_as_built_nominal')), ('comparator_trips_low_band', rngc('cmp_trips_tau_asb_low_band')),
            ('raw_1kHz_peak_bar_abs', rngc('raw_pk_bar', 'max')), ('filtered_peak_bar_abs', rngc('filt_pk_bar', 'max')),
            ('face_peak_bar_abs', face_pk), ('head_peak_bar_abs', rngc('head_pk_bar', 'max')), ('sig_max_V', rngc('vmax_V', 'max')),
            ('E2_from_light_ms', [min(ch[k]['E2_ms_from_light'][0] for k in c1n), max(ch[k]['E2_ms_from_light'][1] for k in c1n)])]),
            'SIM (open-loop replay of COMB SIM histories; ASSUMED passage model; grid counts are not probabilities)')),
        ('v2p10_chains_reference', tv(OrderedDict((k, OrderedDict([('as_built_aborts_of_896', ch[k]['as_built_aborts_nominal']),
                                                                   ('overrange_475V', ch[k]['overrange_475_in_IGNITION'])]))
                                                  for k in ch if k.startswith('v210')), 'SIM (the superseded 070BG chain, for comparison)'))])
    po['effects'] = OrderedDict([
        ('abort_paths', tv('as built (default build) an FA-1 event of the envelope\'s severity at the A1 relight is aborted in %d-%d of 896 grid '
                           'cases on the C1 chain, by the filtered 30 bar / 5 ms check and the comparator (not by the over-range); with the '
                           'ride-through option 0 (ride_through)' % tuple(rngc('as_built_aborts_nominal')),
                           'SIM fa1_chain_v2p11')),
        ('pc_valid_flag', tv('no FA-1 grid case reaches %s on the C1 chain (SIG max %.3f-%.3f V): PC_VALID is not lost to an FA-1 spike; and a '
                             'reading that did reach it would clear PC_VALID for that tick only (flight, non-sticky)'
                             % (human(C('kPcSensorMax_V')), rngc('vmax_V', 'max')[0], rngc('vmax_V', 'max')[1]), 'SIM + DESIGN')),
        ('logged_fa1_peak', tv('the 1 kHz record under-reads the seat-face peak (raw %.1f-%.1f bar abs logged against face peaks %.1f-%.1f bar abs '
                               'SIM); nothing reaches the above-FS flag (%.1f bar abs); the stand dynamic channel (B-DPC-1) is the peak evidence'
                               % (rngc('raw_pk_bar', 'max')[0], rngc('raw_pk_bar', 'max')[1], min(face_pk.values()), max(face_pk.values()), p456 / 1e5),
                               'SIM + DESIGN')),
        ('recovery', tv(None, 'MISSING: C1 recovery after an over-range (F-10, B-PC-1)'))])
    pdp = pct3['D_passage_period']
    po['period_domain'] = OrderedDict([
        ('lead', v3['pc_overrange_fa1']['period_domain']['lead']),
        ('pc_port', tv('C1 on the seat passage: %s' % pdp['finding'], 'DERIVED from Mechanical pc_line_period_v1 (lossless 1-D acoustics; gas sound '
                                                                     'speed MISSING, bounded 222-400 m/s)')),
        ('C1_period_ms_CC1_6mm3', tv(pdp['C1_at_6mm3'], 'DERIVED')), ('C1_period_ms_CC1_20mm3', tv(pdp['C1_at_20mm3'], 'DERIVED')),
        ('face_peak_statement', tv('stated by Electronics in the v2.11 interim: the line-205 proof basis 1.1 x 102 bar abs (the T <= 1 ms ultimate '
                                   'then in force) sat below the seat-face peaks of the C1 passage model, %.1f / %.1f / %.1f bar abs (CC-1 at c 222 / '
                                   '400 m/s, CC-2; SIM on the ASSUMED 1-D lumped passage model, fa1_chain_v2p11); basis of the peaks: the passage '
                                   'gain on the Combustion v2.4a FA-1 histories (face / head up to %.3f). LEAD 249 (4) restated the proof requirement '
                                   'to >= 166 bar abs (1.1 x FA1S 151.04, 230 (2)); the peaks lie within FA1S and C1 meets it; the face-peak inputs '
                                   'go to REV-COMB-4 (249 (15))'
                                   % (face_pk['c1_cc1_c222_v6'], face_pk['c1_cc1_c400_v6'], face_pk['c1_cc2_c222_v6'],
                                      max(ch[k]['face_over_head_max'] for k in c1n)), 'SIM + LEAD 249 (4), (15)')),
        ('bleed_valves', v3['pc_overrange_fa1']['period_domain']['bleed_valves'])])
    po['v2p11_items'] = [
        OrderedDict([('item', 'FA-1 at the A1 relight: abort (as built) or ride-through'), ('status', 'ride-through BUILT as a build option, default OFF; S6R / S6C evidence; the lead adopts or not (ride_through)')]),
        OrderedDict([('item', 'PC_VALID non-sticky over-range bit (203 (1)(a))'), ('status', 'DONE (flight); stand as built')]),
        OrderedDict([('item', 'above-full-scale flag (203 (1)(a))'), ('status', 'DONE: kPcAboveFs_V %s' % human(C('kPcAboveFs_V')))]),
        OrderedDict([('item', 'transducer port vs proof (194 (1))'), ('status', 'C1 seat-mounted (no sense line); proof 206.8 bar abs >= 166 bar abs (249 (4))')])]
    sdc = copy.deepcopy(v3['pc_overrange_fa1']['stand_dynamic_channel'])
    sdc['fallback_conditioner'] = tv('BOM v2.3 line 265: 4-channel ICP / IEPE conditioner with >= 24 V compliance (PCB 482C series class) if the NI '
                                     '9234 19 V compliance does not hold the 113B22 at the full range; F-8 / F-9 inquiries decide', 'DESIGN (LEAD 203 (7) TO-VERIFY)')
    sdc['placement'] = 'two in use: head flush at the C1 seat and the B-PC-1 reference manifold; one spare (BOM 237 qty 3)'
    po['stand_dynamic_channel'] = sdc
    po['bench'] = ['B-PC-1 on the C1 chain: trims per serial, comparator band, drift, open-wire rows (bench plan v4)',
                   'F-12 over-range row on the spare 070BG (stand reference / P_torch, hydraulic only)',
                   'B-DPC-1 head flush at IGN-1 and the T series (FA-1 history against LC-TB70 and the Combustion spectrum)',
                   'HIL-TR-1: DAC replay of FA-1 / S6R / S6 histories into the C1 input (both builds)',
                   'F-10 Kulite inquiry: above-FS output, recovery, ordering code, cable mass, shock rating']
    po['limits'] = ('COMB SIM histories (lumped construct); ASSUMED passage acoustics and C1 dynamics beyond the datasheet bound; open-loop histories '
                    '(a trip does not change them); nothing here is hardware evidence')
    doc['pc_overrange_fa1'] = po

    # ================================================================================================ ride-through (203 (1)(b) / 216 (3))
    rts = fa1c['ride_through_sizing']
    if abs(rts['kRideOvpTime_s']['v'] - cv('kRideOvpTime_s')) > 1e-9 or abs(rts['kRideWinPostE2_s']['v'] - cv('kRideWinPostE2_s')) > 1e-9 or \
            abs(rts['kRideT45_s']['v'] - cv('kRideT45_s')) > 1e-9 or cv('kRideCmpTauMin_s') < rts['kRideTauW_s']['v']:
        raise SystemExit('ride-through constants differ from fa1_chain_v2p11 sizing')
    s6r_b = OrderedDict()
    for b_ in s6r['builds']:
        rr = [c_ for c_ in s6r_req if c_['build'] == b_['build']]
        ct = [c_ for c_ in s6r_ctrl if c_['build'] == b_['build']]
        s6r_b[b_['build']] = OrderedDict([
            ('ride_through', bool(b_['ride_through'])), ('comparator_tau_ms', b_['comparator_tau_ms']), ('comparator_band_high', bool(b_['trip_shift_band'])),
            ('firmware_overpressure_check', 'off (hardware path alone)' if b_['fw_ovp_off'] else 'on'),
            ('required_runs', len(rr)), ('aborted_inside_LC_TB70', sum(1 for c_ in rr if c_['pass'] and c_['inside_LC_TB70'])),
            ('causes', OrderedDict(sorted(Counter(c_['cause'] for c_ in rr).items()))),
            ('trigger_to_abort_ms_max', max(c_['trigger_to_abort_ms'] for c_ in rr)),
            ('span_above_45_bar_ms_max', max(c_['span_above_45_ms'] for c_ in rr)),
            ('peak_head_bar_abs_max', max(c_['peak_head_bar_abs'] for c_ in rr)),
            ('zones_reached', sorted(set(c_['zone_max'] for c_ in rr))),
            ('aborts_inside_ride_window', sum(1 for c_ in rr if c_['abort_in_ride_window'])),
            ('jfwd_rule_triggered', sum(1 for c_ in rr if c_['jfwd_rule_triggered'])),
            ('controls_fa1_spike_alone', OrderedDict(sorted(Counter(c_['cause'] for c_ in ct).items())))])
    if any(v_['aborted_inside_LC_TB70'] != v_['required_runs'] for v_ in s6r_b.values()):
        raise SystemExit('S6R: a required run not aborted inside LC-TB70')
    s6c_by = OrderedDict()
    for c_ in s6c['cases']:
        s6c_by.setdefault(c_['case'], OrderedDict())[c_['tau']] = c_
    s6c_delta = []
    for k_, v_ in s6c_by.items():
        ab_ = [c_ for t_, c_ in v_.items() if t_.startswith('as_built')][0]
        for t_, c_ in v_.items():
            if not t_.startswith('as_built'):
                s6c_delta.append(OrderedDict([('case', k_), ('variant', t_), ('cause', c_['cause']),
                                              ('comparator_trip_later_ms', round(c_['inj_to_hw_comparator_trip_ms'] - ab_['inj_to_hw_comparator_trip_ms'], 1)),
                                              ('abort_later_ms', round(c_['inj_to_abort_ms'] - ab_['inj_to_abort_ms'], 1)),
                                              ('peak_head_higher_bar', round(c_['peak_head_bar_abs'] - ab_['peak_head_bar_abs'], 2)),
                                              ('zone_max', c_['zone_max']), ('inside_LC_TB70', c_['inside_LC_TB70'])]))
    dl = lambda key: [min(d_[key] for d_ in s6c_delta), max(d_[key] for d_ in s6c_delta)]
    rt = OrderedDict()
    rt['decision'] = [cite(203, '(b) CANDIDATE: ride-through', 420), cite(216, '(3) R2-03, 203 (1)(b) RESTATED', 900)]
    rt['status'] = tv('CANDIDATE: built as a build option (-DECU_RIDE_THROUGH=1; kRideThroughBuild %s in the flight build); adoption on the S6R / '
                      'S6C evidence is the lead\'s; the stand and the pad first start never use it' % human(C('kRideThroughBuild')),
                      'DESIGN config.h; test_core "ride-through is a build option"')
    rt['window'] = tv('flight relights only (rule FLIGHT_RELIGHT), from the ignition-lift command E1 to E2 + %s' % human(C('kRideWinPostE2_s')),
                      'DESIGN; test_core "ride-through never applies" (stand, pad first start)')
    rt['constants'] = [
        OrderedDict([('name', 'kRideOvpTime_s'), ('value', C('kRideOvpTime_s')), ('basis', rts['kRideOvpTime_s']['basis'] + '; LEAD 216 (3): >= 13 ms + margin')]),
        OrderedDict([('name', 'kRideWinPostE2_s'), ('value', C('kRideWinPostE2_s')), ('basis', rts['kRideWinPostE2_s']['basis'] + '; LEAD 216 (3): >= E2 + 8 ms + margin (reviewer 070BG 8.0 ms)')]),
        OrderedDict([('name', 'kRideT45_s'), ('value', C('kRideT45_s')), ('basis', rts['kRideT45_s']['basis'] + ' (bounds a genuine event inside the window)')]),
        OrderedDict([('name', 'kRideOverrangeN'), ('value', C('kRideOverrangeN')), ('basis', 'LEAD 216 (3): N >= 2 consecutive HIGH over-range ticks for the IGNITION rule in the window (C1: 0 of 896 FA-1 cases reach 4.75 V = %.1f bar abs; as built N = 1)' % (p475 / 1e5))]),
        OrderedDict([('name', 'kRideCmpTauNom_s'), ('value', C('kRideCmpTauNom_s')), ('basis', 'DESIGN ride-through BOM variant: C330 = 2 x 270 nF C0G 5 % in parallel (540 nF, BOM v2.3 line 260) on the unchanged 47.5k / 47.5k tap: 23.75k x 540 nF; FIXED (never switched by firmware; the v2.11 draft switching parts are deleted, LEAD 216 (3))')]),
        OrderedDict([('name', 'kRideCmpTauMin_s'), ('value', C('kRideCmpTauMin_s')), ('basis', 'DERIVED 12.825 ms x (1 - 0.0035) x (1 - 0.053): R 0.1 %% + TCR 25 ppm/K x 100 K; C 5 %% + C0G 30 ppm/K x 100 K (DATASHEET-class, part TO-SELECT); >= %s (first zero-trip grid RC at the low band edge, fa1_chain_v2p11)' % human(OrderedDict([('v', rts['kRideTauW_s']['v']), ('unit', 's'), ('tag', ''), ('src', 'fa1c kRideTauW_s')])))]),
        OrderedDict([('name', 'kRideCmpTauMax_s'), ('value', C('kRideCmpTauMax_s')), ('basis', 'DERIVED 12.825 ms x 1.0035 x 1.053: bounds the genuine over-pressure cost (S6R / S6C run at it)')])]
    rt['sizing_grid'] = tv(OrderedDict([('persistence_ms', fa1c['ride_through_outcome_grid']['persistence_ms_used']),
                                        ('comparator_tau_ms', fa1c['ride_through_outcome_grid']['tau_w_ms_used']),
                                        ('t45_ms', fa1c['ride_through_outcome_grid']['t45_ms']),
                                        ('c1_chain_aborts_of_896', OrderedDict((k, fa1c['ride_through_outcome_grid']['per_chain'][k]['aborts_low_band']) for k in c1n))]),
                           'SIM fa1_chain_v2p11 ride_through_outcome_grid (FA-1 spikes ridden through on every C1 chain)')
    rt['S6R_in_window_overpressure'] = OrderedDict([
        ('file', 'results/sil_v2p11/S6R_in_window_overpressure.json %s' % sha(os.path.join(SIL, 'S6R_in_window_overpressure.json'))),
        ('scenario', s6r['scenario']),
        ('result', tv('%d runs (%d cases x %d builds): %d of %d required runs abort with the head pressure-time inside LC-TB70; %d controls (FA-1 '
                      'spike alone) inside; %d runs have their INPUT outside LC-TB70 (below); the ECU is outside LC-TB70 in %d runs'
                      % (s6r['runs'], s6r['runs'] // len(s6r['builds']), len(s6r['builds']), s6r['required_passed'], s6r['required_cases'],
                         len(s6r_ctrl), len(s6r_in_out), s6r['runs_outside_envelope_ecu']), 'SIM')),
        ('per_build', s6r_b),
        ('jfwd_rule', tv('the J-FWD rule (> 60 bar abs, CHANGELOG 248 founder rule) is triggered in %d required runs (the FA-1 envelope + 50 bar '
                         'plateau family: zone 3, peak %.2f bar abs): after such an abort the J-FWD joint counts as used (bench plan v4 F-14)'
                         % (sum(1 for c_ in s6r_req if c_['jfwd_rule_triggered']), max(c_['peak_head_bar_abs'] for c_ in s6r_req if c_['jfwd_rule_triggered'])),
                         'SIM + LEAD 248')),
        ('input_outside_envelope', tv('%d runs (the Combustion v2.4a FA-1 replay max-face case, alone and with a 50 bar plateau, in all %d builds): '
                                      'input head peak %.2f bar abs > Z3 %.3f bar abs; 46 of 896 grid cases peak above it (141 above 63.1). Not '
                                      'Electronics\' to fix: routed to REV-COMB-4 and Mechanical by CHANGELOG 249 (15). No v2.11 claim depends on '
                                      'these runs (the required set excludes them; the ECU abort times in them are recorded)'
                                      % (len(s6r_in_out), len(s6r['builds']), max(c_['input_peak_bar_abs'] for c_ in s6r_in_out), 75.519),
                                      'SIM + LEAD 249 (15)')),
        ('abort_value', abort_value_note)])
    rt['S6C_fixed_rc_whole_burn_cost'] = OrderedDict([
        ('file', 'results/sil_v2p11/S6C_rc_cost.json %s' % sha(os.path.join(SIL, 'S6C_rc_cost.json'))),
        ('scenario', s6c['scenario']),
        ('result', tv('%d cases (7 faults x 3 RC values): with the fixed RC (12.825 / 13.552 ms) the comparator trips %.1f to %.1f ms later than '
                      'as built, the abort %.1f to %.1f ms later, the head peak %.2f to %.2f bar higher; every case inside LC-TB70 (zones 0-1), '
                      'J-FWD rule never triggered' % (len(s6c['cases']), dl('comparator_trip_later_ms')[0], dl('comparator_trip_later_ms')[1],
                                                      dl('abort_later_ms')[0], dl('abort_later_ms')[1], dl('peak_head_higher_bar')[0],
                                                      dl('peak_head_higher_bar')[1]), 'SIM')),
        ('rows', s6c_rows), ('delta_vs_as_built', s6c_delta), ('abort_value', abort_value_note)])
    rt['sil_defect_found_and_fixed'] = tv('S6 "band_high" cases shifted only the v2.10 070BG comparator trip (ovp_trip_Pa_g); on the default C1 chain '
                                          'they ran at the nominal trip. Fixed before the record (both chains shifted); every S6 / S6R / S6C '
                                          'band-high result in this file is from the fixed harness', 'SIL harness (sim.cpp), v2.11 pre-record')
    ideal_ride = [c_ for c_ in s6r['cases'] if c_['family'] == 'step50_ideal' and c_['build'].startswith('ride')]
    t45_ms = cv('kRideT45_s') * 1e3
    if not ideal_ride or any(not c_['aborted'] for c_ in ideal_ride) or min(c_['trigger_to_abort_ms'] for c_ in ideal_ride) <= t45_ms + 1.0:
        raise SystemExit('S6R step50_ideal ride-build cases: not all aborted later than the T45 time (seat-ringing statement)')
    ideal_causes = sorted(set(c_['cause'] for c_ in ideal_ride))
    rt['seat_ringing_finding'] = OrderedDict([
        ('v', 'ideal 25 us pressure steps ring the C1 seat passage in the SIL model (laminar-only damping ASSUMED), so the continuous T45 guard (raw '
              '> 45 bar for %s) does not fire on them; the envelope is still met through the ride-window end and the comparator. The main step '
              'cases use a 1.0 ms rise (Mechanical\'s LC-TB70 pulse convention, 10-90 %% rise >= 0.8 ms an input property). Whether a real seat '
              'passage rings like this is MISSING (B-DPC-1 / HIL-TR-1; OI-SEAT-RINGING)' % human(C('kRideT45_s'))),
        ('record_evidence', tv('the %d ride-build step50_ideal runs all abort %.1f-%.1f ms after the trigger (%s), none at the T45 time (%.0f ms + '
                               '1 tick): T45 did not fire' % (len(ideal_ride), min(c_['trigger_to_abort_ms'] for c_ in ideal_ride),
                                                              max(c_['trigger_to_abort_ms'] for c_ in ideal_ride), ' / '.join(ideal_causes), t45_ms),
                               'SIM results/sil_v2p11/S6R_in_window_overpressure.json (DERIVED from the abort times)')),
        ('raw_reading_swing', tv('the 1 kHz raw reading oscillates about 38-61 bar abs after an ideal step', 'SIM, pre-record diagnostic run '
                                 '(v2p11_notes/PROGRESS.md 2026-10-20T22:56:50Z); the recorded S6R traces keep only the head pressure, so the '
                                 'swing is not in the record'))])
    rt['tests'] = [T(r'203 \(1\)\(b\) ride-through \(flight relight\)'), T(r'ride-through never applies'), T(r'ride-through is a build option'),
                   T(r'over-range N = 2')]
    rt['limits'] = ('SIL plant and C1 passage on ASSUMED / COMB SIM inputs; head pressure from a profile x decay construct after the trigger '
                    '(sim.h gop); LC-TB70 checked on the plant-step head pressure; nothing here is physical approval')
    doc['ride_through'] = rt

    # ================================================================================================ case-TC abort channel (Part A, 249 (1)-(3))
    a1a, a1b = ctc['A1a_false_trip_side'], ctc['A1b_low_reading_tolerance']
    tfb = tf1['T_F1_basis_rate']
    st_hi = ctc['station_history_B1']['B1_rev3_merged']['station_max_C']
    if abs(a1a['worst_case_K'] - 7.78) > 1e-9 or abs(a1a['rss_K'] - 3.55) > 1e-9 or tfb['verdict'] != 'A175' or abs(tfb['after_B_TC_1_calibration']['at_7p03_K_per_s_K'] - 10.28) > 1e-9:
        raise SystemExit('case_tc_channel / tf1_rate values changed since the Part A rulings')
    doc['case_tc_channel'] = OrderedDict([
        ('file', 'results/case_tc_channel_v1.json %s (calc/v2p11/case_tc_channel_v1.py); results/tf1_rate_v1.json %s (calc/v2p11/tf1_rate_v1.py)'
                 % (sha(os.path.join(RES, 'case_tc_channel_v1.json')), sha(os.path.join(RES, 'tf1_rate_v1.json')))),
        ('decision', cite(243, '(3) ABORT VALUE', 520)),
        ('ruling', cite(249, '(1) CASE-TC ABORT CHANNEL', 1150)),
        ('abort', C('kCaseOverTemp_K')), ('persistence', C('kOverTempTime_s')),
        ('armed_window', a1a['armed_window']),
        ('false_trip_side', tv(OrderedDict([('criterion', a1a['criterion']), ('worst_case_K', a1a['worst_case_K']), ('rss_K', a1a['rss_K']),
                                            ('margin_K', a1a['margin_K']), ('worst_nominal_reading_C', round(st_hi + a1a['worst_case_K'], 2)),
                                            ('board_minus40_to_105C_worst_case_K', a1a['board_hot_variant']['worst_case_K']),
                                            ('verdict', a1a['verdict'])]),
                               'DERIVED: DATASHEET MAX31856 19-7534 Rev 0, LITERATURE IEC 60584-1 Class 1 (AS RECALLED, TO-VERIFY), ASSUMED '
                               'layout / EMI terms; ACCEPTED by the lead (249 (1))')),
        ('false_trip_terms', [OrderedDict([('term', t_['term']), ('bound_K', t_['bound_K']), ('source', t_['source'])]) for t_ in a1a['terms']]),
        ('hot_day_sensitivity', a1a['hot_day_sensitivity']),
        ('low_reading_tolerance', tv(OrderedDict([('definition', a1b['definition']), ('formula', a1b['formula_K']),
                                                  ('static_worst_K', a1b['static_worst_K']), ('placement_K', a1b['placement_K']['v']),
                                                  ('surface_mount_steady_K', a1b['surface_mount']['steady_error_K']),
                                                  ('tau_design_target_s', a1b['surface_mount']['tau_target_s']),
                                                  ('tau_calculated_s', a1b['surface_mount']['tau_calc_s']),
                                                  ('detection_delay_s', a1b['detection_delay_s']['v']),
                                                  ('detection_delay_basis', a1b['detection_delay_s']['basis']),
                                                  ('rows', a1b['rows'])]),
                                     'DERIVED (DESIGN install, tau <= 0.25 s target; B-TC-1 verifies); ACCEPTED 249 (1)')),
        ('surface_mount_install', a1b['surface_mount']['installation_DESIGN']),
        ('after_B_TC_1_calibration', tv(OrderedDict([('method', a1b['after_B_TC_1_calibration']['method']),
                                                     ('static_worst_K', a1b['after_B_TC_1_calibration']['static_worst_K']),
                                                     ('formula', tfb['after_B_TC_1_calibration']['formula']),
                                                     ('at_7p03_K_per_s_K', tfb['after_B_TC_1_calibration']['at_7p03_K_per_s_K']),
                                                     ('per_bound', tfb['after_B_TC_1_calibration']['per_bound'])]), 'DERIVED')),
        ('T_F1_basis', tv(OrderedDict([('rule', tfb['rule']), ('r_m1_K_per_s', tfb['r_K_per_s']), ('stated_r_K_per_s', tfb['stated_r_K_per_s']),
                                       ('stated_r_rule', tfb['stated_r_rule']), ('basis_rows', tfb['basis_rows']), ('verdict', tfb['verdict']),
                                       ('lead_ruling', tfb['lead_ruling'])]), 'DERIVED + LEAD 249 (3)')),
        ('T_F1_ruling', cite(249, '(3) T-F1 EXPOSURE BASIS', 1250)),
        ('persistence_review', OrderedDict((k, ctc['persistence'][k]) for k in ('as_built_v2p10', 'conversion_count', 'v2p11', 'alternative_not_proposed'))),
        ('relight_start_limit', OrderedDict([('limit', C('kCaseRelightMax_K')), ('allowance_K', ctc['A2_relight_refusal']['allowance_K']),
                                             ('checks', [ctc['A2_relight_refusal']['check_consistency'], ctc['A2_relight_refusal']['check_no_nominal_refusal']]),
                                             ('decision', cite(249, '(4) RELIGHT AND TRANSDUCER', 330))])),
        ('stand_T0', OrderedDict([('limit', C('kCaseStandArmMax_K')), ('rule', AB4['CASE_WARM_STAND'][0].replace('{kCaseStandArmMax_K}', human(C('kCaseStandArmMax_K')))),
                                  ('decision', cite(249, '(2) STAND T0 RULE', 760)),
                                  ('checklist', 'bench plan v4 F-13 founder pre-fire checklist row (the control)'),
                                  ('test', T(r'items 3/5: stand ARM refused'))])),
        ('bench', 'bench plan v4 B-TC-1: tau <= 0.25 s and |offset| <= 0.6 K on the pad, the static terms at 150 C on a heated coupon against a '
                  'reference (BOM v2.3 line 266); then the T0_max re-derivation (249 (2)) and the calibrated tol_lo for T-F1'),
        ('limits', 'SIM thermal histories (Mechanical, 20 C start); DATASHEET / LITERATURE terms as tagged; ASSUMED install and layout terms; '
                   'nothing here is a measured channel')])

    # ================================================================================================ limits in force (value + basis each)
    hwb = (cv('kHbleedHwBothNom_s') * (1 - cv('kHbleedHwBothErr')), cv('kHbleedHwBothNom_s') * (1 + cv('kHbleedHwBothErr')))
    L_ = lambda name, value, basis, decision=None, **kw: OrderedDict([('limit', name), ('value', value), ('basis', basis)] +
                                                                    ([('decision', decision)] if decision else []) + list(kw.items()))
    doc['limits_v2p11'] = [
        L_('case-TC abort A (TC1 / TC2)', C('kCaseOverTemp_K'), 'A = 150 C (LEAD 243 (3)); false-trip side 7.78 K worst case / 3.55 K RSS inside '
           '+12.3 K at the 137.74 C B1 station (case_tc_channel); persistence %s (2-3 MAX31856 conversions)' % human(C('kOverTempTime_s')),
           cite(249, '(1) CASE-TC ABORT CHANNEL', 300), persistence=C('kOverTempTime_s')),
        L_('case-TC start / relight limit and ARM limit (TC1 / TC2)', C('kCaseRelightMax_K'), 'A1 purge-to-end-of-relight rise 11.9 K + 1 s longer '
           'relight 3.0 K + 1 K relative channel = 15.9 K below A (130 C + 15.9 K = 145.9 C <= 150 C); A1 nominal start reading <= 99.5 C',
           cite(249, '(4) RELIGHT AND TRANSDUCER', 330)),
        L_('nozzle-holder TC3 abort and ARM limit', C('kNozzleHolderOverTemp_K'), '250 C ASSUMED (unchanged); the ARM refusal on it is accepted',
           cite(249, '(4) RELIGHT AND TRANSDUCER', 330)),
        L_('stand T0 ARM limit (stand mode, TC1 / TC2)', C('kCaseStandArmMax_K'), '24 C: the 12.26 K false-trip margin is a 20 C-start margin '
           '(dT_station / dT0 about 0.96); a backstop, the founder checklist row F-13 is the control; re-derived after B-TC-1 as T0_max = 20 + '
           '(12.26 - e_hi,cal) / 0.96 C', cite(249, '(2) STAND T0 RULE', 400)),
        L_('purge both-open command cap', C('kHbleedCap_s'), 'LEAD 203 (3) <= 2.55 s; 230 (3): the scheduled command span %.2f s does not fit a '
           '2.39 s cap, so 2.55 s is kept; physical flow at the cap 2.60 s = 76.05 g on the one basis 29.25 g/s, 80.76 g at the warm end 31.06 g/s'
           % (cv('kPurgeFlow_s') + cv('kHbleedOpenTime_s') - cv('kHbleedCloseTime_s')), cite(230, '(3) Purge (OI-42; line 216 (5))', 330)),
        L_('hardware both-commanded-open timer (U576-U579, DESIGN, not drawn)', C('kHbleedHwBothNom_s'),
           'LTC6993-2 RSET 63.4k, DIVCODE 8 (AS-RECALLED, TO-VERIFY): %.3f-%.3f s with the 3.1 %% tolerance; drops V1 only; the firmware cap acts '
           'first (minimum %.3f s > cap + 1 tick)' % (hwb[0], hwb[1], hwb[0]), cite(216, '(5) R2-05, 203 (3) RESTATED', 330), tolerance=C('kHbleedHwBothErr')),
        L_('vented-mass limit and flow basis', C('kPurgeVentLimit_kg'), 'LEAD 216 (5): the limit is the vented mass; one flow basis %s (LEAD 230 '
           '(3)); measured-time form after CF-4 / B-BLEED-1: overlap <= 76 g / mdot_meas - (t_close - t_open)_meas' % human(C('kPurgeMdotBasis_kgps')),
           cite(216, '(5) R2-05, 203 (3) RESTATED', 330), flow_basis=C('kPurgeMdotBasis_kgps')),
        L_('ride-through persistence / window / T45 / over-range N / fixed RC (CANDIDATE, default OFF)',
           OrderedDict([('kRideOvpTime_s', C('kRideOvpTime_s')), ('kRideWinPostE2_s', C('kRideWinPostE2_s')), ('kRideT45_s', C('kRideT45_s')),
                        ('kRideOverrangeN', C('kRideOverrangeN')), ('kRideCmpTauNom_s', C('kRideCmpTauNom_s')), ('kRideCmpTauMin_s', C('kRideCmpTauMin_s')),
                        ('kRideCmpTauMax_s', C('kRideCmpTauMax_s'))]), 'see ride_through.constants (each with its basis)',
           cite(216, '(3) R2-03, 203 (1)(b) RESTATED', 330)),
        L_('Pc transducer proof', tv('C1 %.1f bar abs' % proof_c1_bar, 'DATASHEET (1.5 x 2000 psi)'), 'requirement >= %.1f bar abs (1.1 x FA1S '
           '151.04, 230 (2)), replacing 112 bar abs' % proof_req_bar, cite(249, '(4) RELIGHT AND TRANSDUCER', 600, 10)),
        L_('Pc over-range / above-FS levels (C1)', OrderedDict([('kPcSensorMax_V', C('kPcSensorMax_V')), ('kPcAboveFs_V', C('kPcAboveFs_V'))]),
           '%.1f / %.2f bar abs on the C1 transfer (pc_transducer_v3 E)' % (p475 / 1e5, p456 / 1e5), cite(203, '(1) OI-FA1-PC-OVERRANGE', 300)),
        L_('firmware Pc over-pressure abort', OrderedDict([('kPcOverPressureAbs_Pa', C('kPcOverPressureAbs_Pa')), ('kPcOverPressureTime_s', C('kPcOverPressureTime_s'))]),
           'filtered absolute Pc (RE-20); hardware U330 on C1 %.2f bar abs (%.2f-%.2f)' % (u330['trip_nominal_Pa_abs']['v'] / 1e5,
                                                                                         u330['trip_range_abs_Pa']['v'][0] / 1e5, u330['trip_range_abs_Pa']['v'][1] / 1e5)),
        L_('R2 window / ECU backstop / hold lift / FC re-send bound', OrderedDict([('kR2WindowMax_s', C('kR2WindowMax_s')), ('kR2HoldBackstop_s', C('kR2HoldBackstop_s')),
                                                                                   ('kR2HoldLift_m', C('kR2HoldLift_m')), ('kFcDrogueResendMax', C('kFcDrogueResendMax'))]),
           '0.8 s for W10 < 6 m/s (227 (5), confirmed with conditions by S17 v2.11); backstop = window + 2 FC frames + link latency (216 (2)(b)); '
           'Combustion v2.4b start-level lift (230 (4)); 10 re-sends = 0.2 s (216 (2)(a))', cite(227, '(5) R2 starve window', 200)),
        L_('cold rule', OrderedDict([('kTankIgnMin_K', C('kTankIgnMin_K')), ('kTankColdArmMargin_K', C('kTankColdArmMargin_K'))]),
           'ARM margin = 1.5 x the PREPRESS Tsat drop %s + repeatability %s, rounded up (SIL S10v211 drop max %.4f K)'
           % (human(C('kTankColdPrepressDrop_K')), human(C('kTankColdRepeat_K')), s10c['prepress_drop_max_K']), cite(216, '(7) R2-11 OI-GUARD-BAND', 300)),
        L_('A7 high-side blank', C('kA7StartHiBlank_s'), 'E2 .. E2 + 0.45 s on the stand and in flight (four conditions, start_monitors.A7_flight_blank)',
           cite(216, '(8) RE-12', 260)),
        L_('light-rule baseline check', C('kIgnBaseCheck_Pa'), 'residual + 0.1 bar; per location (pad / stand refuse, A1 keeps / zeroes P0)',
           cite(216, '(4) R2-04, 203 (5) RESTATED per location', 300))]

    # ================================================================================================ carried v3 sections (config leaves re-read from v2.11)
    cfg_changes = []
    carry = lambda key: refresh_cfg(copy.deepcopy(v3[key]), C, cfg_changes, key)
    ot = carry('over_thrust')
    if not ot['rg16_note'].endswith('not made in v2.10'):
        raise SystemExit('over_thrust.rg16_note text changed in v3?')
    ot['rg16_note'] = ot['rg16_note'][:-len('not made in v2.10')] + 'not made in v2.11 (unchanged since v2.10)'
    doc['over_thrust'] = ot
    e3 = carry('eng03_pintle_rate')
    e3['lift_clamp_RE04'] = tv('while the reference travels (or the pintle has not arrived), the lift command is clamped to the map lift at the '
                               'active setpoint + 1 bar; integrator held during pintle travel. SIL v2.11: S5 plant Pc max %.2f bar abs, %d '
                               'PC_OVERPRESSURE in %d; probe F worst %.2f bar abs, %d PC_OVERPRESSURE'
                               % (s5['pc_max_abs_max_Pa'] / 1e5, s5['ovp_aborts'], s5['runs'], pf['worst_plant_Pc_bar_abs'], pf['pc_overpressure_aborts']),
                               'DESIGN, SIL-tuned (results/sil_v2p11 S5_mc.json, probeF)')
    doc['eng03_pintle_rate'] = e3
    doc['pintle_rail'] = carry('pintle_rail')

    ecu = carry('ecu')
    ecu['schematic']['v2p11_board_items_not_drawn'] = tv(
        'schematic v2.6 NOT drawn: the v2.11 board items exist as DESIGN in config.h / pc_transducer_v3 / BOM v2.3 only: three C1 bridge '
        'channels (INA333 + RG + REF buffer OPA2333 + RFI filter + open-wire bias, lines 252-257), U330 values for the C1 chain (R332 174k / R333 '
        '29.4k, tap 47.5k / 47.5k), U570 R574 806k (line 258), the ride-through C330B footprint (line 260), the both-commanded-open timer '
        'U576-U579 (lines 261-264), the C1 harness breaks (line 259). KiCad v2.5 still shows the 070BG Pc chain', 'DESIGN (not drawn); OI-SCHEMATIC-V2P6')
    pw = ecu['purge_window']
    pw['cap_relation'] = ('the window bounds the scheduled POWERED span (fill step + flow + vent), not the both-open overlap: the overlap is bounded by '
                          'the firmware cap %s (LEAD 203 (3), kept by 230 (3)) and, independent of the firmware, by the hardware both-commanded-open '
                          'timer U576-U579 (DESIGN, %s nominal; head_end_bleed_provision.hardware_both_open_timer); a cap-length one-shot on PURGE_EN '
                          'would cut the scheduled flow' % (human(C('kHbleedCap_s')), human(C('kHbleedHwBothNom_s'))))
    pw['ecu_visibility'] = ('the ECU cannot read PURGE_WIN (no free pin); a stuck-high window chain is latent -> CHK-PW and a proposed pre-flight '
                            'check with PURGE_EN low (not in firmware v2.11; OI-WINDOW-LATENT); the both-open timer is not readable either (CHK-BT)')
    ecu['adc2']['P_TORCH'] = ('P_torch stays on the TE 070BG (J901): divider 12.7k / 4.02k and filter as the v2.10 Pc chain; its scaling is in '
                              'calc/pc_transducer_v2.py (the v2.10 070BG chain, kept for P_torch; its label "J610" for P_torch is wrong: the '
                              'connector is J901)')
    ecu['pc_conditioning_c1'] = tv('per channel (Pc J601, P_feed J602, P_mid J511): bridge on +5V_SNS (ratiometric), RFI filter, INA333 G %.2f, REF '
                                   'from a buffered select-on-test divider, open-wire bias; the INA output is the existing PC_SIG / PFEED_SIG / '
                                   'P_MID_SIG net (divider, anti-alias RC, ADS131M04, U330 / U570 unchanged in topology)'
                                   % econd['gain']['v']['G_E96'], 'DESIGN pc_transducer_v3 E (not drawn)')
    doc['ecu'] = ecu
    act = carry('actuators')
    act['bleed_valves']['hardware_both_open_timer'] = ('v2.11 DESIGN (not drawn): V1\'s gate drive = U574 output AND NOT(U578 Q): V1 drops when both '
                                                      'drives have been high for T_hw (%s nominal) and stays off until a command drops; V2 untouched; '
                                                      'no MCU pin (head_end_bleed_provision.hardware_both_open_timer)' % human(C('kHbleedHwBothNom_s')))
    doc['actuators'] = act
    doc['igniter'] = carry('igniter')

    sen = carry('sensors')
    ptr = sen['pressure_transducers']
    ptr['selection'] = tv(OrderedDict([('PC', 'Kulite XTL-190SM-2000A (C1, seat-mounted on the head, J601)'), ('P_FEED', 'Kulite XTL-190SM-2000A (C1, J602)'),
                                       ('P_MID', 'Kulite XTL-190SM-2000A (C1, J511)'), ('P_TORCH', 'TE M3234-000005-070BG (J901)'),
                                       ('P_TANK', 'TE M3234-000005-170BG (J603)'), ('stand_static_reference', 'TE M3234-000005-070BG (B-PC-1, BOM 199)')]),
                          'DESIGN pc_transducer_v3 (LEAD 205, 206 (3)); BOM v2.3 lines 199, 200, 251')
    ptr['connectors'] = 'Pc J601 (C1 integral cable to an in-line break), P_feed J602 (FS-01 block), P_tank J603, P_torch J901, P_mid J511'
    ptr['conditioning'] = 'C1 bridge channels: pc_overrange_fa1.ecu_chain; 070BG / 170BG: 0.5-4.5 V ratiometric on +5V_SNS as before'
    ptr['hw_ovp'] = tv('U330 on the C1 chain: trip %.2f bar abs nominal, band %.2f-%.2f bar abs; firmware abort %s abs filtered %s'
                       % (u330['trip_nominal_Pa_abs']['v'] / 1e5, u330['trip_range_abs_Pa']['v'][0] / 1e5, u330['trip_range_abs_Pa']['v'][1] / 1e5,
                          human(C('kPcOverPressureAbs_Pa')), human(C('kPcOverPressureTime_s'))), 'DERIVED pc_transducer_v3 F')
    ptr['fault_window']['max_meaning'] = ('%s = %.1f bar abs on the C1 chain (Pc, P_feed, P_mid; LEAD 205); 74.4 bar g on the 070BG (P_torch)'
                                          % (human(C('kPcSensorMax_V')), p475 / 1e5))
    ptr['pmid_comparator'] = 'U570 on the C1 P_mid chain: head_end_bleed_provision.pmid_comparator'
    ptr['mass'] = tv('C1 %.1f g per channel (body %.1f g DATASHEET + %.1f g cable at 10 g/m ASSUMED); mass_statement'
                     % (pct3['H_mass']['v']['per_channel_g'], pct3['H_mass']['v']['body_g'], pct3['H_mass']['v']['cable_g']), pct3['H_mass']['tag'])
    tcs = sen['thermocouples']
    tcs['case_abort_rule'] = 'in-burn abort on TC1 / TC2 above the case abort for the persistence (abort_matrix OVER_TEMP); channel budget: case_tc_channel'
    tcs['persistence'] = C('kOverTempTime_s')
    tcs['start_and_arm_limit'] = C('kCaseRelightMax_K')
    tcs['stand_arm_max'] = C('kCaseStandArmMax_K')
    tcs['nozzle_holder_limit'] = C('kNozzleHolderOverTemp_K')
    tcs['install'] = a1b['surface_mount']['installation_DESIGN']
    sen['thermocouples'] = tcs
    sen['stand_dynamic_pc'] = tv('B-DPC-1: PCB 113B22 (5 kpsi = 344.75 bar at +/-5 V; maximum pressure 15 kpsi = 1034 bar) + NI 9234 at 51.2 kS/s (AC '
                                 'coupled, -3 dB 0.5 Hz), flat to >= 10 kHz incl. the mount; head flush at the C1 seat (stand only, IGN-1 and the T '
                                 'series); fallback IEPE conditioner BOM v2.3 line 265; see pc_overrange_fa1.stand_dynamic_channel',
                                 'LEAD CHANGELOG 172 (5), 194 (7), 203 (7); DATASHEET pcb.com 113B22, NI 377849B-01')
    doc['sensors'] = sen

    il = carry('interlocks')
    il['tank_cold'] = OrderedDict([
        ('limit', C('kTankIgnMin_K')), ('arm_margin', C('kTankColdArmMargin_K')), ('prepress_drop', C('kTankColdPrepressDrop_K')),
        ('repeatability', C('kTankColdRepeat_K')),
        ('rule', tv('ARM refused (TANK_COLD) when the coldest tank estimate (lower of the wall DS18B20 readings and Tsat(P_tank)) is below the limit '
                    '+ %s; IGNITE in PREPRESS refused below the limit (pad first start, stand) with the SAFE EXIT: back to ARMED on the refusal '
                    'tick, MV latch dropped, pintle seated, CLOSED switch expected within %s, never a wait with the MV open; flight relight: '
                    'flagged only (RE-17)' % (human(C('kTankColdArmMargin_K')), human(C('kMvCloseConfirm_s'))),
                    'DESIGN config.h / engine_ecu.cpp (LEAD 216 (7))')),
        ('margin_basis', tv('1.5 x the PREPRESS Tsat drop %s + repeatability %s = %.3f K, rounded up to %s; SIL S10v211: drop max %.4f K, estimate - plant '
                            '%s K, %d cases, %d fail' % (human(C('kTankColdPrepressDrop_K')), human(C('kTankColdRepeat_K')),
                                                          1.5 * cv('kTankColdPrepressDrop_K') + cv('kTankColdRepeat_K'), human(C('kTankColdArmMargin_K')),
                                                          s10c['prepress_drop_max_K'], s10c['estimate_minus_plant_K_range'], len(s10c['cases']), s10c['fail']),
                            'DERIVED + SIM (results/sil_v2p11/S10v211_cold_rule.json)')),
        ('s5_effect', 'S5 pad MC v2.11: TANK_COLD in %d runs (the 0.42 K margin moves the near-limit runs from an IGNITE refusal to an ARM '
                      'refusal); PREPRESS safe exits %d' % (s5_causes_named.get('TANK_COLD', 0), s5['prepress_safe_exit_runs'])),
        ('decision', cite(216, '(7) R2-11 OI-GUARD-BAND', 420)),
        ('tests', [T(r'cold ARM margin'), T(r'PREPRESS safe exit')])])
    il['wind_launch_commit'] = tv('W10 < 6 m/s AND sigma_u(3 m) <= 1.0 m/s over the 10 min before ARM (GSE anemometer, BOM v2.3 line 250; founder '
                                  'items F-5 / F-11)', 'LEAD CHANGELOG 181 (6): HARD rule for A1 (was provisional, line 161)')
    il['wind_launch_commit_decision'] = cite(181, 'becomes a HARD rule for A1', 260)
    il['case_tc_at_arm'] = tv('ARM refused OVER_TEMP when TC1 or TC2 reads above %s or TC3 above %s, and unless both case TCs are valid; stand mode: '
                              'refused CASE_WARM_STAND above %s' % (human(C('kCaseRelightMax_K')), human(C('kNozzleHolderOverTemp_K')),
                                                                   human(C('kCaseStandArmMax_K'))),
                              'DESIGN (LEAD rulings 249 (2), (4)); test_core "items 3/5: stand ARM refused"')
    doc['interlocks'] = il
    doc['safing'] = carry('safing')
    pb = carry('power_budget')
    pb['v2p11_sense_rail'] = tv('+5V_SNS gains the three C1 bridges (<= 5 mA each at >= 1 kOhm, DATASHEET Kulite; 15 mA) plus 3 x INA333 and 2 x '
                                'OPA2333 (< 0.5 mA in all) against the LT1761-5 100 mA rating; the +5V_SNS re-sum in ecu_design.py is NOT redone '
                                '(schematic v2.6 not drawn)', 'DATASHEET + DERIVED; OI-POWER')
    doc['power_budget'] = pb
    doc['loop_rates_and_latency'] = carry('loop_rates_and_latency')
    doc['link_loss'] = carry('link_loss')
    fs = carry('fail_safe_states')
    fs['Pc sensor fault'] = ('RUN: open-loop feed-forward map on P_feed + fault flag; IGNITION: abort; flight HIGH over-range: PC_VALID 0 on that tick '
                             'only (non-sticky, LEAD 203 (1)(a)), LOW still latches')
    fs['Pc over-pressure'] = ('hardware comparator U330 on the C1 chain (trip %.2f bar abs nominal, band %.2f-%.2f) latches and removes the ARM bus '
                              'independent of firmware; firmware abort %s abs filtered for %s'
                              % (u330['trip_nominal_Pa_abs']['v'] / 1e5, u330['trip_range_abs_Pa']['v'][0] / 1e5, u330['trip_range_abs_Pa']['v'][1] / 1e5,
                                 human(C('kPcOverPressureAbs_Pa')), human(C('kPcOverPressureTime_s'))))
    fs['purge window'] = ('FC PURGE_EN low or the one-shot expired: both bleed drives forced off in hardware; both drives high for longer than the '
                          'both-commanded-open timer (%.3f-%.3f s, DESIGN, not drawn): V1 forced off' % hwb)
    fs['case TC'] = 'both case TCs lost: stand treated hot (abort), flight burn continues and the relight is refused CASE_HOT (RE-08)'
    doc['fail_safe_states'] = fs

    # ---- FMEA rows A1 (v2.11 evidence)
    fm = copy.deepcopy(v3['fmea_rows_a1'])
    fm[0]['mitigation'] = ('none for over-thrust on A1: recorded by the lead (RV3-12). R2 and the FC ABORT at t_E2 + W (W = 0.8 s, LEAD 227 (5)) '
                           'cover the no-thrust side only (drogue held)')
    fm[0]['tag'] = 'DESIGN / LEAD; SIL v210-15, v210-16, S14 (v2.11 record)'
    fm[1] = OrderedDict([
        ('id', 'FMEA-A1-FLAMEOUT-PCLOSS-DROGUE'),
        ('mode', 'undetected flame-out right after E2 with the Pc channel invalid, drogue attached (FLAMEOUT_OPT not yet armed, A3 suspended)'),
        ('effect', 'cold N2O flow gives apparent thrust that R2 can read as a light; with the lit plateau carried through the R2 v2 filter a dead '
                   'vehicle can be released'),
        ('detection', 'none in the ECU (Pc invalid); FC R2 v2 on the accelerometer thrust; FLAMEOUT_OPT once armed (photodiode main-chamber view)'),
        ('mitigation', 'lift-commanded R2 hold at %.5f mm (cold flow in the hold %.2f-%.2f N SIM) + the mode-3 flush at the Pc-invalid onset (LEAD '
                       '227 (6)) + the photodiode view or a re-taken reference: 0 of %d dead evaluations released at 0.5 / 0.8 s (W10 < 6 m/s); '
                       'R2 not met -> FC ABORT at t_E2 + 0.8 s (drogue descent), ECU backstop E2 + %s'
                       % (cv('kR2HoldLift_m') * 1e3, fcold_rng[0], fcold_rng[1], sum(rr['W0.8']['n'] for rr in v_hold_flush), human(C('kR2HoldBackstop_s')))),
        ('not_covered', 'all-winds conditions (%d of 1000 normal dead runs released at 0.8 s; the A1 wind rule is HARD), photodiode-blind families '
                        'with reference none (%d / %d of 1000 at 0.8 s), FC frame noise above the 227 (6) budget, chamber / injector heat '
                        'pick-up (TO-VERIFY)' % (aw['W0.8']['dead_released'], v_noopt[0]['W0.8']['dead_released'], v_noopt[1]['W0.8']['dead_released'])),
        ('source', cite(227, '(5) R2 starve window', 260)),
        ('tag', 'DESIGN / LEAD; SIM S17v2 (drogue_release_support.r2v2_sweep)')])
    fm[2] = OrderedDict([
        ('id', 'FMEA-A1-LIT-PCLOSS-HOLD'),
        ('mode', 'lit relight with the Pc channel lost after E2 while the drogue is attached'),
        ('effect', 'thrust held by the lift-commanded hold until R2 releases (SIL lit thrust in the hold %.1f-%.1f N); a starved plateau is released up '
                   'to %.2f s at the 0.8 s window (reference none); at the lit F_min 33.14 N corners no lit run is released (relight lost, drogue '
                   'kept, 230 (5) open item)' % (flit_rng[0], flit_rng[1], st_none[1])),
        ('detection', 'TLM_FAST d2-d3 = 0xFFFF, PC_VALID clear; log tlm_flags b0 (hold active), b2 (backstop)'),
        ('mitigation', 'after the release (or the backstop at E2 + %s) the command returns at <= %s; impulse lost during the hold is GNC\'s trade'
                       % (human(C('kR2HoldBackstop_s')), human(C('kStartRamp_Nps')))),
        ('source', 'LEAD CHANGELOG 186 (2), 216 (9), 230 (4), (5); S17v2'),
        ('tag', 'SIM (S17v2); plateau stand-in')])
    fm.append(OrderedDict([
        ('id', 'FMEA-A1-LOST-DROGUE0'),
        ('mode', 'the FC DROGUE 0 (release) report is lost on the bus'),
        ('effect', 'v2.10: the hold stayed on for the rest of the burn (R2-02); v2.11: the FC re-sends (at most %d, 0.2 s) and the ECU ends the hold '
                   'at E2 + %s whatever the report' % (cv('kFcDrogueResendMax'), human(C('kR2HoldBackstop_s')))),
        ('detection', 'TLM_RELIGHT d6 b6 still 1 after the release (FC: DROGUE_ECHO log); EVENT R2_BACKSTOP 0x24'),
        ('mitigation', 'FC re-send rule + ECU backstop (LEAD 216 (2)); B-FC-1 LOST DROGUE 0 row'),
        ('source', cite(216, '(2) R2-02 ADOPTED in full', 300)),
        ('tag', 'DESIGN; SIM test_core "lost DROGUE 0", "R2 backstop is per burn"')]))
    doc['fmea_rows_a1'] = fm

    # ---- pad go / no-go A1
    ap = comb['igniter']['sequence']['v']['arm_preconditions']
    if not any('V1 and V2 closed' in x_ for x_ in ap):
        raise SystemExit('combustion.json v2.4b igniter.sequence.v.arm_preconditions no longer lists the bleed valves closed')
    pg = copy.deepcopy(v3['pad_go_no_go_a1'])
    pg['rule'] = ('every item GO before the A1 launch commit; one NO-GO stops the count. The ECU items are SIL evidence (v2.11) until B-ECU-1, '
                  'B-BLEED-1, B-TC-1 and B-FC-1 pass on hardware')
    for it in pg['items']:
        it['source'] = it['source'].replace('ECU v2.10', 'ECU v2.11').replace('combustion.json v2.4a igniter.sequence.arm_preconditions',
                                                                              'combustion.json v2.4b igniter.sequence.v.arm_preconditions')
        if it['item'] == 'purge window':
            it['go'] = ('CHK-PW and CHK-BT passed on this board; PURGE_EN low at the pad (a stuck-high window chain is latent to the ECU)')
            it['source'] = 'LEAD CHANGELOG 166 (3), 216 (5); bench plan v4 CHK-PW, CHK-BT'
    pg['items'].append(OrderedDict([('item', 'case TCs'), ('go', 'TC1 and TC2 valid and at or below %s, TC3 at or below %s (else ARM is refused '
                                                                   'OVER_TEMP)' % (human(C('kCaseRelightMax_K')), human(C('kNozzleHolderOverTemp_K')))),
                                    ('source', 'LEAD 249 (4); ECU v2.11 ARM check; test_core "v2.11 case A - 3 K"')]))
    pg['bench_plan'] = '06-electronics/docs/bench_plan_v4.md, A1 pad go/no-go list'
    doc['pad_go_no_go_a1'] = pg
    hg = copy.deepcopy(v3['harness_across_gimbal'])
    if not hg['bundle'].startswith('Pc (3 + shield)'):
        raise SystemExit('harness_across_gimbal.bundle text changed in v3?')
    hg['bundle'] = ('Pc C1 bridge (4 + shield: the Kulite integral 0.9 m cable to an in-line break, BOM v2.3 line 259)' + hg['bundle'][len('Pc (3 + shield)'):])
    doc['harness_across_gimbal'] = hg
    gse = copy.deepcopy(v3['gse_interface'])
    gse['anemometer'] = 'GSE anemometer at 3 m (launch commit wind rule HARD for A1, BOM v2.3 line 250; founder items F-5 / F-11)'
    doc['gse_interface'] = gse

    # ================================================================================================ head-end bleed provision (v2.11)
    hb3 = v3['head_end_bleed_provision']
    t_o, t_c, dt_ = cv('kHbleedOpenTime_s'), cv('kHbleedCloseTime_s'), cv('kDt_s')
    cfg_txt = rd(os.path.join(CORE, 'config.h'))
    mcd_m = re.search(r'Cd 0\.80 \((\d+\.\d+) g/s, ASSUMED\)', cfg_txt)
    if not mcd_m:
        raise SystemExit('config.h: the "Cd 0.80 (.. g/s, ASSUMED)" purge-flow statement not found')
    rg = lambda x, n=2: round(x + 1e-9, n)
    mdots = OrderedDict([('basis_29p25', (cv('kPurgeMdotBasis_kgps') * 1e3, 'LEAD 230 (3): the ONE flow basis, 289.5 K (Combustion v2.4b)')),
                         ('warm_end_31p06', (cv('kPurgeMdotWarm_kgps') * 1e3, 'Combustion v2.4b band warm end, 297.15 K (Cd ASSUMED)')),
                         ('cd0p80_33p13', (float(mcd_m.group(1)), 'Combustion band top at Cd 0.80 (ASSUMED; config.h statement)'))])
    span = cv('kPurgeFlow_s') + t_o - t_c                      # scheduled both-open COMMAND span
    win_tmax = hb3['hardware_window']['t_max_s']
    durs = [('scheduled flow kPurgeFlow_s', cv('kPurgeFlow_s'), 'DESIGN (LEAD 164 (1))'),
            ('firmware cap: physical flow = cap + t_close - t_open', cv('kHbleedCap_s') + t_c - t_o, 'DERIVED (valve times ASSUMED 30 / 80 ms)'),
            ('hardware both-open timer, firmware cap failed: T_hw,max + t_close - t_open', hwb[1] + t_c - t_o, 'DERIVED (DESIGN timer, not drawn)'),
            ('PURGE_WIN window bound, cap and timer failed: t_max + t_close - t_open', win_tmax + t_c - t_o, 'DERIVED (hardware_window.t_max_s)')]
    lim_g = cv('kPurgeVentLimit_kg') * 1e3
    mass_rows = []
    for name_, d_, tg_ in durs:
        row_ = OrderedDict([('case', name_), ('flow_s', rg(d_, 4)), ('tag', tg_)])
        for key_, (md_, _b) in mdots.items():
            row_['vented_g_at_%s_gps' % key_] = rg(md_ * d_)
        row_['basis_minus_76g_g'] = rg(mdots['basis_29p25'][0] * d_ - lim_g)
        mass_rows.append(row_)
    want = [(0, 'basis_29p25', 73.13), (1, 'basis_29p25', 76.05), (1, 'warm_end_31p06', 80.76), (0, 'warm_end_31p06', 77.65),
            (1, 'cd0p80_33p13', 86.14), (0, 'cd0p80_33p13', 82.83), (2, 'basis_29p25', 81.65), (2, 'warm_end_31p06', 86.70),
            (2, 'cd0p80_33p13', 92.48), (3, 'basis_29p25', 96.33)]
    for i_, k_, v_ in want:
        if abs(mass_rows[i_]['vented_g_at_%s_gps' % k_] - v_) > 0.006:
            raise SystemExit('purge mass row %d %s = %s, the texts quote %s' % (i_, k_, mass_rows[i_]['vented_g_at_%s_gps' % k_], v_))
    for s_ in ('81.65 g at 29.25 g/s', '86.70 g at 31.06 g/s', '92.48 g at 33.13 g/s'):
        if s_ not in bench:
            raise SystemExit('bench plan v4 CHK-BT residual text %r not found' % s_)
    if not (span + 2 * dt_ < cv('kHbleedCap_s') and span + 2 * dt_ > 2.39 and (2.43 + t_o - t_c) + 2 * dt_ < 2.39 and 2.43 >= cv('kPurgeFlowMin_s')):
        raise SystemExit('230 (3) cap arithmetic changed')
    if not (hwb[0] > cv('kHbleedCap_s') + dt_):
        raise SystemExit('both-open timer minimum not after the cap + 1 tick')
    s12c = OrderedDict((c_['case'], c_) for c_ in s12['cases'])
    ev_keys = ['cap_v1_close_inhibited_EVIDENCE', 'hw_timer_alone_min_2.577s_cap_off_close_inhibited_EVIDENCE',
               'hw_timer_alone_nom_2.659s_cap_off_close_inhibited_EVIDENCE', 'hw_timer_alone_max_2.741s_cap_off_close_inhibited_EVIDENCE']
    ev_rows = [OrderedDict([('case', k_), ('both_commanded_open_s', s12c[k_]['both_valves_cmd_open_s']),
                            ('hw_timer_cut_after_both_rise_s', s12c[k_]['hw_cut_after_both_rise_s']),
                            ('purge_mass_g_SIL_plant', s12c[k_]['purge_mass_g']), ('final_state', s12c[k_]['final_state'])]) for k_ in ev_keys]
    if [r_['hw_timer_cut_after_both_rise_s'] for r_ in ev_rows] != [None, 2.577, 2.659, 2.742]:
        raise SystemExit('S12 hardware-timer EVIDENCE cases changed')
    so_keys = ['stuck_open_after_lift_d0.6mm', 'stuck_open_after_lift_d0.8mm', 'stuck_open_after_lift_d1.0mm', 'stuck_open_first_burn_d1.0mm']
    so_rows = [OrderedDict([('case', k_), ('stand_variant_fails', (k_ + '_stand') in s12c and not s12c[k_ + '_stand']['pass']),
                            ('vented_g_SIL_plant', s12c[k_]['purge_mass_g']), ('leak_flag_after_injection_s', s12c[k_]['leak_flag_after_injection_s']),
                            ('plant_mid_frac', s12c[k_]['plant_mid_frac']), ('pass', s12c[k_]['pass'])]) for k_ in so_keys]
    smain = rd(os.path.join(FWD, 'sil', 'sil_main.cpp'))
    if 's.hb_stuck_open_at[0] = s.hb_stuck_open_at[1] = t' not in smain or 'both_open_at(TI + 0.80)' not in smain:
        raise SystemExit('S12 stuck-open injection is no longer the both-valves form')
    u570 = pct3['G_pmid_comparator_U570']
    hb = OrderedDict()
    hb['architecture'] = tv('2 NC valves in series (V1, V2), restrictors 2 x 0.707 mm upstream of V1 (1.0 mm equivalent), P_mid Kulite XTL-190SM-2000A '
                            '(C1, J511, LEAD 206 (3)) between them on the U570 comparator into the pin 23 ladder; V1 = pin 15 AND PURGE_WIN AND NOT '
                            '(both-open timer), V2 = pin 24 AND PURGE_WIN, low-side on +12V_ARM',
                            'DESIGN / LEAD 164, 166 (3), 206 (3), 216 (5); schematic v2.6 NOT drawn for the C1 P_mid and the timer')
    hb['fitted'] = hb3['fitted']
    sch = refresh_cfg(copy.deepcopy(hb3['schedule']), C, cfg_changes, 'head_end_bleed_provision/schedule')
    sch['text'] = ('PURGE: MV open, pintle seated; fill step V1 only (path proof on P_mid); V2 opens; FLOW %s; V1 close command %s before E0 + its '
                   'closing time; closure step: vent (P_mid low 5 ticks) then hold test (100 ms). The ECU never truncates the flow for T_fire (a '
                   'RELIGHT before the purge is complete waits); the both-open COMMAND cap %s ends an over-long overlap. The v2.10 statement that '
                   'the cap does not truncate the flow under valve tolerances is WITHDRAWN (LEAD 216 (5))'
                   % (human(C('kPurgeFlow_s')), human(C('kPurgeFlowEndLead_s')), human(C('kHbleedCap_s'))))
    hb['schedule'] = sch
    hb['closure_rule'] = hb3['closure_rule']
    hb['achieved_flow_report'] = hb3['achieved_flow_report']
    hb['masses'] = OrderedDict([
        ('limit', C('kPurgeVentLimit_kg')),
        ('flow_bases_gps', OrderedDict((k_, OrderedDict([('v', rg(v_[0])), ('basis', v_[1])])) for k_, v_ in mdots.items())),
        ('rows', mass_rows),
        ('quantity', hb3['mass']['quantity']),
        ('tag', 'DERIVED (flow basis x physical flow time; valve times kHbleedOpenTime_s / kHbleedCloseTime_s ASSUMED 30 / 80 ms; B-BLEED-1 '
                'measures the flow and the times)')])
    hb['cap_decision_230_3'] = OrderedDict([
        ('question', cite(230, '(3) Purge (OI-42; line 216 (5))', 760)),
        ('answer', tv('the scheduled purge does NOT fit a 2.39 s cap: its both-open command span F + t_open - t_close = %.2f s (+ up to 2 ticks) '
                      'is above 2.39 s, and a 2.39 s cap would end the %.2f s scheduled flow at 2.39 + t_close - t_open = %.2f s. The cap stays '
                      '%s (config.h static_asserts: the span ends before the cap; the 230 (3) fit check)'
                      % (span, cv('kPurgeFlow_s'), 2.39 + t_c - t_o, human(C('kHbleedCap_s'))), 'DERIVED config.h')),
        ('warm_end_vented_mass', tv('warm end 31.06 g/s: %.2f g at the cap (%.2f s of flow), %.2f g for the scheduled %.2f s; Cd 0.80 (%.2f g/s, '
                                    'ASSUMED): %.2f / %.2f g; on the one basis 29.25 g/s: %.2f / %.2f g against the 76 g limit'
                                    % (mass_rows[1]['vented_g_at_warm_end_31p06_gps'], mass_rows[1]['flow_s'], mass_rows[0]['vented_g_at_warm_end_31p06_gps'],
                                       mass_rows[0]['flow_s'], mdots['cd0p80_33p13'][0], mass_rows[1]['vented_g_at_cd0p80_33p13_gps'],
                                       mass_rows[0]['vented_g_at_cd0p80_33p13_gps'], mass_rows[1]['vented_g_at_basis_29p25_gps'],
                                       mass_rows[0]['vented_g_at_basis_29p25_gps']), 'DERIVED')),
        ('option_not_made', tv('kPurgeFlow_s 2.43 s (above the %s Combustion floor): command span %.2f s fits a 2.39 s cap; flow at that cap %.2f s '
                               '= %.2f g at 29.25 g/s and %.2f g at 31.06 g/s, inside 76 g at the warm end (2.39 s is the warm-end form: 76 / 31.06 - '
                               '0.05 = %.3f s, 230 (3)); not made: the 2.5 s flow is LEAD 164 (1)'
                               % (human(C('kPurgeFlowMin_s')), 2.43 + t_o - t_c, 2.39 + t_c - t_o, rg(mdots['basis_29p25'][0] * (2.39 + t_c - t_o)),
                                  rg(mdots['warm_end_31p06'][0] * (2.39 + t_c - t_o)), lim_g / mdots['warm_end_31p06'][0] - (t_c - t_o)), 'DERIVED')),
        ('decision', 'LEAD (230 (3)): 2.55 s with the warm-end mass above, or the 2.43 s flow option with a 2.39 s cap')])
    hb['measured_time_form'] = tv('after CF-4 / B-BLEED-1: both-open overlap <= 76 g / mdot_measured - (t_close - t_open)_measured; with the one '
                                  'basis and the ASSUMED valve times: 76 / 29.25 - 0.05 = %.3f s (230 (3): <= 2.548 s)'
                                  % (lim_g / mdots['basis_29p25'][0] - (t_c - t_o)), 'DERIVED (LEAD 216 (5), 230 (3))')
    hb['hardware_both_open_timer'] = OrderedDict([
        ('decision', cite(216, '(5) R2-05, 203 (3) RESTATED', 1000)),
        ('design', tv('BOTH = V1 drive AND V2 drive (U576 74LVC1G08 on the U574 / U575 outputs, after the PURGE_WIN gating); U577 LTC6993-2 '
                      '(rising edge, retriggerable: each both-open episode is timed from its own start; POL 1, RSET 63.4k 0.1 %, DIVCODE 8 = '
                      'NDIV 2^21: T = 2.097152 s x 63.4 / 50); U578 74LVC1G74 latches BOTH at the end of the pulse (CLR by BOTH low); U579 '
                      '74LVC1G08: V1 gate = U574 output AND /Q. V1 drops when both drives have been high for T_hw and stays off until a command '
                      'drops; V2 untouched (the mid still vents); BOTH is taken before U579 (no self-clearing loop); no MCU pin, no firmware path',
                      'DESIGN config.h documentation block; schematic v2.6 NOT drawn; BOM v2.3 lines 261-264; LTC6993 Rev F Table 1 DIVCODE '
                      'AS-RECALLED, TO-VERIFY before layout')),
        ('kHbleedHwBothNom_s', C('kHbleedHwBothNom_s')), ('kHbleedHwBothErr', C('kHbleedHwBothErr')),
        ('range_s', tv([rg(hwb[0], 3), rg(hwb[1], 3)], 'DERIVED (DATASHEET LTC6993 Rev F 3.0 % grade range + 0.1 % RSET)')),
        ('schedule_not_cut', tv('T_hw,min %.3f s > cap + 1 tick %.3f s > scheduled command span %.2f s + 2 ticks: the firmware cap acts first in every '
                                'schedule and the scheduled flow is never cut by the timer (config.h static_assert)'
                                % (hwb[0], cv('kHbleedCap_s') + dt_, span), 'DERIVED')),
        ('answer_216_5', 'it CAN be done without cutting the scheduled flow under the stated timing tolerances (above), so 166 (3) is not restated; '
                         'the residual with the firmware cap failed is the timer bound (masses row 3: %.2f-%.2f g), not the PURGE_WIN 96-104 g'
                         % (mass_rows[2]['vented_g_at_basis_29p25_gps'], mass_rows[2]['vented_g_at_cd0p80_33p13_gps'])),
        ('sil_s12_evidence', tv(ev_rows, 'SIM S12 v2.11 (SIL plant flow about 31.4 g/s nominal, an ESTIMATE above the 29.25 g/s basis; sim.cpp '
                                         'hb_both_timer; the firmware V1 close command inhibited by a test hook; the cap case with the timer '
                                         'off)')),
        ('not_bounded', 'a both-open command chattering faster than T_hw (the firmware cap has the same limit; PURGE_WIN still bounds the powered '
                        'span); the pad BIT must not hold both valves open for more than 2.5 s'),
        ('bench', 'bench plan v4 CHK-BT (width 2.577-2.741 s over 10 trials and the board temperature extremes; schedule not cut; cap disabled; '
                  're-trigger; residual)'),
        ('test', T(r'hardware both-open timer'))])
    hb['hardware_window'] = hb3['hardware_window']
    hb['pad_bit'] = hb3['pad_bit']
    hb['leak_monitor'] = hb3['leak_monitor']
    hb['ladder'] = hb3['ladder']
    hb['pmid_comparator'] = tv(OrderedDict([
        ('transducer', 'Kulite XTL-190SM-2000A (C1) on its INA333 chain (pc_overrange_fa1.ecu_chain transfer), J511'),
        ('values_ohm', u570['values']['v']), ('trip_rise_bar_abs', round(u570['trip_rise_Pa_abs']['v'] / 1e5, 3)),
        ('release_bar_abs', round(u570['release_Pa_abs']['v'] / 1e5, 3)), ('comparator_band_bar', round(u570['band_Pa']['v'] / 1e5, 3)),
        ('levels', u570['trip_rise_Pa_abs']['tag']), ('band_note', u570['band_Pa']['tag']),
        ('low_threshold_option', u570['oi_bleed_detect_low_threshold_option']['v'])]),
        'DESIGN (E96) / DERIVED calc/v2p11/pc_transducer_v3.py G (results/pc_transducer_v3.json %s)' % sha(os.path.join(RES, 'pc_transducer_v3.json')))
    hb['oi_bleed_detect'] = OrderedDict([
        ('decision', cite(203, '(4) S12 OI-BLEED-DETECT', 360)),
        ('status', 'OPEN: no detection design in v2.11; the residual vented masses are stated for GNC and the FMEA (the 203 (4) alternative; '
                   'fmea_rows_a1 FMEA-A1-BLEED-BOTH-OPEN)'),
        ('mode_label_correction', tv('the S12 cases behind 203 (4) inject BOTH valves stuck open (sil_main.cpp both_open_at sets hb_stuck_open_at[0] and '
                                     '[1]): the bleed path open, P_mid at %.2f x P_feed on the decided path (restrictors upstream of V1), about 3 bar '
                                     'abs, below the U570 band (%.2f / %.2f bar abs), so it reads like a vented mid. The label "V1 stuck open with V2 '
                                     'closed" (the v2.10 Electronics text, carried into 203 (4)) is wrong: with V1 alone stuck open and V2 closed '
                                     'P_mid = P_feed (high) and the leak monitor flags it after %s (S12 v1_stuck_open_at_E0: pass, stand BLEED_FAULT); '
                                     'the undetected mode is the double failure of the series pair'
                                     % (so_rows[2]['plant_mid_frac'], u570['trip_rise_Pa_abs']['v'] / 1e5, u570['release_Pa_abs']['v'] / 1e5,
                                        human(C('kHbleedLeakTime_s'))), 'SIM S12 + DESIGN sil_main.cpp')),
        ('residual_masses', tv(so_rows, 'SIM S12 v2.11 (SIL plant ESTIMATE, Cd 0.70 ASSUMED; vented mass from the injection to the end of the run)')),
        ('low_threshold_candidate', 'a U570 threshold near 2 bar abs would separate a both-open path (about 3 bar abs) from a vented mid (about 1 bar abs) '
                                    'only if the C1 zero drift at BL-08 is small; with the MISSING BL-08 temperature excursion (60 C: +/- 1.5 bar) the '
                                    'separation is not shown: NOT adopted (pc_transducer_v3 G)'),
        ('owner', 'Electronics (detection) / LEAD (accept the FMEA residual or ask for a detection design)')])
    hb['sil_s12'] = OrderedDict([('cases', len(s12['cases'])), ('pass', sum(1 for c_ in s12['cases'] if c_['pass'])), ('fail', s12['fail']),
                                 ('fail_cases', [c_['case'] for c_ in s12['cases'] if not c_['pass']]),
                                 ('mass_over_limit_cases', s12['mass_over_limit_cases']), ('mass_note', s12['mass_note']),
                                 ('label_note', 'the S12 scenario text keeps its "S12 v2.10" label: it is the v2.11 run (manifest record)')])
    hb['sil_s11_fault_path_v4'] = hb3['sil_s11_fault_path_v4']
    hb['sil_s11_note'] = 'v2.10 record (results/fault_path_v4.json, unchanged and hash-checked as a carried input); S11 is not re-run in v2.11'
    hb['naming_note'] = hb3['naming_note']
    doc['head_end_bleed_provision'] = hb
    doc['fmea_rows_a1'].append(OrderedDict([
        ('id', 'FMEA-A1-BLEED-BOTH-OPEN'),
        ('mode', 'both head-end bleed valves stuck open (double failure of the series pair) in a burn'),
        ('effect', 'N2O vents overboard through the 1.0 mm equivalent restriction while the Pc loop holds the setpoint (S12 flow split: injector '
                   'change < 0.1 %%); SIL vented mass %.2f / %.2f / %.2f g for d 0.6 / 0.8 / 1.0 mm after the lift, %.2f g over a first burn'
                   % (so_rows[0]['vented_g_SIL_plant'], so_rows[1]['vented_g_SIL_plant'], so_rows[2]['vented_g_SIL_plant'], so_rows[3]['vented_g_SIL_plant'])),
        ('detection', 'none on the stand; flight first burn: leak flag %.2f s after the injection (SIM); P_mid sits below the U570 band'
                      % so_rows[3]['leak_flag_after_injection_s']),
        ('mitigation', 'none in v2.11 (OI-BLEED-DETECT); pad BIT S1 / S3 catch a single stuck-open valve before flight'),
        ('source', cite(203, '(4) S12 OI-BLEED-DETECT', 260)),
        ('tag', 'SIM S12 v2.11 (SIL plant ESTIMATE); residual for GNC / FMEA (LEAD 203 (4))')]))

    # ================================================================================================ log, BOM, bench plan, mass
    ovr_m = re.search(r'uint8_t ovr_flags;\s*//(.*?)\n\s*uint16_t crc16', proto, re.S)
    if not ovr_m:
        raise SystemExit('protocol.h: ovr_flags comment not found')
    ovr_txt = ' '.join(x_.strip().lstrip('/').strip() for x_ in ovr_m.group(1).split('\n'))
    doc['log_v12'] = tv('LogRecord v%d = %d bytes at 1 kHz: v11 + ovr_flags (%s); LIGHT_SPIKE ls_flags b7 = above full scale; tlm_flags b2 = R2 '
                        'backstop reached' % (log_ver, log_size, ovr_txt), 'DESIGN protocol.h; test_core "LogRecord v12 is 180 bytes"')
    bom_csv = os.path.join(RES, 'bom_v2p3.csv')
    rd(bom_csv, 'rb')
    bs = bom3['summary']
    bad_price = [r_['line'] for r_ in bom3['rows'] if not (r_['delivered_price_DK6400'].startswith('TO-QUOTE') or
                                                         (r_['delivered_price_DK6400'] == 'n/a' and r_['price_basis'].startswith('NO PURCHASE')))
                 or str(r_['unit_price']).strip() in ('0', '0.0', '0.00') or 'from' in (str(r_['unit_price']) + r_['delivered_price_DK6400']).lower()]
    if bad_price or bs['rows'] != len(bom3['rows']):
        raise SystemExit('BOM v2.3 price rule broken in rows %s (or the row count)' % bad_price)
    doc['bom'] = OrderedDict([
        ('file', '06-electronics/results/bom_v2p3.csv (v2.3) %s; results/bom_v2p3.json %s (calc/v2p11/bom_v2p3.py)' % (sha(bom_csv), sha(os.path.join(RES, 'bom_v2p3.json')))),
        ('summary', OrderedDict((k_, bs[k_]) for k_ in ('version', 'date', 'ship_to', 'basis', 'inputs', 'rows', 'rows_catalogue_priced', 'rows_to_quote',
                                                       'rows_no_purchase', 'sections', 'n_amendments', 'known_catalogue_subtotal_by_currency',
                                                       'known_subtotal_note', 'total', 'rfq_rows_LEAD_216_6', 'blocked', 'tags'))),
        ('delta_rows_v2p11', [OrderedDict([('line', r_['line']), ('part', r_['part']), ('qty', r_['qty']), ('spare', r_['spare_recommended']),
                                           ('delivered_price_DK6400', r_['delivered_price_DK6400']), ('tag', r_['tag'])]) for r_ in bom3['rows'] if r_['line'] >= 251]),
        ('amendments_rev_elec_2', [OrderedDict([('line', a_['line']), ('field', a_['field']), ('basis', a_['basis'])]) for a_ in bs['amendments'] if 'R2-' in a_['basis']]),
        ('price_rule', 'checked: every row is TO-QUOTE delivered to Soenderborg DK-6400 (DK VAT, shipping and duty) or n/a (no purchase); the 3 '
                       'catalogue listings are recorded as listing prices only; no zero and no "from" price')])
    fb = bench.split('## 0. Founder block')[1].split('## 1. Order and gates')[0]
    founder = [(m_.group(1), m_.group(2).strip()) for m_ in re.finditer(r'^\| (F-\d+) \| ([^|]+) \|', fb, re.M)]
    if [f_[0] for f_ in founder] != ['F-%d' % i_ for i_ in range(1, 15)]:
        raise SystemExit('bench plan v4 founder block is not F-1..F-14: %s' % [f_[0] for f_ in founder])
    heads = re.findall(r'^### (.+)$', bench.split('## 2. Tests')[1].split('## 3. Outputs')[0], re.M)
    need = [('B-TC-1 heading', any(h_.startswith('B-TC-1') for h_ in heads)), ('CHK-BT heading', any(h_.startswith('CHK-BT') for h_ in heads)),
            ('B-TC-1 tau row', 'tau ≤ 0.25 s' in bench), ('B-FC-1 LOST DROGUE 0 row', '| LOST DROGUE 0 (LEAD 216 (2)(c)' in bench),
            ('F-13 stand T0', founder[12][1].startswith('stand T0 rule')), ('F-14 J-FWD', founder[13][1].startswith('J-FWD rule')),
            ('IGN-1 E2 - light <= 20 ms', '| E2 − light | ≤ 20 ms' in bench)]
    if not all(v_ for _k, v_ in need):
        raise SystemExit('bench plan v4 rows missing: %s' % [k_ for k_, v_ in need if not v_])
    doc['bench_plan'] = OrderedDict([
        ('file', '06-electronics/docs/bench_plan_v4.md %s' % sha(bench_path)),
        ('tests', heads),
        ('founder_block', [OrderedDict([('id', i_), ('action', a_)]) for i_, a_ in founder]),
        ('founder_block_rule', cite(216, '(6) R2-06', 520)),
        ('v2p11_rows_checked', [k_ for k_, _v in need]),
        ('note', 'bench plan v3 is superseded; every row passes on hardware before the item it closes is used; nothing here has been run')])
    hm = pct3['H_mass']['v']
    pc_add_kg = hm['per_channel_g'] / 1e3
    net_kg = hm['delta_kg'] + pc_add_kg
    mech_worst = mtrig['dm_landing_without_TC09_thinning_kg']
    if not (net_kg < 0.10 and mech_worst + pc_add_kg < 0.10):
        raise SystemExit('mass statement: a combination reaches the 0.10 kg trigger - review')
    doc['mass_statement'] = OrderedDict([
        ('electronics_changes', tv(OrderedDict([('P_feed_plus_P_mid_C1_g', hm['P_feed_plus_P_mid_g']), ('carried_by_Mechanical_g', hm['carried_g']),
                                                ('P_feed_P_mid_delta_kg', hm['delta_kg']), ('Pc_C1_added_on_the_gimballed_head_g', hm['per_channel_g']),
                                                ('removed_070BG_and_sense_line_g', None), ('net_kg', round(net_kg, 3))]),
                                   'DERIVED (DATASHEET C1 body 4 g; cable 10 g/m ASSUMED; the removed Pc 070BG and its sense line are MISSING from the '
                                   'Electronics side: Mechanical owns the ledger)')),
        ('gnc_trigger', mtrig['rule']),
        ('against_trigger', tv('Electronics net %+.3f kg; worst combination: Mechanical v3.5.2 %+.4f kg (without the TC-09 thinning) + the C1 Pc '
                               'addition with no credit for the P_feed / P_mid reduction = %+.3f kg; below the 0.10 kg re-fly trigger in every '
                               'combination. Not CONFIRMED (nothing weighed): information for GNC, not a re-fly input'
                               % (net_kg, mech_worst, mech_worst + pc_add_kg), 'DERIVED + Mechanical CALC (mechanical.json gimballed_mass_properties_v352)')),
        ('owner', 'Mechanical carries the C1 masses and the removed 070BG / sense line in the ledger (requests)')])

    # ================================================================================================ open issues (v2.11)
    arm_log = rd(os.path.join(RES, 'arm_build_v2p11_log.txt'))
    arm_warn = int(re.search(r'warnings: (\d+), all -Wdouble-promotion; errors: (\d+)', arm_log).group(1))
    arm_src = OrderedDict(re.findall(r'(\w+\.(?:cpp|h)) ([0-9a-f]{16})', arm_log.split('# source sha256/16:')[1].split('\n')[0]))
    arm_src_now = OrderedDict()
    for f_ in arm_src:
        p_ = os.path.join(CORE, f_)
        rd(p_, 'rb')
        arm_src_now[f_] = sha(p_)
    if arm_src_now != arm_src:
        raise SystemExit('ARM build log sources differ from the current tree: %s vs %s' % (arm_src, arm_src_now))
    lit13 = [c_ for k_ in ('B_residual_corners', 'C_rezero', 'D_purge_starts') for c_ in s13[k_] if c_.get('plant_lit') and c_.get('E2_minus_light_ms') is not None]
    off_ = lambda c_: abs(float(re.search(r'([+-]\d\.\d)bar', c_['case']).group(1))) if re.search(r'([+-]\d\.\d)bar', c_['case']) else 0.0
    e2_all = [min(c_['E2_minus_light_ms'] for c_ in lit13), max(c_['E2_minus_light_ms'] for c_ in lit13)]
    e2_03 = max(c_['E2_minus_light_ms'] for c_ in lit13 if off_(c_) <= 0.3 + 1e-9)
    st15, fl15 = s15['stand'], s15['flight']
    a1_amb = sum(amc['base_amb_runs_lit_unlit'])
    oi = lambda id_, sev, issue, owner, closure: OrderedDict([('id', id_), ('severity', sev), ('issue', issue), ('owner', owner), ('closure', closure)])
    doc['open_issues'] = [
        oi('OI-HAL', 'HIGH', 'Teensy HAL not written (RE-06); TLM_SLOW undefined; %d ARM -Wdouble-promotion warnings (v2.10: 93); objects only, not '
           'linked' % arm_warn, 'Electronics', 'HAL-1, B-ECU-1'),
        oi('OI-POWER', 'HIGH', 'RE-09: +12V_ARM and the ARM bus over rating in the purge and E0 overlaps; the E0 row CANNOT PASS as designed (OI-E0-SUPPLY, '
           'bench plan v4 B-PWR-2); time-resolved budget, sequencing and peak-and-hold not done; v2.11 adds about 15 mA of C1 bridge current on '
           '+5V_SNS (power_budget.v2p11_sense_rail; the re-sum is not redone)', 'Electronics', 'power sequencing / capacity decided before the layout; B-PWR-2'),
        oi('OI-BLEED-VALVE', 'HIGH', 'bleed valve not selected (LEAD 206 (4) search continues); peak-and-hold not drawn; valve times ASSUMED (30 / 80 ms) in '
           'the cap, the masses and the timer margins', 'Electronics / Mechanical', 'selection; B-BLEED-1'),
        oi('OI-PURGE-CAP', 'HIGH', 'cap %s kept (230 (3): the scheduled command span %.2f s does not fit 2.39 s); vented mass at the cap %.2f g on the one '
           'basis 29.25 g/s (76 g limit), %.2f g at the warm end 31.06 g/s, %.2f g at Cd 0.80; firmware cap failed: the hardware both-open timer '
           'bounds %.2f-%.2f g (PURGE_WIN alone %.2f-%.2f g); option: kPurgeFlow_s 2.43 s with a 2.39 s cap (head_end_bleed_provision.cap_decision_230_3)'
           % (human(C('kHbleedCap_s')), span, mass_rows[1]['vented_g_at_basis_29p25_gps'], mass_rows[1]['vented_g_at_warm_end_31p06_gps'],
              mass_rows[1]['vented_g_at_cd0p80_33p13_gps'], mass_rows[2]['vented_g_at_basis_29p25_gps'], mass_rows[2]['vented_g_at_cd0p80_33p13_gps'],
              mass_rows[3]['vented_g_at_basis_29p25_gps'], mass_rows[3]['vented_g_at_cd0p80_33p13_gps']),
           'LEAD', 'lead decision on the cap; measured-time form after CF-4 / B-BLEED-1'),
        oi('OI-WINDOW-LATENT', 'MEDIUM', 'stuck-high purge-window chain and the both-open timer are invisible to the ECU (no free pin); a pre-flight check with '
           'PURGE_EN low is not in firmware v2.11', 'Electronics / FC owner', 'CHK-PW, CHK-BT; firmware BIT step'),
        oi('OI-BLEED-DETECT', 'MEDIUM', 'S12 (SIM): both bleed valves stuck open (the 203 (4) label is corrected in head_end_bleed_provision.oi_bleed_detect) are '
           'not detected on the stand and are flagged %.2f s after injection in the flight first burn (P_mid below the U570 band on the decided path); '
           'SIL vented %.2f / %.2f / %.2f g (d 0.6 / 0.8 / 1.0 mm, after the lift), %.2f g (first burn); no detection design in v2.11'
           % (so_rows[3]['leak_flag_after_injection_s'], so_rows[0]['vented_g_SIL_plant'], so_rows[1]['vented_g_SIL_plant'],
              so_rows[2]['vented_g_SIL_plant'], so_rows[3]['vented_g_SIL_plant']),
           'Electronics / LEAD', 'LEAD: accept the FMEA residual (FMEA-A1-BLEED-BOTH-OPEN) or ask for a detection design; B-BLEED-1'),
        oi('OI-A1-BASE-AMB', 'MEDIUM', 'replaces OI-RE02-CRITERIA (closed under the 216 (4) per-location criteria, 0 fails in both builds). A1 relight BASE_AMB: '
           'P0 := 0, the lift is commanded, the A7 HOLD band aborts PC_SENSOR %s after the lift, no light, no false E2 (relight lost, fail-safe); '
           '%d of %d runs in the S13 A Monte Carlo at the A1 state; 216 (4) set no A1 target' % (human(C('kA7Time_s')), a1_amb, amc['runs_lit'] + amc['runs_unlit']),
           'LEAD', 'accept the outcome or rule the alternative (keep the measured P0 below ambient; not implemented)'),
        oi('OI-TEB-FALSE-LIGHT', 'MEDIUM', 'S9 +/-1.034 bar TEB cases fail as in v2.9 / v2.10 (the v2.11 run uses the C1 chain with the same injected biases)',
           'LEAD / Electronics', 'B-PC-1 residual <= 0.3 bar, then kBpc1Shown'),
        oi('OI-GUARD-BAND', 'MEDIUM', 'cold side CLOSED by LEAD 216 (7) (ARM margin %s, PREPRESS safe exit; S5: TANK_COLD %d, safe exits %d). Open: the '
           'uncalibrated P_tank hot interlock needs the tank <= about 19.8 C; wall-vs-bulk offset MISSING; countdown margin above 15 C MISSING'
           % (human(C('kTankColdArmMargin_K')), s5_causes_named.get('TANK_COLD', 0), s5['prepress_safe_exit_runs']),
           'Electronics / Mechanical', 'B-PT-1'),
        oi('OI-E2-LATENCY', 'LOW', 'E2 - light (SIL): p50 %d / max %d ms in S5, %d / %d ms in S15 (flight), %d / %d ms (stand); A1 relight %d-%d ms over the S13 '
           'B / C / D lit cases, %d ms at the offset corners within the 0.3 bar B-PC-1 residual, %d ms at the -0.6 bar corners: the IGN-1 '
           'criterion (<= 20 ms) has no margin at those corners; GNC models thrust onset at E2 (GNC to confirm 20 ms)'
           % (s5['light_to_E2_ms_p50'], s5['light_to_E2_ms_max'], fl15['lit_to_e2_ms_p50'], fl15['lit_to_e2_ms_max'], st15['lit_to_e2_ms_p50'],
              st15['lit_to_e2_ms_max'], e2_all[0], e2_all[1], e2_03, e2_all[1]), 'Combustion / Electronics / GNC', 'IGN-1'),
        oi('OI-RE15', 'HIGH', 'no layout; pin-function check, footprints, derating table not done', 'Electronics', 'RE-15 checks before fabrication'),
        oi('OI-SCHEMATIC-V2P6', 'HIGH', 'schematic v2.6 NOT drawn: three C1 bridge channels, U330 / U570 values on C1, the ride-through C330B variant, the '
           'both-open timer U576-U579, the C1 harness breaks; ERC and the netlist cross-check cover v2.5 only (ecu.schematic.v2p11_board_items_not_drawn)',
           'Electronics', 'schematic v2.6 + ERC + netlist cross-check before RE-15'),
        oi('OI-GIMBAL-JAM', 'MEDIUM', 'S6 gimbal_jam_moving_cmd: small-amplitude jam undetected (RE-24 test-based, LEAD 203 (6)); the abort is not inhibited '
           'near touchdown (LEAD 227 (7))', 'Electronics + GNC', 'B-TVC-1'),
        oi('OI-TB-MEOP', 'ACCEPTED', 'S6 throat block: plant Pc %.2f bar abs, %.0f ms above MEOP (R2-15: not 72 ms); inside LC-TB70 (S6C)'
           % (tb70['Pc_max_abs_Pa'] / 1e5, tb70['t_Pc_above_MEOP_s'] * 1e3), 'Mechanical FEA', 'LC-TB70 (04-fea/v352/lc_tb70_envelope_v1.json)'),
        oi('OI-FC', 'HIGH', 'FC: PURGE_EN discrete; R2 v2 at W 0.8 s with the mode-3 flush at the Pc-invalid onset (227 (6)), the reference choice and the '
           'frame-noise budget (<= %.2f N rms iid at 0.8 s); DROGUE reports with the re-send rule (<= %d re-sends, 0.2 s) and the DROGUE_ECHO log '
           '(216 (2)(a)); the d6 b6 echo check before a RELIGHT; no decision on the A7 high flag before E2 + 0.45 s (216 (8) condition 3); the FC Pc '
           'branch margin at E2; the PURGE commit L* 1.3 s with no unpurged RELIGHT (the ECU refuses it: UNPURGED %d); FC_THRUST valid flag clear on '
           'A1; PC_VALID launch commit; IMU filter delay' % (nf8['iid_sigma_for_Pmax_1e-3_N'], cv('kFcDrogueResendMax'), refuse['UNPURGED']),
           'FC owner + GNC', 'B-FC-1, HIL-OT-1'),
        oi('OI-38-R2-COMMAND-HOLD', 'HIGH', 'ECU side in SIL: lift-commanded hold at %.5f mm, backstop E2 + %s, per-tick Pc validity (S17 v2.11: 0 dead releases '
           'with the hold and the flush at either window, W10 < 6 m/s, photodiode view). Open: the FC side; GNC R2 v2 re-run with the flush / reference '
           '/ noise budget; the FC Pc branch margin; the lit F_min 33.14 N corners (230 (5)); CF-3 at 0.21776 mm; injector / feed soak-back heat '
           'TO-VERIFY' % (cv('kR2HoldLift_m') * 1e3, human(C('kR2HoldBackstop_s'))),
           'GNC (FC) / Combustion / Electronics', 'GNC R2 v2 re-run; B-FC-1; CF-3 start-lift point'),
        oi('OI-FA1-PC-OVERRANGE', 'HIGH', 'C1 chain (v2.11): 0 of 896 FA-1 grid cases reach the over-range or the above-FS flag; as built the A1 relight aborts '
           '%d-%d of 896 (filtered 30 bar / 5 ms and the comparator); the ride-through option (default OFF) aborts 0 and S6R aborts %d of %d required '
           'in-window over-pressure runs inside LC-TB70; adoption is the lead\'s; C1 output above full scale and recovery MISSING (F-10)'
           % (rngc('as_built_aborts_nominal')[0], rngc('as_built_aborts_nominal')[1], s6r['required_passed'], s6r['required_cases']),
           'LEAD (adopt the ride-through or not) / Electronics / founders (F-10, B-PC-1, B-DPC-1)', 'LEAD decision; B-PC-1; B-DPC-1 at IGN-1 / T series; HIL-TR-1'),
        oi('OI-A1-PCLOSS-OVERTHRUST', 'ACCEPTED (FMEA record)', 'A1: no over-thrust detector after an in-flight Pc loss (fmea_rows_a1)', 'LEAD / GNC',
           'none on A1; RG-16 budget before FC_THRUST is armed on any mission'),
        oi('OI-STAND-LATE-LIGHT', 'LOW', 'S15 v2.11 stand: %d of %d lit plants end NO_IGNITION (light later than the stand W); flight %d of %d; fail-safe by '
           'design (R2-19)' % (st15['no_ignition_or_torch_fault'], st15['plant_lit'], fl15['no_ignition_or_torch_fault'], fl15['plant_lit']),
           'Combustion / LEAD', 'IGN-1 (record E1 -> light on every stand start)'),
        oi('OI-UNPURGED-RELIGHT', 'MEDIUM', 'the ECU guard is DONE (LEAD 203 (7): flight build with the bleed fitted refuses a RELIGHT in COAST, UNPURGED %d). '
           'Remaining: (a) with an UNPRIMED / UNKNOWN line in flight with the bleed fitted there is no relight path (PURGE needs the direct path: '
           'refused PURGE_PATH; RELIGHT in COAST refused UNPURGED); (b) the torch-kept ride-through of the gap is not implemented; (c) Combustion\'s '
           'latency model takes E2 as Pc > 3 bar abs while the ECU flight E2 is the relative rule' % refuse['UNPURGED'],
           'LEAD / Combustion / GNC (FC)', 'LEAD on (a); FC rule in the FSW record (B-FC-1); CF-4 O-3, IGN-1'),
        oi('OI-GEN-TABLES', 'MEDIUM', 'gen_tables.py v3.3 cannot parse the combustion.json v2.4b igniter sequence; engine_params.h / plant_tables.h / '
           'gnc_tables.h / valve_map_table.h stay generated from combustion.json v2.3 (HISTORICAL); v2.3 -> v2.4b leaf diff of the read keys: %d numeric '
           'changes outside the igniter sequence, %d inside (results/gen_tables_v2p4b_leafdiff_v1.json); the four values with no source text are now '
           'sourced by Combustion v2.4b (firmware_constant_sources_v2p4b; mapping confirmed in requests_answered)'
           % (leafd['summary']['numeric_changes_outside_igniter_sequence'], leafd['summary']['igniter_sequence_numeric_changes']),
           'Electronics (parser) + Combustion (machine-readable sequence)', 'gen_tables v3.4, regenerate, diff, re-run the SIL record'),
        oi('OI-FMIN-LIT', 'MEDIUM', 'lit F_min 33.14 N (3 of 72 Combustion corners never reach 37.16 N at 0.21776 mm, LEAD 230 (5)): S17 v2.11 with the lit '
           'thrust capped there: no lit run released at either window with the flush (relight lost, drogue kept); without the flush, reference none, %d '
           'of 1000 normal lit runs released' % R_(rows_litcap, lbl('normal', True, False, 'none_GNC_sim6'))['W0.8']['lit_released'],
           'GNC (R2 v2 re-run) / LEAD', '230 (5) open item'),
        oi('OI-PHOTODIODE-VIEW', 'HIGH', 'the dead-side result with reference none needs the photodiode main-chamber view (FLAMEOUT_OPT armed): photodiode-blind '
           'families with the flush release %d / %d (normal_noopt) and %d / %d (starved040_noopt) of 1000 dead runs at 0.5 / 0.8 s; with the reference '
           're-taken at the ECU E2 or at the light: none' % (v_noopt[0]['W0.5']['dead_released'], v_noopt[0]['W0.8']['dead_released'],
                                                              v_noopt[1]['W0.5']['dead_released'], v_noopt[1]['W0.8']['dead_released']),
           'Combustion / Mechanical (view) / GNC (reference)', 'IGN-1 photodiode row (view proven with the torch closed) or the GNC reference choice'),
        oi('OI-FC-PC-BRANCH', 'MEDIUM', 'with the FC Pc branch (release on Pc valid and filtered Pc >= 3.0 bar abs) every normal-family run is released at the '
           'E2 frame: Pc_f at E2 3.04 bar abs, 0.04 bar above the branch threshold, so R2 never decides those runs (drogue_release_support.r2v2_sweep.'
           'verdict_227_5.fc_pc_branch_finding)', 'GNC / FC owner', 'state the branch margin or move the threshold; GNC R2 v2 re-run'),
        oi('OI-R2-23-GLITCH', 'LOW', 'a HIGH over-range glitch later in the burn (E2 + 350 ms) is also seen by the filtered channel and the U330 tap: as built '
           'HW_OVERPRESSURE at every command, the ride-through build PC_OVERPRESSURE / HW_OVERPRESSURE except at 200 N (fail-safe, relight lost); '
           'the real glitch rate is MISSING', 'Electronics / founders', 'B-PC-1, HIL-TR-1'),
        oi('OI-FACE-PEAK', 'ROUTED', 'C1 seat-face peaks %.1f-%.1f bar abs (SIM on the ASSUMED 1-D lumped passage model) against the 102 bar abs T <= 1 ms '
           'ultimate of line 205; LEAD 249 (4) restated the proof requirement (>= 166 bar abs; C1 206.8 bar abs) and the peaks lie within FA1S 151.04'
           % (min(face_pk.values()), max(face_pk.values())), 'REV-COMB-4 / Combustion / Mechanical (CHANGELOG 249 (15))', 'REV-COMB-4'),
        oi('OI-S6R-INPUT', 'ROUTED', '%d S6R runs have their INPUT outside LC-TB70: the Combustion v2.4a FA-1 replay max-face case peaks %.2f bar abs > Z3 '
           '75.519 bar abs; 46 of 896 grid cases peak above 75.519 (141 above 63.1); no v2.11 claim depends on them'
           % (len(s6r_in_out), max(c_['input_peak_bar_abs'] for c_ in s6r_in_out)), 'REV-COMB-4 / Mechanical (CHANGELOG 249 (15))', 'REV-COMB-4; LC-TB70'),
        oi('OI-SEAT-RINGING', 'MEDIUM', 'ideal 25 us steps ring the C1 seat passage in the SIL model (laminar-only damping ASSUMED): the T45 guard does not '
           'fire on them (record: the ride-build ideal-step aborts come at the window end or the comparator, ride_through.seat_ringing_finding); the '
           '1 kHz raw swing about 38-61 bar abs is from a pre-record diagnostic (not in the record); whether a real passage rings like this is MISSING; '
           'the main step cases use a 1.0 ms rise (LC-TB70 pulse convention)', 'Electronics / Combustion / founders', 'B-DPC-1, HIL-TR-1'),
        oi('OI-STALE-LABELS', 'LOW', 'disclosed, no binary effect: config.h l.757-768 still describes the v2.10 thrust-commanded hold (the v2.11 rule is in '
           'r2_command_hold; the kR2HoldThrust_N tag is current); config.h l.832-834 / 865-866 describe the v2.10 170BG P_mid chain (LMV331, 9.86 / '
           '8.86 bar g; "restriction DOWNSTREAM of V2") while the decided path and U570 on C1 are as in head_end_bleed_provision; config.h l.900 says '
           'U576-U578 (the timer is U576-U579, l.945); scenario labels S9 (v2.6 TEB), S12 "S12 v2.10", S14_v2p10, S15, S16, S17_r2hold, probeF; test_core '
           'v210-16 "0.5 s adopted, 0.8 s checked"; results/pc_transducer_v3.json records the pre-249 (4) 112.2 bar abs check and its combustion v2.4a '
           'input; BOM 212 / 214 notes name "electronics.json v2", BOM 245 still names the over-range row B-PC-1 (now F-12); mech_params.h / '
           'mech_tables.h name mechanical.json v2 (regenerated from v2.2: the comment line only); the manifest rebuild paths and the "scratch" '
           'field of results/gen_headers_regen_check_v2p11.json point to a removed scratch folder, and the manifest "date" field is the tool '
           'default', 'Electronics', 'v2.12 text pass (comments, labels)')]

    # ================================================================================================ requests (v2.11)
    apc = comb['igniter']['sequence']['v']
    chk_c = [('1.1 x 102 = 112 bar abs' in apc['arm_preconditions'][3], 'igniter.sequence.v.arm_preconditions[3]'),
             ('112 bar abs' in comb['pc_dynamic_channel']['v']['flight'], 'pc_dynamic_channel.v.flight'),
             ('1.1 x 102 = 112 bar abs' in comb['pc_dynamic_channel']['v']['stand_proof_rating_v2p4b']['v']['rule'], 'pc_dynamic_channel.v.stand_proof_rating_v2p4b.v.rule'),
             ('Electronics: E0 + 0.15 s' in apc['start'][0]['action'], 'igniter.sequence.v.start[0].action'),
             ('Electronics E0 + 0.15 s' in comb['abort_matrix_v2p4']['v']['A14'], 'abort_matrix_v2p4.v.A14'),
             ('Electronics E0 + 0.15 s' in comb['cf4_gate']['v']['pass_criteria'][5], 'cf4_gate.v.pass_criteria[5]')]
    if not all(x_ for x_, _p in chk_c):
        raise SystemExit('combustion.json v2.4b stale items changed: %s' % [p_ for x_, p_ in chk_c if not x_])
    gpb = gnc['flight_software']['relight_sequence_placeholder']['v']['purge_bound']
    if abs(gpb['ecu_cap_mass_kg_rev2'] - 0.073) > 1e-9 or '2.5 s ECU duration cap' not in gpb['note_rev2']:
        raise SystemExit('gnc.json v3.1 purge_bound changed')
    if '448.15 K abort' not in lctb['zones']['Z1']['case']:
        raise SystemExit('LC-TB70 Z1 label changed')
    doc['requests'] = [
        'FC owner (LEAD 216 (2)(a), 216 (8), 227 (5) / (6), 186 (1) / (2), 203 (7)): DROGUE 1 / 0 reports with the re-send rule (new sequence number on '
        'every TLM_RELIGHT frame still showing d6 b6 = 1, from the second, at most %d, then DROGUE_ECHO); R2 v2 at W 0.8 s with the mode-3 flush at the '
        'Pc-invalid onset; confirm no FC decision uses the A7 high flag (d6 b7) before E2 + 0.45 s (216 (8) condition 3); read refuse UNPURGED %d as '
        '"PURGE first"; PURGE_EN discrete; PC_VALID launch commit; FC_THRUST valid flag clear on A1' % (cv('kFcDrogueResendMax'), refuse['UNPURGED']),
        'GNC (LEAD 216 (1), 227 (6), 230 (5)): R2 v2 re-run with the flush and the reference choice (none / ECU E2 / light); state the counting start and '
        'whether d_app holds FC measurement noise; the FC frame-noise budget (<= %.2f N rms iid, %.2f N AR(1) at 0.8 s for P(dead release) <= 1e-3; '
        '5 N rms is not admissible); the FC Pc-branch margin at E2 (Pc_f 3.04 vs 3.0 bar abs); the lit F_min 33.14 N corners'
        % (nf8['iid_sigma_for_Pmax_1e-3_N'], nf8['mc_ar1_sigma_for_P_1e-3_bounding_run_N']),
        'GNC (gnc.json v3.1 flight_software.relight_sequence_placeholder.v.purge_bound): ecu_cap_mass_kg_rev2 = 0.073 kg is described as "at the 2.5 s ECU '
        'duration cap"; 2.5 s is the scheduled FLOW (%.2f g on the one basis 29.25 g/s); the both-open command cap is %s = %.2f s of flow = %.2f g '
        '(%.2f g at 31.06 g/s); with the firmware cap failed the hardware timer bounds %.2f g; PURGE_WIN alone %.2f g. Residual for both valves stuck '
        'open: FMEA-A1-BLEED-BOTH-OPEN (up to %.2f g SIL)' % (mass_rows[0]['vented_g_at_basis_29p25_gps'], human(C('kHbleedCap_s')), mass_rows[1]['flow_s'],
                                                             mass_rows[1]['vented_g_at_basis_29p25_gps'], mass_rows[1]['vented_g_at_warm_end_31p06_gps'],
                                                             mass_rows[2]['vented_g_at_basis_29p25_gps'], mass_rows[3]['vented_g_at_basis_29p25_gps'],
                                                             so_rows[3]['vented_g_SIL_plant']),
        'GNC (information): Electronics mass change %+.3f kg (mass_statement), below the 0.10 kg trigger in every combination; not confirmed' % net_kg,
        'Combustion (combustion.json v2.4b): the flight Pc proof is ">= 1.1 x 102 = 112 bar abs" in igniter.sequence.v.arm_preconditions[3], '
        'pc_dynamic_channel.v.flight / .stand_proof_rating_v2p4b.v.rule (and open_interface_issues[5], fa1_spectra_v2p4b.contradiction): LEAD 249 (4) '
        'made it >= 166 bar abs (1.1 x FA1S 151.04); the C1 part (206.8 bar abs) meets it',
        'Combustion (combustion.json v2.4b): the closure deadline attributed to Electronics as "E0 + 0.15 s" in igniter.sequence.v.start[0].action, '
        'abort_matrix_v2p4.v.A14 and cf4_gate.v.pass_criteria[5] is stale: the ECU uses the torch gate E0 + %s (kTorchGate_s, v2.10 and v2.11)'
        % human(C('kTorchGate_s')),
        'Combustion (LEAD 194 (4)): injector-body and feed soak-back temperature at the relight for the start-level cold-flow bound (S17 v2.11 dead '
        'margin +%.3f N at 0.8 s with the flush); CF-3 start-lift point with a load cell at 0.21776 mm' % nf8['margin_min_N'],
        'Combustion: keep the epoch igniter sequence machine-readable (one field per value) so gen_tables can read it (OI-GEN-TABLES); bleed flow on the '
        'decided path for the B-BLEED-1 pass / fail; tolerance of a later E0 after the flow (kPurgeHoldMax_s basis)',
        'REV-COMB-4 / Mechanical (CHANGELOG 249 (15)): the C1 face-peak inputs (OI-FACE-PEAK) and the S6R input finding (OI-S6R-INPUT)',
        'Mechanical: carry the C1 masses (Pc 13.1 g on the gimballed head; P_feed + P_mid 26.3 g instead of 2 x 50 g) and the removed 070BG / sense '
        'line in the ledger; the C1 seat temperature MECO -> RELIGHT for the drift budget (RE-07; a seat thermocouple / hot-day re-run, LEAD 205); '
        'the C1 height inside 30 mm (cable dia MISSING); bleed valve mass and mounting once selected',
        'Mechanical (LC-TB70 04-fea/v352/lc_tb70_envelope_v1.json): zone Z1 is labelled "case at the 448.15 K abort"; the abort in force is 423.15 K '
        '(LEAD 243 (3)); Electronics reads Z1 as the TB thermal field of the old abort (hotter than any state the 423.15 K abort admits): relabel '
        'or confirm',
        'LEAD: (1) adopt the ride-through build option or not (ride_through, OI-FA1-PC-OVERRANGE); (2) purge cap 2.55 s with the warm-end mass, or the '
        '2.43 s flow with a 2.39 s cap (cap_decision_230_3); (3) the A1 BASE_AMB outcome (OI-A1-BASE-AMB); (4) no flight relight path with an '
        'UNPRIMED / UNKNOWN line and the bleed fitted (OI-UNPURGED-RELIGHT (a)); (5) the both-stuck-open bleed residual for the FMEA (OI-BLEED-DETECT; '
        'the 203 (4) label corrected); (6) the 249 (13) record (MANIFEST 620b3d566fe0c8b9) is superseded by two re-records with identical binaries: '
        'cite MANIFEST %s' % sha(os.path.join(SIL, 'MANIFEST_v1.json')),
        'Founders (bench plan v4 section 0): F-1..F-14 now (RFQs for BOM 237 / 238 / 244 / 245 / 250 / 251 delivered to Soenderborg DK-6400, the TE / '
        'PCB / NI / Kulite inquiries, the anemometer mast and logger, the spare-070BG over-range row, the stand T0 checklist row, the J-FWD rule); '
        'B-TC-1 with the TC calibrator (BOM 266)']

    # ================================================================================================ requests answered
    fcs = comb['firmware_constant_sources_v2p4b']['v']['constants']
    eph = rd(os.path.join(CORE, 'engine_params.h'))
    unit_scale = {'N/s': 1.0, 's': 1.0, 'bar abs': 1e5}
    fcs_rows = []
    for k_, v_ in fcs.items():
        mm_ = re.match(r'(k\w+) = ([\d.]+) (N/s|s|bar abs)$', k_)
        if not mm_:
            raise SystemExit('combustion firmware_constant_sources key not parsed: %r' % k_)
        nm_, val_ = mm_.group(1), float(mm_.group(2)) * unit_scale[mm_.group(3)]
        line_ = [ln_ for ln_ in eph.split('\n') if re.match(r'constexpr float %s = ' % nm_, ln_)]
        ok_ = (len(line_) == 1 and ('= %s;' % v_['firmware'][0]) in line_[0] and v_['firmware'][1] in line_[0]
               and abs(C(nm_, 'eng')['v'] - val_) <= 1e-9 * max(1.0, abs(val_)))
        if not ok_:
            raise SystemExit('combustion firmware_constant_sources %s does not map onto engine_params.h' % k_)
        fcs_rows.append(OrderedDict([('constant', nm_), ('value', C(nm_, 'eng')), ('combustion_key', k_), ('mapping', 'CONFIRMED (value, literal and comment)')]))
    doc['requests_answered'] = [
        OrderedDict([('request', mech_req[0] if mech_req else None),
                     ('answer', 'false-trip side: %.2f K worst case / %.2f K RSS (%.2f K over a -40..105 C board) inside the +12.3 K margin at A = 150 C '
                                '(worst nominal reading %.2f C); persistence %s (2-3 MAX31856 conversions), detection delay %.2f s at the station rate; '
                                'low-reading tolerance tol_lo = %s (incl. the surface-mount steady error %.2f K and placement %.2f K); T-F1 on the A 175 '
                                'rows (r 7.03 K/s > 7.00); after B-TC-1 calibration %.2f K at 7.03 K/s. ACCEPTED by the lead (249 (1)-(3))'
                                % (a1a['worst_case_K'], a1a['rss_K'], a1a['board_hot_variant']['worst_case_K'], st_hi + a1a['worst_case_K'],
                                   human(C('kOverTempTime_s')), a1b['detection_delay_s']['v'], a1b['formula_K'], a1b['surface_mount']['steady_error_K'],
                                   a1b['placement_K']['v'], tfb['after_B_TC_1_calibration']['at_7p03_K_per_s_K'])),
                     ('where', 'case_tc_channel; limits_v2p11')]),
        OrderedDict([('request', 'Combustion v2.4b open_items_v2p4b OI-46: "Electronics confirms the mapping" of the firmware constant source texts'),
                     ('answer', fcs_rows), ('where', 'engine_params.h (generated, combustion v2.3; values unchanged in v2.4b)')]),
        OrderedDict([('request', cite(230, '(3) Purge (OI-42; line 216 (5))', 300)), ('answer', 'cap 2.55 s kept; warm-end masses stated; lead decides'),
                     ('where', 'head_end_bleed_provision.cap_decision_230_3')]),
        OrderedDict([('request', cite(227, '(5) R2 starve window', 300)), ('answer', 'CONFIRMED for W10 < 6 m/s with conditions (not returned)'),
                     ('where', 'drogue_release_support.r2v2_sweep.verdict_227_5')]),
        OrderedDict([('request', cite(227, '(6) Mode-3 estimator', 300)), ('answer', 'flush implemented in the S17 R2 v2 evaluator (the ECU has no '
                                                                                    'mode-3 filter; the flight implementation is the FC owner\'s, GNC '
                                                                                    're-runs R2 with it); S17 run; FC frame-noise budget %.2f N rms iid '
                                                                                    'at 0.8 s against the %+.3f N mode-3 margin (bounding run)'
                                                                                    % (nf8['iid_sigma_for_Pmax_1e-3_N'], nf8['margin_min_N'])),
                     ('where', 'drogue_release_support.r2v2_sweep.noise_budget_227_6')])]

    # ================================================================================================ numbers quoted in earlier sections (checked)
    sc_r2 = rd(os.path.join(FWD, 'sil', 'sc_v211_r2.inc'))
    if 'Pc_f at E2 = 3.04 bar abs, 0.04 bar above the branch threshold' not in sc_r2:
        raise SystemExit('sc_v211_r2.inc no longer records Pc_f at E2 = 3.04 bar abs (fc_pc_branch_finding / OI-FC-PC-BRANCH text)')
    cases_csv = os.path.join(RES, 'fa1_chain_v2p11_cases.csv')
    cases_rows = list(csv.DictReader(rd(cases_csv).splitlines()))
    if sha(cases_csv) != fa1c['inputs']['cases_csv']['sha256_16']:
        raise SystemExit('fa1_chain_v2p11_cases.csv differs from the hash in fa1_chain_v2p11.json')
    z3_top, z2_top = lctb['zones']['Z3']['P_bar_abs'][1], lctb['zones']['Z2']['P_bar_abs'][1]
    head_pk = [float(r_['head_pk_bar']) for r_ in cases_rows if r_['chain'] == 'c1_cc1_c222_v6']
    grid_above = (len(head_pk), sum(1 for x_ in head_pk if x_ > z3_top), sum(1 for x_ in head_pk if x_ > z2_top))
    if grid_above != (896, 46, 141) or abs(z3_top - 75.519) > 1e-9 or abs(z2_top - 63.1) > 1e-9:
        raise SystemExit('FA-1 grid head peaks above the LC-TB70 Z3 / Z2 tops changed: %s (texts quote 896 / 46 / 141)' % (grid_above,))
    gl_t = sorted(set(g_['glitch_from_E2_ms'] for g_ in gl_late))
    if gl_t != [350] and gl_t != [350.0]:
        raise SystemExit('R2-23 late glitch time changed: %s (OI-R2-23-GLITCH says E2 + 350 ms)' % gl_t)
    if '= 73 bar' in rd(os.path.join(CORE, 'engine_ecu.cpp')) or '06/2026' in cfg_txt:
        raise SystemExit('R2-12 / R2-17 comment corrections are not in the tree')
    s6cmp = OrderedDict((c_['case'], c_) for c_ in cmp_files['S6_aborts.json']['cases'])
    r209 = OrderedDict()
    for k_ in ('pintle_jam_steady_cmd_detect_late', 'pc_reads_low_x0p70_500N_24C_Cd0p8_over_thrust_pc_valid'):
        c_ = s6cmp[k_]
        r209[k_] = OrderedDict([('cause_v2p10_v2p11', c_['cause_name']), ('abort_time_changed_v2p10_to_v2p11', '/inj_to_abort_s' in c_.get('changed', {}))])
        if c_['cause_name'][0] != c_['cause_name'][1]:
            raise SystemExit('R2-09 case %s changed cause in v2.11' % k_)

    # ================================================================================================ REV-ELEC-2 author status (R2-01..R2-23)
    sev_of = OrderedDict()
    for sev_, part_ in (('MAJOR', rev2.split('### MAJOR')[1].split('### MINOR')[0]), ('MINOR', rev2.split('### MINOR')[1].split('### NOTE')[0]),
                        ('NOTE', rev2.split('### NOTE')[1].split('## 3. CONFIRMATIONS')[0])):
        for m_ in re.finditer(r'\*\*(R2-\d\d)(?: \(MAJOR\))?\. (.+?)\*\*', part_):
            sev_of[m_.group(1)] = (sev_, m_.group(2).strip())
    if list(sev_of) != r2_ids or Counter(v_[0] for v_ in sev_of.values()) != Counter({'MAJOR': 6, 'MINOR': 10, 'NOTE': 7}):
        raise SystemExit('REVIEW-ELECTRONICS-R2 severities not 6 / 10 / 7: %s' % Counter(v_[0] for v_ in sev_of.values()))
    disp = {'R2-01': '(1) R2-01', 'R2-02': '(2) R2-02 ADOPTED in full', 'R2-03': '(3) R2-03, 203 (1)(b) RESTATED',
            'R2-04': '(4) R2-04, 203 (5) RESTATED per location', 'R2-05': '(5) R2-05, 203 (3) RESTATED', 'R2-06': '(6) R2-06',
            'R2-11': '(7) R2-11 OI-GUARD-BAND', 'R2-22': '(9) R2-22', 'R2-23': 'R2-23: Electronics states'}
    for k_ in ('R2-07', 'R2-08', 'R2-09', 'R2-10', 'R2-12', 'R2-13', 'R2-14', 'R2-15', 'R2-16', 'R2-17', 'R2-20', 'R2-21'):
        disp[k_] = '(10) Text and record items'
    l216_10 = CL.lines[215].split('(10) Text and record items')[1]
    if any(k_ not in l216_10 for k_, v_ in disp.items() if v_.startswith('(10)')):
        raise SystemExit('216 (10) no longer lists every item mapped to it')
    sm_ = lambda st, ev, res=None: OrderedDict([('status', st), ('evidence', ev)] + ([('residual', res)] if res else []))
    st_r2 = OrderedDict([
        ('R2-01', sm_('CLOSED WITH RESIDUAL', 'S17 v2.11 sweep (results/sil_v2p11/S17v2_r2v2_sweep.json %s): Pc-loss onsets 1-50 ms x 10 frame phases x '
                      'seeded noise, 200 / 500 N, hold on / off, against GNC R2 v2 (offline) at 0.5 and 0.8 s: drogue_release_support.r2v2_sweep '
                      '(verdict_227_5, noise_budget_227_6)' % sha(os.path.join(SIL, 'S17v2_r2v2_sweep.json')),
                      'GNC: the counting start, the flush in the FC, whether d_app holds FC noise (216 (1)); OI-PHOTODIODE-VIEW; OI-FC-PC-BRANCH')),
        ('R2-02', sm_('CLOSED WITH RESIDUAL', 'FC re-send rule (kFcDrogueResendMax %d, 0.2 s), ECU backstop E2 + %s (window + 2 FC frames + latency, '
                      'static_assert), EVENT R2_BACKSTOP 0x24 / tlm_flags b2; %s; %s; bench plan v4 B-FC-1 LOST DROGUE 0 row'
                      % (cv('kFcDrogueResendMax'), human(C('kR2HoldBackstop_s')), T(r'lost DROGUE 0'), T(r'R2 backstop is per burn')),
                      'the FC implementation is the FC owner\'s (OI-FC)')),
        ('R2-03', sm_('CLOSED WITH RESIDUAL', 'ride_through: persistence %s (>= 13 ms + 2 ms), window E1 .. E2 + %s, over-range N %d, T45 guard %s, '
                      'comparator RC FIXED %s (12.10-13.55 ms); S6R %d / %d required runs aborted inside LC-TB70; S6C whole-burn cost (21 cases, '
                      'all inside)' % (human(C('kRideOvpTime_s')), human(C('kRideWinPostE2_s')), cv('kRideOverrangeN'), human(C('kRideT45_s')),
                                       human(C('kRideCmpTauNom_s')), s6r['required_passed'], s6r['required_cases']),
                      'still a CANDIDATE (lead adoption); schematic v2.6 not drawn; OI-SEAT-RINGING; the S6R input finding is routed (OI-S6R-INPUT)')),
        ('R2-04', sm_('CLOSED WITH RESIDUAL', 'per location (light_rule.base_check_per_location): S13 B extension 0 fails in both builds under the 216 (4) '
                      'criteria; %s' % T(r'216 \(4\) BASE_AMB per location'), 'the A1 BASE_AMB outcome is the lead\'s (OI-A1-BASE-AMB)')),
        ('R2-05', sm_('CLOSED WITH RESIDUAL', 'one flow basis %s (230 (3)); cap %s kept as the provisional software limit; the "not truncated" '
                      'statement withdrawn; measured-time form stated; hardware both-open timer DESIGN (U576-U579, %.3f-%.3f s) with S12 EVIDENCE '
                      'cases and CHK-BT; %s' % (human(C('kPurgeMdotBasis_kgps')), human(C('kHbleedCap_s')), hwb[0], hwb[1], T(r'hardware both-open timer')),
                      'the cap decision is the lead\'s (230 (3)); the timer is not drawn; LTC6993 DIVCODE AS-RECALLED')),
        ('R2-06', sm_('CLOSED', 'bench plan v4 section 0: %d founder rows F-1..F-14 (RFQs delivered to DK-6400 for BOM 237 / 238 / 244 / 245 / 250 and '
                      '251, the TE / PCB / NI / Kulite inquiries, the anemometer mast and logger, the spare-070BG over-range row F-12, F-13 stand T0, '
                      'F-14 J-FWD rule)' % len(founder))),
        ('R2-07', sm_('CLOSED', 'pc_overrange_fa1.firmware_behaviour states the per-tick validity (flight HIGH over-range non-sticky, LOW latches, the '
                      'stand latch); the v3 sentence on the RUN validity (latched for the power cycle) is not carried and is in the self_check stale-string list')),
        ('R2-08', sm_('CLOSED', 'Makefile l.31-34 comment corrected; build/test_core_nohooks: %s' % man['test_core']['all_logs']['test_core_nohooks_log.txt'] +
                      ' (results/sil_v2p11/test_core_nohooks_log.txt %s; the hook-only case excluded)' % sha(os.path.join(SIL, 'test_core_nohooks_log.txt')))),
        ('R2-09', sm_('CLOSED (disclosed and explained)', 'the v2.9 -> v2.10 S6 timing changes come from the v2.10 RE-04 lift clamp and the integrator hold '
                      'during pintle travel (kLiftArriveTol_m 0.10 mm): a jam at a steady command keeps |cmd - lift| <= 0.1195 mm < kPintleStallErr_m '
                      '0.15 mm until the 4.5 s SHUTDOWN moves the command (abort +1.571 s); the Pc x0.70 over-thrust case reaches 650 N about 0.2 s later '
                      '(abort +0.365 s) [SIM v2.10 traces]. v2.11 vs v2.10: %s. Accepted by the author; the reviewer accepts or not'
                      % '; '.join('%s cause %s, abort time changed %s' % (k_, v_['cause_v2p10_v2p11'][1], v_['abort_time_changed_v2p10_to_v2p11'])
                                  for k_, v_ in r209.items()))),
        ('R2-10', sm_('CLOSED', 'S5 statistics over the flying runs with the denominators (firmware.sil_record_v2p11.S5_pad_mc: %d flying of %d runs)'
                      % (s5['flying_runs'], s5['runs']))),
        ('R2-11', sm_('CLOSED (cold side)', 'ARM margin %s (1.5 x the PREPRESS drop + repeatability) and the PREPRESS safe exit (interlocks.tank_cold); '
                      'S10v211 %d cases, %d fail; %s; %s' % (human(C('kTankColdArmMargin_K')), len(s10c['cases']), s10c['fail'], T(r'cold ARM margin'),
                                                             T(r'PREPRESS safe exit')), 'OI-GUARD-BAND hot side (B-PT-1)')),
        ('R2-12', sm_('CLOSED', 'config.h l.%d-%d A7 comment corrected (start_monitors.A7_flight_blank condition 1); engine_ecu.cpp no longer says '
                      '"(> 4.75 V = 73 bar)" (checked)' % (cl_a[0], cl_b[0]))),
        ('R2-13', sm_('CLOSED WITH RESIDUAL', 'bench plan v4: the E0 row is an open design item OI-E0-SUPPLY with an owner (B-PWR-2); B-PNT-1 states the '
                      'position-loop t10-90 and does not compare it with the S5 thrust step; IGN-1 E2 - light <= 20 ms; T1-T4 written out; B-FC-1 '
                      'LOST DROGUE 0 row', 'OI-E0-SUPPLY (OI-POWER); the 20 ms criterion has no margin at the -0.6 bar S13 corners (OI-E2-LATENCY)')),
        ('R2-14', sm_('CLOSED', 'BOM v2.3 amendments: %s' % ', '.join('line %d %s' % (a_['line'], a_['field']) for a_ in doc['bom']['amendments_rev_elec_2']
                                                                    if 'R2-14' in a_['basis']))),
        ('R2-15', sm_('CLOSED', 'S6 record: %.2f bar abs, %.0f ms above MEOP (sil_fail_dispositions, OI-TB-MEOP); checked against LC-TB70 in pressure-time '
                      'form (S6C inside)' % (tb70['Pc_max_abs_Pa'] / 1e5, tb70['t_Pc_above_MEOP_s'] * 1e3))),
        ('R2-16', sm_('CLOSED', 'starve threshold at both R2 v2 windows: released at every frame phase up to %.2f s (0.5 s) and %.2f s (0.8 s), reference '
                      'none, flush (r2v2_sweep.starve_threshold_R2_16)' % (st_none[0], st_none[1]))),
        ('R2-17', sm_('CLOSED', 'config.h 070BG citations now M3200 08/2018 (no 06/2026 left, checked); the 0.5-4.5 V response stays TO-VERIFY with TE '
                      '(F-7); moot for flight after LEAD 205')),
        ('R2-18', sm_('NOTED (not assigned by 216)', 'the C1 SIL chain (sil/sim.h pc_chain 1) limits each sample at the rails; the 070BG chain (pc_chain 0, '
                      'averaged limit) is kept for comparison only')),
        ('R2-19', sm_('NOTED (not assigned by 216)', 'S15 v2.11 stand: %d of %d lit plants NO_IGNITION (flight %d); bench plan v4 IGN-1 row "Late lights on '
                      'the stand (R2-19)"; OI-STAND-LATE-LIGHT' % (st15['no_ignition_or_torch_fault'], st15['plant_lit'], fl15['no_ignition_or_torch_fault']))),
        ('R2-20', sm_('CLOSED', 'results/sil_v2p11/test_core.json version v2.11; BOM line 250 HARD (LEAD 181 (6)) by amendment', 'the v2.10 scenario '
                      'labels that remain are disclosed (OI-STALE-LABELS)')),
        ('R2-21', sm_('CLOSED', 'results/fa1_chain_v2p11.json %s: four C1 chains (the 070BG chains kept as the reference)' % sha(os.path.join(RES, 'fa1_chain_v2p11.json')))),
        ('R2-22', sm_('CLOSED', 'lift-commanded hold at kR2HoldLift_m %.5f mm = the kIgnLiftTab_m A1 row (checked); %s'
                      % (cv('kR2HoldLift_m') * 1e3, T(r'lift-commanded R2 hold')))),
        ('R2-23', sm_('CLOSED', 'r2_command_hold.r2_23: a HIGH over-range tick after E2 engages the hold for that tick only (S17v2 glitch runs; test_core '
                      '"lift-commanded R2 hold")'))])
    doc['rev_elec_2_author_status'] = OrderedDict([
        ('note', 'Electronics statement for REV-ELEC-3; acceptance is the reviewer\'s'),
        ('review', 'reviews/REVIEW-ELECTRONICS-R2.md %s (REVISE: 0 BLOCKING, 6 MAJOR, 10 MINOR, 7 NOTE)' % sha(rev2_path)),
        ('disposition', cite(216, 'On REV-ELEC-2 (line 215)', 300)),
        ('items', [OrderedDict([('id', k_), ('severity', sev_of[k_][0]), ('finding', sev_of[k_][1]),
                                ('disposition_216', cite(216, disp[k_], 260) if k_ in disp else 'not assigned by line 216 (NOTE)')] +
                               list(st_r2[k_].items())) for k_ in r2_ids])])
    r1 = copy.deepcopy(v3['rev_elec_1_author_status'])
    r1['OPEN'] = [
        'RE-02 (rule implemented; the S13 B criteria are met per location under LEAD 216 (4) in both builds; residual: the A1 BASE_AMB outcome, LEAD)',
        'RE-05 (firmware cap 2.55 s, hardware purge window and the v2.11 both-open timer (DESIGN, not drawn); no qualifying valve; peak-and-hold not '
        'designed; the cap decision is the lead\'s, 230 (3))',
        'RE-06 (not done: Teensy HAL not written)',
        'RE-07 (partly done: firmware + SIL coast drift cases; B-PC-1 drift measurement open; the C1 seat temperature MECO -> RELIGHT requested from '
        'Mechanical)',
        'RE-09 (not done: time-resolved power budget, sequencing, peak-and-hold; OI-E0-SUPPLY; about 15 mA of C1 bridges added on +5V_SNS)',
        'RE-10 (partly done: P_mid level and closure from ASSUMED valve times, P_mid now on C1 / U570; final path timing open until B-BLEED-1)',
        'RE-15 (not done: no layout; pin-function check, footprints, derating table; schematic v2.6 not drawn)',
        'RE-28 (not done on hardware: HIL-RST-1 in bench plan v4; no in-flight recovery path by LEAD decision)']
    if not r1['DISPOSITIONED'][0].startswith('RE-24'):
        raise SystemExit('v3 rev_elec_1_author_status DISPOSITIONED order changed')
    r1['DISPOSITIONED'][0] = ('RE-24 (test-based, LEAD 203 (6): B-TVC-1 measures the undetected-jam bound and GNC shows a jam at that bound does not '
                              'lose a landing; the abort is not inhibited near touchdown, LEAD 227 (7))')
    r1['notes_v2p11'] = ['RE-12 (in CLOSED): the flight extension of the A7 high-side blank is ACCEPTED as DESIGN (LEAD 216 (8)); conditions 1, 2 and 4 '
                         'done, condition 3 is the FC owner\'s (start_monitors.A7_flight_blank)']
    doc['rev_elec_1_author_status'] = r1

    # ================================================================================================ self-check, change summary, write
    stale = stale_scan(doc)
    if stale:
        raise SystemExit('stale strings / values outside the history keys:\n  ' + '\n  '.join(stale))
    scan_doc = OrderedDict((k_, v_) for k_, v_ in doc.items() if k_ not in HISTORY_KEYS_V4)
    scan = json.dumps(scan_doc, ensure_ascii=False)
    n_a5, n_a5_ok = len(re.findall(r'\bA5\b', scan)), scan.count(G3.A5_ALLOWED)
    if n_a5 != n_a5_ok:
        raise SystemExit('A5 token outside the history keys: %d found, %d allowed (%s)' % (n_a5, n_a5_ok, G3.A5_ALLOWED))
    n_quoted = sum(len(c_['thresholds']) for c_ in matrix)
    doc['self_check'] = OrderedDict([
        ('abort_matrix', OrderedDict([('causes', len(matrix)), ('enum_causes', len(abort_enum) - 1), ('constants_quoted', n_quoted),
                                      ('rule', 'trigger numbers only from config.h placeholders; every listed constant quoted; none unresolved'),
                                      ('result', 'PASS')])),
        ('firmware_version', '%s (config.h stamp = Makefile header)' % fw_ver),
        ('schematic_version', '%s (generator REV = KiCad root rev = pin map rows); v2.6 NOT drawn (OI-SCHEMATIC-V2P6)' % rev),
        ('sil_manifest', 'firmware_version %s; binaries %s identical to a rebuild of the current tree; test_core %s / no-hooks %s; scenarios_file at its '
                         'current hash' % (man['firmware_version'], ', '.join(sorted(bins)), man['test_core']['all_logs']['test_core_log.txt'],
                                           man['test_core']['all_logs']['test_core_nohooks_log.txt'])),
        ('arm_build_log', 'results/arm_build_v2p11_log.txt: %d warnings, 0 errors; its recorded source hashes equal the current tree (%s)'
                          % (arm_warn, ', '.join('%s %s' % kv_ for kv_ in arm_src.items()))),
        ('structural_checks', [k_ for k_ in struct]),
        ('interfaces', 'gnc.json v3.1 4f3209323b0e0ed4, mechanical.json v2.2 f790d31b5ca7d954, combustion.json v2.4b fd3a7da6d27c7c66, LC-TB70 '
                       '6f710726e4787134, REVIEW-ELECTRONICS-R2 c7dee8d6c73c9920 asserted; every CHANGELOG citation checked for its marker'),
        ('carried_inputs', 'all %d unchanged since v3 (inputs.carried_inputs)' % len(carried_check)),
        ('quoted_numbers', 'purge masses (10 values) vs the config.h / bench plan texts; FA-1 grid head peaks above Z3 / Z2 (%d / %d of %d); Pc_f at E2 '
                           '3.04 bar abs in sc_v211_r2.inc; the R2-23 late-glitch time; the S6R / S6C / S17v2 counts used in the texts' % (grid_above[1], grid_above[2], grid_above[0])),
        ('stale_strings_absent', G3.STALE_STRINGS + STALE_V4),
        ('history_values_only_in_context', OrderedDict((k_, list(v_)) for k_, v_ in CONTEXT_ALLOWED.items())),
        ('a5_token_scan', 'stand-alone A5 tokens outside %s: %d, all of them "%s" (LEAD CHANGELOG 186 (4))' % (', '.join(HISTORY_KEYS_V4), n_a5, G3.A5_ALLOWED)),
        ('carried_constants_refreshed', len(cfg_changes)),
        ('kelvin_difference_rule', 'a K constant below 100 K is a temperature difference and is rendered in K only (v3 rendered kTankWallUnc_K '
                                   'as "0.56 K (-272.6 C)" in the TANK_HOT trigger; the JSON values are unchanged)'),
        ('constant_tag_rule', 'tag = the bracketed [..] text of the constant\'s header comment; v4 reads a bracket that closes on a later // line '
                              'to its end (v3 kept the first 120 characters): %d constants completed (%s); a carried leaf whose tag changed only '
                              'this way is listed under carried_constants_refreshed' % (len(tags_completed), ', '.join(n.split('::')[1] for n in tags_completed))),
        ('scope', 'consistency of this file with its sources only; not a check of the design or of hardware')])
    doc['change_summary_v3_to_v4'] = [
        'v3 (firmware v2.10) -> v4 (firmware v2.11, SIL record %s, MANIFEST %s); STAGED, the hub v3 file is unchanged' % (man['record_sha256_16'], sha(os.path.join(SIL, 'MANIFEST_v1.json'))),
        'config.h v2.10 -> v2.11 (computed, firmware.config_diff_v2p10): changed %s; added %d constants (%s)' % (', '.join(cdiff_changed), len(cdiff_added), ', '.join(cdiff_added)),
        'rebuilt from the v2.11 sources: firmware, sil_fail_dispositions, can_interface (v2.11 items on the v3 base), relight_interface, abort_matrix '
        '(%d causes, CASE_WARM_STAND added), light_rule (per location), start_monitors (A7_flight_blank), drogue_release_support (r2v2_sweep), '
        'r2_command_hold (lift-commanded, backstop, R2-23), pc_overrange_fa1 (C1 chain), head_end_bleed_provision (one basis, cap decision, both-open '
        'timer, label correction), log_v12, bom (v2.3), bench_plan (v4), open_issues, requests, rev_elec_1_author_status' % len(matrix),
        'new sections: ride_through, case_tc_channel, limits_v2p11, mass_statement, requests_answered, rev_elec_2_author_status, lead_rulings_v2p11, '
        'changelog_folding (lines 203-%d), superseded_v3' % max(r_['line'] for r_ in doc['changelog_folding']),
        'carried from v3 with the listed corrections and every embedded config constant re-read from v2.11 (%d refreshed, below): over_thrust, '
        'eng03_pintle_rate, pintle_rail, ecu, actuators, igniter, sensors, interlocks, safing, power_budget, loop_rates_and_latency, link_loss, '
        'fail_safe_states, fmea_rows_a1 (rows 2-3 rebuilt, 2 added), pad_go_no_go_a1, harness_across_gimbal, gse_interface, units' % len(cfg_changes),
        'not carried (history, readable in v3): change_summary_v2_to_v3, superseded_v2, oi37_interface_hygiene, log_v11, relight_interface '
        'unpurged_relight_contest / purge_commit_decision_note_194_3 / purge_commit_history_181, head_end_bleed_provision.mass',
        'open issue changes: OI-RE02-CRITERIA closed -> OI-A1-BASE-AMB; added OI-SCHEMATIC-V2P6, OI-FMIN-LIT, OI-PHOTODIODE-VIEW, OI-FC-PC-BRANCH, '
        'OI-R2-23-GLITCH, OI-FACE-PEAK, OI-S6R-INPUT, OI-SEAT-RINGING, OI-STALE-LABELS; OI-PURGE-CAP, OI-BLEED-DETECT, OI-GUARD-BAND, OI-TB-MEOP, '
        'OI-FA1-PC-OVERRANGE, OI-UNPURGED-RELIGHT, OI-GEN-TABLES, OI-38 restated',
        'requests: the v3 Combustion request on the four sequence values without source text is answered by combustion v2.4b '
        '(firmware_constant_sources_v2p4b; mapping confirmed); the v3 GNC hold-lift request (0.2154 mm) is superseded by the lift-commanded hold',
        OrderedDict([('carried_constants_refreshed', cfg_changes)])]
    doc['inputs']['files_read_sha256_16'] = READ
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write('\n')
    print('electronics.json v4 -> %s (%d top-level keys, %d abort causes, %d constants quoted, %d open issues, %d requests, %d limits, %d CHANGELOG '
          'items folded, %d carried constants refreshed; firmware %s, schematic %s)'
          % (a.out, len(doc), len(matrix), n_quoted, len(doc['open_issues']), len(doc['requests']), len(doc['limits_v2p11']),
             len(doc['changelog_folding']), len(cfg_changes), fw_ver, rev))


if __name__ == '__main__':
    main()
