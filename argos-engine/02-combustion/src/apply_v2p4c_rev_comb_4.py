#!/usr/bin/env python3
"""Combustion v2.4c: text-only corrections after REV-COMB-4 and the LEAD CHANGELOG line 256 purge decision.

Author: the lead (2026-10-21). No model is re-run; no SIM, CEA or FE result changes.
Sources: reviews/REVIEW-COMBUSTION-R4.md (2908321d7f75d439; REV-COMB-4, ACCEPT WITH CORRECTIONS) and CHANGELOG
lines 227 (5), 230 (1)-(3), 243 (3), 249 (1)/(4), 253 (7)/(8) and 256.
Reads the six v2.4b hub files (sha256/16 asserted) and writes the six v2.4c files to STAGE_DIR; publishing is a
separate step. Every replaced JSON leaf is kept under superseded_v2p4c with the finding that replaced it; the md
edits above the appended sections are in place, so REPORT / CF-4 / T1-T4 / RESPONSE keep their v2.4b line numbers.
usage: python3 -I apply_v2p4c_rev_comb_4.py STAGE_DIR STAMP_UTC   (STAMP_UTC from date -u, e.g. 2026-10-21T09:40:00Z)
"""
import copy, hashlib, json, os, re, sys

HUB = '/home/claude/work/shared-fallback/engine'
SRC = {
    'json': ('interfaces/combustion.json', 'fd3a7da6d27c7c66'),
    'report': ('02-combustion/REPORT.md', 'd8b795478d4013ee'),
    'cf4': ('02-combustion/CF-4-SPEC.md', '60bbc51f6f487682'),
    't1t4': ('02-combustion/T1-T4-REGRESSION-SPEC.md', 'b0c42b09ba47cb9c'),
    'resp': ('02-combustion/REVISION-RESPONSE-R3.md', '21791d15dc88eaeb'),
    'ds': ('02-combustion/DATASHEET-INPUTS-COMBUSTION.md', '46a8222018666b1d'),
}
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
SELF = sha16(open(os.path.abspath(__file__), 'rb').read())
LOG = []  # (file key, where, finding or decision, what)

# ---------------------------------------------------------------- markdown helpers
TXT = {k: RAW[k] for k in ('report', 'cf4', 't1t4', 'resp', 'ds')}


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


def lset(k, n, startswith, new, fid, what):
    L = TXT[k].split('\n')
    assert L[n - 1].startswith(startswith), (k, n, L[n - 1][:80])
    assert '\n' not in new
    L[n - 1] = new
    TXT[k] = '\n'.join(L)
    LOG.append((k, 'line %d' % n, fid, what))


# ---------------------------------------------------------------- JSON helpers
J = json.loads(RAW['json'])
assert json.dumps(J, indent=1, ensure_ascii=False) == RAW['json'], 'v2.4b JSON does not round-trip'
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
    ps = P(path)
    if ps not in SUP:
        SUP[ps] = {'v': copy.deepcopy(getp(path)), 'replaced_by': [fid]}
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
    LOG.append(('json', P(path + [key]) + ' (new)', fid, what))


SEQ = ['igniter', 'sequence', 'v']
PDC = ['pc_dynamic_channel', 'v']
SPR = PDC + ['stand_proof_rating_v2p4b', 'v']
PROOF_NEW = ("proof >= 166.14 bar abs (1.1 x FA1S 151.04; LEAD 249 (4)); C1 Kulite XTL-190SM-2000A 206.8 bar abs "
             "(DATASHEET 1.5x rule) meets it; OI-41 DECIDED by LEAD 230 (2)")
RESOLVED = ("RESOLVED by LEAD 230 (2) (band values 94 / 121 / 147 / 94 bar abs; FA1S bounds every period) and 249 (4) "
            "(flight Pc proof >= 166.14 bar abs)")
OI41_STATUS = ("DECIDED by LEAD 230 (2) (final on REV-COMB-4): band values 94 / 121 / 147 / 94 bar abs for structural "
               "SDOF paths; FA1S 151.04 bar abs bounds every period and case (max 146.88, margin 4.16 bar) and is the "
               "design case for pressure-filled passages; per-mode values are an analysis path only; flight Pc proof "
               ">= 166.14 bar abs (249 (4))")
OI42_STATUS = ("2.43 s scheduled flow with the 2.39 s cap ADOPTED (253 (7)(ii); final on REV-COMB-4, LEAD 256 (2)): "
               "needed 2.2 / 1.9 / 1.8 s at 283.15 / 289.5 / 297.15 K unlined; vented <= 66.7 / 70.8 / 75.1 g at "
               "Cd 0.70; conditions (a) cold-corner 2.2 s stated, (b) measured Cd x A >= 0.91 x the Cd 0.70 value, "
               "(c) unlined; (d) after CF-4 the flow and cap are re-set from the measured Cd x A by the measured-time "
               "form, never above 2.43 / 2.39 s, so the 297.15 K vent stays <= 76 g (LEAD 257 (2), on REV-GNC-7: at Cd 0.80 "
               "the fixed schedule vents about 85.5 g at 297.15 K and fails the A1 reserve test)")
VENT_TEXT = ("vented N2O at 2.43 s, unlined, Cd 0.70 <= 66.7 / 70.8 / 75.1 g at 283.15 / 289.5 / 297.15 K and 75.75 g "
             "at the 2.44 s of flow the cap allows; at Cd 0.80 the fixed schedule would vent about 80.5 g at 289.5 K and "
             "85.5 g at 297.15 K [ESTIMATE], so after CF-4 the flow and cap are re-set from the measured Cd x A, never above "
             "2.43 / 2.39 s, keeping the 297.15 K vent <= 76 g (LEAD 257 (2); REV-COMB-4 R4-07; REV-GNC-7; "
             "purge_decision_v2p4c)")
PHOTO = ("pcf_tmax 0.8 s holds on the dead side only with the photodiode main-chamber view (FLAMEOUT_OPT armed) or the "
         "GNC reference re-taken at the ECU E2 / light; photodiode-blind families release 42 (normal_noopt) / 98 "
         "(starved040_noopt) of 1000 dead runs at 0.8 s (OI-PHOTODIODE-VIEW, HIGH, open for IGN-1; REV-COMB-4 section 6)")
P4C_TEXT = ("lit side at 0.21776 mm, torch 0: every corner that reaches 37.16 N within E2 + 0.857 s does so by E2 + 0.205 s "
            "(+3 frames: 0.235 s); 3 of 72 corners never reach 37.16 N in the 0.5 or 0.8 s window: one "
            "(Cd0.65|a0.6|n0.68|ri0.3|eta0.85) crosses at E2 + 0.857 s (a window >= 0.887 s with 3 frames would rescue "
            "it), the other two stay below 37.16 N to the end of the 1.0 s record (36.33 / 36.80 N, still rising); the "
            "count is the same for every window from 0.235 to 0.857 s, so pcf_tmax 0.8 s (227 (5)) is not limited by "
            "the lit side; the low corners are a threshold matter (GNC / lead) (REV-COMB-4 R4-03, DERIVED on SIM)")
HOLD_TEXT = ("H >= 0.30 s unlined / 0.31 s lined on the 2500 N/s ramp to 200 N (latest A3 trip 0.282 / 0.290 s + one "
             "10 ms frame, rounded up to 10 ms; REV-COMB-4 R4-14)")

# ---- R4-05 / R4-12: proof texts
jrep(SEQ + ['arm_preconditions', 3],
     "proof >= 1.1 x 102 = 112 bar abs (lead basis; Combustion's all-case 0.1-1 ms spectrum gives 1.1 x 120.3 = 132 bar abs, OI-41)",
     PROOF_NEW, 'R4-05', 'flight Pc proof 112 -> 166.14 bar abs (1.1 x FA1S); C1 meets it; OI-41 decided')
jrep(SEQ + ['arm_preconditions', 3], "P_torch 0-70 bar class (ENG-09)",
     "P_torch 0-70 bar class (ENG-09; it sees the FA-1 passage pressure, design case FA1S 151.04 bar abs: its proof "
     "(>= 166.14 bar abs, or isolation) and its saturation and recovery are Electronics v2.12 items, REV-COMB-4 R4-12)",
     'R4-12', 'P_torch transducer: FA-1 passage pressure note routed to Electronics')
jrep(['open_interface_issues', 5, 'status'],
     "proof >= 112 bar abs per the lead; Combustion's all-case 0.1-1 ms value gives 132 bar abs: OI-41",
     PROOF_NEW, 'R4-05', 'OI-6 status: proof 166.14 bar abs')
jrep(PDC + ['stand'],
     "range >= 100 bar abs (FA-1 construct head peak up to 88.0 bar abs; LEAD 194 (7)); proof rating >= 1.1 x the all-case "
     "FA-1 spectrum at the transducer path period: flush mount (T <= 0.1 ms) >= 103 bar abs (1.1 x 93.6), carried as the "
     "112 bar abs class of the flight unit (LEAD 205); path period 0.1-1 ms >= 132 bar abs (1.1 x 120.3);",
     "range >= 100 bar abs flush, >= 132 bar abs with a sense line (FA-1 construct head peak up to 88.0 bar abs; LEAD 194 "
     "(7); REV-COMB-4 R4-09); proof rating >= 1.1 x the decided FA-1 band value at the transducer path period: flush "
     "mount (path period <= 0.1 ms) >= 103.4 bar abs (1.1 x 94); 0.1-1 ms path >= 133.1 bar abs (1.1 x 121) (LEAD 230 "
     "(2)); the flight unit's >= 166.14 bar abs (LEAD 249 (4)) covers every path period;",
     'R4-05, R4-09', 'stand channel: proof 103.4 / 133.1 bar abs, range 132 bar abs with a sense line')
jrep(PDC + ['flight'], "proof >= 112 bar abs (lead)", "proof >= 166.14 bar abs (1.1 x FA1S; LEAD 249 (4))",
     'R4-05', 'flight unit proof 166.14 bar abs')
jrep(SPR + ['rule'], "(LEAD 205 uses 1.1 x 102 = 112 bar abs for the flight unit)",
     "(flight unit: 1.1 x FA1S = 166.14 bar abs, LEAD 249 (4))", 'R4-05', 'proof rule: flight unit 166.14 bar abs')
jset(SPR + ['flush_T_le_0p1ms_bar_abs', 'adopted'], 103.4, 'R4-05', 'flush proof adopted 112.0 -> 103.4 (1.1 x 94)', old=112.0)
jadd(SPR + ['flush_T_le_0p1ms_bar_abs'], 'band_value_LEAD_230_2', 94, 'R4-05', 'decided band value 94 bar abs')
jset(SPR + ['path_0p1_to_1ms_bar_abs', 'adopted'], 133.1, 'R4-05', '0.1-1 ms proof adopted 132.0 -> 133.1 (1.1 x 121)', old=132.0)
jadd(SPR + ['path_0p1_to_1ms_bar_abs'], 'band_value_LEAD_230_2', 121, 'R4-05', 'decided band value 121 bar abs')
jadd(SPR, 'flight_unit_all_periods_bar_abs', 166.14, 'R4-05', 'flight unit proof 166.14 bar abs (249 (4))')
jset(SPR + ['contradiction'], RESOLVED, 'R4-05', 'OI-41 contradiction RESOLVED (230 (2), 249 (4))')
jset(['fa1_spectra_v2p4b', 'v', 'contradiction'], RESOLVED, 'R4-05', 'OI-41 contradiction RESOLVED (230 (2), 249 (4))')

# ---- R4-06: closure deadline = torch gate E0 + 0.16 s
jrep(SEQ + ['start', 0, 'action'], "(Electronics: E0 + 0.15 s)",
     "(Electronics v4: E0 + 0.16 s = the torch gate, 160 ms, kTorchGate_s)", 'R4-06', 'closure deadline E0 + 0.16 s')
jrep(['abort_matrix_v2p4', 'v', 'A14'], "(<= torch gate E0 + 0.16 s; Electronics E0 + 0.15 s)",
     "(closure deadline = torch gate, E0 + 0.16 s; Electronics v4)", 'R4-06', 'A14: closure deadline E0 + 0.16 s')
jrep(['cf4_gate', 'v', 'pass_criteria', 5], "(Electronics E0 + 0.15 s)", "(Electronics v4: E0 + 0.16 s)",
     'R4-06', 'CF-4 P6: closure deadline E0 + 0.16 s')
jadd(SEQ + ['start', 0, 'action_superseded'], 'note_v2p4c',
     "the E0 + 0.15 s of this history text is superseded: Electronics v4 E0 + 0.16 s (REV-COMB-4 R4-06)", 'R4-06',
     'history note')

# ---- LEAD 256 (2): purge FINAL (2.43 s flow, 2.39 s cap)
jrep(SEQ + ['start', 0, 'action'], "both taps flow 2.5 s;",
     "both taps flow 2.43 s (the decided scheduled flow, LEAD 253 (7)(ii), final in 256 (2); the v2.4b records were "
     "run with 2.5 s of flow);", 'LEAD 256 (2)', 'scheduled flow 2.5 -> 2.43 s')
jrep(SEQ + ['start', 0, 'action'],
     "ECU both-open cap <= 2.55 s (LEAD 203 (3)); vented mass on the Combustion record basis <= 72.93 g at 2.50 s and "
     "<= 76.05 g at 2.60 s of flow (purge_basis_v2p4b)",
     "ECU both-open cap <= 2.39 s (LEAD 253 (7)(ii), final in 256 (2); it replaces the 2.55 s of 203 (3)); " + VENT_TEXT,
     'LEAD 256 (2)', 'cap 2.55 -> 2.39 s; vented mass at 2.43 s')
jadd(SEQ + ['start', 0], 't_s_note_v2p4c',
     "-2.90 s is the analysed command time (2.5 s of flow ending at E0 - 0.05 s); with the decided 2.43 s of flow the "
     "flow ends at E0 - 0.12 s if PURGE stays at E0 - 2.90 s, or PURGE moves to E0 - 2.83 s for an end at E0 - 0.05 s "
     "[DERIVED: 0.35 s MV ramp]; Electronics v2.12 states which", 'LEAD 256 (2)', 'PURGE command time note')
jrep(SEQ + ['relight', 1], "(2.5 s of flow, theta <= 2 deg, balanced or axial vent)",
     "(2.5 s of flow as analysed in the v2.4b records; the decided scheduled flow is 2.43 s with the 2.39 s cap, LEAD "
     "253 (7)(ii) and 256 (2); Electronics v2.12 states the command time, E0 - 2.90 s or E0 - 2.83 s; theta <= 2 deg, "
     "balanced or axial vent)", 'LEAD 256 (2)', 'relight: decided flow and command time')
TS = ['relight_purge', 'v', 'timing_s']
jset(TS + ['flow'], 2.43, 'LEAD 256 (2)', 'flow 2.5 -> 2.43 s', old=2.5)
jadd(TS, 'flow_analysed_v2p4b', 2.5, 'LEAD 256 (2)', 'analysed flow 2.5 s kept')
jadd(TS, 'both_open_cap_decided_v2p4c', 2.39, 'LEAD 256 (2)', 'cap 2.39 s')
jadd(TS, 'needed_flow_unlined_283p15K', 2.2, 'R4-07', 'cold corner 2.2 s')
jadd(TS, 'needed_flow_unlined_297p15K', 1.8, 'R4-07', 'warm corner 1.8 s')
jadd(TS, 'needed_flow_lined_283p15K', 2.5, 'R4-07', 'lined cold corner 2.5 s')
jadd(TS, 'needed_flow_unlined_note_v2p4c',
     "needed_flow_unlined 1.9 s is the 289.5 K value; 2.2 s at 283.15 K and 1.8 s at 297.15 K (REV-COMB-4 R4-07, DERIVED "
     "on the author's model); 2.2 s is stated wherever 1.9 s is quoted (LEAD 256 (2)(a))", 'LEAD 256 (2)(a)', 'note')
jset(TS + ['min_flow_before_T_fire_delay'], 2.2, 'LEAD 256 (2)(a)', 'minimum flow 1.9 -> 2.2 s (cold corner)', old=1.9)
jadd(TS, 'PURGE_command_rel_E0_note_v2p4c',
     "-2.9 is the analysed command time; with 2.43 s of flow it ends the flow at E0 - 0.12 s, or PURGE moves to "
     "E0 - 2.83 s for an end at E0 - 0.05 s [DERIVED]; Electronics v2.12 decides", 'LEAD 256 (2)', 'note')
jadd(['relight_purge', 'v', 'filter_F2'], 'margins_at_2p43_s_v2p4c',
     "at the decided 2.43 s of flow: 0.23 / 0.53 / 0.63 s over the needed flow at 283.15 / 289.5 / 297.15 K (unlined); "
     "0.18 / 0.13 s at 283.15 K with the FD-01 element bounds (REV-COMB-4, DERIVED); margin_at_2p5_s is the analysed "
     "basis", 'R4-07', 'margins at 2.43 s')
jadd(['relight_purge'], 'decision_note_v2p4c',
     "the records in this block were run with 2.5 s of flow (the analysed basis); the decided schedule is 2.43 s of "
     "flow with the 2.39 s both-open cap (purge_decision_v2p4c)", 'LEAD 256 (2)', 'note')
jset(['purge_commit_rule_v2p4b', 'v', 'ecu_cap'],
     "both-open cap <= 2.39 s with the 2.43 s scheduled flow (LEAD 253 (7)(ii), FINAL in 256 (2); it replaces the "
     "2.55 s of 203 (3)): flow at the cap 2.44 s, 71.37 g at 29.25 g/s and 75.75 g on the warm-end bound (75.79 g at "
     "31.06 g/s), inside the 76 g basis; after CF-4 / B-BLEED-1 the flow and cap are re-set from the measured Cd x A by "
     "the measured-time form, overlap <= 76 g / mdot(297.15 K) - (t_close - t_open) with mdot(297.15 K) from the measured "
     "Cd x A, never above 2.43 / 2.39 s (LEAD 257 (2); OI-42)", 'LEAD 256 (2), 257 (2)', 'ECU cap 2.39 s; CF-4 re-set')
for blk in ('purge_basis_v2p4b', 'purge_basis_line216_v2p4b'):
    jadd([blk], 'decision_note_v2p4c',
         "the 2.5 s schedule and the 2.55 s cap analysed here are superseded by the decided 2.43 s flow with the "
         "2.39 s both-open cap (LEAD 253 (7)(ii), final in 256 (2); purge_decision_v2p4c); the basis 29.25 g/s stands",
         'LEAD 256 (2)', 'note')

# ---- LEAD consistency: case-thermocouple relight limit (CHANGELOG 249 (4))
jrep(SEQ + ['arm_preconditions', 5], "RELIGHT refused if a case thermocouple reads > 433.15 K",
     "RELIGHT refused if a case thermocouple reads > 403.15 K (130 C; kCaseRelightMax_K, LEAD 249 (4); the start and "
     "ARM limit on TC1 / TC2 is the same value; the 433.15 K of v2.4b is superseded)", 'LEAD 249 (4)',
     'relight refusal 433.15 -> 403.15 K')
jrep(SEQ + ['relight', 2], "RELIGHT refused if a case thermocouple > 433.15 K",
     "RELIGHT refused if a case thermocouple > 403.15 K (LEAD 249 (4))", 'LEAD 249 (4)', 'relight refusal 403.15 K')

# ---- R4-04: pcf_tmax 0.8 s
jrep(['drogue_release_hold', 'v', 'line175_5_note_v2p4a'],
     "otherwise hold the drogue and ECU ABORT at t_E2 + 0.5 s: pcf_tmax 0.5 s, LEAD 181 (4); 0.8 s not adopted)",
     "otherwise hold the drogue and ECU ABORT at t_E2 + 0.8 s: pcf_tmax 0.8 s, ADOPTED by LEAD 227 (5) for the "
     "W10 < 6 m/s launch-commit envelope (reverses 181 (4); Electronics v2.11 S17 confirms or returns it))",
     'R4-04', 'ABORT at t_E2 + 0.8 s (227 (5))')
jset(['superseded_v2p4b', 'v', 'ABORT at t_E2 + 0.8 s'],
     "t_E2 + 0.5 s (181 (4)); reversed by LEAD 227 (5): t_E2 + 0.8 s is current", 'R4-04', 'history entry corrected')
jadd(['drogue_release_hold', 'v'], 'pcf_tmax_condition_v2p4c', PHOTO, 'REV-COMB-4 section 6', 'photodiode condition')

# ---- R4-03, R4-14, R4-15, R4-17, R4-18
jset(['p4c_lit_side_v2p4b', 'v', 'implications', 'pcf_tmax'], P4C_TEXT, 'R4-03', 'one low corner crosses at E2 + 0.857 s')
jrep(['purge_commit_rule_v2p4a', 'v', 'line181_2_answer', 'below_L_star'],
     "H >= 0.30 s on the 2500 N/s ramp to 200 N (0.31 s with the 10 ms frame margin)", HOLD_TEXT, 'R4-14',
     'hold wording 0.30 s unlined / 0.31 s lined')
jadd(['a1_apogee_target_v2p4b'], 'throat_growth_basis_note_v2p4c',
     "1.90 / 2.10 % = 1.86 / 2.05 % x 8.443 / 8.258 s = 1.902 / 2.096 % [DERIVED]; if the 1.86 % belongs to the 8.24 s "
     "record (REPORT 16.8), the values are 1.906 / 2.100 %, rounding to 1.91 / 2.10 %; the NZ-01 conclusions do not "
     "change (REV-COMB-4 R4-15)", 'R4-15', 'time-basis note')
jadd(['cold_flow_start_lift_v2p4b'], 'spi_note_v2p4c',
     "with the SPI flux the cold-flow bound is 19.0-20.1 N over 283.15-289.5 K (F_bound_SPI_N; 19.5 N at 286.70 K per "
     "REV-COMB-4), above the 16.31 N margin: the CF-3 start-lift acceptance is not a formality (REV-COMB-4 R4-17)",
     'R4-17', 'SPI-flux note')
jadd(['fa1_per_mode_peq_v2p4b'], 'note_v2p4c',
     "shares FEA3D modal_v351ca2b_c71 (9af80c657eed11ac); ca2c (619272cd3b66072b) changes the bin-level bounds by -0.6 "
     "to +0.2 bar (REV-COMB-4); analysis path only (230 (2))", 'R4-18', 'ca2b / ca2c note')

# ---- R4-08: open items
OI = ['open_items_v2p4b', 'v']
assert getp(OI + [0, 'id']) == 'OI-41' and getp(OI + [1, 'id']) == 'OI-42' and getp(OI + [10, 'id']) == 'OI-51'
assert getp(OI + [12, 'id']) == 'updates'
jadd(OI + [0], 'status', OI41_STATUS, 'R4-08', 'OI-41 DECIDED')
jadd(OI + [1], 'status', OI42_STATUS, 'R4-08', 'OI-42 ADOPTED')
jrep(OI + [10, 'action'], "modal_v351ca2b_c71",
     "modal_v351ca2c_c71 (ca2b is superseded by the ca2c modal fold, line 243)", 'R4-18', 'OI-51 names ca2c')
jadd(OI + [12, 'items'], 'OI-41 (v2.4c)', "DECIDED by LEAD 230 (2) and 249 (4) (REV-COMB-4 R4-08)", 'R4-08', 'update')
jadd(OI + [12, 'items'], 'OI-42 (v2.4c)', "2.43 s flow / 2.39 s cap ADOPTED, final (253 (7)(ii), 256 (2))", 'R4-08', 'update')
jadd(OI + [12, 'items'], 'OI-49 (v2.4c)',
     "still open: gnc.json is v3.1 (4f3209323b0e0ed4) at v2.4c, with no 210 m record; v3.2 follows REV-GNC-7", 'R4-08', 'update')
jadd(OI + [12, 'items'], 'OI-51 (v2.4c)', "action names modal_v351ca2c_c71 (REV-COMB-4 R4-18)", 'R4-18', 'update')

# ---- REV-COMB-4 section 6: OI-UNPURGED-RELIGHT (a) and (c)
jadd(['purge_commit_rule_v2p4b', 'v'], 'unprimed_line_v2p4c',
     "an unprimed or UNKNOWN-line relight with the bleed fitted stays refused for A1 (fail-safe) (LEAD 253 (7)(iv); "
     "OI-UNPURGED-RELIGHT (a)); GNC states the lost-relight mission outcome in gnc.json v3.2", 'REV-COMB-4 section 6',
     'OI-UNPURGED-RELIGHT (a)')
E2N = ("the holds and latencies here are counted from the model E2 (Pc > 3.0 bar abs for 10 ms); the ECU flight E2 is "
       "the relative rule and comes at most 14.7 ms before the model E2 (E2_rule_v2p4b; OI-UNPURGED-RELIGHT (c), "
       "REV-COMB-4 section 6)")
jadd(['release_hold_v2p4b'], 'E2_note_v2p4c', E2N, 'REV-COMB-4 section 6', 'OI-UNPURGED-RELIGHT (c)')
jadd(['relight_purge'], 'E2_note_v2p4c', E2N, 'REV-COMB-4 section 6', 'OI-UNPURGED-RELIGHT (c)')

# ---- new blocks
J['fa1_p_torch_v2p4c'] = {
    'v': {
        'design_case': ("P_torch during FA-1: design case FA1S 151.04 bar abs uniform over the passage (REV-COMB-4 R4-01); "
                        "linear lossless passage peaks <= 129.9 bar abs at the J-FWD tap and <= 148.7 at the torch seat for "
                        "c 150-1200 m/s; the band values 94 / 121 / 147 / 94 do not bound gas-filled passages"),
        'tap_station_peak_bar_abs_by_c_m_s': {'150': 129.85, '181': 121.96, '202': 116.61, '222': 108.0},
        'cases_above_102_bar_abs_at_tap_by_c_m_s': {'150': 48, '181': 42, '202': 36, '222': 12, '400-450': 22},
        'seat_peak_max_bar_abs': 148.72,
        'cases_above_FA1S_any_station_c_150_to_1200': 0,
        'mechanical_row': ("tap-wall v2 at FA1S 151.04 bar abs uniform, DLF 1.0 (Mechanical work tree jfwd_tapwall_v352_v2.json "
                           "9f8849412d4419d7, read by the reviewer): sigma 136.9 MPa; MS_y +0.670 / MS_u +0.785 at the thread "
                           "temperature (SOAK52); MS_y +0.294 at the screw temperature (SOAK52); +0.275 at SOAK70 (governing); "
                           "Lame factor 2.2094 [CALC on SIM]; the reviewer's linear-term estimate agrees within 0.002; R4-01 "
                           "closes when Mechanical publishes the row with the ligament's lowest local natural frequency "
                           "(expected well above 10 kHz)"),
        'DLF_note': ("151.04 exceeds the linear tap peak by >= 16 % (129.85 at c 150; >= 24 % at c >= 181), so a local "
                     "ligament DLF up to 1.16 is covered; the tap-ligament local mode should sit far above the passage "
                     "periods 0.29-2.02 ms"),
        'not_modelled': ['wave steepening and shock reflection', 'losses', 'torch-chamber compliance', 'N2O decomposition',
                         'a blocked-outlet deflagration'],
        'other_load_cases': ("MEOP: dead-ended passage, uniform Pc <= 45 bar abs (quasi-static); torch run about 3 bar abs; "
                             "the 75.5 bar FA-1 pulse row is superseded (head peak 88.02 bar abs, which the passage "
                             "amplifies); the line-176 rows (90 / 102 bar abs) do not cover the passage"),
        'pc_port_face_R4_09': ("lossless bound over c 181-1200 m/s: 130.2 / 131.3 / 130.5 bar abs (CC-1 6 mm3 / CC-1 20 mm3 / "
                               "CC-2); C1 over-range margin >= 6.6 bar at c >= 181 m/s (Electronics v2.12 states it)"),
        'transducer_R4_12': ("the P_torch transducer TE M3234-000005-070BG (74.4 bar g full scale) sees the passage pressure and "
                             "over-ranges during FA-1: proof >= 166.14 bar abs or isolation, and its saturation and recovery "
                             "(Electronics v2.12)"),
    },
    'tag': ("DERIVED by the reviewer (linear lossless two-segment duct, ASSUMED) on SIM FA-1 head histories; design case "
            "LEAD 230 (1); Mechanical row CALC on SIM"),
    'src': ("reviews/REVIEW-COMBUSTION-R4.md R4-01, R4-09, R4-12 (2908321d7f75d439); reviews/combustion/r4/"
            "r4_torch_passage.json (8cb4b0c80173b88d), r4_pc_port_face.json (94f5a39166a8f778)"),
}
J['fa1_grid_statistics_v2p4c'] = {
    'v': {
        'statement': ("the FA-1 head peaks above the Z3 ceiling are physical SIM bracket cases on an ASSUMED construct, not "
                      "an artefact (the v2.4b histories equal v2.4a to 1e-9)"),
        'thresholds_bar_abs': [75.519, 63.1, 60.0],
        'cases_above_all_896': [46, 141, 185],
        'cases_above_baseline_168': [5, 19, 26],
        'as_written_448_above_75p519': 28,
        'max_head_peak_bar_abs': 88.02,
        'by_OF_above_75p519': {'OF4': {'n': 11, 'max': 88.02}, 'OF8': {'n': 1, 'max': 75.85}, 'OF10': {'n': 0},
                               'OF12': {'n': 0}},
        'shape_of_the_46': {'outside_Z3_by': 'peak only', 'time_above_63p1_ms_max': 1.669, 'Z3_limit_ms': 3.0,
                            'rise_10_90_ms_min': 0.842, 'Z3_rise_limit_ms': 0.8, 'time_above_75p519_ms_max': 0.699},
        'pulse_check': {'Z3_as_written_ESP_max_bar_abs': 147.29,
                        'ceiling_88p1_same_shapes_ESP_bar_abs_at_3p0_1p7_1p0_ms_above_63p1': [171.45, 165.03, 152.6],
                        'FA1S_bar_abs': 151.04, 'conclusion': 'raising only the ceiling admits pulses above FA1S'},
        'spectrum_bound': ("FA1S bounds every grid spectrum at every period 0.005-2000 ms: max 146.88 bar abs at 3.5 ms "
                           "(margin 4.16 bar)"),
        'proposed_Z3_prime': ("Z3': head peak <= 88.1 bar abs AND undamped SDOF ESP of the head history <= 151.04 bar abs "
                              "at every period 0.02-50 ms (every FA-1 grid case meets it: max 146.88 at 3.5 ms)"),
        'alternatives': 'tighter shape limits that imply it, or a higher FA1S (needs FE; not in this package)',
        'owners': ("Mechanical (LC-TB70 envelope v2: the restated Z3 and the joint-replacement rule); Electronics v2.12 "
                   "re-classifies the 10 S6R runs and the 29-33 N-04 burn-on cases against it"),
        'line_253_8_wording': ("a 60 bar replace-all rule would mark the joint used in 185 of the 896 FA-1 hard-start bracket "
                               "cases (a SIM grid count on an ASSUMED construct, not a rate of normal lights) (LEAD 256 (4), "
                               "REV-COMB-4 R4-10)"),
        'status': ("OPEN: the lead rules on Z3' or Mechanical's alternative at Mechanical's pre-publication post; 253 (7)(i) "
                   "stays adopted on that condition (256 (3))"),
    },
    'tag': 'DERIVED by the reviewer on SIM histories (ASSUMED construct)',
    'src': ("reviews/REVIEW-COMBUSTION-R4.md R4-02; reviews/combustion/r4/r4_fa1_envelope_stats.json (9a4f010f2fd37049), "
            "r4_z3_pulse_check.json (8807b744c7e3b74b)"),
}
J['purge_decision_v2p4c'] = {
    'v': {
        'decision': ("2.43 s scheduled purge flow (both-open overlap 2.38 s + 0.05 s) with the 2.39 s both-open cap, ADOPTED "
                     "by LEAD 253 (7)(ii) and FINAL in 256 (2) on REV-COMB-4; it replaces the 2.5 s schedule and the 2.55 s cap"),
        'flow_s': 2.43, 'both_open_overlap_s': 2.38, 'cap_both_open_s': 2.39, 'flow_at_cap_s': 2.44,
        'analysed_basis': ("the v2.4b records, tables and CF-4 model numbers were run with 2.5 s of flow ending at E0 - 0.05 s "
                           "(PURGE at E0 - 2.90 s); they stay the analysed basis, which is more flow than decided"),
        'needed_flow_unlined_s': {'283.15 K': 2.2, '289.5 K': 1.9, '297.15 K': 1.8},
        'needed_flow_lined_283p15K_s': 2.5,
        'P_abort_lined_283p15K_at_2p43s': 0.061,
        'P_abort_unlined_at_2p43s': '0 at all three corners (W 0.65 s; the author model)',
        'margins_at_2p43s_unlined_s': {'283.15 K': 0.23, '289.5 K': 0.53, '297.15 K': 0.63},
        'margins_283p15K_with_FD01_element_bounds_s': [0.18, 0.13],
        'vented_N2O_at_2p43s_unlined_Cd0p70_g': {'283.15 K': [30.7, 66.7], '289.5 K': [32.6, 70.8], '297.15 K': [33.4, 75.1]},
        'vented_N2O_bound_law_g': {'283.15 K': 66.4, '289.5 K': 70.7, '297.15 K': 75.4, 'at_cap_2p44s_of_flow': 75.75},
        'vented_N2O_Cd0p80_fixed_schedule_g': {'289.5 K': 80.5, '297.15 K': 85.5, '297.15 K, 2.44 s of flow at the cap': 85.8},
        'vented_N2O_Cd0p80_tag': ("ESTIMATE: 2.43 s x 33.13 g/s at 289.5 K (average rate); at 297.15 K the Cd 0.80 / 0.70 "
                                  "ratio 1.1326 on 31.06 g/s (REV-GNC-7 interim 2); with the fixed 2.43 / 2.39 s schedule, "
                                  "which (d) re-sets after CF-4"),
        'a1_reserve_test_REV_GNC_7': {
            'test': 'CHANGELOG line 208 against the v3d reference (A1 210 m, v351, N = 500 per base, dip onset 80 g)',
            '76 g': 'UB95 0.854 pp liquid / 0.617 pp powered: PASS',
            '80.5 g': 'UB95 0.972 / 0.617 pp: PASS (margin 0.028 pp)',
            'first_fail_g': 82.1,
            '85.5-85.8 g': 'UB95 1.206 pp liquid: FAIL (powered 0.736 pp passes)',
            'tag': 'DERIVED from SIM by REV-GNC-7 (interim 2, 09:25:51Z); above 80 g a linear per-run shift, ESTIMATE'},
        'conditions_LEAD_256_2': {
            'a': 'wherever 1.9 s is quoted as the needed flow, 2.2 s at the 283.15 K cold corner is stated with it',
            'b': ("CF-4 / B-BLEED-1 shows a measured Cd x A of the two-tap path >= 0.91 x the Cd 0.70 value (>= 0.95 x "
                  "with the FD-01 element bound), else the flow is re-sized"),
            'c': 'the line stays unlined (lined, 283.15 K needs 2.5 s)'},
        'condition_d_LEAD_257_2': (
            "after CF-4 / B-BLEED-1, kPurgeFlow_s and the both-open cap are re-set from the measured Cd x A by the "
            "measured-time form of purge_basis_line216_v2p4b, with the mass flow taken at 297.15 K: both-open overlap "
            "<= 76 g / mdot(297.15 K) - (t_close - t_open), never above the decided 2.43 s / 2.39 s; the 297.15 K vent then "
            "stays <= 76 g at any measured Cd x A, and the 283.15 K need stays met because need and limit both scale with "
            "1 / (Cd x A) (margin on the 10 ms steps 0.23 s at a Cd x A ratio of 1, 0.21 s at 1.08 and 1.13 (Cd 0.80), "
            "0.19 s at 1.2) [DERIVED; the scaling is ASSUMED, as in (b)]; if the "
            "constants are not re-set, the measured Cd x A must also be <= 1.08 x the Cd 0.70 value (vent <= 82 g at the "
            "cap, REV-GNC-7's bound) or GNC re-runs the A1 reserve test at the measured vented mass; a temperature-scheduled "
            "flow (1.8 s needed at 297.15 K) is not adopted"),
        'reserve': ("vented N2O is judged against the 76 g basis (G73 decided, G80 sensitivity) and the A1 N2O reserve "
                    "(a1_reserve_test_REV_GNC_7); with (d) the vent stays <= 76 g, which passes; the 253 (7)(ii) "
                    "re-fly-trigger wording is withdrawn (REV-COMB-4 R4-11)"),
        'basis': ("29.25 g/s = 76 g / 2.5982 s of flow at 289.5 K (27.58-31.06 g/s over 283.15-297.15 K; "
                  "purge_basis_line216_v2p4b)"),
        'PURGE_command_time': ("open: Electronics v2.12 states E0 - 2.90 s (the flow ends at E0 - 0.12 s) or E0 - 2.83 s "
                               "(the flow ends at E0 - 0.05 s) [DERIVED]"),
        'CF4': ("CF-4 v2.2 runs the decided flow, adds a run at or below 283.15 K or states the cold corner model-only, "
                "checks the Cd x A acceptance in P5 and records the measured Cd x A that re-sets the flow and cap (d)"),
        'electronics': ("kPurgeFlow_s 2.43 s; command span 2.38 s inside the 2.39 s cap; flow at the cap 2.44 s (Electronics "
                        "v4 head_end_bleed_provision.cap_decision_230_3.option_not_made, now decided); after CF-4 both are "
                        "calibration constants re-set by (d), never above these values"),
    },
    'tag': ("LEAD (decision and conditions); DERIVED by REV-COMB-4 on the author's SIM model (Cd 0.70 ASSUMED); ESTIMATE "
            "(Cd 0.80 mass); A1 reserve test DERIVED from SIM by REV-GNC-7 (ESTIMATE above 80 g)"),
    'src': ("CHANGELOG 253 (7)(ii), 256 (2), 257 (2); reviews/REVIEW-COMBUSTION-R4.md R4-07; reviews/combustion/r4/"
            "r4_purge_corners.json (9249ed093c21a3a3); REV-GNC-7 interim 2 (the review file follows)"),
}
J['electronics_open_issues_v2p4c'] = {
    'v': {
        'OI-UNPURGED-RELIGHT': {
            'severity': 'MEDIUM (Electronics v4)',
            'a': ("an unprimed or UNKNOWN-line relight with the bleed fitted stays refused for A1 (fail-safe) (LEAD 253 (7)(iv)); "
                  "purge_commit_rule_v2p4b.v.unprimed_line_v2p4c"),
            'b': 'the torch-kept ride-through of the post-light vapour gap stays a research option (not implemented)',
            'c': ("the latency and hold blocks use the model E2 (Pc > 3.0 bar abs for 10 ms); the ECU flight E2 comes at most "
                  "14.7 ms earlier (E2_rule_v2p4b); notes added in release_hold_v2p4b and relight_purge"),
            'status': 'OPEN until Combustion models an unpurged relight (253 (7)(iv))'},
        'OI-PHOTODIODE-VIEW': {'severity': 'HIGH (Electronics v4)', 'condition': PHOTO,
                               'status': 'OPEN for IGN-1 (view proven with the torch closed) or the GNC reference choice'},
        'OI-GEN-TABLES': {'severity': 'MEDIUM (Electronics v4)',
                          'answer': ("machine-readable igniter sequence added: igniter_sequence_fields_v2p4c (one field per "
                                     "value; Electronics v4 requests[7]); gen_tables v3.4 reads it, regenerates, diffs and "
                                     "re-runs the SIL record"),
                          'status': 'Combustion part DONE in v2.4c; Electronics part open'},
        'OI-E2-LATENCY': 'LOW; open (IGN-1)',
        'OI-STAND-LATE-LIGHT': 'LOW; open (IGN-1)',
        'OI-SEAT-RINGING': ("MEDIUM; open (B-DPC-1 / HIL-TR-1); the FA-1 grid's minimum 10-90 % rise is 0.842 ms against the "
                            "ideal 25 us steps"),
        'OI-38-R2-COMMAND-HOLD': 'HIGH; open (GNC R2 v2 / B-FC-1 / CF-3)',
        'routed_to_electronics_v2p12': [
            'R4-09: Pc-port face bound 130.2 / 131.3 / 130.5 bar abs over c 181-1200 m/s; C1 over-range margin >= 6.6 bar',
            'R4-12: P_torch 070BG proof against FA1S 151.04 bar abs (>= 166.14 bar abs or isolate); saturation and recovery',
            ('R4-13: config.h:831 cites the superseded purge_sizing_v2p4.json; cite purge_duration_v2p4.json '
             '(1ff6bfcd7d2f454c): 1.9 s at 289.5 K on 2 x 0.707 mm and 2.2 s at 283.15 K'),
            'R4-02: re-classify the 10 S6R runs and the 29-33 N-04 burn-on cases against the restated Z3',
            'LEAD 256 (2)(a): state 2.2 s at 283.15 K wherever 1.9 s is quoted',
            'LEAD 256 (2): the PURGE command time with 2.43 s of flow (E0 - 2.90 or - 2.83 s)',
            ('LEAD 257 (2): kPurgeFlow_s and the both-open cap are calibration constants, re-set after CF-4 from the '
             'measured Cd x A by the measured-time form (mdot at 297.15 K), never above 2.43 / 2.39 s')],
    },
    'tag': 'REV-COMB-4 section 6 dispositions; Electronics v4 open_issues (electronics.json 11f7896ad0d0613b)',
    'src': 'reviews/REVIEW-COMBUSTION-R4.md section 6',
}


def F(fid, v, unit, src, tag):
    return {'id': fid, 'v': v, 'unit': unit, 'src': src, 'tag': tag}


S0, S1, S2, S3, S4, S5, S6 = ['igniter.sequence.v.start[%d]' % i for i in range(7)]
FW = 'firmware_constant_sources_v2p4b'
LW = 'igniter.sequence.v.light_windows_W_s'
SH = 'igniter.sequence.v.shutdown'
AP = 'igniter.sequence.v.arm_preconditions'
DR = 'drogue_release_hold.v.line175_5_note_v2p4a'
J['igniter_sequence_fields_v2p4c'] = {
    'v': {
        'format': ("one field per value: id, v, unit, src (a combustion.json path or a LEAD line), tag; times are relative "
                   "to E0 unless the id says otherwise; for gen_tables (OI-GEN-TABLES; Electronics v4 requests[7])"),
        'fields': [
            F('purge.commit_lead_L_star', 1.3, 's', S0 + '; LEAD 186 (1)', 'LEAD'),
            F('purge.PURGE_command_analysed', -2.9, 's', 'relight_purge.v.timing_s; Electronics v2.12 states the flight value', 'DESIGN (analysed)'),
            F('purge.MV_ramp', 0.35, 's', 'relight_purge.v.timing_s', 'DESIGN'),
            F('purge.flow_scheduled', 2.43, 's', 'purge_decision_v2p4c; LEAD 253 (7)(ii), 256 (2)', 'LEAD'),
            F('purge.flow_end', -0.05, 's', 'LEAD line 164', 'LEAD'),
            F('purge.both_open_cap', 2.39, 's', 'purge_decision_v2p4c; LEAD 256 (2)', 'LEAD'),
            F('purge.needed_flow_unlined_283p15K', 2.2, 's', 'purge_decision_v2p4c; REV-COMB-4 R4-07', 'DERIVED'),
            F('purge.needed_flow_unlined_289p5K', 1.9, 's', 'relight_purge.v.timing_s.needed_flow_unlined', 'SIM'),
            F('purge.valve_open_close_times', [0.03, 0.08], 's', 'purge_basis_line216_v2p4b.v.cap_rule', 'ASSUMED'),
            F('purge.closure_deadline', 0.16, 's', S3 + '; Electronics v4 kTorchGate_s (= the torch gate)', 'DESIGN'),
            F('spark.rate', 50, 'Hz', S1, 'DESIGN'),
            F('spark.energy', 0.05, 'J', S1 + ' (50 mJ)', 'DESIGN'),
            F('spark.start', 0.02, 's', S1, 'DESIGN'),
            F('spark.train_max', 0.5, 's', FW + ' kSparkTrain_s', 'DESIGN'),
            F('torch_gate.latest_E1', 0.16, 's', S2, 'DESIGN'),
            F('E1.median', 0.09, 's', S3 + ' (torch_gate_v2p4)', 'SIM'),
            F('E1.persistence', 0.01, 's', S3, 'DESIGN'),
            F('E1_to_E2.torch_loss_both_sensors', 0.005, 's', S3 + ' (FA-1 (b), A16)', 'DESIGN'),
            F('start_lift.h_s_20C', 0.2039, 'mm', S3 + '; start_level_lift_v2p4b', 'DESIGN'),
            F('start_lift.h_s_A1_286p70K', 0.21776, 'mm', 'start_level_lift_v2p4b.v.line216_9 (ECU row)', 'DESIGN'),
            F('start_lift.t_lift', [0.0287, 0.0295], 's', S3, 'DERIVED'),
            F('start_lift.flow_cap_20C', 37.1, 'g/s', S3 + '; CF-3', 'LEAD (cap)'),
            F('start_lift.flow_cap_A1', 37.4, 'g/s', S3 + '; CF-3', 'LEAD (cap)'),
            F('W.flight_first_start_from_lift_command', 0.4, 's', LW, 'LEAD'),
            F('W.flight_relight_from_lift_command', 0.65, 's', LW, 'LEAD'),
            F('W.stand_from_lift_command', 0.35, 's', LW, 'LEAD'),
            F('W.relight_plan_limit_E2', 0.81, 's', S4 + ' (torch gate 0.16 + W 0.65)', 'LEAD'),
            F('E2.rise_over_prelift_baseline', 0.8, 'bar', S5 + ' (filtered AND raw Pc)', 'DESIGN'),
            F('E2.persistence', 0.01, 's', S5, 'DESIGN'),
            F('E2.floor', 1.8, 'bar abs', S5, 'DESIGN'),
            F('E2.SOL2_after_SOL1_max', 0.02, 's', S5, 'DESIGN'),
            F('E2.ECU_before_model_max', 0.0147, 's', 'E2_rule_v2p4b.v.shift_bound_s', 'DERIVED'),
            F('E2.worst_purged_median_p99_max', [0.442, 0.589, 0.626], 's', S5 + ' (rg01_line_states_v2p4)', 'SIM'),
            F('E3.thrust_fraction_of_command', 0.9, '-', S6 + ' (ENG-04)', 'REQ'),
            F('propane.SOL2_close_backstop_time', 0.4, 's', FW + ' kPropaneOffPcAbs_Pa', 'DESIGN'),
            F('propane.SOL2_close_backstop_Pc', 5.0, 'bar abs', FW + ' kPropaneOffPcAbs_Pa', 'DERIVED'),
            F('ramp.start_ramp_max', 2500, 'N/s', FW + ' kStartRamp_Nps', 'DESIGN'),
            F('ramp.pintle_to_ignition_lift_legacy', 0.12, 's', FW + ' kPintleToIgnitionLift_s', 'DESIGN (legacy)'),
            F('shutdown.throttle_down_before_MECO_max', 0.75, '-', SH + '[0] (ENG-05)', 'LEAD'),
            F('shutdown.MV_seat_confirm_Pc_below', 2.0, 'bar abs', SH + '[2]', 'DESIGN'),
            F('shutdown.MV_deenergise_after_command_max', 0.3, 's', SH + '[2]', 'DESIGN'),
            F('shutdown.ground_hold_before_safing', 30, 's', SH + '[3]', 'DESIGN'),
            F('arm.tank_T_range', [15, 24], 'C', AP + '[0] (ENG-12; interlock_guard_band)', 'REQ'),
            F('arm.P_torch_refuse_above', 1.05, 'bar abs', AP + '[2]', 'DESIGN'),
            F('arm.relight_case_TC_refuse_above', 403.15, 'K', AP + '[5]; LEAD 249 (4) kCaseRelightMax_K', 'LEAD'),
            F('release.accel_thrust_threshold', 37.16, 'N', DR + ' (LEAD 175 (5))', 'LEAD'),
            F('release.frames', 3, '-', DR, 'LEAD'),
            F('release.frame_rate', 100, 'Hz', DR, 'LEAD'),
            F('release.pcf_tmax', 0.8, 's', DR + '; LEAD 227 (5)', 'LEAD'),
            F('stand_abort.N2_purge_min', 60, 's', 'igniter.sequence.v.abort_if_no_ignition[1]', 'LEAD'),
            F('stand_abort.N2_purge_rate_min', 10, 'g/s', 'igniter.sequence.v.abort_if_no_ignition[1]', 'LEAD'),
            F('stand_abort.hold_before_approach_min', 15, 'min', 'igniter.sequence.v.abort_if_no_ignition[1]', 'LEAD'),
        ],
    },
    'tag': 'index of values already in this file or decided by the lead (LEAD 249 (4), 256 (2)); no new model value',
    'src': 'REV-COMB-4 section 6 (OI-GEN-TABLES)',
}
J['t4_duration_note_v2p4c'] = {
    'v': {
        'finding': ("N-07: T1-T4 v3's own objectives fix no DC-D or DC-C duration; its T4 row reads 'DC-D ... law check only' "
                    "with 7.02 kg; the durations come from GNC's DC-D v2 (32.0 + 8.0 + 10.0 s; 6.31 kg ox) [ASSUMED]"),
        'objectives': ("erosion per cycle and soak temperatures need the B1 sizing duty (B1 p99 21.76 s at mean throttle 0.257, "
                       "1.54 kg; B1 max 23.58 s, 1.63 kg); relight latency needs an A1-like relight from a soaked state "
                       "(A1 p99 record: 3.78 s at 0.88, coast to 22.79 s, then 4.59 s at 0.47)"),
        'shortest_firing_estimate': ("burn 1 on the B1 p99 profile (21.76 s; 23.58 s if the life rule is sized on max), a coast "
                                     "of about 19 s, then one relight of about 4.6 s at about 0.47 throttle: about 2.0 kg of N2O "
                                     "against 7.02 kg; a third start is a repeat only; DC-C (27.0 + 9.5 s, 2.39 kg) carries no "
                                     "Combustion T4 objective"),
        'status': 'GNC (REV-GNC-7) confirms the T4 profile; 7.02 kg stays the planning value until then (T1-T4 v3.1 line 294)',
    },
    'tag': 'ESTIMATE (REV-COMB-4 from the GNC records)',
    'src': 'reviews/REVIEW-COMBUSTION-R4.md section 6 (N-07)',
}
J['lead_decisions_folded_v2p4c'] = {
    'v': {
        '227 (5)': 'R2 starve window pcf_tmax 0.8 s ADOPTED for the W10 < 6 m/s launch-commit envelope (reverses 181 (4))',
        '230 (1)': ("TC-01 J-FWD not met on a conservative basis; design change sized to FA1S 151.04 bar abs (Mechanical; "
                    "re-map published in line 254)"),
        '230 (2)': ('band values RESTATED to 94 / 121 / 147 / 94 bar abs; FA1S stays the bound for every period; the per-mode '
                    'rule stays an analysis path'),
        '230 (3)': 'ONE purge flow basis 29.25 g/s ADOPTED; 2.39 s fixed cap if the scheduled flow fits',
        '243 (3)': 'case TC abort A = 150 C (423.15 K) ADOPTED (supersedes the 175 C of 188 (5)); channel accepted in 249 (1)',
        '249 (4)': ('kCaseRelightMax_K 403.15 K (130 C); flight Pc proof >= 166 bar abs = 1.1 x FA1S (written 166.14, '
                    'REV-COMB-4 R4-05); the C1 pick meets it'),
        '253 (7)(i)': 'ride-through ADOPTED with conditions; Z3 restatement added (256 (3))',
        '253 (7)(ii)': '2.43 s scheduled flow with the 2.39 s cap, FINAL in 256 (2) with conditions (a)-(c)',
        '253 (7)(iv)': 'an unprimed or UNKNOWN-line relight with the bleed fitted stays refused for A1 (fail-safe)',
        '253 (8)': 'provisional TB-state used-joint aborts; wording corrected by 256 (4)',
        '256': 'REV-COMB-4 ACCEPTED; combustion v2.4c is text only (this revision)',
        '257 (2)': ('purge condition (d): after CF-4 the flow and cap are re-set from the measured Cd x A by the '
                    'measured-time form (mass flow at 297.15 K), never above 2.43 / 2.39 s, so the vent stays <= 76 g '
                    '(on REV-GNC-7: the fixed schedule at Cd 0.80 vents about 85.5 g at 297.15 K and fails the A1 reserve test)'),
    },
    'tag': 'LEAD (CHANGELOG)',
    'src': 'CHANGELOG lines 227, 230, 243, 249, 253, 256, 257',
}

# ---------------------------------------------------------------- CF-4 v2.2
mrep('cf4', "Version 2.1 (Combustion v2.4b), 2026-10-19 (staged 2026-10-13; final fold of LEAD lines 214-228, last change bullet below).",
     "Version 2.2 (Combustion v2.4c), 2026-10-21: text corrections from REV-COMB-4 (`reviews/REVIEW-COMBUSTION-R4.md`, "
     "`2908321d7f75d439`) and the LEAD line 256 purge decision, applied by the lead; the v2.2 changes are listed in §13 at "
     "the end; the edits are in place, so lines 1-191 keep their v2.1 numbers. v2.1 (`60bbc51f6f487682`) is archived as "
     "`02-combustion/superseded/v2p4b/CF-4-SPEC.md`. The v2.1 header follows unchanged. Version 2.1 (Combustion v2.4b), "
     "2026-10-19 (staged 2026-10-13; final fold of LEAD lines 214-228, last change bullet below).",
     'v2.4c', 'version header v2.2', line=3)
mrep('cf4', "Electronics sets it at E0 + 0.15 s.",
     "Electronics v4 sets it at the torch gate, E0 + 0.16 s (160 ms, kTorchGate_s; v2.2 correction, REV-COMB-4 R4-06).",
     'R4-06', 'closure deadline E0 + 0.16 s', line=15)
mrep('cf4', "both head-end bleed taps vent for 2.5 s, and the flow stops 0.05 s before T_fire (E0).",
     "both head-end bleed taps vent for the decided 2.43 s of flow (LEAD 253 (7)(ii), final in 256 (2); the model numbers "
     "of this specification were run with 2.5 s), and the flow stops 0.05 s before T_fire (E0).",
     'LEAD 256 (2)', 'decided flow 2.43 s', line=26)
mrep('cf4', "and 2.5 s of flow ending 0.05 s before E0,",
     "and the decided 2.43 s of flow ending 0.05 s before E0 (LEAD 256 (2); the model behind the claim was run with 2.5 s "
     "and needs at most 2.2 s, at the 283.15 K corner),", 'LEAD 256 (2)', 'C-RL with 2.43 s', line=33)
mrep('cf4', "needs 1.9 s of flow (<= 1.94 s with the FD-01 element)",
     "needs 1.9 s of flow at 289.5 K (<= 1.94 s with the FD-01 element) and 2.2 s at 283.15 K (REV-COMB-4)",
     'R4-07; LEAD 256 (2)(a)', 'needed flow with the cold corner', line=35)
lappend('cf4', 64, "Tank at the A1 relight state: 43.5-46.5 bar, 286.7-289.5 K.",
        " v2.2 (REV-COMB-4 R4-07): the 283.15 K relight corner needs the most flow (2.2 s unlined); add at least one IS-2 run "
        "with the tank at or below 283.15 K, or state in the test record that the cold corner is model-only.",
        'R4-07', 'cold-corner run or model-only statement')
lappend('cf4', 66, "A1 profile (LEAD lines 213, 214 and 227 (1); new in v2.1).",
        " v2.2: the decided 2.43 s of flow with the 2.39 s both-open cap vents <= 66.7 / 70.8 / 75.1 g at 283.15 / 289.5 / "
        "297.15 K (Cd 0.70) and 75.75 g at the 2.44 s of flow the cap allows, inside 76 g (LEAD 256 (2); REV-COMB-4 R4-07, "
        "DERIVED). At Cd 0.80 the same schedule would vent about 80.5 g at 289.5 K and 85.5 g at 297.15 K [ESTIMATE], above "
        "the 82.1 g at which GNC's A1 reserve test first fails (REV-GNC-7), so P5 records the measured Cd x A and the flow "
        "and cap are re-set from it (LEAD 257 (2)).", 'LEAD 256 (2), 257 (2)', 'vented mass of the decided schedule')
mrep('cf4', "PURGE is commanded at E0 - 2.90 s and gives 2.5 s of flow ending at E0 - 0.05 s;",
     "PURGE is commanded at the flight command time that Electronics v2.12 states (E0 - 2.83 s ends the decided 2.43 s of "
     "flow at E0 - 0.05 s; E0 - 2.90 s, the analysed command time with 2.5 s of flow, ends it at E0 - 0.12 s [DERIVED]);",
     'LEAD 256 (2)', 'PURGE command time from Electronics', line=90)
mrep('cf4', "t_open, t_close from the valve position channels |",
     "t_open, t_close from the valve position channels. v2.2 (LEAD 256 (2)(b); REV-COMB-4 R4-07): the measured Cd x A of the "
     "two-tap path must be >= 0.91 x the Cd 0.70 value (>= 0.95 x with the 4x FD-01 element bound), else the flow is "
     "re-sized; with the decided 2.43 s of flow and the 2.39 s cap the model vents <= 66.7 / 70.8 / 75.1 g at 283.15 / "
     "289.5 / 297.15 K (Cd 0.70). From the measured Cd x A, kPurgeFlow_s and the both-open cap are re-set by the "
     "measured-time form, overlap <= 76 g / mdot(297.15 K) - (t_close - t_open), never above 2.43 / 2.39 s, so the "
     "297.15 K vent stays <= 76 g; without the re-set the measured Cd x A must also be <= 1.08 x the Cd 0.70 value (vent "
     "<= 82 g, inside GNC's A1 reserve test) (LEAD 257 (2); REV-GNC-7) |", 'LEAD 256 (2)(b), 257 (2)',
     'P5: Cd x A acceptance and the re-set', line=102)
mrep('cf4', "The deadline is at or before the torch gate, E0 + 0.16 s; Electronics sets it at E0 + 0.15 s (`electronics.json` v2).",
     "The deadline is the torch gate, E0 + 0.16 s (Electronics v4: 160 ms, kTorchGate_s; REV-COMB-4 R4-06).",
     'R4-06', 'P6: closure deadline E0 + 0.16 s', line=103)

# ---------------------------------------------------------------- T1-T4 v3.1
mrep('t1t4', "(RG-03), v3", "(RG-03), v3.1", 'v2.4c', 'title v3.1', line=1)
mrep('t1t4', "Combustion v2.4b, 2026-10-13. Replaces v2",
     "v3.1 (Combustion v2.4c), 2026-10-21: text corrections from REV-COMB-4 (`reviews/REVIEW-COMBUSTION-R4.md`, "
     "`2908321d7f75d439`) applied by the lead: the proof values of line 83 (R4-05; LEAD 230 (2), 249 (4)) and the T4 N2O "
     "note on line 294 (N-07); the edits are in place, so the line numbers are kept; v3 (`b0c42b09ba47cb9c`) is archived "
     "as `02-combustion/superseded/v2p4b/T1-T4-REGRESSION-SPEC.md`. The v3 header follows unchanged. Combustion v2.4b, "
     "2026-10-13. Replaces v2", 'v2.4c', 'version header v3.1', line=3)
mrep('t1t4', "Flush mount (path period <= 0.1 ms): >= 103 bar abs, use >= 112 bar abs (1.1 x 102, the line-205 value). "
     "Short sense line with a path period of 0.1-1 ms: >= 132 bar abs.",
     "Flush mount (path period <= 0.1 ms): >= 103.4 bar abs (1.1 x 94, the LEAD 230 (2) band value). Short sense line with "
     "a path period of 0.1-1 ms: >= 133.1 bar abs (1.1 x 121), with a range >= 132 bar abs (REV-COMB-4 R4-09). The flight "
     "unit's proof >= 166.14 bar abs (1.1 x FA1S 151.04; LEAD 249 (4)) covers every path period.",
     'R4-05', 'stand proof 103.4 / 133.1 bar abs', line=83)
mrep('t1t4', "(seat-mounted miniature unit, proof >= 112 bar abs)",
     "(seat-mounted miniature unit, proof >= 166.14 bar abs = 1.1 x FA1S 151.04, LEAD 249 (4); the C1 Kulite "
     "XTL-190SM-2000A pick, 206.8 bar abs, meets it)", 'R4-05', 'flight unit proof 166.14 bar abs', line=83)
lappend('t1t4', 294, "- **T4** (DC-D duty cycle, S230 grain, 3 starts) uses 7.02 kg",
        " v3.1 note (REV-COMB-4 N-07, ESTIMATE from the GNC records): the Combustion T4 objectives (erosion per cycle and "
        "soak temperatures at the B1 sizing duty; relight latency from a soaked state) need about 2.0 kg of N2O: burn 1 on "
        "the B1 p99 profile (21.76 s; 23.58 s if the life rule is sized on max), a coast of about 19 s, then one relight of "
        "about 4.6 s at about 0.47 throttle; a third start is a repeat only, and DC-C carries no Combustion T4 objective. "
        "GNC (REV-GNC-7) confirms the profile; 7.02 kg stays the planning value until then.", 'N-07', 'T4 N2O note')

# ---------------------------------------------------------------- REVISION-RESPONSE-R3 (annotations)
mrep('resp', "Version v2.4b, 2026-10-19",
     "v2.4c note (2026-10-21, lead): this file records the v2.4b answer to REV-COMB-3. REV-COMB-4 "
     "(`reviews/REVIEW-COMBUSTION-R4.md`, `2908321d7f75d439`) closed all 17 R3 items (10 CLOSED, 7 CLOSED WITH RESIDUAL); "
     "the v2.4c corrections are listed in REPORT §17 and annotated in place below (row R3-01, §6 point 3, §9 item 3). The "
     "line references resolve against the v2.4b files as answered: REPORT, CF-4 and T1-T4 keep their line numbers in "
     "v2.4c (in-place edits), and `combustion.json` v2.4b is kept as `02-combustion/superseded/v2p4b/combustion.json`. "
     "Superseded since: the 112 bar abs proof texts (row R3-10, §6 point 1) by >= 166.14 bar abs (LEAD 249 (4)), and the "
     "ABORT time of row R3-09 (0.5 s after E2) by 0.8 s after E2 (LEAD 227 (5)). Version v2.4b, 2026-10-19",
     'v2.4c', 'v2.4c header note', line=3)
mrep('resp', "0.30 s at zero residual on the 2500 N/s ramp to 200 N (0.31 s with the 10 ms frame margin)",
     "0.30 s at zero residual on the 2500 N/s ramp to 200 N unlined and 0.31 s lined (latest A3 trip 0.282 / 0.290 s + one "
     "10 ms frame, rounded up to 10 ms; v2.4c wording, REV-COMB-4 R4-14)", 'R4-14', 'R3-01 row: hold wording', line=17)
lappend('resp', 117, "3. Release hold for GNC P6c:",
        " [v2.4c, REV-COMB-4 R4-14: every Table 2.18 value already includes the frame: H >= 0.30 s unlined / 0.31 s lined on "
        "the 2500 N/s ramp to 200 N (latest A3 trip 0.282 / 0.290 s + one 10 ms frame, rounded up to 10 ms).]",
        'R4-14', 'section 6 point 3 annotated')
mrep('resp', "pcf_tmax 0.8 s is not limited by the lit side.",
     "pcf_tmax 0.8 s is not limited by the lit side [v2.4c, REV-COMB-4 R4-03: one of the 3 corners (Cd 0.65, a 0.6, n 0.68, "
     "ri 0.3, eta 0.85) crosses 37.16 N at E2 + 0.857 s; the other two stay below it to the end of the 1.0 s record "
     "(36.33 / 36.80 N, still rising); the count is the same for every window from 0.235 to 0.857 s, so the conclusion "
     "stands].", 'R4-03', 'section 9 item 3 annotated', line=158)

# ---------------------------------------------------------------- REPORT (in place; header sha filled after the JSON)
mrep('report', "Version 2.4b, 2026-10-19 (staged 2026-10-13; final fold of LEAD lines 214-228 and the lead requests of 2026-10-19 in §16).",
     "Version 2.4c, 2026-10-21: text-only corrections after the independent delta re-review REV-COMB-4 "
     "(`reviews/REVIEW-COMBUSTION-R4.md`, `2908321d7f75d439`, ACCEPT WITH CORRECTIONS, accepted by the lead in CHANGELOG "
     "line 256) and the line-256 purge decision, applied by the lead; no model was re-run. Interface: "
     "`interfaces/combustion.json` v2.4c (sha256/16 `@@JSON_SHA16@@`). Every change is listed in §17. All edits above §17 "
     "are in place, so lines 1-3161 keep their v2.4b numbers and line references to v2.4b still resolve. v2.4b of this "
     "report (`d8b795478d4013ee`) and of the interface (`fd3a7da6d27c7c66`) are archived in `02-combustion/superseded/v2p4b/`. "
     "The v2.4b header follows unchanged. Version 2.4b, 2026-10-19 (staged 2026-10-13; final fold of LEAD lines 214-228 "
     "and the lead requests of 2026-10-19 in §16).", 'v2.4c', 'version header v2.4c', line=3)
mrep('report', "Needed flow time 1.9 s (<= 1.94 s with the FD-01 element), P_abort 0 at W 0.65 s in 200 000 samples per case,",
     "Needed flow time 1.9 s at the 289.5 K basis (<= 1.94 s with the FD-01 element) and 2.2 s at the 283.15 K relight "
     "corner (REV-COMB-4); the decided 2.43 s flow with the 2.39 s both-open cap (LEAD 253 (7)(ii), final in 256 (2)) covers "
     "283.15-297.15 K unlined, the 2.5 s above being the analysed basis; on that basis P_abort 0 at W 0.65 s in 200 000 "
     "samples per case,", 'R4-07; LEAD 256 (2)', 'needed flow with the cold corner; decided flow', line=24)
mrep('report', "0.30 s with the 2500 N/s ramp to 200 N (0.31 s with the 10 ms frame margin)",
     "0.30 s unlined / 0.31 s lined with the 2500 N/s ramp to 200 N (latest A3 trip 0.282 / 0.290 s + one 10 ms frame, "
     "rounded up to 10 ms; v2.4c wording, REV-COMB-4 R4-14)", 'R4-14', 'hold wording', line=45)
mrep('report', ">= 112 bar abs flush-mounted (103 needed), >= 132 bar abs for a 0.1-1 ms path;",
     ">= 103.4 bar abs flush-mounted (1.1 x 94), >= 133.1 bar abs for a 0.1-1 ms path (1.1 x 121; LEAD 230 (2)); the flight "
     "unit's >= 166.14 bar abs (1.1 x FA1S 151.04; LEAD 249 (4)) covers every path period; range >= 132 bar abs with a "
     "sense line (REV-COMB-4 R4-05, R4-09);", 'R4-05, R4-09', 'stand channel proof and range', line=50)
mrep('report', "<= the torch gate; Electronics E0 + 0.15 s", "= the torch gate, E0 + 0.16 s; Electronics v4, kTorchGate_s",
     'R4-06', 'closure deadline E0 + 0.16 s', count=3)
mrep('report', "<= the torch gate (Electronics: E0 + 0.15 s)", "the torch gate (Electronics v4: E0 + 0.16 s, kTorchGate_s)",
     'R4-06', 'closure deadline E0 + 0.16 s', count=2)
mrep('report', "by the closure deadline <= the torch gate (E0 + 0.15 s)",
     "by the closure deadline, the torch gate (E0 + 0.16 s; Electronics v4)", 'R4-06', 'closure deadline E0 + 0.16 s')
mrep('report', "(2.2 s lined). Over the needed time, P_abort is 0",
     "(2.2 s lined) at the 289.5 K basis; at the 283.15 K relight corner 2.2 s unlined and 2.5 s lined (REV-COMB-4). Over "
     "the needed time, P_abort is 0", 'R4-07', 'cold-corner needed flow', line=519)
mrep('report', "Needed Tp is the worst slip bracket.",
     "Needed Tp is the worst slip bracket. v2.4c (REV-COMB-4 R4-16): the s 1.0 bracket unlined and the swall bracket lined "
     "read 1.2 and 1.3 s, as in `purge_duration_v2p4.json` (checked by the lead against the file; the v2.4b table had 1.1 "
     "and 1.2 s); the governing 1.9 / 2.2 s do not change. These needed times are at the 289.5 K basis; at the 283.15 K "
     "relight corner the need is 2.2 s unlined and 2.5 s lined (REV-COMB-4 R4-07).", 'R4-16, R4-07', 'Table 2.13 note',
     line=691)
mrep('report', "| 1.7 / 1.2 / 1.1 / 1.9 |", "| 1.7 / 1.2 / 1.2 / 1.9 |", 'R4-16', 'Table 2.13 unlined s 1.0: 1.1 -> 1.2 s', count=2)
mrep('report', "| 2.0 / 1.2 / 1.2 / 2.2 |", "| 2.0 / 1.3 / 1.2 / 2.2 |", 'R4-16', 'Table 2.13 lined swall: 1.2 -> 1.3 s', count=2)
mrep('report', "(LEAD line 205): proof >= 112 bar abs, range covering the 45 bar MEOP with the 30 bar abort resolvable",
     "(LEAD line 205): proof >= 166.14 bar abs (1.1 x FA1S 151.04; LEAD line 249 (4), v2.4c), range covering the 45 bar "
     "MEOP with the 30 bar abort resolvable", 'R4-05', 'flight Pc proof 166.14 bar abs', line=1175)
mrep('report', "in-burn abort at 448.15 K for 0.2 s while the MV is open; RELIGHT refused above 433.15 K (§7.4).",
     "in-burn abort at 423.15 K (150 C) for 0.2 s while the MV is open (CHANGELOG 243 (3), 249 (1); it supersedes the "
     "448.15 K of 188 (5)); RELIGHT refused above 403.15 K (130 C, kCaseRelightMax_K, 249 (4); it supersedes 433.15 K) "
     "(§7.4; v2.4c lead consistency fold).", 'LEAD 243 (3), 249 (4)', 'case TC limits 423.15 / 403.15 K', line=1687)
mrep('report', "command ABORT at t_E2 + 0.5 s (pcf_tmax 0.5 s, line 181 (4); the 0.8 s of the v2.4a text is superseded)",
     "command ABORT at t_E2 + 0.8 s (pcf_tmax 0.8 s, ADOPTED by line 227 (5); the 0.5 s of line 181 (4) is superseded)",
     'R4-04', 'ABORT at t_E2 + 0.8 s', line=1807)
mrep('report', "proof >= 112 bar abs (lead basis 1.1 x 102; 132 bar abs on Combustion's all-case 0.1-1 ms value, OI-41)",
     "proof >= 166.14 bar abs (1.1 x FA1S 151.04; LEAD line 249 (4)); C1 Kulite XTL-190SM-2000A 206.8 bar abs (DATASHEET "
     "1.5x rule) meets it; OI-41 DECIDED by line 230 (2)", 'R4-05', 'flight Pc proof 166.14 bar abs', line=1866)
mrep('report', "P_torch 070BG (ENG-09 >= 70 bar; RC-13 d);",
     "P_torch 070BG (ENG-09 >= 70 bar; RC-13 d; it sees the FA-1 passage pressure, design case FA1S 151.04 bar abs: its "
     "proof (>= 166.14 bar abs, or isolation) and its saturation and recovery are Electronics v2.12 items, REV-COMB-4 "
     "R4-12);", 'R4-12', 'P_torch transducer note', line=1866)
mrep('report', "RELIGHT refused if a case thermocouple reads > 433.15 K (LEAD).",
     "RELIGHT refused if a case thermocouple reads > 403.15 K (130 C; LEAD 249 (4), kCaseRelightMax_K; the 433.15 K of "
     "v2.4b is superseded).", 'LEAD 249 (4)', 'relight refusal 403.15 K', line=1884)
mrep('report', "Either case thermocouple > 448.15 K for 0.2 s, armed while the MV is open (LEAD; supersedes 433.15 K)",
     "Either case thermocouple > 423.15 K (150 C) for 0.2 s, armed while the MV is open (LEAD 243 (3), 249 (1); supersedes "
     "448.15 K and 433.15 K)", 'LEAD 243 (3)', 'A12 case abort 423.15 K', line=1966)
mrep('report', "RELIGHT refused if a case TC > 433.15 K at the command",
     "RELIGHT refused if a case TC > 403.15 K at the command (249 (4))", 'LEAD 249 (4)', 'A12 relight refusal 403.15 K',
     line=1966)
mrep('report', "and the flight Pc proof (1.1 x 102 = 112 bar abs, line 205) follows from it.",
     "and the flight Pc proof follows from it (v2.4c: decided by lines 230 (2) and 249 (4): band values 94 / 121 / 147 / "
     "94 bar abs; flight Pc proof >= 166.14 bar abs = 1.1 x FA1S).", 'R4-05', 'OI-41 decided', line=2106)
mrep('report', "(LEAD line 205; proof >= 112 bar abs, range covering the 45 bar MEOP; §7.4)",
     "(LEAD line 205; proof >= 166.14 bar abs, line 249 (4); range covering the 45 bar MEOP; §7.4)", 'R4-05',
     'flight Pc proof 166.14 bar abs', line=2279)
mrep('report', ">= 100 bar abs with proof >= 112 bar abs flush-mounted (>= 132 bar abs for a 0.1-1 ms path; > 1 ms not acceptable) (LEAD line 194 (7); T1-T4 v3).",
     ">= 100 bar abs (>= 132 bar abs with a sense line) with proof >= 103.4 bar abs flush-mounted (>= 133.1 bar abs for a "
     "0.1-1 ms path; > 1 ms not acceptable; line 230 (2)) (LEAD line 194 (7); T1-T4 v3.1).", 'R4-05, R4-09',
     'stand channel proof and range', line=2396)
mrep('report', "flush mount >= 103 bar abs, carried as the 112 bar abs class of the line-205 flight unit; a 0.1-1 ms path >= 132 bar abs;",
     "flush mount >= 103.4 bar abs (1.1 x 94); a 0.1-1 ms path >= 133.1 bar abs (1.1 x 121; line 230 (2)); the line-249 (4) "
     "flight unit (>= 166.14 bar abs) covers every path period; range >= 132 bar abs with a sense line (REV-COMB-4 R4-09);",
     'R4-05, R4-09', 'stand channel proof and range', line=2408)
mrep('report', "(seat-mounted, proof >= 112 bar abs per the lead; Combustion's all-case 0.1-1 ms value gives 132 bar abs, OI-41)",
     "(seat-mounted, proof >= 166.14 bar abs = 1.1 x FA1S 151.04, line 249 (4); the C1 Kulite XTL-190SM-2000A, 206.8 bar "
     "abs, meets it; OI-41 DECIDED by line 230 (2))", 'R4-05', 'OI-6 row: proof 166.14 bar abs', line=2520)
mrep('report', "range >= 100 bar abs, proof >= 112 bar abs flush (>= 132 bar abs for a 0.1-1 ms path; > 1 ms not acceptable; line 194 (7))",
     "range >= 100 bar abs (>= 132 bar abs with a sense line), proof >= 103.4 bar abs flush (>= 133.1 bar abs for a "
     "0.1-1 ms path; > 1 ms not acceptable; lines 194 (7), 230 (2))", 'R4-05, R4-09', 'OI-34 row: proof and range', line=2553)
mrep('report', "(E rule until OI-51) | Lead; Mechanical |",
     "(E rule until OI-51). v2.4c: " + OI41_STATUS + " | Lead (decided); Mechanical |", 'R4-08', 'OI-41 row DECIDED', line=2560)
mrep('report', "adds about 0.66 g per K above 289.5 K (OI-49) | Lead; Electronics; founders |",
     "adds about 0.66 g per K above 289.5 K (OI-49). v2.4c: " + OI42_STATUS + " | Lead (decided); Electronics; founders |",
     'R4-08', 'OI-42 row ADOPTED', line=2561)
mrep('report', "| ABORT at t_E2 + 0.8 s (v2.4a §7.3) | Line 181 (4) set pcf_tmax 0.5 s | Corrected (R3-09) |",
     "| ABORT at t_E2 + 0.8 s (v2.4a §7.3) | 181 (4) set 0.5 s; 227 (5) re-adopted 0.8 s | Current: t_E2 + 0.8 s |",
     'R4-04', 'superseded-evidence row', line=2639)
mrep('report', "pcf_tmax: at 0.21776 mm every corner that reaches 37.16 N does so by E2 + 0.205 s (+3 frames 0.235 s), inside "
     "both windows; the 3 corners that never reach it are not rescued by a longer window (F at 1 s >= 36.33 N), so the "
     "0.8 s window of line 227 (5) is not limited by the lit side.",
     "pcf_tmax: at 0.21776 mm every corner that reaches 37.16 N within E2 + 0.857 s does so by E2 + 0.205 s (+3 frames "
     "0.235 s), inside both windows; 3 of 72 corners never reach 37.16 N in the 0.5 or 0.8 s window: one "
     "(Cd0.65|a0.6|n0.68|ri0.3|eta0.85) crosses at E2 + 0.857 s (a window >= 0.887 s with 3 frames would rescue it), the "
     "other two stay below 37.16 N to the end of the 1.0 s record (36.33 / 36.80 N, still rising); the count is the same "
     "for every window from 0.235 to 0.857 s, so the 0.8 s window of line 227 (5) is not limited by the lit side; the low "
     "corners are a threshold matter (GNC / lead) (v2.4c, REV-COMB-4 R4-03).", 'R4-03', 'P4c sentence corrected', line=3120)
mrep('report', "and 2.10 % at n 0.68 (above it, as at 8.258 s: OI-40),",
     "and 2.10 % at n 0.68 (above it, as at 8.258 s: OI-40) (v2.4c basis note, REV-COMB-4 R4-15: 1.86 / 2.05 % x 8.443 / "
     "8.258 s = 1.902 / 2.096 % [DERIVED]; if the 1.86 % belongs to the 8.24 s record, as stated below, the values are "
     "1.906 / 2.100 %, rounding to 1.91 / 2.10 %; the NZ-01 conclusions do not change),", 'R4-15', 'time-basis note',
     line=3136)

# ---------------------------------------------------------------- DATASHEET-INPUTS v2.4c (no line references: rows may be added)
DL = TXT['ds'].split('\n')


def ds_row(prefix):
    idx = [i for i, s in enumerate(DL) if s.startswith(prefix)]
    assert len(idx) == 1, (prefix, idx)
    return idx[0]


i = ds_row('Version v2.4b, 2026-10-19. Owner: Combustion and Propulsion.')
old = ("Version v2.4b, 2026-10-19. Owner: Combustion and Propulsion. Built by `02-combustion/src/build_datasheet_inputs_v2p4b.py` "
       "from `interfaces/combustion.json` v2.4b (values by key; the published file carries the same values) and the v2.4b "
       "data files named in each row.")
assert DL[i].count(old) == 1
DL[i] = DL[i].replace(old, "Version v2.4c, 2026-10-21. Owner: Combustion and Propulsion. Edited by the lead "
                      "(`02-combustion/src/apply_v2p4c_rev_comb_4.py`) from v2.4b (`46a8222018666b1d`, built by "
                      "`02-combustion/src/build_datasheet_inputs_v2p4b.py` from `interfaces/combustion.json` v2.4b) with the "
                      "REV-COMB-4 corrections (R4-03, R4-08, R4-17) and LEAD lines 230 (2), 249 (4) and 256 (2); two rows "
                      "added (FA-1 in gas-filled passages; Pc transducer proof). Values as in `interfaces/combustion.json` "
                      "v2.4c and the data files named in each row.")
LOG.append(('ds', 'header', 'v2.4c', 'version header v2.4c'))
i = ds_row('| Worst-case steady thrust and Pc')
assert DL[i].count("876 N, 42.85 bar abs at the 30 C bound") == 1
DL[i] = DL[i].replace("876 N, 42.85 bar abs at the 30 C bound",
                      "876 N, 42.85 bar abs at a 30 C state (SUPERSEDED in `combustion.json`: 30 C is not credible, the ARM "
                      "interlock is at 24 C; REV-COMB-4 R4-17)")
LOG.append(('ds', 'row Worst-case steady thrust', 'R4-17', '876 N labelled SUPERSEDED'))
i = ds_row('| Start level (relight)')
for o, n in (("dead-engine cold flow <= 12.86 N (CONDITIONAL on CF-3)",
              "dead-engine cold flow <= 12.86 N (CONDITIONAL on CF-3); one of the 3 low corners crosses 37.16 N at E2 + 0.857 s, "
              "the other two stay below it to the end of the 1.0 s record (R4-03); with the SPI flux the cold-flow bound is "
              "19.0-20.1 N over 283.15-289.5 K (19.5 N at 286.70 K), above the 16.31 N margin, so the CF-3 start-lift "
              "acceptance is not a formality (R4-17)"),
             ("`data/v2p4b/p4c_lit_side_v2p4b.json` (`12f7699ddbeeecda`) |",
              "`data/v2p4b/p4c_lit_side_v2p4b.json` (`12f7699ddbeeecda`); `data/v2p4b/cold_flow_start_lift_v2p4b.json` "
              "(`28ce48092f33da1b`) |")):
    assert DL[i].count(o) == 1, o
    DL[i] = DL[i].replace(o, n)
LOG.append(('ds', 'row Start level', 'R4-03, R4-17', 'low corner and SPI-flux bound'))
i = ds_row('| Relight purge flow basis |')
DL[i] = ("| Relight purge flow (decided) | 2.43 s scheduled flow (both-open overlap 2.38 s + 0.05 s) with the 2.39 s both-open "
         "cap (LEAD 253 (7)(ii), final in 256 (2)); needed flow 2.2 / 1.9 / 1.8 s at 283.15 / 289.5 / 297.15 K unlined; vented "
         "N2O at 2.43 s <= 66.7 / 70.8 / 75.1 g at 283.15 / 289.5 / 297.15 K (Cd 0.70), 75.75 g at the 2.44 s of flow the cap "
         "allows; basis 29.25 g/s = 76 g / 2.5982 s of flow at 289.5 K (27.58-31.06 g/s over 283.15-297.15 K) | conditions "
         "(256 (2)): (a) 2.2 s at 283.15 K stated wherever 1.9 s is quoted; (b) measured Cd x A of the two-tap path >= 0.91 x "
         "the Cd 0.70 value (>= 0.95 x with the FD-01 element bound), else re-size; (c) the line stays unlined (lined, "
         "283.15 K needs 2.5 s); (257 (2)): (d) after CF-4 the flow and cap are re-set from the measured Cd x A by the "
         "measured-time form (mass flow at 297.15 K), never above 2.43 / 2.39 s, so the 297.15 K vent stays <= 76 g; at "
         "Cd 0.80 the fixed schedule would vent about 85.5 g at 297.15 K [ESTIMATE] and fail GNC's A1 reserve test (first "
         "fail 82.1 g; REV-GNC-7); Cd 0.60-0.80 ASSUMED; the PURGE command time is set by Electronics v2.12 | LEAD (flow, "
         "cap, re-set rule); DERIVED (REV-COMB-4 on the SIM model; ASSUMED Cd); A1 reserve test DERIVED from SIM (REV-GNC-7) "
         "| `data/v2p4b/purge_basis_line216_v2p4b.json` (`ca2ee1f0ea0f0194`); `reviews/combustion/r4/r4_purge_corners.json` "
         "(`9249ed093c21a3a3`); CHANGELOG 257 (2) |")
LOG.append(('ds', 'row Relight purge flow', 'LEAD 256 (2), 257 (2); R4-08', 'row replaced with the decided flow'))
i = ds_row('| FA-1 hard start: structural load |')
DL[i] = ("| FA-1 hard start: structural load | head equivalent static pressure, all 896 cases, undamped: 93.6 bar abs "
         "(T <= 0.1 ms), 120.3 (0.1-1 ms; 115.4 at zeta 0.02, 109.6 at zeta 0.05), 146.9 (1-20 ms), 93.6 (20-50 ms, at "
         "T = 21.1 ms near its lower edge); peak head pressure 88.0 bar abs; FA1S 151.04 bar abs bounds every period and case "
         "(max 146.88, margin 4.16 bar) | band values 94 / 121 / 147 / 94 bar abs DECIDED for structural SDOF paths (LEAD "
         "230 (2); the line-194 (1) values 90 / 93 / 102 are superseded); FA1S is the design case for pressure-filled passages "
         "(next row); per-mode values are an analysis path only; damping ASSUMED (no modal test) | SIM histories (ASSUMED "
         "inputs); DERIVED spectra; LEAD (230 (2)) | `data/v2p4b/fa1_spectra_damped_v2p4b.json` (`3a84a905052d5364`) |")
DL.insert(i + 1,
          "| FA-1 in gas-filled passages (P_torch passage, Pc port) | design case FA1S 151.04 bar abs uniform over the passage; "
          "linear lossless passage peaks <= 129.9 bar abs at the J-FWD tap and <= 148.7 bar abs at the torch seat (c 150-1200 "
          "m/s); Pc-port face <= 130.2 / 131.3 / 130.5 bar abs (CC-1 6 mm3 / CC-1 20 mm3 / CC-2) over c 181-1200 m/s; the band "
          "values do not bound gas-filled passages | linear lossless duct (ASSUMED); not modelled: wave steepening and shock "
          "reflection, losses, torch-chamber compliance, N2O decomposition, a blocked-outlet deflagration; Mechanical's "
          "tap-wall row at FA1S passes (worst MS_y +0.275, SOAK70 [CALC on SIM]; published with Mechanical's next CHANGELOG "
          "line) | DERIVED (REV-COMB-4 on SIM histories); LEAD design case (230 (1)) | "
          "`reviews/combustion/r4/r4_torch_passage.json` (`8cb4b0c80173b88d`), `r4_pc_port_face.json` (`94f5a39166a8f778`) |")
DL.insert(i + 2,
          "| Pc transducer proof | flight unit >= 166.14 bar abs (1.1 x FA1S 151.04); the C1 Kulite XTL-190SM-2000A pick, "
          "206.8 bar abs (DATASHEET 1.5x rule), meets it; stand dynamic channel: flush >= 103.4 bar abs (1.1 x 94), 0.1-1 ms "
          "path >= 133.1 bar abs (1.1 x 121), range >= 100 bar abs flush and >= 132 bar abs with a sense line | path period "
          "> 1 ms not acceptable for the dynamic channel; the P_torch 070BG over-ranges during FA-1 (its proof and recovery "
          "are Electronics v2.12 items) | LEAD (249 (4), 230 (2)); DATASHEET (C1 rating, Electronics) | `combustion.json` "
          "v2.4c pc_dynamic_channel |")
LOG.append(('ds', 'row FA-1 structural load', 'R4-08; LEAD 230 (2)', 'band values DECIDED'))
LOG.append(('ds', 'new rows', 'R4-01, R4-05, R4-09', 'FA-1 in gas-filled passages; Pc transducer proof'))
i = ds_row('| FA-1 at TC-01 J-FWD (per-mode) |')
o = "| DERIVED on SIM shares (FEA3D) and SIM histories; damping ASSUMED |"
assert DL[i].count(o) == 1
DL[i] = DL[i].replace(o, "| DERIVED on SIM shares (FEA3D) and SIM histories; damping ASSUMED; analysis path only (LEAD 230 (2)): "
                      "TC-01 J-FWD was not met conservatively and the design change is sized to FA1S (230 (1)); shares from "
                      "FEA3D ca2b (ca2c moves the bin bounds by -0.6 to +0.2 bar, REV-COMB-4) |")
LOG.append(('ds', 'row FA-1 at TC-01 J-FWD', 'R4-08, R4-18', 'analysis path only; ca2c'))
i = ds_row('- The FA-1 rows are proposals for the lead (OI-41)')
DL[i] = ("- OI-41 is DECIDED (LEAD 230 (2) band values; 249 (4) flight Pc proof); the per-mode row is an analysis path only and "
         "still depends on the FEA3D share vector (OI-51) and on damping (OI-52). Open: the Z3 restatement of the LC-TB70 "
         "envelope (Mechanical; REV-COMB-4 R4-02); the PURGE command time (Electronics v2.12).")
DL.insert(i + 1, "- pcf_tmax 0.8 s (LEAD 227 (5)) holds on the dead side only with the photodiode main-chamber view (FLAMEOUT_OPT "
          "armed) or the GNC reference re-taken at the ECU E2 / light; photodiode-blind families release 42 / 98 of 1000 dead "
          "runs at 0.8 s (OI-PHOTODIODE-VIEW, open for IGN-1).")
LOG.append(('ds', 'notes', 'R4-08; REV-COMB-4 section 6', 'OI-41 decided; open items; photodiode condition'))
TXT['ds'] = '\n'.join(DL)
for s in TXT['ds'].split('\n'):
    if s.startswith('| ') and not s.startswith('|---'):
        assert s.count('|') == 6, s[:80]

# ---------------------------------------------------------------- invariants on the in-place md edits
for k in ('report', 'cf4', 't1t4', 'resp'):
    a, b = RAW[k].split('\n'), TXT[k].split('\n')
    assert len(a) == len(b), (k, len(a), len(b))
    for n, (x, y) in enumerate(zip(a, b), 1):
        if x.startswith('|'):
            assert x.count('|') == y.count('|'), (k, n)

# ---------------------------------------------------------------- appended sections (CF-4 §13)
CF4_13 = """## 13. v2.2 changes (Combustion v2.4c, 2026-10-21)

Text corrections from REV-COMB-4 (`reviews/REVIEW-COMBUSTION-R4.md`; R3-08 residual, R4-06, R4-07) and the LEAD purge decisions of lines 256 and 257 (2). The edits are in place, so lines 1-191 keep their v2.1 numbers.
- §1 (line 26) and C-RL (line 33): the decided 2.43 s of flow with the 2.39 s both-open cap; the model numbers stay on the analysed 2.5 s, which is more flow than decided.
- Line 35: the needed flow is 1.9 s at 289.5 K and 2.2 s at 283.15 K (LEAD 256 (2)(a)).
- §4 (line 64): at least one IS-2 run at or below 283.15 K, or the cold corner stated model-only.
- §4 (line 66): the vented mass of the decided schedule (<= 75.1 g at 297.15 K, Cd 0.70; 75.75 g at the cap); at Cd 0.80 the same schedule would vent about 85.5 g at 297.15 K [ESTIMATE], which fails GNC's A1 reserve test (REV-GNC-7).
- §4 (line 90): the PURGE command time is the one Electronics v2.12 states.
- P5 (line 102): the measured Cd x A of the two-tap path >= 0.91 x the Cd 0.70 value (>= 0.95 x with the FD-01 element bound), else the flow is re-sized (LEAD 256 (2)(b)); from the measured Cd x A, kPurgeFlow_s and the both-open cap are re-set by the measured-time form with the mass flow at 297.15 K, never above 2.43 / 2.39 s, so the 297.15 K vent stays <= 76 g; without the re-set, Cd x A <= 1.08 x the Cd 0.70 value (LEAD 257 (2); REV-GNC-7); the line stays unlined (256 (2)(c)).
- P6 (line 103) and the v2.0 change list (line 15): the closure deadline is the torch gate, E0 + 0.16 s (Electronics v4, kTorchGate_s).

No test has been run; this specification approves nothing."""
TXT['cf4'] = TXT['cf4'].rstrip('\n') + '\n\n' + CF4_13 + '\n'
LOG.append(('cf4', 'section 13 (new, at the end)', 'v2.4c', 'v2.2 change list'))

# ---------------------------------------------------------------- write CF-4, T1-T4, RESPONSE, DATASHEET; then the JSON
OUT = {}
for k in ('cf4', 't1t4', 'resp', 'ds'):
    b = TXT[k].encode('utf-8')
    open(os.path.join(stage, OUTNAME[k]), 'wb').write(b)
    OUT[k] = sha16(b)

jset(['cf4_gate', 'spec_version'], 'CF-4-SPEC v2.2 (v2.4c, %s)' % OUT['cf4'], 'v2.4c', 'CF-4 v2.2', old=J0['cf4_gate']['spec_version'])
jadd(['files'], 'v2p4c', {
    'v': {'report': '02-combustion/REPORT.md v2.4c (section 17 lists every change)',
          'response': '02-combustion/REVISION-RESPONSE-R3.md (v2.4c annotations; sha256/16 %s)' % OUT['resp'],
          'specs': {'02-combustion/T1-T4-REGRESSION-SPEC.md': {'version': 'v3.1 (v2.4c)', 'sha256_16': OUT['t1t4']},
                    '02-combustion/CF-4-SPEC.md': {'version': 'v2.2 (v2.4c)', 'sha256_16': OUT['cf4']}},
          'datasheet_inputs': '02-combustion/DATASHEET-INPUTS-COMBUSTION.md v2.4c (%s)' % OUT['ds'],
          'writer': '02-combustion/src/apply_v2p4c_rev_comb_4.py (lead; sha256/16 %s)' % SELF,
          'archive_v2p4b': ('02-combustion/superseded/v2p4b/ (combustion.json, REPORT, REVISION-RESPONSE-R3, CF-4, T1-T4, '
                            'DATASHEET-INPUTS; HASHES.txt)'),
          'review': 'reviews/REVIEW-COMBUSTION-R4.md (2908321d7f75d439)'},
    'tag': 'index'}, 'v2.4c', 'file index v2.4c')
J['datasheet_inputs_v2p4c'] = {
    'v': {'file': '02-combustion/DATASHEET-INPUTS-COMBUSTION.md', 'version': 'v2.4c', 'sha256_16': OUT['ds'],
          'builder': '02-combustion/src/apply_v2p4c_rev_comb_4.py (lead edit of the v2.4b file 46a8222018666b1d)',
          'changes': ('R4-03, R4-08, R4-17; LEAD 230 (2), 249 (4), 256 (2), 257 (2); rows added: FA-1 in gas-filled '
                      'passages, Pc transducer proof')},
    'tag': 'index (each row carries its own tag)', 'src': 'REPORT v2.4c section 17'}

# version fields
NOTE = ("v2.4c (2026-10-21, lead): text-only corrections from REV-COMB-4 (reviews/REVIEW-COMBUSTION-R4.md 2908321d7f75d439; "
        "R4-01 to R4-08, R4-12, R4-14 to R4-18 and the section 6 open-item texts) and the decisions of CHANGELOG lines 227 (5), "
        "230, 243 (3), 249 (4), 253 (7), 256 and 257 (2), applied by 02-combustion/src/apply_v2p4c_rev_comb_4.py; no model "
        "run and no SIM, CEA or FE result changed; decided values updated (purge flow 2.43 s and cap 2.39 s, re-set after "
        "CF-4 from the measured Cd x A, proof values, case-TC relight limit 403.15 K, pcf_tmax 0.8 s, closure deadline "
        "E0 + 0.16 s). Every replaced leaf is kept in "
        "superseded_v2p4c with its finding; new blocks fa1_p_torch_v2p4c, fa1_grid_statistics_v2p4c, purge_decision_v2p4c, "
        "electronics_open_issues_v2p4c, igniter_sequence_fields_v2p4c (OI-GEN-TABLES), t4_duration_note_v2p4c, "
        "lead_decisions_folded_v2p4c, datasheet_inputs_v2p4c, edit_log_v2p4c. All v2.4b keys kept.")
STATUS = ("v2.4c REVISION (digital only), 2026-10-21: the lead's text-only fold of REV-COMB-4 (ACCEPT WITH CORRECTIONS, "
          "accepted in CHANGELOG line 256). Design point unchanged. No number is MEASURED. The relight claim is gated by CF-4; "
          "FA-1 is accepted for design continuation only. Folded: OI-41 DECIDED (230 (2) band values 94 / 121 / 147 / 94 bar "
          "abs; FA1S 151.04 bar abs bounds every period and is the design case for gas-filled passages, 230 (1), R4-01); "
          "flight Pc proof >= 166.14 bar abs (249 (4)); purge FINAL: 2.43 s scheduled flow with the 2.39 s both-open cap and "
          "conditions (a)-(c) (253 (7)(ii), 256 (2)), and (d) the CF-4 re-set from the measured Cd x A that keeps the "
          "297.15 K vent <= 76 g (257 (2)); pcf_tmax 0.8 s (227 (5)); closure deadline = torch gate E0 + 0.16 s "
          "(Electronics v4); case-TC relight limit 403.15 K (249 (4)). Open: the Z3 restatement (R4-02, Mechanical; "
          "fa1_grid_statistics_v2p4c); the PURGE command time (Electronics v2.12); OI-49 to OI-52. A1 apogee target 210 m "
          "DECIDED; tank 2.00 kg. Nothing here is physical approval.")
jset(['version'], 'v2.4c', 'v2.4c', 'version', old='v2.4b')
jset(['date'], '2026-10-21', 'v2.4c', 'date', old='2026-10-19')
jset(['revision_note'], NOTE, 'v2.4c', 'revision note')
J['revision_history'].append(J0['revision_note'])
LOG.append(('json', 'revision_history[%d] (new)' % (len(J['revision_history']) - 1), 'v2.4c', 'v2.4b revision note kept'))
jset(['status'], STATUS, 'v2.4c', 'status')
jset(['supersedes'], ("combustion.json v2.4b (fd3a7da6d27c7c66), kept as 02-combustion/superseded/v2p4b/combustion.json; v2.4a "
                      "(5237d4584bad38c4) as before (02-combustion/data/v2/combustion_interface_v2p4a_as_published.json and "
                      "02-combustion/superseded/v2p4a/combustion.json)"), 'v2.4c', 'supersedes')
J['superseded_v2p4c'] = {'v': SUP, 'version': 'v2.4b', 'superseded_by': 'v2.4c (2026-10-21)',
                         'tag': 'history: every leaf replaced in v2.4c, keyed by its path, with the finding or decision that replaced it'}
J['edit_log_v2p4c'] = {
    'v': [{'file': OUTNAME[k] if k != 'json' else 'combustion.json', 'where': w, 'by': f, 'what': t} for k, w, f, t in LOG],
    'script': '02-combustion/src/apply_v2p4c_rev_comb_4.py', 'script_sha256_16': SELF, 'stamp_utc': stamp,
    'inputs_sha256_16': {SRC[k][0]: SRC[k][1] for k in SRC},
    'outputs_sha256_16': {SRC[k][0]: OUT[k] for k in OUT},
    'note': 'the REPORT rows of section 17 are added after this file is written; REPORT cites this file by sha',
    'tag': 'index'}

# every v2.4b key path is kept
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
for ps, rec in SUP.items():
    pass  # originals were deep-copied from the v2.4b tree before each change
jb = json.dumps(J, indent=1, ensure_ascii=False).encode('utf-8')
open(os.path.join(stage, 'combustion.json'), 'wb').write(jb)
OUT['json'] = sha16(jb)

# ---------------------------------------------------------------- REPORT: header sha and section 17
assert TXT['report'].count('@@JSON_SHA16@@') == 1
TXT['report'] = TXT['report'].replace('@@JSON_SHA16@@', OUT['json'])
FNAME = {'json': 'interfaces/combustion.json', 'report': 'REPORT.md', 'cf4': 'CF-4-SPEC.md', 't1t4': 'T1-T4-REGRESSION-SPEC.md',
         'resp': 'REVISION-RESPONSE-R3.md', 'ds': 'DATASHEET-INPUTS-COMBUSTION.md'}
rows = []
for k, w, f, t in LOG:
    cell = lambda s: s.replace('|', '/').replace('`', '')
    rows.append('| %s | %s | %s | %s |' % (FNAME[k], cell(w), cell(f), cell(t)))
SEC17 = """## 17. v2.4c: REV-COMB-4 corrections and LEAD lines 256-257 (2026-10-21)

Applied by the lead with `src/apply_v2p4c_rev_comb_4.py` (sha256/16 `{self}`, run at {stamp} from date -u). Text only: no model was re-run and no SIM, CEA or FE result changed. Sources: `reviews/REVIEW-COMBUSTION-R4.md` (`2908321d7f75d439`; REV-COMB-4, ACCEPT WITH CORRECTIONS: 0 blocking, 2 major, 11 minor, 5 notes), CHANGELOG line 256 (the lead accepts the review and makes the purge decision final) and line 257 (2) (the purge re-set rule, on REV-GNC-7's A1 reserve finding). Lines 1-3161 keep their v2.4b numbers; this section is new. Files: `interfaces/combustion.json` v2.4c (`{json}`), `CF-4-SPEC.md` v2.2 (`{cf4}`), `T1-T4-REGRESSION-SPEC.md` v3.1 (`{t1t4}`), `REVISION-RESPONSE-R3.md` with v2.4c annotations (`{resp}`), `DATASHEET-INPUTS-COMBUSTION.md` v2.4c (`{ds}`). The v2.4b set is archived in `superseded/v2p4b/` with `HASHES.txt`.

### 17.1 Decisions folded

- **Purge (line 253 (7)(ii), FINAL in 256 (2)).** 2.43 s scheduled flow (both-open overlap 2.38 s + 0.05 s) with the 2.39 s both-open cap. The records, tables and model numbers of §2.8 and CF-4 were run with 2.5 s of flow (PURGE at E0 - 2.90 s) and stay the analysed basis, which is more flow than decided. Needed flow (REV-COMB-4, DERIVED on the author's model, Cd 0.70 ASSUMED): 2.2 / 1.9 / 1.8 s at 283.15 / 289.5 / 297.15 K unlined; 2.5 s lined at 283.15 K (P_abort 0.061 at 2.43 s lined). Margins at 2.43 s unlined: 0.23 / 0.53 / 0.63 s; 0.18 / 0.13 s at 283.15 K with the FD-01 element bounds. Vented N2O at 2.43 s, Cd 0.70: <= 66.7 / 70.8 / 75.1 g; 75.75 g at the 2.44 s of flow the cap allows. Conditions (256 (2)): (a) 2.2 s at 283.15 K is stated wherever 1.9 s is quoted; (b) CF-4 / B-BLEED-1 shows a measured Cd x A of the two-tap path >= 0.91 x the Cd 0.70 value (>= 0.95 x with the FD-01 element bound), else the flow is re-sized; (c) the line stays unlined. Condition (d) (257 (2)): at Cd 0.80 the fixed schedule would vent about 80.5 g at 289.5 K and 85.5 g at 297.15 K (85.8 g at the cap) [ESTIMATE]; GNC's A1 reserve test (line 208, REV-GNC-7, DERIVED from SIM, ESTIMATE above 80 g) passes 76 g and 80.5 g and first fails at 82.1 g. So after CF-4, kPurgeFlow_s and the both-open cap are re-set from the measured Cd x A by the measured-time form of `purge_basis_line216_v2p4b`, with the mass flow at 297.15 K (overlap <= 76 g / mdot(297.15 K) - (t_close - t_open)), never above 2.43 / 2.39 s. The 297.15 K vent then stays <= 76 g at any measured Cd x A, and the 283.15 K margin stays positive because need and limit both scale with 1 / (Cd x A): 0.23 s at a Cd x A ratio of 1, 0.21 s at 1.08 and 1.13, 0.19 s at 1.2, on the 10 ms steps [DERIVED; the scaling ASSUMED, as in (b)]. Without the re-set, the measured Cd x A must also be <= 1.08 x the Cd 0.70 value (vent <= 82 g, REV-GNC-7's bound), or GNC re-runs the reserve test at the measured vented mass. A temperature-scheduled flow is not adopted. The PURGE command time is Electronics' (v2.12): E0 - 2.90 s ends the 2.43 s flow at E0 - 0.12 s, E0 - 2.83 s at E0 - 0.05 s [DERIVED]. The 253 (7)(ii) re-fly-trigger wording is withdrawn (R4-11). `combustion.json` `purge_decision_v2p4c`.
- **FA-1 load (OI-41 DECIDED by 230 (2)).** Band values 94 / 121 / 147 / 94 bar abs for structural SDOF paths; FA1S 151.04 bar abs bounds every period and case (max 146.88, margin 4.16 bar) and is the design case for gas-filled passages; per-mode values are an analysis path only.
- **Pc transducer proof (249 (4)).** Flight unit >= 166.14 bar abs = 1.1 x FA1S (166 and 166.1 understate 1.1 x 151.04); the C1 Kulite XTL-190SM-2000A pick (206.8 bar abs, DATASHEET 1.5x rule) meets it. Stand dynamic channel: flush >= 103.4 bar abs (1.1 x 94), 0.1-1 ms path >= 133.1 bar abs (1.1 x 121), range >= 100 bar abs flush and >= 132 bar abs with a sense line (R4-09).
- **pcf_tmax 0.8 s (227 (5)).** Current; the 0.5 s of 181 (4) is superseded (R4-04). It holds on the dead side only with the photodiode main-chamber view (FLAMEOUT_OPT armed) or the GNC reference re-taken at the ECU E2 / light (OI-PHOTODIODE-VIEW).
- **Closure deadline (R4-06).** The torch gate, E0 + 0.16 s (Electronics v4, kTorchGate_s).
- **Case thermocouple limits (lead consistency fold).** In-burn abort at 423.15 K (150 C) for 0.2 s (CHANGELOG 243 (3); channel accepted in 249 (1)); RELIGHT refused above 403.15 K (130 C, kCaseRelightMax_K, 249 (4)). They replace the 448.15 K and 433.15 K this report still quoted; REV-COMB-4 did not list them, and the lead found them while applying v2.4c.

### 17.2 FA-1 in gas-filled passages (R4-01, R4-09) and the Z3 restatement (R4-02)

- **P_torch.** 102 bar abs does not cover the torch passage during FA-1. On the reviewer's linear lossless two-segment duct (ASSUMED) driven by the 896 head histories, the J-FWD tap station peaks at 129.85 / 121.96 / 116.61 / 108.00 bar abs at c 150 / 181 / 202 / 222 m/s (48 / 42 / 36 / 12 cases above 102; 22 at c 400-450), the closed seat at up to 148.72 bar abs, and no case exceeds 151.04 bar abs at any c from 150 to 1200 m/s [DERIVED]. Design case: FA1S 151.04 bar abs uniform over the passage. Mechanical's tap-wall row at that load (DLF 1.0) passes, worst MS_y +0.275 at SOAK70 [CALC on SIM], and closes R4-01 when Mechanical publishes it. Not modelled: wave steepening and shock reflection, losses, torch-chamber compliance, N2O decomposition, a blocked-outlet deflagration. The P_torch 070BG over-ranges during FA-1; its proof and recovery are Electronics items (R4-12). `fa1_p_torch_v2p4c`.
- **Pc port.** Lossless bound over c 181-1200 m/s: 130.2 / 131.3 / 130.5 bar abs (CC-1 6 mm3 / CC-1 20 mm3 / CC-2); the C1 over-range margin is >= 6.6 bar at c >= 181 m/s, not about 16 bar (Electronics v2.12).
- **Z3 (OPEN, Mechanical).** The 46 head peaks above 75.519 bar abs (141 above 63.1, 185 above 60; max 88.02) are physical SIM bracket cases on the ASSUMED construct. All 46 leave Z3 by the peak only (time above 63.1 bar abs <= 1.669 ms against 3.0; 10-90 % rise >= 0.842 ms against 0.8). Raising only the ceiling to 88.1 bar abs admits pulses with an ESP of 171.45 / 165.03 / 152.60 bar abs, above FA1S; Z3 as written admits 147.29. Proposed Z3': head peak <= 88.1 bar abs AND undamped SDOF ESP of the head history <= 151.04 bar abs at every period 0.02-50 ms (every grid case meets it: max 146.88 at 3.5 ms). The lead rules at Mechanical's pre-publication post; 253 (7)(i) stays adopted on that condition. `fa1_grid_statistics_v2p4c`.

### 17.3 Changes, by file

| File | Where | Finding or decision | Change |
|---|---|---|---|
{rows}
| REPORT.md | section 17 (new, at the end) | v2.4c | this section |

### 17.4 Not changed, and open

- The §2.8 tables, the CF-4 model numbers and the vented-mass brackets keep the 2.5 s analysed basis.
- REVISION-RESPONSE-R3 keeps its v2.4b answers; v2.4c only annotates them.
- Open: the Z3 restatement (Mechanical; R4-02); the PURGE command time and the CF-4 re-set of the purge constants (Electronics v2.12; 257 (2)); the Electronics items R4-09, R4-12, R4-13 and the S6R / N-04 re-classification (v2.12); N-07, the T4 N2O (GNC, REV-GNC-7; T1-T4 v3.1 line 294); OI-PHOTODIODE-VIEW (IGN-1); OI-UNPURGED-RELIGHT; OI-49 to OI-52 as in §16.10.
- Nothing in this section is physical approval.
""".format(self=SELF, stamp=stamp, json=OUT['json'], cf4=OUT['cf4'], t1t4=OUT['t1t4'], resp=OUT['resp'], ds=OUT['ds'],
           rows='\n'.join(rows))
TXT['report'] = TXT['report'].rstrip('\n') + '\n\n' + SEC17
b = TXT['report'].encode('utf-8')
open(os.path.join(stage, 'REPORT.md'), 'wb').write(b)
OUT['report'] = sha16(b)

summary = {'stamp': stamp, 'script_sha16': SELF, 'out_sha16': OUT, 'json_leaves_replaced': len(SUP),
           'log_rows': len(LOG), 'by_file': {k: sum(1 for r in LOG if r[0] == k) for k in FNAME}}
open(os.path.join(stage, 'APPLY-SUMMARY.json'), 'w').write(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
