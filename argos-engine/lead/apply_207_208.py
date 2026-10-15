# REV-GNC-5: SUPERVISION entry, CHANGELOG 207 (result) and 208 (lead), REQUIREMENTS bullet.
import json, hashlib, shutil

HUB = '/home/claude/work/shared-fallback/engine'
SP = '/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad'
CL = f'{HUB}/interfaces/CHANGELOG.md'
SUP = f'{HUB}/reviews/SUPERVISION.json'
REQ = f'{HUB}/00-requirements/REQUIREMENTS.md'


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


assert h16(CL) == '37d45a7f44977079', h16(CL)
assert h16(SUP) == '234e3f048c6e82c9', h16(SUP)
assert h16(REQ) == '8a0b92545b51362c', h16(REQ)
REV = h16(f'{HUB}/reviews/REVIEW-GNC-R3.md')
assert REV == 'f2aafa51c7117ba8', REV
for p in (CL, SUP, REQ):
    shutil.copyfile(p, f"{SP}/{p.rsplit('/', 1)[1]}.pre-207")

lines = open(CL).read().split('\n')
if lines[-1] == '':
    lines = lines[:-1]
assert len(lines) == 206, len(lines)

l207 = (
    "2026-10-13 | review | (result) | REV-GNC-5 independent check of GNC staging rev3 (MANIFEST_rev3 79c2c8cd5d10e3c4, "
    "rev3_results.json e0f6e7611fe523b5) and of lead line 204: PUBLISHABLE WITH CORRECTIONS; 0 BLOCKING, 1 MAJOR, 6 MINOR, 6 NOTE. "
    "Reproduced (SIM/DERIVED): 19 arms re-flown from the staged v2.12 tree and pins (16 Monte Carlo, 3 P5; byte-identical or identical on "
    "every staged column); P6 late-commit table and gate-delay tolerance; P6c; P2 with and without the dip onset; P3; all 44 P5 strict "
    "windowed totals; F7; F9; v2.12 bit-check parts A and B; v2.9 suite parts A0/G/K/V/RF (A1 and N not re-run). P by realised lead "
    "(nominal start): 0.993 at 2.1-2.4 s, 0.982 at 1.9-2.1 s, 0.835 at 1.7-1.9 s, 0.009 at 1.3-1.5 s. MAJOR RV5-01: the 204 (3) apogee "
    "rule has no non-inferiority margin, monotonicity condition or fixed onset (at a 62 g onset liq v35t passes 275 m but loses 265 m; "
    "passing bands carry a 0.8-1.9 pp undetected-deficit upper bound; the sweep floor 245 m is the only v35a pass). MINOR: RV5-02 the "
    "250 m planning value has no flown support at the line-206 mass (~v35a + 0.20 kg); RV5-03 pooled over two bases all ECU-hold arms "
    "lose against release at E2 (rh300c200 -11/+2 p 0.0225); RV5-04 D_crit per threshold (3.765 s at 2.1 s; +0.156 s on pc bases); "
    "RV5-05 the e19|G73|L400 loss is 40/43 at W10 >= 6 m/s; RV5-06 withdrawn values unmarked in staged evaluation files and P4 gap_N/T_mid_N; "
    "RV5-07 proposal [9] predates the 2.55 s cap. NOTES RV5-08..13 (H 0.30 s is 0.25 ms short of the frame rule for lin1.0|LO; carry "
    "both 0.5 and 0.8 s R2 windows; AR(1) wording; reproducibility closure; P5 apex conservative). Line 204 (1), (2), (4) follow; (3) "
    "needs restating. Proposals per the review table: [5], [7], [8], [10] publishable as written; [0]-[4], [6], [9] with corrections; none not publishable (the review's summary count 5/6 differs from its own table 4/7; the table is used). SIM/DERIVED; not physical approval | "
    f"reviews/REVIEW-GNC-R3.md {REV}; reviews/gnc/rev3/MANIFEST_REV-GNC-5.sha256 ce04a68c0539b7a1 (71/71 re-verified by lead); "
    "SUPERVISION.json REV-GNC-5; why: lead 204 (5)"
)

l208 = (
    f"2026-10-13 | lead | (decision) | On REV-GNC-5 (line {len(lines) + 1}): verdict recorded as given. "
    "(1) RV5-01, 204 (3) RESTATED: the A1 apogee target is the highest 5 m band h for which h and every lower flown band show no "
    "significant pooled loss (two main bases, paired, p < 0.05) against the v3d reference with the dip onset FIXED at 80 g on both arms "
    "(upper end of the R3-17 bracket, until the OI-32 outlet geometry sets the true onset), AND a one-sided 95 % upper bound on the pooled "
    "P deficit <= 1.0 pp (delta set by the lead). The sweep extends below 245 m until a band passes; the candidate band and the band above "
    "it are flown on all four bases; N may rise to 1000 per base to resolve delta. The rev4 P2 re-fly on massprops v3.5.1 "
    "(488b47f9d55ff91b) uses this rule, with sensitivity arms for the 0.15 kg valve target, the v3.5.2 levers and an ~80 g purge (203 (3)). "
    "(2) RV5-02: the 250 m planning value is WITHDRAWN; planning value <= 245 m, TO-VERIFY by rev4 P2. "
    "(3) RV5-03 and RV5-08 strengthen 204 (2) NOT ADOPTED. Its revisit rule becomes: an expected gain q x P_total >= 0.5 pp per flight "
    "(q = gate-fault probability) with an ECU timing margin >= 10 ms on the hold frame rule, or the CF-4/T4 condition of 204 (2). "
    "(4) RV5-04: in 204 (1) the gate-delay tolerance for the ~2.1 s threshold is D_crit 3.765 s (A1_none, A1J_none; +0.156 s on the pc "
    "bases); 3.465 s belongs to the 2.4 s threshold. Predictor failure (commit at the plain trigger) is a separate fault class. "
    "(5) RV5-05, RV5-09, RV5-10 recorded: the e19|G73|L400 loss lies at W10 >= 6 m/s (outside the hard launch-commit rule); R2 v2 "
    "carries both the 0.5 s (all winds 34.88 N, margin +2.28 N, 0/2072) and the 0.8 s windows; 'AR(1) fails everywhere' in 204 (4) is "
    "corrected to 'fails for the same-RMS variants' (with frame-level RMS equal, B1 comp passes at all three correlation times). "
    "(6) GNC corrects proposals [0]-[4], [6], [9], marks withdrawn values in the evaluation files and stages the v2.10/v2.11 trees and "
    "iface_v3c (RV5-06/07/11); REV-GNC-5 then does a delta re-check before gnc.json v3.2 is published. Nothing here is physical approval | lead"
)

lines += [l207, l208]
open(CL, 'w').write('\n'.join(lines) + '\n')

d = json.load(open(SUP))
assert 'REV-GNC-5' not in [r['id'] for r in d['reviews']]
d['reviews'].append({
    'id': 'REV-GNC-5',
    'date': '2026-10-13',
    'reviewer': 'Independent reviewer agent (not the author; also REV-GNC-3 and REV-GNC-4)',
    'author': 'Space/GNC specialist agent',
    'deliverable': '01-systems-gnc/staging_v3.1/rev3 (GNC rev3: P2-P6, P8-P9; 11 v3.2 proposals) and lead line 204',
    'hashes_sha256_16': {
        '01-systems-gnc/staging_v3.1/rev3/MANIFEST_rev3.sha256': '79c2c8cd5d10e3c4',
        '01-systems-gnc/staging_v3.1/rev3/results/rev3_results.json': 'e0f6e7611fe523b5',
        '01-systems-gnc/staging_v3.1/rev3/REPORT-GNC-rev3.md': '4726faa1ce2ab39d',
        'interfaces/gnc.json': '4f3209323b0e0ed4',
    },
    'criteria': '(a) reproduction by re-flight of staged arms and own statistics (P6, P6c, P2 with/without dip onset, P3, P5 windowed budget, F7, F9, F11); (b) independent bit-check re-runs; (c) marking of values withdrawn by line 194; (d) whether line 204 (1)-(4) follow from the evidence; (e) publishability of each v3.2 proposal',
    'verdict': 'PUBLISHABLE WITH CORRECTIONS',
    'blocking': [],
    'major': ['RV5-01 apogee rule lacks non-inferiority margin, monotonicity and a fixed onset'],
    'minor': ['RV5-02', 'RV5-03', 'RV5-04', 'RV5-05', 'RV5-06', 'RV5-07'],
    'notes': ['RV5-08', 'RV5-09', 'RV5-10', 'RV5-11', 'RV5-12', 'RV5-13'],
    'line_204_assessment': '(1) follows (D_crit pairing corrected); (2) NOT ADOPTED follows and is strengthened; (3) band statement reproduces, rule needs restating; (4) follows with nuances',
    'proposals': 'per review table: [5], [7], [8], [10] publishable as written; [0], [1], [2], [3], [4], [6], [9] with corrections; 0 not publishable. The review summary says 5/6; its table gives 4/7 and is used',
    'confirmed': '19 arms re-flown identical; P6 table; P6c; P2; P3; 44 P5 strict totals; F7; F9; v2.12 bit-check A/B; v2.9 suite A0/G/K/V/RF',
    'reviewer_artefacts': {
        'dir': 'reviews/gnc/rev3/',
        'manifest': 'reviews/gnc/rev3/MANIFEST_REV-GNC-5.sha256',
        'manifest_sha256_16': 'ce04a68c0539b7a1',
        'verified_by_lead': '71/71 OK',
    },
    'review_file': 'reviews/REVIEW-GNC-R3.md',
    'review_file_sha256_16': REV,
    'lead_disposition': f'CHANGELOG line {len(lines)}',
    'not_physical_approval': True,
})
open(SUP, 'w').write(json.dumps(d, indent=1, ensure_ascii=False))

req = open(REQ).read()
old = "A1 apogee target set on the v3.5.1 ledger by the no-significant-loss rule (planning value 250 m PROVISIONAL)"
assert req.count(old) == 1
req = req.replace(old, "A1 apogee target set on the v3.5.1 ledger by the rule of CHANGELOG 208 (planning value 250 m WITHDRAWN by 208 (2))")
req += (
    "- A1 apogee rule (CHANGELOG 208, restates 204 (3)): highest 5 m band with no significant pooled loss against the v3d reference at "
    "that band and every lower flown band, dip onset fixed at 80 g, and a one-sided 95 % upper bound on the pooled P deficit <= 1.0 pp; "
    "planning value <= 245 m TO-VERIFY by GNC rev4 P2 on massprops v3.5.1.\n"
)
open(REQ, 'w').write(req)
print('CL', len(lines), h16(CL), 'SUP', h16(SUP), len(d['reviews']), 'REQ', h16(REQ))
