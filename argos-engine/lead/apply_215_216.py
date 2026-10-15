# REV-ELEC-2: save review, SUPERVISION entry, CHANGELOG 215 (result) and 216 (lead), REQUIREMENTS bullet.
import json, hashlib, shutil, os

HUB = '/home/claude/work/shared-fallback/engine'
SP = '/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad'
CL = f'{HUB}/interfaces/CHANGELOG.md'
SUP = f'{HUB}/reviews/SUPERVISION.json'
REQ = f'{HUB}/00-requirements/REQUIREMENTS.md'
RF = f'{HUB}/reviews/REVIEW-ELECTRONICS-R2.md'


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


assert h16(CL) == 'b503abf661bcf358', h16(CL)
assert h16(SUP) == '11cb4fd4dbd3f6e1', h16(SUP)
assert h16(REQ) == 'd516f4afe3da55d1', h16(REQ)
assert not os.path.exists(RF), RF
for p in (CL, SUP, REQ):
    shutil.copyfile(p, f"{SP}/{p.rsplit('/', 1)[1]}.pre-215")
shutil.copyfile(f'{SP}/REV-ELEC-2.extract.md', RF)
REV = h16(RF)
MAN = h16(f'{HUB}/reviews/electronics/r2/MANIFEST_REV-ELEC-2.sha256')
assert MAN == 'ecb1045f348efec9', MAN

lines = open(CL).read().split('\n')
if lines[-1] == '':
    lines = lines[:-1]
assert len(lines) == 214, len(lines)

l215 = (
    "2026-10-13 | review | (result) | REV-ELEC-2 independent delta re-review of Electronics v2.10 (hub copy; SHA256SUMS-v2.10 "
    "674eef94498822dd 502/502, archive/v2.9 406/406) and of lead line 203: REVISE; 0 BLOCKING, 6 MAJOR, 10 MINOR, 7 NOTE. Reproduced "
    "(SIM): rebuild of sil, sil_bpc1, test_core equal to MANIFEST_v1 6d1dd43ddeeba0d7 binary hashes; test_core 309/0; 22 SIL outputs "
    "byte-identical (S17, S6, S15, S5 300, probe F, S14, S16, S12, S13 B-ext both builds); S5 extended to 3000 runs (plant Pc p99.9 27.316 "
    "bar abs, max 28.224, 0 PC_OVERPRESSURE); independent FA-1 chain on 896 cases agrees with the author (aborts as built 361-376 vs "
    "362-379); electronics.json v3 vs config.h 154/154. RE statuses truthful (17 CLOSED: 11 confirmed, 6 with residuals; 8 OPEN true; 4 "
    "DISPOSITIONED confirmed). MAJOR: R2-01 the S17 'no released dead vehicle at the W10 < 6 m/s bound' holds only for Pc lost within ~8 ms "
    "of E2 and calm (10-20 ms onsets release 1/20-7/10; 5 N rms frame noise with the hold releases 42/100); R2-02 one lost DROGUE 0 frame "
    "keeps the R2 hold for the rest of the burn (lit, released vehicle held at 62.5 N); R2-03 line 203 (1)(b) acceptance set cannot fail "
    "(no in-window genuine over-pressure in S6/S9) and the governing quantity is the detector-side duration (filtered run above 30 bar <= 12 "
    "ms; persistence 15 ms or comparator RC >= 10 ms leave 0 trips; 276-310 firmware trips fall after E2, filtered Pc above 30 bar until "
    "E2 + 8.0 ms); R2-04 line 203 (5) 'MV never opened' cannot be met (MV latch precedes the BASE_HIGH check), pad BASE_HIGH is a PC_SENSOR "
    "abort not a refuse code, A1 BASE_HIGH proceeds to RUN by design and BASE_AMB (offset below ~-0.7 bar) lifts then aborts; R2-05 purge "
    "cap: the 75.9 g basis is ambiguous, at 29.8 g/s the 2.55 s cap gives 77.5 g and the 2.5 s schedule meets 76 g only for mdot <= 30.4 "
    "g/s, the truncation check cannot fail by construction, and the hardware one-shot bound is 3.293 s of flow (96.2-103.5 g), so 166 (3) "
    "is not met; R2-06 bench plan v3 has no step the founders can execute now. MINOR R2-07..R2-16 (json l.2035 wrong on Pc validity; "
    "test_core is hooks-build evidence only, no-hooks build fails; undisclosed S6 timing changes v2.9->v2.10; S5 statistics include 714 "
    "non-flying runs; OI-GUARD-BAND mechanism isolated: IGNITE refused TANK_COLD after a 0.16 K PREPRESS Tsat drop, 186/3000 S5 runs do "
    "not fly, ECU then waits in PREPRESS with the MV open; stale comments; bench-plan residuals; O2-clean notes missing on BOM rows 212, "
    "214, 245; '72 ms above MEOP' stale, v2.10 gives 34 ms; S17 starve threshold 0.46-0.48 s not reported). NOTES R2-17..R2-23. RE-12: "
    "ACCEPT the flight extension of the A7 high-side blank E2..E2 + 0.45 s as DESIGN with four conditions. Line 203: (1)(a), (2), (4), (6), "
    "(7) follow; (1)(b), (3), (5) REVISE. SIM/DERIVED/DATASHEET; not physical approval | "
    f"reviews/REVIEW-ELECTRONICS-R2.md {REV}; reviews/electronics/r2/MANIFEST_REV-ELEC-2.sha256 {MAN} (55/55 re-verified by lead); "
    "SUPERVISION.json REV-ELEC-2; why: lead 203 (8)"
)

l216 = (
    "2026-10-13 | lead | (decision) | On REV-ELEC-2 (line 215): verdict recorded as given; Electronics v2.11 takes every finding as a delta. "
    "(1) R2-01: electronics.json l.1946 and the line-195 S17 result are RESTATED as conditional (Pc lost within ~8 ms of E2, calm). Electronics "
    "extends S17 to Pc-loss onsets 1-50 ms x 10 frame phases x seeded frame noise, at 200 and 500 N, with and without the hold, and re-runs "
    "it against GNC's R2 v2 (not the stand-in) at both the 0.5 s and 0.8 s windows; GNC states the R2 counting start, the estimator flush and "
    "whether the 20.85 N d_app bound already contains FC measurement noise. Until that sweep closes, the 'no released dead vehicle' claim "
    "is not used for the A1 relight P; the R2 v2 freeze waits for it. "
    "(2) R2-02 ADOPTED in full: (a) FC rule: after DROGUE 0, re-send with a new sequence number until d6 b6 = 0 is seen, with a stated bound; "
    "(b) ECU backstop: the hold ends no later than E2 + 0.8 s (the longer R2 v2 window) + a margin Electronics states (>= 2 FC frames + link "
    "latency), logged; (c) a B-FC-1 row and a test_core case for a lost DROGUE 0. "
    "(3) R2-03, 203 (1)(b) RESTATED (still CANDIDATE for flight; stand keeps the abort): the ride-through is sized from detector-side "
    "durations re-derived for the line-205 transducer chain: filtered persistence >= 13 ms plus a stated margin, over-range count N >= 2, "
    "and the comparator RC FIXED (not switched in a window; reviewer recommendation adopted so the hardware path stays independent of "
    "firmware), with its value (RC >= 10 ms at the low band edge or the line-205 equivalent) costed on genuine over-pressure over the whole "
    "burn. Firmware window from E1 to at least E2 + 8 ms plus margin. Acceptance: S6 gains in-window genuine over-pressure cases (50 bar "
    "step, ramps to 60 bar, FA-1 followed by 35-50 bar plateaus) and each must abort with head pressure-time inside Mechanical's LC-TB70 "
    "envelope, which Mechanical states in pressure-time form (R2-15: the v2.10 throat-blocked case is 53.4 bar abs for 34 ms above MEOP, "
    "not 72 ms). "
    "(4) R2-04, 203 (5) RESTATED per location: pad/stand BASE_HIGH = PC_SENSOR abort with BASE_HIGH, lift never commanded, MV closed by the "
    "abort; A1 BASE_HIGH = RUN on the measured P0 (186/166 (1) unchanged); BASE_AMB: Electronics states the outcome per location and its "
    "occurrence on the A1 relight population, with refusal before lift as the pad/stand target; torch gate not reached = TORCH_FAULT; all "
    "unlit runs 0 false E2. "
    "(5) R2-05, 203 (3) RESTATED: the purge limit is the vented mass, so the ECU cap takes measured-time form after CF-4/B-BLEED-1: both-open "
    "overlap <= 76 g / mdot_measured - (t_close - t_open)_measured. Until then one flow basis is carried, the one Combustion v2.4b states, "
    "with GNC's G80 arm as the high-basis sensitivity; the 2.55 s commanded cap stays as a provisional software limit and the 'not "
    "truncated' statement is withdrawn. 166 (3) stands: v2.11 designs a hardware timer on the both-commanded-open condition that drops V1 "
    "at the cap plus tolerance, independent of firmware. If Electronics shows it cannot be done without cutting the scheduled flow under "
    "the timing tolerances, the lead restates 166 (3) and the hardware-window residual (96-104 g) goes to GNC and the FMEA. "
    "(6) R2-06: the founder-executable block is added to the bench plan and to the founder action list: RFQs delivered to Sonderborg "
    "DK-6400 for BOM rows 237, 238, 244, 245, 250 (no price until quoted); TE (070BG saturation, recovery, post-over-range shift; line-205 "
    "replacement unit), PCB (113B22 excitation at 19 V compliance, coating) and NI inquiries; the anemometer mast and logger; the spare-070BG "
    "over-range row on a bench supply and DAQ, hydraulic only, never returned to N2O service. "
    "(7) R2-11 OI-GUARD-BAND: the cold rule gets an ARM-time margin of at least the PREPRESS Tsat drop (0.16 K SIM, to be re-derived) plus "
    "the Tsat estimate uncertainty, stated by Electronics; and an IGNITE refusal in PREPRESS leads to a defined safe exit (MV closed, back "
    "to SAFE/ARMED) within a stated time, never a wait with the MV open. "
    "(8) RE-12: the flight extension of the A7 high-side blank E2..E2 + 0.45 s is ACCEPTED as DESIGN with the reviewer's four conditions "
    "(config.h l.369-372 corrected; electronics.json states the blind window and that the 30 bar abort, comparator, A3 and the A7 low side "
    "stay armed; the FC owner confirms no decision uses the A7 high flag before E2 + 0.45 s; test v210-2 extended on d6 b7). "
    "(9) R2-22: the ECU R2 hold becomes a lift-commanded hold at Combustion v2.4b's start-level lift (Pc is invalid during the hold, so the "
    "thrust map adds nothing); CF-3 measures at that lift with the encoder recorded. R2-23: Electronics states, with S6/S17 evidence, "
    "whether high over-range ticks after E2 engage the hold. "
    "(10) Text and record items R2-07, R2-08 (no-hooks test_core run), R2-09 (S6 timing disclosure), R2-10 (S5 statistics over flying "
    "runs with stated denominators), R2-12, R2-13, R2-14 (O2-clean notes, hydraulic pump reserved), R2-15, R2-16 (starve threshold at "
    "both R2 v2 windows), R2-17, R2-20, R2-21 (new FA-1 chain for the line-205 transducer) go into v2.11 and electronics.json v4, which "
    "folds lines 203, 205, 208 and this line. REV-ELEC-3 delta-reviews the v2.11 handback. Nothing here is physical approval | lead"
)

lines += [l215, l216]
open(CL, 'w').write('\n'.join(lines) + '\n')

d = json.load(open(SUP))
assert 'REV-ELEC-2' not in [r['id'] for r in d['reviews']]
d['reviews'].append({
    'id': 'REV-ELEC-2',
    'date': '2026-10-13',
    'reviewer': 'Independent reviewer agent (not the author; also REV-ELEC-1)',
    'author': 'Electronics specialist agent',
    'deliverable': '06-electronics v2.10 hub copy (firmware, SIL sil_v2p10, FA-1 harness, bench_plan_v3, BOM v2.2, REPORT-v2.10-HANDBACK) and interfaces/electronics.json v3; lead line 203',
    'hashes_sha256_16': {
        '06-electronics/SHA256SUMS-v2.10.txt': '674eef94498822dd',
        '06-electronics/REPORT-v2.10-HANDBACK.md': '05af80b9cdbee9b5',
        '06-electronics/firmware/src/core/config.h': '0880af5a27880a5b',
        '06-electronics/firmware/src/core/engine_ecu.cpp': '6e62a7e4e37930bd',
        '06-electronics/results/sil_v2p10/MANIFEST_v1.json': '6d1dd43ddeeba0d7',
        '06-electronics/results/sil_v2p10/S17/S17_r2hold.json': 'c125095719fa563a',
        '06-electronics/results/fa1_overrange_v2p10.json': 'f2b07a3d780a289c',
        '06-electronics/results/bleed_driver_v1.json': '298b405b0621acd5',
        '06-electronics/results/bom_v2p2.csv': '75723fd39be88c20',
        '06-electronics/docs/bench_plan_v3.md': 'aa82f280feeeee4c',
        'interfaces/electronics.json': '38bf149f368c1d4c',
    },
    'criteria': '(a) RE-01..RE-29 status truth; (b) independent rebuild and SIL re-runs under reviewer control, S5 to 3000 runs, reviewer-written FA-1 chain on 896 cases; (c) R2 command hold logic, interface and limits (reviewer probe on S17); (d) electronics.json v3 vs config.h; (e) 070BG and 113B22/NI 9234 datasheet answers to line 194; (f) whether line 203 (1)-(7) follow from the evidence, RE-12; (g) founder executability of bench plan v3',
    'verdict': 'REVISE',
    'blocking': [],
    'major': [
        'R2-01 S17 W10 bound result conditional on early Pc loss and calm',
        'R2-02 single lost DROGUE 0 frame keeps the R2 hold',
        'R2-03 line 203 (1)(b) acceptance cannot fail; size from detector-side durations',
        'R2-04 line 203 (5) S13 criteria cannot be met as written; classes missing',
        'R2-05 line 203 (3) purge cap basis, non-discriminating check, hardware bound above cap (166 (3) not met)',
        'R2-06 bench plan v3 has no founder-executable step',
    ],
    'minor': ['R2-07', 'R2-08', 'R2-09', 'R2-10', 'R2-11', 'R2-12', 'R2-13', 'R2-14', 'R2-15', 'R2-16'],
    'notes': ['R2-17', 'R2-18', 'R2-19', 'R2-20', 'R2-21', 'R2-22', 'R2-23'],
    'deliverable_verdicts': {
        'firmware v2.10 core': 'ACCEPT WITH COMMENTS as the v2.10 SIL baseline',
        'SIL record sil_v2p10': 'ACCEPT WITH COMMENTS',
        'FA-1 harness / fa1_overrange_v2p10.json': 'ACCEPT as SIM evidence for the 070BG no-line chain',
        'interfaces/electronics.json v3': 'ACCEPT WITH COMMENTS as the working interface',
        'bench plan v3': 'REVISE',
        'BOM v2.2': 'ACCEPT WITH COMMENTS',
        'REPORT-v2.10-HANDBACK': 'ACCEPT WITH COMMENTS',
    },
    'line_203_assessment': '(1)(a) follows; (1)(b) REVISE; (2) follows, superseded by 205; (3) REVISE; (4) follows; (5) REVISE; (6) follows; (7) follows with NOTE R2-22',
    're12_recommendation': 'ACCEPT flight extension of the A7 high-side blank E2..E2 + 0.45 s as DESIGN with four conditions',
    'confirmed': 'rebuild equals MANIFEST_v1 binaries; test_core 309/0; 22 SIL outputs byte-identical; S5 3000 runs 0 PC_OVERPRESSURE; FA-1 chain agrees; json vs config.h 154/154; RE statuses truthful',
    'reviewer_artefacts': {
        'dir': 'reviews/electronics/r2/',
        'manifest': 'reviews/electronics/r2/MANIFEST_REV-ELEC-2.sha256',
        'manifest_sha256_16': MAN,
        'verified_by_lead': '55/55 OK',
    },
    'review_file': 'reviews/REVIEW-ELECTRONICS-R2.md',
    'review_file_sha256_16': REV,
    'lead_disposition': f'CHANGELOG line {len(lines)}',
    'not_physical_approval': True,
})
open(SUP, 'w').write(json.dumps(d, indent=1, ensure_ascii=False))

req = open(REQ).read()
if not req.endswith('\n'):
    req += '\n'
req += (
    "- Electronics review REV-ELEC-2 decisions (CHANGELOG 216): S17 R2 result conditional until the onset/phase/noise sweep against GNC R2 "
    "v2; ECU backstop ends the R2 hold by E2 + 0.8 s + stated margin and the FC re-sends DROGUE 0; FA-1 ride-through (flight CANDIDATE) "
    "sized from detector-side durations with a fixed comparator RC and in-window over-pressure acceptance cases against Mechanical's "
    "LC-TB70 pressure-time envelope; S13 criteria per location; purge cap in measured-time form (overlap <= 76 g / mdot - valve-time term) "
    "after CF-4/B-BLEED-1, hardware both-open timer per 166 (3); cold-rule ARM margin and a safe PREPRESS exit on IGNITE refusal; A7 "
    "high-side blank E2..E2 + 0.45 s accepted for flight with conditions; lift-commanded R2 hold.\n"
)
open(REQ, 'w').write(req)
print('REV', REV, 'CL', len(lines), h16(CL), 'SUP', h16(SUP), len(d['reviews']), 'REQ', h16(REQ))
