# Append CHANGELOG 193/194, SUPERVISION REV-COMB-3, REQUIREMENTS amendments (183, 186, 188, 194).
import json, hashlib, sys

HUB = '/home/claude/work/shared-fallback/engine'
CL = f'{HUB}/interfaces/CHANGELOG.md'
SUP = f'{HUB}/reviews/SUPERVISION.json'
REQ = f'{HUB}/00-requirements/REQUIREMENTS.md'


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


assert h16(CL) == '6b0d6d439e2f3439', h16(CL)
assert h16(SUP) == '8e0346a9fb0e07a0', h16(SUP)
assert h16(REQ) == 'ef308e24783cba0e', h16(REQ)
REV = h16(f'{HUB}/reviews/REVIEW-COMBUSTION-R3.md')
assert REV == 'a786101f28d45d6f', REV

lines = open(CL).read().split('\n')
if lines[-1] == '':
    lines = lines[:-1]
assert len(lines) == 192, len(lines)
n193, n194 = len(lines) + 1, len(lines) + 2

l193 = (
    "2026-10-13 | review | (result) | REV-COMB-3 independent re-review of Combustion v2.4a (REPORT 062e307a8d25e1ec, "
    "REVISION-RESPONSE-R2 e99595103ee17214, CF-4-SPEC a94211a295fe0224, T1-T4-REGRESSION-SPEC bbf0ea642453dc7a, combustion.json "
    "5237d4584bad38c4) and of lead line 186: REVISE (targeted); 0 BLOCKING, 2 MAJOR, 8 MINOR, 7 NOTE. MAJOR R3-01: the E2 + 0.22 s "
    "release hold of the 186 (1) alternative comes from one state (LO-worst unlined gap 0.193 s + 22 ms A3); over the PURGE NOT RUN "
    "records the latest A3 trip after E2 is 0.282 s (LO unlined) on the 2500 N/s ramp to 200 N, 0.177 s on the ramp to 500 N and "
    "0.727 s with flow held at the lift, so ~0.30 s / ~0.19 s / no hold within W; at 0.22 s the released-then-A3 class remains "
    "(LO ramp mean 0.054, max 0.41). MAJOR R3-02: the FA-1 pressure DLF stops at 1 ms; from the 896 stored histories the equivalent "
    "static pressure is 112-146 bar abs at 1.5-10 ms (all cases: head 146.3, aft 146.4 at 3 ms; baseline head 138.8), and line 173 "
    "has no period domain. MINOR: R3-03 the 1.8 kN x 4 ms rectangle bounds only to ~20 ms (FA-1 above it at >= 25 ms; impulse above "
    "steady 28.4 vs 7.2 N s, on the ASSUMED pool plateau); R3-04 92 bar is below the author's own 92.2-92.9 estimate (published 0.1 ms "
    "histories give 90.7 at 0.25 ms); R3-05 the start-level cold-flow margin (1.22-1.30x on Cd x A x G) is untested at the start "
    "lift; R3-06 T1-T4 flux test one-sided; R3-07 T1-T4 lacks red lines, validity rules, char removal, counts and N2O (T1 2t = 8 s "
    "uses 1.93 kg); R3-08 CF-4 lacks red lines, IS-1/IS-2 preparation, probe threshold, run/N2O budget, and is baselined on v3.4.1 "
    "with stale section 1; R3-09 stale text (0.6 s claim, 0.81 s scope, E2 + 0.8 s, 316L lip; H19 melt bound to recompute for "
    "IN718); R3-10 stand dynamic Pc channel range unstated (070BG >= 70 bar clips the 83-88 bar peaks). NOTES R3-11..R3-17 incl. "
    "R3-14 heat TO-VERIFY belongs at the injector body, R3-15 frozen prediction for NZ-01, R3-17 landing outlet dip at 60-80 g "
    "against GNC's ASSUMED 60 g residual. Line 186: (1) L* 1.3 s FOLLOWS, the 0.22 s alternative does NOT; (2) FOLLOWS as a design "
    "mitigation, margin conditional; (3) usable only with a prediction frozen before each firing; (4), (5) FOLLOW. Reproduced with "
    "own code: unpurged classes (Table 2.17 within 0.0012), cold-flow bound (54 rows within 9.4e-6), tank arithmetic, FA-1 tables "
    "(author SDOF within 1.56 %). SIM/DERIVED; not physical approval | "
    f"reviews/REVIEW-COMBUSTION-R3.md {REV}; reviews/combustion/r3/MANIFEST_REV-COMB-3.sha256 a8ddc0f9854683d4 (16/16 re-verified "
    "by lead); SUPERVISION.json REV-COMB-3; why: lead 186 (6)"
)

l194 = (
    f"2026-10-13 | lead | (decision) | On REV-COMB-3 (line {n193}): verdict recorded as given (REVISE, targeted). "
    "(1) R3-02/R3-04, line 173 RESTATED with a period domain (replaces its 'for all parts' sentence and the 92 bar value): the FA-1 "
    "equivalent static pressure at head and aft is 90 bar abs quasi-static only for load paths whose governing natural period T <= "
    "0.1 ms; for 0.1 < T <= 1 ms, yield at 93 bar abs (design; R3-04, replaces 92; J-FWD A4-80 stays positive, about +0.28 DERIVED "
    "from +0.29 at 92) and ultimate at 102 bar abs (sensitivity); for T > 1 ms, yield and ultimate at the all-case spectrum value at "
    "the part's period (Combustion v2.4b publishes head and aft spectra to >= 20 ms; reviewer DERIVED up to 146.4 bar abs at 3 ms), "
    "or at Mechanical's FA1S step case (DLF 2.0, about 151 bar abs), which is the design case for every pressure-loaded load path "
    "until Mechanical's modal closure (188 (8)) lists each path with its period and basis. Candidates to list first: pintle and "
    "servo linkage, equipment on the forward closure (FS-01/MV-P, bleed valves), nozzle on the J1 lip, Pc port and sense line. SF "
    "1.0 as in 188 (9). mechanical.json v2.2 carries the FA-1 entry with this domain (amends 186 (4)). A part that fails at its "
    "period is a DESIGN CHANGE item, or Mechanical shows its period from the modal model. "
    "(2) R3-03: the 1.8 kN x 4 ms thrust rectangle is the load only for parts with T <= 20 ms (REQUIREMENTS l.118 'low-frequency "
    "parts' corrected); for T > 20 ms (vehicle modes, equipment on isolators, tank mounts) the FA-1 long-period thrust spectrum "
    "(reviewer DERIVED: 1.76 kN at 25 ms, 1.45 kN at 40 ms, 1.04 kN at 100 ms, whole history; pool plateau ASSUMED) is the load. "
    "Combustion publishes it in v2.4b; the lead carries it into ICD-AIRFRAME v2.1 for the airframe owner. "
    "(3) R3-01: the 'E2 + 0.22 s' of 186 (1) is WITHDRAWN. The unpurged alternative is flown by GNC only as a comparator with the "
    "population hold table: H >= 0.30 s with the 2500 N/s ramp to 200 N flown during the hold, H >= 0.19 s with the ramp to 500 N, "
    "and no admissible hold with flow held at the start lift. Because 186 (2) holds the command at the start level while the "
    "drogue is attached with Pc invalid, the alternative is not admissible with Pc invalid. GNC counts the residual "
    "released-then-A3 class from Combustion's per-record classes (v2.4b) and the P cost of the longer hold (REPORT l.1727). The "
    "baseline of 186 (1) is unchanged: below L* = 1.3 s no purge and no unpurged relight; the adoption rule is unchanged. "
    "(4) R3-05/R3-14: the 186 (2) command hold stays ADOPTED; its 16.31 N margin is stated as CONDITIONAL on Cd x A x G at the start "
    "lift. CF-3 adds a start-lift point: mdot and load-cell F at the start-level lift with the encoder lift recorded; acceptance F "
    "<= 16.31 N minus the heat allowance, or mdot <= 52.6-56.3 g/s; a failure returns the hold level and the W10 rule to the lead. "
    "The heat TO-VERIFY moves from chamber heat pick-up to injector-body and feed soak-back temperature at the relight (heat at tank "
    "pressure, threshold 2.8-3.7 kW). GNC's R2 v2 uses F_cold plus the grain_q1d start-level lit history (fuel-starved 0.1-0.4 s at "
    "0.2039 mm), not 62.5 N x pcf_k. "
    "(5) R3-15/R3-16: 186 (3) reads '... more than 2 % beyond the erosion predicted for that firing, the prediction frozen before "
    "the firing and updated only with earlier firings'. 186 (5) reads 'quasi-static coverage needs 13.6 mm of liquid (78.6-82.5 g); "
    "766 g remains at the end of the purge flow, 9.3-9.7x'. "
    "(6) R3-17: GNC checks the landing usable reserve against the outlet dip onset (60-62 g at 125 N, 68-69 g at 250 N, 78-80 g at "
    "500 N; DERIVED) instead of the ASSUMED 3 % (60 g) residual; Mechanical's OI-32 outlet geometry closes it. "
    "(7) R3-10: the stand dynamic Pc channel for IGN-1 and the T series is >= 100 bar abs with a stated proof rating (founder "
    "instrumentation item); Electronics states the 070BG flight transducer's over-range behaviour and its effect on the 30 bar "
    "abort, the Pc-valid flag and the logged FA-1 peak. "
    "(8) R3-06/R3-07/R3-08: the T1-T4 flux test becomes two-sided (shown only if |S - S_ox| <= 1.645 sigma; S below that is "
    "'neither shown': the default gate stays and Combustion re-evaluates the burn limit on the measured axial profile). T1-T4 and "
    "CF-4 gain red lines and abort criteria, validity rules for short firings, the IS-1/IS-2 preparation, the continuous-liquid "
    "probe threshold, the char-removal procedure, counts and N2O budgets (T1 at 2t = 8 s uses 1.93 kg: state the stand tank "
    "capacity or shorten t) and a TO-QUOTE line (Sønderborg DK-6400). CF-4 is re-baselined on the frozen v3.5.1 bleed path. "
    "(9) R3-09/R3-11: v2.4b folds line 186 and this line, removes the stale text, and recomputes the H19 lip-melt bound for IN718 "
    "with a datasheet melting range (the recalled 1260-1336 C is TO-VERIFY). "
    "(10) Combustion v2.4b is launched (max); re-review is a delta check of the R3-01 and R3-02 numbers, the rest by document diff. "
    "Nothing here is physical approval | lead"
)

lines += [l193, l194]
open(CL, 'w').write('\n'.join(lines) + '\n')

# --- SUPERVISION ---------------------------------------------------------------------------
d = json.load(open(SUP))
assert 'REV-COMB-3' not in [r['id'] for r in d['reviews']]
d['reviews'].append({
    'id': 'REV-COMB-3',
    'date': '2026-10-13',
    'reviewer': 'Independent reviewer agent (not the author; not the REV-COMB-1 or REV-COMB-2 author)',
    'author': 'Combustion specialist agent',
    'deliverable': '02-combustion v2.4a (REPORT.md, REVISION-RESPONSE-R2.md, CF-4-SPEC.md, T1-T4-REGRESSION-SPEC.md, combustion.json v2.4a) and lead line 186',
    'hashes_sha256_16': {
        '02-combustion/REPORT.md': '062e307a8d25e1ec',
        '02-combustion/REVISION-RESPONSE-R2.md': 'e99595103ee17214',
        '02-combustion/CF-4-SPEC.md': 'a94211a295fe0224',
        '02-combustion/T1-T4-REGRESSION-SPEC.md': 'bbf0ea642453dc7a',
        'interfaces/combustion.json': '5237d4584bad38c4',
        '02-combustion/data/v2p4a/HASHES.txt': 'b5e951a4864badd1',
    },
    'criteria': '(a) status of the R2 items; (b) independent re-derivation with own code: unpurged-start classes over the PURGE NOT RUN records, cold-flow bound, tank-outlet arithmetic; (c) FA-1 tables against the line 173 rule incl. pressure and thrust SDOF spectra beyond 1 ms; (d) founder executability of CF-4 and T1-T4; (e) whether line 186 (1)-(5) follow from the evidence; (f) stale values in and after the fold',
    'verdict': 'REVISE (targeted)',
    'blocking': [],
    'major': [
        'R3-01 E2 + 0.22 s release hold from one state; population needs ~0.30 s on the 200 N ramp, none with lift flow',
        'R3-02 FA-1 pressure DLF truncated at 1 ms (112-146 bar abs at 1.5-10 ms); line 173 lacks a period domain',
    ],
    'minor': ['R3-03', 'R3-04', 'R3-05', 'R3-06', 'R3-07', 'R3-08', 'R3-09', 'R3-10'],
    'notes': ['R3-11', 'R3-12', 'R3-13', 'R3-14', 'R3-15', 'R3-16', 'R3-17'],
    'rev_comb_2_status': 'R2-03, R2-09, R2-11 PARTLY; R2-01, R2-10, R2-13 CONFIRMED; R2-04 CLOSED (new defects R3-06/07)',
    'line_186_assessment': '(1) L* 1.3 s FOLLOWS, 0.22 s alternative does not; (2) FOLLOWS as design mitigation, margin conditional; (3) usable with frozen prediction; (4) FOLLOWS; (5) FOLLOWS, wording',
    'confirmed': 'unpurged classes (Table 2.17 within 0.0012), cold-flow bound (54 rows within 9.4e-6), tank arithmetic, FA-1 Tables 7.6a/b exact, author SDOF within 1.56 %; SDOF self-test < 0.1 %',
    'reviewer_artefacts': {
        'dir': 'reviews/combustion/r3/',
        'manifest': 'reviews/combustion/r3/MANIFEST_REV-COMB-3.sha256',
        'manifest_sha256_16': 'a8ddc0f9854683d4',
        'verified_by_lead': '16/16 OK',
    },
    'review_file': 'reviews/REVIEW-COMBUSTION-R3.md',
    'review_file_sha256_16': REV,
    'lead_disposition': f'CHANGELOG line {n194}',
    'not_physical_approval': True,
})
open(SUP, 'w').write(json.dumps(d, indent=1, ensure_ascii=False))

# --- REQUIREMENTS ----------------------------------------------------------------------------
req = open(REQ).read()
old = 'FA-1 pulse load is an envelope (interim: 90 bar abs quasi-static at head and aft; 1.8 kN for 4 ms thrust spike for low-frequency parts).'
assert req.count(old) == 1
req = req.replace(old, old[:-1] + f' [period domain amended by CHANGELOG 173 and {n194}: see the last bullet; "low-frequency parts" means T <= 20 ms].')
if not req.endswith('\n'):
    req += '\n'
req += (
    "- Max-thrust FEA criterion (CHANGELOG 183): thermal (secondary) stress in metal parts is accepted only when primary MS >= 0 at SF 1.5/2.0, "
    "P+Q range <= 2 Fty(T), LCF >= 50 hot cycles (x2 on strain or x20 on cycles) and part temperature within its sourced time-at-temperature "
    "limit (188 (5)); otherwise DESIGN CHANGE. TC-02 head and GM-01/02 gimbal ring are DESIGN CHANGE items. NZ-01 graphite throat: acceptance "
    "test-based (cracked-but-contained HYPOTHESIS) if mechanical capture is shown; inspection after every static fire, spares in the BOM.\n"
    "- Combustion v2.4a decisions (CHANGELOG 186, as amended by 194): PURGE commits iff the lead to the plain relight trigger is >= L* = 1.3 s "
    "(both brackets; replaces 1.7 s); below it no purge and no unpurged relight on that pass. While the drogue is attached with Pc invalid the "
    "ECU open-loop command is held at the start level (62.5 N) until release; margin CONDITIONAL on the CF-3 start-lift measurement (F <= 16.31 N "
    "minus heat allowance, or mdot <= 52.6-56.3 g/s). NZ-01 refutation: throat-area change > 2 % beyond the erosion predicted for that firing "
    "(prediction frozen before the firing), a non-axisymmetric step, or a missing fragment. N2O tank outlet geometry (OI-32) is a Mechanical item.\n"
    "- REV-MECH-1 decisions (CHANGELOG 188): safety factors: nominal states (LC1-LC4, LC6, TS1, TS2, SEGP, TB70) ENG-10 1.5/2.0; abnormal states "
    "(LC2F, BN, TBS) 1.0/1.5; FA-1 per the last bullet. Every fastener, O-ring and seal gets a BOM line; until then a 0.20 kg hardware allowance "
    "counts against the 0.10 kg GNC re-fly trigger. ENG-11 gimbal stiffness spread (3133-7406 N m/rad) is assessed by GNC for loop robustness. "
    "BL-02 wall clash fixed on the engine side. A 3D assembled-engine FE at LC1 and LC3 (8 deg stop) is the headline FEA.\n"
    f"- FA-1 loads with period domain (CHANGELOG {n194}; supersedes the FA-1 sentence of the CHANGELOG 172 bullet): equivalent static pressure "
    "at head and aft 90 bar abs for load paths with T <= 0.1 ms; 93 bar abs yield / 102 bar abs ultimate for 0.1 < T <= 1 ms; for T > 1 ms the "
    "published all-case spectrum at the part's period, or FA1S (DLF 2.0, about 151 bar abs) until Mechanical's modal closure lists every "
    "pressure-loaded load path with its period; SF 1.0. Thrust: 1.8 kN x 4 ms for T <= 20 ms; the FA-1 long-period thrust spectrum for "
    "T > 20 ms (airframe ICD). Stand dynamic Pc channel >= 100 bar abs. T1-T4 oxidiser-flux test two-sided.\n"
)
open(REQ, 'w').write(req)

print('CHANGELOG', n193, n194, h16(CL))
print('SUPERVISION', h16(SUP), len(d['reviews']))
print('REQUIREMENTS', h16(REQ))
