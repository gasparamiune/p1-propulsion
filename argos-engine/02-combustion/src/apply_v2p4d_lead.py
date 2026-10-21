#!/usr/bin/env python3
"""Combustion v2.4d: the lead's text-only fold of CHANGELOG lines 258 (2)-(4), 259 and 260 into the v2.4c set.

Author: the lead (2026-10-21). No model is re-run; no SIM, CEA or FE result changes. One planning value changes: the T4
N2O (about 2.0 kg, ESTIMATE, against the 7.02 kg DC-D record), on GNC's N-07 answer in gnc.json v3.2 (LEAD 261).
Sources: CHANGELOG 258 (REV-GNC-7 accepted; purge (d1) / (d2); Z3 v2 and the Q_JFWD replace rule; routing), 259 (Mechanical's
J-FWD follow-ups: tap wall v3, LC-TB70 envelope v2, mechanical.json v2.4) and 260 (gnc.json v3.2 published).
Reads the v2.4c hub files (sha256/16 asserted) and writes combustion.json, REPORT.md, CF-4-SPEC.md, T1-T4-REGRESSION-SPEC.md
and DATASHEET-INPUTS-COMBUSTION.md to STAGE_DIR; REVISION-RESPONSE-R3.md is unchanged. Publishing is a separate step.
Every replaced JSON leaf is kept under superseded_v2p4d with the decision that replaced it; the md edits are in place
(appended notes, one inserted datasheet row), so REPORT / CF-4 / T1-T4 keep their v2.4c line numbers.
usage: python3 -I apply_v2p4d_lead.py STAGE_DIR STAMP_UTC   (STAMP_UTC from date -u, e.g. 2026-10-21T11:40:00Z)
"""
import copy, hashlib, json, os, re, sys

HUB = '/home/claude/work/shared-fallback/engine'
SRC = {
    'json': ('interfaces/combustion.json', '661db0a593462382'),
    'report': ('02-combustion/REPORT.md', '7a9acd3df5937303'),
    'cf4': ('02-combustion/CF-4-SPEC.md', '4e36be703a9e7d44'),
    't1t4': ('02-combustion/T1-T4-REGRESSION-SPEC.md', 'b00b2d852ed3475c'),
    'ds': ('02-combustion/DATASHEET-INPUTS-COMBUSTION.md', '29ed6d45c55ff234'),
}
UNCHANGED = {'02-combustion/REVISION-RESPONSE-R3.md': '370875c3645eb49c'}
REFS = {
    'interfaces/mechanical.json': '66bc53d88d444679',
    'interfaces/gnc.json': 'bde317782574cbd9',
    'reviews/REVIEW-GNC-R5.md': '6b86fcd326568646',
    'reviews/REVIEW-ELECTRONICS-R3.md': 'fcf05f8bc7382cd1',
    'reviews/REVIEW-COMBUSTION-R4.md': '2908321d7f75d439',
    '04-fea/v352/lc_tb70_envelope_v2.json': '7ebd2fd63dc878ef',
    '04-fea/v352/jfwd_tapwall_v352_v3.json': 'ef70572ec92b05b0',
}
CL_LINES = {258: 'b254707692a9a345', 259: '7edb995f3a4679bb', 260: 'c46be350277748c0'}  # sha256/16 of the line + '\n'
OUTNAME = {k: os.path.basename(v[0]) for k, v in SRC.items()}
stage, stamp = sys.argv[1], sys.argv[2]
assert re.fullmatch(r'2026-10-21T\d\d:\d\d:\d\dZ', stamp), stamp
os.makedirs(stage, exist_ok=True)


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


RAW = {}
for k, (rel, h) in SRC.items():
    b = open(os.path.join(HUB, rel), 'rb').read()
    assert sha16(b) == h, (k, sha16(b), h)
    RAW[k] = b.decode('utf-8')
for rel, h in list(UNCHANGED.items()) + list(REFS.items()):
    assert sha16(open(os.path.join(HUB, rel), 'rb').read()) == h, rel
CL = open(os.path.join(HUB, 'interfaces/CHANGELOG.md'), encoding='utf-8').read().split('\n')
for n, h in CL_LINES.items():
    assert CL[n - 1].startswith('2026-10-21 | '), n
    assert sha16((CL[n - 1] + '\n').encode('utf-8')) == h, (n, sha16((CL[n - 1] + '\n').encode('utf-8')))
SELF = sha16(open(os.path.abspath(__file__), 'rb').read())
LOG = []  # (file key, where, decision, what)

# ---------------------------------------------------------------- source facts asserted (the texts below quote them)
MJ = json.load(open(os.path.join(HUB, 'interfaces/mechanical.json')))
assert MJ['version'] == 'v2.4'
ENV = MJ['lc_tb70_envelope_v352']
Z3G = ENV['Z3_v2']['grid']
assert (Z3G['n_inside_v2'], Z3G['n_inside_v1'], Z3G['S_max_bar_abs'], Z3G['margin_to_FA1S_bar']) == (896, 850, 146.881, 4.159)
assert ENV['Z3_v2']['status'].startswith('ADOPTED by the lead at the go 2026-10-21T10:47:17Z')
RRG = ENV['jfwd_replace_rule_v2']['grid']
assert (RRG['n_Q_JFWD_above_60_of_896'], RRG['n_peak_above_60_of_896'], RRG['n_Q_above_60_with_peak_le_60'],
        RRG['lowest_peak_with_Q_above_60_bar_abs'], RRG['Q_over_peak_gauge_ratio_max']) == (298, 185, 113, 49.781, 1.2989)
assert ENV['jfwd_replace_rule_v2']['level_bar_abs'] == 60.0
assert ENV['jfwd_replace_rule_v2']['basis_minimum_at_60bar_nominal_factors'] == {
    'MS_y': ['TC-01 ligament (LC2U)', 0.328], 'MS_u': ['TC-01 ligament trend 78.6 C', 0.312]}
assert ENV['jfwd_replace_rule_v2']['jfwd_band']['band_ms'] == [0.2, 0.5]
assert 'requests_v352' in MJ and 'Z3 v2' in MJ['requests_v352'][4]
TW = json.load(open(os.path.join(HUB, '04-fea/v352/jfwd_tapwall_v352_v3.json')))
assert TW['version'] == 'v3'
CMP = TW['comparison_with_reviewer_estimate']
assert (CMP['SOAK52']['this_row_MS_y_thread_T'], CMP['SOAK52']['this_row_MS_y_screw_T'],
        CMP['SOAK70']['this_row_MS_y_screw_T'], CMP['Lame_passage_factor_governing_wall']) == (0.67, 0.294, 0.275, 2.2094)
for s in ('sigma 136.9 MPa, MS_y +0.670 / MS_u +0.785 at the TC-02 thread temperature 94.9 C', 'MS_y +0.275 (SOAK70, 158.6 C)',
          'Flags within 0.05 or negative (3750 column, all walls): 0', '>= 26 kHz', '(<= 3.45 kHz)', 'wall 1.6355 mm net'):
    assert s in TW['verdict'], s
GJ = json.load(open(os.path.join(HUB, 'interfaces/gnc.json')))
assert GJ['version'] == 'v3.2'
N07 = GJ['duty_cycles']['note_n07_rev_gnc_7']
for s in ('no GNC objective needs the DC-D v2 duty', 'inside the A = 150 C limit',
          'the DC-D first burn would cross at about 23.5 s, merged bound', "sits with REV-COMB-4's shortest T4 firing",
          'about 2.0 kg'):
    assert s in N07, s
R5 = open(os.path.join(HUB, 'reviews/REVIEW-GNC-R5.md'), encoding='utf-8').read()
assert 'RV7-04' in R5

# ---------------------------------------------------------------- markdown helpers
TXT = {k: RAW[k] for k in ('report', 'cf4', 't1t4', 'ds')}


def _lineno(k, pos):
    return TXT[k].count('\n', 0, pos) + 1


def mrep(k, old, new, fid, what, count=1, line=None):
    """Exact in-place replace (no newline in old or new); count asserted over the file, or within one line."""
    assert '\n' not in old and '\n' not in new, (k, fid)
    if line is None:
        t = TXT[k]
        c = t.count(old)
        assert c == count, (k, fid, c, old[:90])
        where, i = [], 0
        for _ in range(c):
            j = t.find(old, i)
            where.append(_lineno(k, j))
            i = j + len(old)
        TXT[k] = t.replace(old, new)
    else:
        L = TXT[k].split('\n')
        c = L[line - 1].count(old)
        assert c == count, (k, fid, line, c, old[:90])
        L[line - 1] = L[line - 1].replace(old, new)
        TXT[k] = '\n'.join(L)
        where = [line]
    LOG.append((k, 'line ' + ', '.join(str(n) for n in where), fid, what))


def lappend(k, n, startswith, add, fid, what):
    L = TXT[k].split('\n')
    assert L[n - 1].startswith(startswith), (k, n, L[n - 1][:80])
    assert '\n' not in add
    L[n - 1] = L[n - 1] + add
    TXT[k] = '\n'.join(L)
    LOG.append((k, 'line %d' % n, fid, what))


def linsert(k, after, startswith, new, fid, what):
    L = TXT[k].split('\n')
    assert L[after - 1].startswith(startswith), (k, after, L[after - 1][:80])
    assert '\n' not in new
    L.insert(after, new)
    TXT[k] = '\n'.join(L)
    LOG.append((k, 'line %d (new)' % (after + 1), fid, what))


# ---------------------------------------------------------------- JSON helpers
J = json.loads(RAW['json'])
assert json.dumps(J, indent=1, ensure_ascii=False) == RAW['json'], 'v2.4c JSON does not round-trip'
assert J['version'] == 'v2.4c'
J0 = copy.deepcopy(J)
SUP = {}


def P(path):
    s = ''
    for i, k in enumerate(path):
        s += ('[%d]' % k) if isinstance(k, int) else (('.' if i else '') + k)
    return s


def getp(path):
    o = J
    for k in path:
        o = o[k]
    return o


def setp(path, val):
    getp(path[:-1])[path[-1]] = val


def _sup(path, fid):
    """Keep the v2.4c value (from the untouched copy J0), so a later edit of a sub-path cannot leak into the record."""
    ps = P(path)
    if ps not in SUP:
        o = J0
        for k in path:
            o = o[k]
        SUP[ps] = {'v': copy.deepcopy(o), 'replaced_by': [fid]}
    elif fid not in SUP[ps]['replaced_by']:
        SUP[ps]['replaced_by'].append(fid)


def jrep(path, old, new, fid, what):
    s = getp(path)
    assert isinstance(s, str), P(path)
    c = s.count(old)
    assert c == 1, (P(path), fid, c, old[:90])
    _sup(path, fid)
    setp(path, s.replace(old, new))
    LOG.append(('json', P(path), fid, what))


def jset(path, new, fid, what, old=None):
    cur = getp(path)
    assert not isinstance(cur, (dict, list)) or isinstance(new, type(cur)), P(path)
    if old is not None:
        assert cur == old, (P(path), cur)
    _sup(path, fid)
    setp(path, new)
    LOG.append(('json', P(path), fid, what))


def jadd(path, key, val, fid, what):
    o = getp(path)
    assert isinstance(o, dict) and key not in o, (P(path), key)
    o[key] = val
    LOG.append(('json', (P(path + [key]) if path else key) + ' (new)', fid, what))


def jappend(path, val, fid, what):
    o = getp(path)
    assert isinstance(o, list) and val not in o, P(path)
    _sup(path, fid)
    o.append(val)
    LOG.append(('json', P(path) + '[%d] (new)' % (len(o) - 1), fid, what))


D2, D3, D4, M259, T4 = 'LEAD 258 (2)', 'LEAD 258 (3)', 'LEAD 258 (4)', 'LEAD 259 (1)', 'N-07; gnc v3.2; LEAD 261'

# ---------------------------------------------------------------- (1) Z3 v2 and the J-FWD replace rule (258 (3))
FG = ['fa1_grid_statistics_v2p4c', 'v']
jset(FG + ['status'], ("CLOSED (LEAD 258 (3), go 2026-10-21T10:47:17Z): Z3 v2 ADOPTED = Z3' above as written plus the v1 window "
                       "(first-to-last crossing of 63.1 bar abs <= 3.0 ms) and rise (10-90 % first rise >= 0.8 ms) kept, Z3 "
                       "allowed only inside the light window; 896 / 896 grid cases inside [DERIVED on SIM; grid counts on an "
                       "ASSUMED construct]; NOT EVALUATED in flight; 253 (7)(i) stays adopted, its 256 (3) condition met; see "
                       "z3_jfwd_rulings_v2p4d"), D3, 'Z3 ruling: OPEN -> CLOSED',
     old=("OPEN: the lead rules on Z3' or Mechanical's alternative at Mechanical's pre-publication post; 253 (7)(i) stays "
          "adopted on that condition (256 (3))"))
jset(FG + ['owners'], ("Mechanical (LC-TB70 envelope v2, published: 04-fea/v352/lc_tb70_envelope_v2.json 7ebd2fd63dc878ef and "
                       "mechanical.json v2.4 lc_tb70_envelope_v352, with Z3 v2 and the J-FWD replace rule on Q_JFWD; CHANGELOG "
                       "259 (2)-(3)); Electronics v2.12 re-classifies the 10 S6R runs and the 29-33 N-04 burn-on cases against "
                       "Z3 v2 (mechanical.json requests_v352[4])"), D3, 'published owners',
     old=("Mechanical (LC-TB70 envelope v2: the restated Z3 and the joint-replacement rule); Electronics v2.12 re-classifies "
          "the 10 S6R runs and the 29-33 N-04 burn-on cases against it"))
_old = J0['fa1_grid_statistics_v2p4c']['v']['line_253_8_wording']
assert _old.endswith('(LEAD 256 (4), REV-COMB-4 R4-10)')
jset(FG + ['line_253_8_wording'], _old + ("; the rule ADOPTED by LEAD 258 (3) uses Q_JFWD = max(head peak, max S(T) over T "
                                          "0.2-0.5 ms), not the peak alone: 298 / 896 grid cases, 113 of them with a head peak "
                                          "of 49.781-60.0 bar abs [SIM grid counts, not rates] (z3_jfwd_rulings_v2p4d)"),
     D3, 'Q_JFWD rule added', old=_old)
jadd([], 'z3_jfwd_rulings_v2p4d', {
    'v': {
        'Z3_v2': {
            'decision': ("ADOPTED by LEAD 258 (3) at the go 2026-10-21T10:47:17Z: REV-COMB-4 Z3' as written (head peak <= 88.1 "
                         "bar abs AND undamped SDOF ESP <= 151.04 bar abs at each of the 406 published periods 0.02-50 ms, S "
                         "from rest at the record start) plus the v1 FA-1 class conditions kept (first-to-last crossing of 63.1 "
                         "bar abs <= 3.0 ms; 10-90 % first rise >= 0.8 ms); Z3 allowed only inside the light window (record "
                         "start to 150 ms after the first 8 bar abs crossing)"),
            'grid': ("896 / 896 grid cases inside (850 inside v1); ESP max 146.881 bar abs at 3.5 ms, margin 4.159 bar to FA1S "
                     "[DERIVED on SIM; grid counts on an ASSUMED construct, not probabilities]"),
            'flight': 'NOT EVALUATED in flight (1 kHz record; the LIGHT_SPIKE raw peak is a lower bound)',
            'not_adopted': ("shape limits (option 2: the smallest box that admits every grid case admits a trapezoid with ESP "
                            "163.71 bar abs, above FA1S), a raised FA1S (option 3; needs FE) and the damped ESP variant "
                            "(structural damping MISSING)"),
            'published_as': ("mechanical.json v2.4 (66bc53d88d444679) lc_tb70_envelope_v352.Z3_v2; 04-fea/v352/"
                             "lc_tb70_envelope_v2.json (7ebd2fd63dc878ef)")},
        'jfwd_replace_rule': {
            'decision': ("ADOPTED by LEAD 258 (3): Q_JFWD = max(head peak over the record, max of S(T) over T 0.2-0.5 ms on the "
                         "light window and each excursion window), not the peak alone; Q_JFWD > 60.0 bar abs at any time in a "
                         "run, no minimum duration, means the line-231 J-FWD inspection (C6 (2) list) and the TC-02 taps gauged "
                         "(M5-6H GO / NO-GO) before the next run"),
            'grid': ("298 / 896 grid cases against 185 for the peak alone; the 113 added cases have a head peak of 49.781-60.0 "
                     "bar abs (Q / peak in gauge up to 1.2989) [SIM grid counts on an ASSUMED construct, not rates]"),
            'why': ("Q_JFWD >= the peak by construction, so it keeps every flag of the 256 (4) peak rule; a false trigger "
                    "costs an inspection, a missed one is an unanalysed joint load"),
            'normal_lights': ("not meant for normal lights (REV-COMB-4 R4-10): a light to MEOP 45 bar abs trips it only below "
                              "a 0.288 ms 10-90 % rise [DERIVED]"),
            'measured_traces': ("on measured stand traces a noise-driven trigger still means the inspection until a "
                                "noise-floor rule is derived from a no-event B-DPC-1 record and reviewed (TO-VERIFY)"),
            'basis': ("Mechanical's rows at 60 bar abs, nominal factors: MS_y +0.328 (TC-01 ligament, LC2U) / MS_u +0.312 "
                      "(TC-01 ligament trend, 78.6 C) [CALC on SIM]"),
            'band': '0.2-0.5 ms J-FWD band ASSUMED (no v3.5.2 J-FWD modal in this package: TO-VERIFY)',
            'replaces': ("the v1 'any head excursion above 60.0 bar abs: replace all J-FWD screws' rule and the HW-101 '60 bar' "
                         "action (drawing texts v2 58683aa9a66a65dd; no hardware-data, BOM or geometry edit)"),
            'electronics': ("Q_JFWD logging and the inside_v2 re-classification of the S6R runs and the N-04 burn-on cases: "
                            "Electronics v2.12 (LEAD 258 (4))"),
            'published_as': 'mechanical.json v2.4 lc_tb70_envelope_v352.jfwd_replace_rule_v2'},
        'open_before_flight_acceptance': [
            'the flight consequence of a flagged first light (relight on a used joint; line 231 covers one Z3 event per assembly) (LEAD)',
            'the damped ESP variant (structural damping MISSING)',
            'the 0.2-0.5 ms J-FWD band (ASSUMED; TO-VERIFY on a v3.5.2 modal)',
            "a shutdown from a case hotter than the rows' soak basis (F4 observation; Mechanical, no limit derived)"],
        'combustion_side': ("no Combustion number changes: the FA-1 grid histories are the v2.4b set and fa1_grid_statistics_v2p4c "
                            "keeps the reviewer's statistics; T1-T4 adds no series-stop item (T-R2 already halts the series at "
                            "any Pc sample above 45 bar abs; the inspection after a Q_JFWD trigger is Mechanical's rule for "
                            "every run of a J-FWD joint)")},
    'tag': ('LEAD (rulings, CHANGELOG 258 (3)); DERIVED on SIM by Mechanical and REV-COMB-4 (grid counts on an ASSUMED '
            'construct); CALC on SIM (basis rows); nothing here is physical approval'),
    'src': ('CHANGELOG 258 (3), 259 (2)-(3); interfaces/mechanical.json v2.4 (66bc53d88d444679); '
            '04-fea/v352/lc_tb70_envelope_v2.json (7ebd2fd63dc878ef); reviews/REVIEW-COMBUSTION-R4.md R4-02, R4-10')},
    D3, 'Z3 v2 and the Q_JFWD rule')
EL = ['electronics_open_issues_v2p4c', 'v', 'routed_to_electronics_v2p12']
jrep(EL + [3], 'against the restated Z3', 'against Z3 v2 (inside_v2; LEAD 258 (3); mechanical.json requests_v352[4])',
     D3, 'Z3 v2 named')
jappend(EL, ('LEAD 258 (2): the (d) re-set takes the upper 95 % bound of the measured N2O Cd x A (d1); CF-4 shows the 283.15 K '
             'need at the re-set flow (d2)'), D2, 'routed (d1) / (d2)')
jappend(EL, ('LEAD 258 (3)-(4): Q_JFWD logging (the head peak and max S(T) over T 0.2-0.5 ms on the light window and each '
             'excursion window; > 60.0 bar abs at any time means the line-231 J-FWD inspection before the next run; '
             'mechanical.json jfwd_replace_rule_v2)'), D4, 'routed Q_JFWD logging')

# ---------------------------------------------------------------- (2) purge (d1) / (d2) (258 (2))
PD = ['purge_decision_v2p4c', 'v']
jadd(PD, 'conditions_LEAD_258_2', {
    'd1': ('the (d) re-set takes the upper 95 % bound of the measured N2O Cd x A of the two-tap path, not its mean: at the '
           'Cd 0.80 ratio r 1.1326 a ratio measured 7.9 % low gives a true vent of 81.99 g, just under the 82.1 g first fail '
           'of the A1 reserve test'),
    'd2': ('CF-4 shows the 283.15 K need at the re-set flow (need and limit both scale with 1 / (Cd x A), ASSUMED); below a '
           'ratio r of 1 condition (b) governs'),
    'basis': ('REV-GNC-7 RV7-04 (reviews/REVIEW-GNC-R5.md 6b86fcd326568646, review section 5 (ii)): vent at the cap <= 75.99 g '
              'for r 1.0-2.0; 283.15 K margin 0.178-0.23 s for r 1.0-1.3, 0.10-0.18 s with FD-01 [DERIVED; the 1 / (Cd x A) '
              'need scaling ASSUMED]'),
    'status': 'DECIDED by LEAD 258 (2); condition (d) of 257 (2) holds'}, D2, 'conditions (d1) / (d2)')
jset(PD + ['CF4'], ("CF-4 v2.3 (v2.4d) runs the decided flow, adds a run at or below 283.15 K or states the cold corner "
                    "model-only, checks the Cd x A acceptance in P5, records the measured Cd x A that re-sets the flow and cap "
                    "(d), takes the re-set from its upper 95 % bound (d1) and shows the 283.15 K need at the re-set flow (d2) "
                    "(LEAD 258 (2))"), D2, 'CF-4 v2.3 with (d1) / (d2)',
     old=("CF-4 v2.2 runs the decided flow, adds a run at or below 283.15 K or states the cold corner model-only, checks the "
          "Cd x A acceptance in P5 and records the measured Cd x A that re-sets the flow and cap (d)"))
jrep(PD + ['electronics'], 're-set by (d), never above these values',
     're-set by (d) with (d1) / (d2) (LEAD 258 (2)), never above these values', D2, '(d1) / (d2)')
jrep(['purge_decision_v2p4c', 'src'], 'REV-GNC-7 interim 2 (the review file follows)',
     'REV-GNC-7 interim 2 and its final, reviews/REVIEW-GNC-R5.md (6b86fcd326568646; RV7-04); CHANGELOG 258 (2)',
     D2, 'review file cited')

# ---------------------------------------------------------------- (3) torch-port wall row (259 (1); wording 258 (4))
PT = ['fa1_p_torch_v2p4c', 'v']
jset(PT + ['mechanical_row'], (
    "tap-wall v3, published (04-fea/v352/jfwd_tapwall_v352_v3.json ef70572ec92b05b0; CHANGELOG 259 (1)), at P_torch = FA1S "
    "151.04 bar abs uniform over the passage, DLF 1.0, 3750 N J-F1 cap, wall 1.6355 mm net at +/-0.25 deg: governing row "
    "SOAK52 (TC-02 thread 94.9 C): sigma 136.9 MPa, MS_y +0.670 / MS_u +0.785; screw-temperature sensitivity MS_y +0.294 at "
    "SOAK52 and +0.275 at SOAK70 (158.6 C); 0 flags; Lame factor 2.2094 [CALC on SIM]; ligament lowest local natural "
    "frequency >= 26 kHz against <= 3.45 kHz in the passage [CALC; edges and span ASSUMED; not an FE modal]; R4-01 CLOSED by "
    "the publication; LEAD 258 (4) corrects the v2.4c wording, which called the SOAK70 sensitivity governing (same numbers); "
    "v1 (P_torch 102 bar abs, MS_y +0.814) superseded"), D4, 'tap wall v3: governing row SOAK52')
_old = J0['fa1_p_torch_v2p4c']['src']
jset(['fa1_p_torch_v2p4c', 'src'], _old + '; Mechanical row: 04-fea/v352/jfwd_tapwall_v352_v3.json (ef70572ec92b05b0; CHANGELOG 259 (1))',
     M259, 'tap wall v3 cited', old=_old)

# ---------------------------------------------------------------- (4) T4 (N-07 answered in gnc.json v3.2; LEAD 261)
TN = ['t4_duration_note_v2p4c']
jset(TN + ['v', 'status'], (
    "CONFIRMED by GNC in gnc.json v3.2 (bde317782574cbd9; duty_cycles.note_n07_rev_gnc_7; published in CHANGELOG 260): no "
    "GNC objective needs the DC-D duty as one firing; GNC's static-fire objectives need DC-D segments, each flown as its own "
    "segment or firing inside the A = 150 C case limit (REV-ELEC-3 N-07: the DC-D first burn would cross it at about 23.5 s, "
    "merged bound [DERIVED]); the A1-like relight objective sits with the shortest T4 firing. T4 is re-sized to that firing "
    "(LEAD 261): planning value about 2.0 kg of N2O [ESTIMATE]; the T4 rows of T1-T4 v3.2 lines 61, 143-145 and 171 stay the "
    "DC-D computation [SIM] until Combustion re-runs them on the re-sized profile (OPEN)"), T4, 'confirmed; T4 re-sized',
    old='GNC (REV-GNC-7) confirms the T4 profile; 7.02 kg stays the planning value until then (T1-T4 v3.1 line 294)')
_old = J0['t4_duration_note_v2p4c']['tag']
jset(TN + ['tag'], _old + '; confirmation DERIVED by GNC (gnc.json v3.2); re-size LEAD 261', T4, 'tags', old=_old)
_old = J0['t4_duration_note_v2p4c']['src']
jset(TN + ['src'], _old + ('; interfaces/gnc.json v3.2 duty_cycles.note_n07_rev_gnc_7; reviews/REVIEW-ELECTRONICS-R3.md N-07 '
                           '(fcf05f8bc7382cd1)'), T4, 'sources', old=_old)

# ---------------------------------------------------------------- (5) lead decisions folded
jadd([], 'lead_decisions_folded_v2p4d', {
    'v': {
        '258 (2)': ('purge condition (d) holds; (d1) the re-set takes the upper 95 % bound of the measured N2O Cd x A; (d2) '
                    'CF-4 shows the 283.15 K need at the re-set flow; below a Cd x A ratio of 1 condition (b) governs'),
        '258 (3) Z3': ("Z3 v2 ADOPTED (REV-COMB-4 Z3' plus the v1 window and rise; light window only); NOT EVALUATED in "
                       "flight; options 2 and 3 and the damped variant not adopted"),
        '258 (3) J-FWD': ('replace rule on Q_JFWD (> 60.0 bar abs at any time in a run: the line-231 inspection and the TC-02 '
                          'taps gauged before the next run), not the peak alone; a noise-floor rule for measured stand traces '
                          'TO-VERIFY'),
        '258 (3) open': ('before flight acceptance (LEAD): the flight consequence of a flagged first light; the damped ESP '
                         'variant; the 0.2-0.5 ms J-FWD band; a shutdown from a case hotter than the soak basis (Mechanical)'),
        '258 (4)': ('combustion v2.4d corrects the fa1_p_torch_v2p4c mechanical_row wording (governing SOAK52; SOAK70 is the '
                    'screw-temperature sensitivity); Q_JFWD logging, the inside_v2 re-classification and the F4 PC_SENSOR '
                    'HIGH abort go to Electronics v2.12'),
        '259': ('Mechanical J-FWD follow-ups published: tap wall v3 (R4-01 closed), LC-TB70 envelope v2, mechanical.json v2.4 '
                '66bc53d88d444679'),
        '260': ('gnc.json v3.2 published (bde317782574cbd9); its N-07 note answers the T4 question (t4_duration_note_v2p4c)'),
        '261': ('T4 re-sized to the shortest firing on the N-07 answer (about 2.0 kg of N2O, ESTIMATE); the T4 rows re-run is '
                'OPEN (Combustion)')},
    'tag': 'LEAD (CHANGELOG)', 'src': 'CHANGELOG lines 258-261'}, 'v2.4d', 'lead decisions folded')

# ---------------------------------------------------------------- markdown: CF-4 v2.3
mrep('cf4', 'Version 2.2 (Combustion v2.4c), 2026-10-21: text corrections',
     ('Version 2.3 (Combustion v2.4d), 2026-10-21: LEAD line 258 (2) folded by the lead: purge conditions (d1) and (d2) in '
      'P5 (line 102) and §10 (line 179); the v2.3 changes are listed in §14 at the end; the edits are in place, so lines '
      '1-204 keep their v2.2 numbers. v2.2 (`4e36be703a9e7d44`) is archived as `02-combustion/superseded/v2p4c/CF-4-SPEC.md`. '
      'The v2.2 header follows unchanged. Version 2.2 (Combustion v2.4c), 2026-10-21: text corrections'),
     'v2.4d', 'version header v2.3', line=3)
mrep('cf4', "(vent <= 82 g, inside GNC's A1 reserve test) (LEAD 257 (2); REV-GNC-7) |",
     ("(vent <= 82 g, inside GNC's A1 reserve test) (LEAD 257 (2); REV-GNC-7). v2.3 (LEAD 258 (2); REV-GNC-7 RV7-04): (d1) "
      "the re-set takes the upper 95 % bound of the measured N2O Cd x A, not its mean (at the Cd 0.80 ratio 1.1326 a ratio "
      "measured 7.9 % low would give a true vent of 81.99 g, just under the 82.1 g first fail of the A1 reserve test); (d2) "
      "the run report shows the 283.15 K need at the re-set flow (the need scaled by 1 / (Cd x A), ASSUMED); below a ratio "
      "of 1 the (b) acceptance governs |"), D2, '(d1) / (d2) in P5', line=102)
lappend('cf4', 179, 'Raw logs (all channels',
        (' v2.3 (LEAD 258 (2)): with the measured Cd x A of the two-tap path, Combustion reports its upper 95 % bound (d1) '
         'and the 283.15 K need at the re-set flow (d2).'), D2, '(d1) / (d2) data')
assert TXT['cf4'].endswith('No test has been run; this specification approves nothing.\n')
SEC14 = """## 14. v2.3 changes (Combustion v2.4d, 2026-10-21)

LEAD line 258 (2) on REV-GNC-7 RV7-04 (`reviews/REVIEW-GNC-R5.md`, `6b86fcd326568646`). The edits are in place, so lines 1-204 keep their v2.2 numbers.
- Line 3: version header v2.3.
- P5 (line 102): (d1) the re-set takes the upper 95 % bound of the measured N2O Cd x A; (d2) the run report shows the 283.15 K need at the re-set flow; below a Cd x A ratio of 1 the (b) acceptance governs.
- §10 (line 179): Combustion reports the upper 95 % bound of the measured Cd x A and the 283.15 K need at the re-set flow.

No test has been run; this specification approves nothing.
"""
TXT['cf4'] = TXT['cf4'] + '\n' + SEC14
LOG.append(('cf4', 'section 14 (new, at the end)', 'v2.4d', 'v2.3 change list'))

# ---------------------------------------------------------------- markdown: T1-T4 v3.2
mrep('t1t4', 'law form (RG-03), v3.1', 'law form (RG-03), v3.2', 'v2.4d', 'title v3.2', line=1)
mrep('t1t4', 'v3.1 (Combustion v2.4c), 2026-10-21: text corrections',
     ("v3.2 (Combustion v2.4d), 2026-10-21: the T4 note on line 294 updated by the lead for GNC's N-07 answer in "
      "`interfaces/gnc.json` v3.2 (`bde317782574cbd9`), with T4 re-sized to the shortest firing (LEAD 261), and a pointer on "
      "line 61; the edits are in place, so the line numbers are kept; v3.1 (`b00b2d852ed3475c`) is archived as "
      "`02-combustion/superseded/v2p4c/T1-T4-REGRESSION-SPEC.md`. The v3.1 header follows unchanged. "
      "v3.1 (Combustion v2.4c), 2026-10-21: text corrections"), 'v2.4d', 'version header v3.2', line=3)
mrep('t1t4', '| T4, DC-D duty cycle (S230 grain, 3 starts) |', '| T4, DC-D duty cycle (S230 grain, 3 starts; v3.2: re-sized, line 294) |',
     T4, 'pointer to the re-size', line=61)
mrep('t1t4', 'GNC (REV-GNC-7) confirms the profile; 7.02 kg stays the planning value until then.',
     ("v3.2 note (lead, Combustion v2.4d): GNC confirms it (`interfaces/gnc.json` v3.2 `bde317782574cbd9`, "
      "duty_cycles.note_n07_rev_gnc_7): no GNC objective needs the DC-D duty as one firing; GNC's static-fire objectives need "
      "DC-D segments, each flown as its own segment or firing inside the A = 150 C case limit (REV-ELEC-3 N-07: the DC-D first "
      "burn would cross that limit at about 23.5 s, merged bound [DERIVED]); the A1-like relight objective sits with the "
      "shortest firing above. T4 is therefore re-sized to that firing (LEAD 261): planning value about 2.0 kg of N2O "
      "[ESTIMATE]; 7.02 kg is the record of the DC-D sequence. The T4 rows of lines 61, 143-145 and 171 stay the DC-D "
      "computation [SIM] until Combustion re-runs them on the re-sized profile (OPEN)."), T4, 'T4 confirmed and re-sized', line=294)

# ---------------------------------------------------------------- markdown: DATASHEET-INPUTS v2.4d
mrep('ds', 'Version v2.4c, 2026-10-21. Owner:',
     ("Version v2.4d, 2026-10-21: the lead's fold of CHANGELOG lines 258-259 (`02-combustion/src/apply_v2p4d_lead.py`): "
      "purge conditions (d1) / (d2) in the purge row, the published torch-port wall row in the FA-1 gas-filled passages row, "
      "a new row for Z3 v2 and the J-FWD replace rule, and the open-items note. Values as in `interfaces/combustion.json` "
      "v2.4d. v2.4c (`29ed6d45c55ff234`) is archived as `02-combustion/superseded/v2p4c/DATASHEET-INPUTS-COMBUSTION.md`. The "
      "v2.4c header follows unchanged. Version v2.4c, 2026-10-21. Owner:"), 'v2.4d', 'version header v2.4d', line=3)
mrep('ds', 'so the 297.15 K vent stays <= 76 g; at Cd 0.80 the fixed schedule',
     ('so the 297.15 K vent stays <= 76 g; (258 (2)): (d1) the re-set takes the upper 95 % bound of the measured N2O Cd x A; '
      '(d2) CF-4 shows the 283.15 K need at the re-set flow; at Cd 0.80 the fixed schedule'), D2, 'purge row (d1) / (d2)')
mrep('ds', 'CHANGELOG 257 (2) |', 'CHANGELOG 257 (2), 258 (2); `reviews/REVIEW-GNC-R5.md` (`6b86fcd326568646`) |', D2,
     'purge row sources')
mrep('ds', ("Mechanical's tap-wall row at FA1S passes (worst MS_y +0.275, SOAK70 [CALC on SIM]; published with Mechanical's "
            "next CHANGELOG line)"),
     ("Mechanical's tap-wall row v3 at FA1S passes: governing SOAK52 MS_y +0.670 / MS_u +0.785; screw-temperature sensitivity "
      "MS_y +0.275 at SOAK70 [CALC on SIM]; ligament lowest local natural frequency >= 26 kHz [CALC, edges and span ASSUMED]; "
      "R4-01 closed (CHANGELOG 259 (1); wording LEAD 258 (4))"), D4, 'tap wall v3: governing row SOAK52')
mrep('ds', '`r4_pc_port_face.json` (`94f5a39166a8f778`) |',
     '`r4_pc_port_face.json` (`94f5a39166a8f778`); `04-fea/v352/jfwd_tapwall_v352_v3.json` (`ef70572ec92b05b0`) |', M259,
     'tap wall v3 cited')
_dl = TXT['ds'].split('\n')
_n19 = [i + 1 for i, s in enumerate(_dl) if s.startswith('| FA-1 in gas-filled passages (P_torch passage, Pc port) |')]
assert len(_n19) == 1
linsert('ds', _n19[0], '| FA-1 in gas-filled passages', (
    "| FA-1 class Z3 v2 and the J-FWD replace rule | Z3 v2: 63.1 < head <= 88.1 bar abs inside the light window, with the "
    "undamped SDOF ESP of the head history <= 151.04 bar abs (FA1S) at each of the 406 periods 0.02-50 ms, first-to-last "
    "crossing of 63.1 bar abs <= 3.0 ms and 10-90 % first rise >= 0.8 ms: 896 / 896 FA-1 grid cases inside (ESP max 146.881 "
    "bar abs at 3.5 ms, margin 4.159 bar); replace rule: Q_JFWD = max(head peak, head ESP at 0.2-0.5 ms) > 60.0 bar abs at "
    "any time in a run means the line-231 J-FWD inspection and the TC-02 taps gauged before the next run (298 / 896 grid "
    "cases; 185 for the peak alone) | grid counts on an ASSUMED construct, not rates; Z3 v2 NOT EVALUATED in flight (1 kHz "
    "record); not meant for normal lights (a light to MEOP trips Q_JFWD only below a 0.288 ms 10-90 % rise); a noise-floor "
    "rule for measured stand traces TO-VERIFY; the 0.2-0.5 ms band ASSUMED (TO-VERIFY on a v3.5.2 modal); damped variant not "
    "adopted (damping MISSING) | LEAD (258 (3)); DERIVED on SIM (Mechanical; REV-COMB-4) | `interfaces/mechanical.json` v2.4 "
    "(`66bc53d88d444679`) `lc_tb70_envelope_v352`; `04-fea/v352/lc_tb70_envelope_v2.json` (`7ebd2fd63dc878ef`); "
    "`combustion.json` `z3_jfwd_rulings_v2p4d`; CHANGELOG 258 (3), 259 (2)-(3) |"), D3, 'row added: Z3 v2 and the J-FWD replace rule')
mrep('ds', 'Open: the Z3 restatement of the LC-TB70 envelope (Mechanical; REV-COMB-4 R4-02); the PURGE command time (Electronics v2.12).',
     ("Z3 v2 and the J-FWD replace rule on Q_JFWD are ADOPTED (LEAD 258 (3); table row 'FA-1 class Z3 v2 and the J-FWD "
      "replace rule'). Open: the PURGE command time "
      '(Electronics v2.12); before flight acceptance (LEAD): the flight consequence of a flagged first light, the damped ESP '
      'variant and the 0.2-0.5 ms J-FWD band.'), D3, 'open-items note')

# ---------------------------------------------------------------- write CF-4, T1-T4, DATASHEET; then the JSON
OUT = {}
for k in ('cf4', 't1t4', 'ds'):
    b = TXT[k].encode('utf-8')
    open(os.path.join(stage, OUTNAME[k]), 'wb').write(b)
    OUT[k] = sha16(b)

jset(['cf4_gate', 'spec_version'], 'CF-4-SPEC v2.3 (v2.4d, %s)' % OUT['cf4'], 'v2.4d', 'CF-4 v2.3',
     old='CF-4-SPEC v2.2 (v2.4c, 4e36be703a9e7d44)')
jadd(['files'], 'v2p4d', {
    'v': {'report': '02-combustion/REPORT.md v2.4d (section 18 lists every change)',
          'response': '02-combustion/REVISION-RESPONSE-R3.md unchanged (370875c3645eb49c)',
          'specs': {'02-combustion/T1-T4-REGRESSION-SPEC.md': {'version': 'v3.2 (v2.4d)', 'sha256_16': OUT['t1t4']},
                    '02-combustion/CF-4-SPEC.md': {'version': 'v2.3 (v2.4d)', 'sha256_16': OUT['cf4']}},
          'datasheet_inputs': '02-combustion/DATASHEET-INPUTS-COMBUSTION.md v2.4d (%s)' % OUT['ds'],
          'writer': '02-combustion/src/apply_v2p4d_lead.py (lead; sha256/16 %s)' % SELF,
          'archive_v2p4c': ('02-combustion/superseded/v2p4c/ (combustion.json, REPORT, CF-4, T1-T4, DATASHEET-INPUTS; '
                            'HASHES.txt)'),
          'sources': dict(REFS, **{'interfaces/CHANGELOG.md line 258 (with its newline)': CL_LINES[258],
                                   'line 259': CL_LINES[259], 'line 260': CL_LINES[260]})},
    'tag': 'index'}, 'v2.4d', 'file index v2.4d')
jadd([], 'datasheet_inputs_v2p4d', {
    'v': {'file': '02-combustion/DATASHEET-INPUTS-COMBUSTION.md', 'version': 'v2.4d', 'sha256_16': OUT['ds'],
          'builder': '02-combustion/src/apply_v2p4d_lead.py (lead edit of the v2.4c file 29ed6d45c55ff234)',
          'changes': ('LEAD 258 (2) purge row; 258 (3) row added (Z3 v2 and the J-FWD replace rule) and the open-items note; '
                      '259 (1) / 258 (4) the FA-1 gas-filled passages row')},
    'tag': 'index (each row carries its own tag)', 'src': 'REPORT v2.4d section 18'}, 'v2.4d', 'datasheet index v2.4d')

NOTE = ("v2.4d (2026-10-21, lead): text-only fold of CHANGELOG lines 258 (2)-(4), 259 and 260 (REV-GNC-7 final "
        "reviews/REVIEW-GNC-R5.md 6b86fcd326568646; Mechanical's J-FWD follow-ups, mechanical.json v2.4 66bc53d88d444679; "
        "gnc.json v3.2 bde317782574cbd9), applied by 02-combustion/src/apply_v2p4d_lead.py; no model run and no SIM, CEA or "
        "FE result changed; one planning value changed (T4 N2O about 2.0 kg, ESTIMATE, against the 7.02 kg DC-D record; "
        "LEAD 261). Every replaced leaf is kept in superseded_v2p4d with its decision; new blocks z3_jfwd_rulings_v2p4d, "
        "lead_decisions_folded_v2p4d, datasheet_inputs_v2p4d, edit_log_v2p4d, files.v2p4d and "
        "purge_decision_v2p4c.v.conditions_LEAD_258_2. All v2.4c keys kept.")
STATUS = ("v2.4d REVISION (digital only), 2026-10-21: the lead's text-only fold of CHANGELOG lines 258-260 on the v2.4c fold "
          "of REV-COMB-4 (line 256). Design point unchanged. No number is MEASURED. The relight claim is gated by CF-4; FA-1 "
          "is accepted for design continuation only. Folded in v2.4c: OI-41 DECIDED (230 (2) band values 94 / 121 / 147 / 94 "
          "bar abs; FA1S 151.04 bar abs bounds every period and is the design case for gas-filled passages, 230 (1), R4-01); "
          "flight Pc proof >= 166.14 bar abs (249 (4)); purge FINAL: 2.43 s scheduled flow with the 2.39 s both-open cap and "
          "conditions (a)-(d) (253 (7)(ii), 256 (2), 257 (2)); pcf_tmax 0.8 s (227 (5)); closure deadline = torch gate E0 + "
          "0.16 s (Electronics v4); case-TC relight limit 403.15 K (249 (4)). Folded in v2.4d: Z3 v2 ADOPTED and the J-FWD "
          "replace rule on Q_JFWD (258 (3); z3_jfwd_rulings_v2p4d); purge (d1) the re-set from the upper 95 % bound of the "
          "measured Cd x A and (d2) the 283.15 K need shown at the re-set flow (258 (2)); the torch-port wall row published, "
          "R4-01 CLOSED (259 (1), 258 (4)); T4 re-sized to the shortest firing on GNC's N-07 answer (gnc.json v3.2; LEAD "
          "261). Open: the PURGE command time and Q_JFWD logging (Electronics v2.12); the T4 rows re-run (Combustion); "
          "before flight acceptance (LEAD): the flight consequence of a flagged first light, the damped ESP variant, the "
          "0.2-0.5 ms J-FWD band; OI-49 to OI-52. A1 apogee target 210 m DECIDED; tank 2.00 kg. Nothing here is physical "
          "approval.")
jset(['version'], 'v2.4d', 'v2.4d', 'version', old='v2.4c')
assert J['date'] == '2026-10-21'
jset(['revision_note'], NOTE, 'v2.4d', 'revision note')
J['revision_history'].append(J0['revision_note'])
LOG.append(('json', 'revision_history[%d] (new)' % (len(J['revision_history']) - 1), 'v2.4d', 'v2.4c revision note kept'))
jset(['status'], STATUS, 'v2.4d', 'status')
jset(['supersedes'], ("combustion.json v2.4c (661db0a593462382), kept as 02-combustion/superseded/v2p4c/combustion.json; v2.4b "
                      "(fd3a7da6d27c7c66) as 02-combustion/superseded/v2p4b/combustion.json; v2.4a (5237d4584bad38c4) as "
                      "before (02-combustion/data/v2/combustion_interface_v2p4a_as_published.json and "
                      "02-combustion/superseded/v2p4a/combustion.json)"), 'v2.4d', 'supersedes')
J['superseded_v2p4d'] = {'v': SUP, 'version': 'v2.4c', 'superseded_by': 'v2.4d (2026-10-21)',
                         'tag': 'history: every leaf replaced in v2.4d, keyed by its path, with the decision that replaced it'}
J['edit_log_v2p4d'] = {
    'v': [{'file': OUTNAME[k] if k != 'json' else 'combustion.json', 'where': w, 'by': f, 'what': t} for k, w, f, t in LOG],
    'script': '02-combustion/src/apply_v2p4d_lead.py', 'script_sha256_16': SELF, 'stamp_utc': stamp,
    'inputs_sha256_16': dict({SRC[k][0]: SRC[k][1] for k in SRC}, **UNCHANGED),
    'outputs_sha256_16': {SRC[k][0]: OUT[k] for k in OUT},
    'note': 'the REPORT rows of section 18 are added after this file is written; REPORT cites this file by sha',
    'tag': 'index'}


# every v2.4c key path is kept
def keypaths(o, p=()):
    if isinstance(o, dict):
        for kk, v in o.items():
            yield p + (kk,)
            yield from keypaths(v, p + (kk,))
    elif isinstance(o, list):
        for n, v in enumerate(o):
            yield from keypaths(v, p + (n,))


def has(o, p):
    for kk in p:
        if isinstance(o, dict):
            if kk not in o:
                return False
        elif isinstance(o, list):
            if not isinstance(kk, int) or kk >= len(o):
                return False
        else:
            return False
        o = o[kk]
    return True


missing = [p for p in keypaths(J0) if not has(J, p)]
assert not missing, missing[:5]
jb = json.dumps(J, indent=1, ensure_ascii=False).encode('utf-8')
open(os.path.join(stage, 'combustion.json'), 'wb').write(jb)
OUT['json'] = sha16(jb)

# ---------------------------------------------------------------- REPORT: header, in-place notes, section 18
mrep('report', 'Version 2.4c, 2026-10-21: text-only corrections',
     ("Version 2.4d, 2026-10-21: the lead's text-only fold of CHANGELOG lines 258-260 (Z3 v2 and the J-FWD replace rule on "
      "Q_JFWD; purge conditions (d1) / (d2); the published torch-port wall row, which closes R4-01; GNC's T4 answer in "
      "gnc.json v3.2, with T4 re-sized); no model was re-run. Interface: `interfaces/combustion.json` v2.4d (sha256/16 "
      "`%s`). Every change is listed in §18. All edits above §18 are in place, so lines 1-3314 keep their v2.4c numbers. "
      "v2.4c of this report (`7a9acd3df5937303`) and of the interface (`661db0a593462382`) are archived in "
      "`02-combustion/superseded/v2p4c/`. The v2.4c header follows unchanged. Version 2.4c, 2026-10-21: text-only "
      "corrections") % OUT['json'], 'v2.4d', 'version header v2.4d', line=3)
mrep('report', '| T4 | Duty cycle with coasts and relights (DC-D: 3 starts, grain split into 3 loads; DC-C into 2) |',
     ('| T4 | Duty cycle with coasts and relights (DC-D: 3 starts, grain split into 3 loads; DC-C into 2; v2.4d: re-sized to '
      'the shortest firing, T1-T4 v3.2 line 294) |'), T4, 'T4 pointer', line=2374)
lappend('report', 3178, '- **P_torch.**',
        (' v2.4d (§18): published as tap wall v3 (CHANGELOG 259 (1); `04-fea/v352/jfwd_tapwall_v352_v3.json`, '
         '`ef70572ec92b05b0`); the governing row is SOAK52, MS_y +0.670 / MS_u +0.785, and +0.275 at SOAK70 is the '
         'screw-temperature sensitivity (LEAD 258 (4)); R4-01 is CLOSED.'), D4, 'note: tap wall v3')
lappend('report', 3180, '- **Z3 (OPEN, Mechanical).**',
        (" v2.4d (§18): CLOSED by LEAD 258 (3): Z3 v2 ADOPTED (Z3' plus the v1 window and rise; 896 / 896 grid cases inside; "
         "NOT EVALUATED in flight); the J-FWD replace rule uses Q_JFWD (298 / 896)."), D3, 'note: Z3 closed')
lappend('report', 3313, '- Open: the Z3 restatement',
        (' v2.4d (§18): the Z3 restatement is closed (258 (3)); N-07 is answered by GNC in gnc.json v3.2 and T4 is re-sized '
         '(T1-T4 v3.2 line 294); (d1) / (d2) are added to the CF-4 re-set (258 (2)).'), 'v2.4d', 'note: open items')
FNAME = {'json': 'interfaces/combustion.json', 'report': 'REPORT.md', 'cf4': 'CF-4-SPEC.md', 't1t4': 'T1-T4-REGRESSION-SPEC.md',
         'ds': 'DATASHEET-INPUTS-COMBUSTION.md'}
rows = []
for k, w, f, t in LOG:
    cell = lambda s: s.replace('|', '/').replace('`', '')
    rows.append('| %s | %s | %s | %s |' % (FNAME[k], cell(w), cell(f), cell(t)))
SEC18 = """## 18. v2.4d: LEAD lines 258-260 folded (2026-10-21)

Applied by the lead with `src/apply_v2p4d_lead.py` (sha256/16 `{self}`, run at {stamp} from date -u). Text only: no model was re-run and no SIM, CEA or FE result changed; one planning value changed (the T4 N2O, §18.1). Sources: CHANGELOG lines 258 (2)-(4), 259 and 260; `reviews/REVIEW-GNC-R5.md` (`6b86fcd326568646`; REV-GNC-7, RV7-04); `interfaces/mechanical.json` v2.4 (`66bc53d88d444679`); `04-fea/v352/lc_tb70_envelope_v2.json` (`7ebd2fd63dc878ef`); `04-fea/v352/jfwd_tapwall_v352_v3.json` (`ef70572ec92b05b0`); `interfaces/gnc.json` v3.2 (`bde317782574cbd9`); `reviews/REVIEW-ELECTRONICS-R3.md` N-07 (`fcf05f8bc7382cd1`). Files after this revision: `interfaces/combustion.json` v2.4d (`{json}`), CF-4-SPEC v2.3 (`{cf4}`), T1-T4 v3.2 (`{t1t4}`), DATASHEET-INPUTS-COMBUSTION v2.4d (`{ds}`); REVISION-RESPONSE-R3 is unchanged (`370875c3645eb49c`). The v2.4c set is archived in `02-combustion/superseded/v2p4c/` with HASHES.txt.

### 18.1 Decisions folded

- **Z3 v2 (258 (3)).** ADOPTED as proposed: REV-COMB-4 Z3' as written (head peak <= 88.1 bar abs AND undamped SDOF ESP <= 151.04 bar abs at each of the 406 published periods 0.02-50 ms, from rest at the record start) with the v1 FA-1 class conditions kept (first-to-last crossing of 63.1 bar abs <= 3.0 ms; 10-90 % first rise >= 0.8 ms); Z3 is allowed only inside the light window (record start to 150 ms after the first 8 bar abs crossing). 896 / 896 grid cases are inside (850 inside v1); ESP max 146.881 bar abs at 3.5 ms, margin 4.159 bar [DERIVED on SIM; grid counts on an ASSUMED construct]. NOT EVALUATED in flight (1 kHz record; the LIGHT_SPIKE raw peak is a lower bound). Shape limits (option 2), a raised FA1S (option 3) and the damped variant are not adopted. `z3_jfwd_rulings_v2p4d`.
- **J-FWD replace rule (258 (3)).** Q_JFWD = max(head peak over the record, max S(T) over T 0.2-0.5 ms on the light window and each excursion window). Q_JFWD > 60.0 bar abs at any time in a run, no minimum duration, means the line-231 J-FWD inspection (C6 (2) list) and the TC-02 taps gauged (M5-6H GO / NO-GO) before the next run. Grid: 298 / 896 against 185 for the peak alone; the 113 added cases have a head peak of 49.781-60.0 bar abs (Q / peak in gauge up to 1.2989) [SIM grid counts, not rates]. Not meant for normal lights: a light to MEOP 45 bar abs trips it only below a 0.288 ms 10-90 % rise [DERIVED]. On measured stand traces a noise-driven trigger still means the inspection until a noise-floor rule is derived from a no-event B-DPC-1 record and reviewed (TO-VERIFY). It replaces Mechanical's v1 rule (any head excursion above 60.0 bar abs).
- **Purge (d1) / (d2) (258 (2)).** Condition (d) of 257 (2) holds (REV-GNC-7 RV7-04: vent at the cap <= 75.99 g for a Cd x A ratio r of 1.0-2.0; 283.15 K margin 0.178-0.23 s for r 1.0-1.3, 0.10-0.18 s with FD-01 [DERIVED; the 1 / (Cd x A) need scaling ASSUMED]). (d1): the re-set takes the upper 95 % bound of the measured N2O Cd x A (at r 1.1326 a ratio measured 7.9 % low gives a true vent of 81.99 g, just under the 82.1 g first fail). (d2): CF-4 shows the 283.15 K need at the re-set flow. Below r 1, condition (b) governs. CF-4 P5 and §10; `purge_decision_v2p4c.v.conditions_LEAD_258_2`.
- **Torch-port wall (259 (1); wording 258 (4)).** Mechanical published tap wall v3 at FA1S 151.04 bar abs uniform over the passage (DLF 1.0): governing row SOAK52 (TC-02 thread 94.9 C), sigma 136.9 MPa, MS_y +0.670 / MS_u +0.785; screw-temperature sensitivity MS_y +0.294 (SOAK52) and +0.275 (SOAK70, 158.6 C); 0 flags [CALC on SIM]; ligament lowest local natural frequency >= 26 kHz against <= 3.45 kHz in the passage [CALC; edges and span ASSUMED; not an FE modal]. R4-01 is CLOSED. The v2.4c wording, which called the SOAK70 sensitivity governing, is corrected (same numbers).
- **T4 (N-07; gnc.json v3.2; LEAD 261).** GNC confirms the N-07 profile: no GNC objective needs the DC-D duty as one firing; GNC's static-fire objectives need DC-D segments, each flown as its own segment or firing inside the A = 150 C case limit (REV-ELEC-3 N-07: the DC-D first burn would cross it at about 23.5 s, merged bound [DERIVED]); the A1-like relight objective sits with the shortest T4 firing. T4 is re-sized to that firing: burn 1 on the B1 p99 profile (21.76 s; 23.58 s if the life rule is sized on max), a coast of about 19 s and one relight of about 4.6 s at about 0.47 throttle, about 2.0 kg of N2O [ESTIMATE] against the 7.02 kg of the DC-D record. The T4 rows of T1-T4 lines 61, 143-145 and 171 stay the DC-D computation [SIM] until Combustion re-runs them on the re-sized profile (OPEN).

### 18.2 Changes, by file

| File | Where | Decision | Change |
|---|---|---|---|
{rows}
| REPORT.md | section 18 (new, at the end) | v2.4d | this section |

### 18.3 Not changed, and open

- No Combustion number changed except the T4 planning value; the FA-1 grid histories are the v2.4b set and the reviewer's statistics in `fa1_grid_statistics_v2p4c` are kept.
- §1-§17 keep their text except the in-place v2.4d notes listed in §18.2; REVISION-RESPONSE-R3 is unchanged.
- T1-T4 §11 adds no series-stop item: T-R2 already halts the series at any Pc sample above 45 bar abs, and the J-FWD inspection after a Q_JFWD trigger is Mechanical's rule for every run of a J-FWD joint (`mechanical.json` `lc_tb70_envelope_v352.jfwd_replace_rule_v2`).
- Open: the PURGE command time, Q_JFWD logging and the S6R / N-04 re-classification against Z3 v2 (Electronics v2.12); the T4 rows re-run (Combustion); before flight acceptance (LEAD): the flight consequence of a flagged first light (relight on a used joint; line 231 covers one Z3 event per assembly), the damped ESP variant (structural damping MISSING), the 0.2-0.5 ms J-FWD band (ASSUMED; TO-VERIFY on a v3.5.2 modal), a shutdown from a case hotter than the soak basis of the rows (Mechanical); OI-PHOTODIODE-VIEW (IGN-1); OI-UNPURGED-RELIGHT; OI-49 to OI-52 as in §16.10.
- Nothing in this section is physical approval.
""".format(self=SELF, stamp=stamp, json=OUT['json'], cf4=OUT['cf4'], t1t4=OUT['t1t4'], ds=OUT['ds'], rows='\n'.join(rows))
assert TXT['report'].endswith('- Nothing in this section is physical approval.\n')
TXT['report'] = TXT['report'] + '\n' + SEC18
b = TXT['report'].encode('utf-8')
open(os.path.join(stage, 'REPORT.md'), 'wb').write(b)
OUT['report'] = sha16(b)

# ---------------------------------------------------------------- stale scan of the outputs (live text only)
STALE = ['restated Z3', 'Z3 restatement', 'OPEN: the lead rules', 'the review file follows', 'SOAK70 (governing)',
         'stays the planning value until then', "published with Mechanical's next", 'R4-01 closes when']
stale = []


def walk(o, path):
    if isinstance(o, dict):
        for kk, v in o.items():
            yield from walk(v, path + [kk])
    elif isinstance(o, list):
        for n, v in enumerate(o):
            yield from walk(v, path + [n])
    else:
        yield path, o


for path, v in walk(J, []):
    if str(path[0]).startswith(('superseded_', 'edit_log_', 'revision_history', 'lead_decisions_folded_v2p4c')):
        continue
    if isinstance(v, str):
        for s in STALE:
            if s in v:
                stale.append(('json', P(path), s))
for k in ('report', 'cf4', 't1t4', 'ds'):
    for n, line in enumerate(TXT[k].split('\n'), 1):
        for s in STALE:
            if s in line and 'v2.4d' not in line and 'v3.2' not in line and 'v2.3' not in line:
                stale.append((k, n, s))
summary = {'stamp': stamp, 'script_sha16': SELF, 'out_sha16': OUT, 'json_leaves_replaced': len(SUP), 'log_rows': len(LOG),
           'by_file': {k: sum(1 for r in LOG if r[0] == k) for k in FNAME}, 'stale_left': stale}
open(os.path.join(stage, 'APPLY-SUMMARY.json'), 'w').write(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
