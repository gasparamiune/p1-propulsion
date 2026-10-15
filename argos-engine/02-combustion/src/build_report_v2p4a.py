#!/usr/bin/env python3
"""build_report_v2p4a.py - REPORT v2.4a from the published REPORT v2.4 by asserted edits.

Usage: python -I build_report_v2p4a.py
Inputs (hash-asserted): hub 02-combustion/REPORT.md v2.4, the staged interface v2.4a,
the FA-1 table snippets written by fa1_tables_v2p4a.py.
Every literal edit must match exactly once; every anchor must be unique.
Output: /home/claude/work/combustion/v2p4a/REPORT.md
"""
import hashlib, re, sys

HUB = '/home/claude/work/shared-fallback/engine/02-combustion/superseded/v2p4/REPORT.md'   # v2.4 as published (archived at the v2.4a publish)
IFACE = '/home/claude/work/combustion/v2p4a/iface/combustion.json'
SNIP = '/home/claude/work/combustion/v2p4a/fa1_tables_snippets.md'
OUT = '/home/claude/work/combustion/v2p4a/REPORT.md'
EXPECT = {HUB: '32e366bd78437dc0', IFACE: '5237d4584bad38c4', SNIP: '119a508c033c8428'}


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


for p, e in EXPECT.items():
    assert h16(p) == e, (p, h16(p), e)

T = open(HUB, encoding='utf-8').read()
N_EDITS = [0]


def rep(old, new, n=1):
    global T
    c = T.count(old)
    assert c == n, ('rep count', c, old[:90])
    T = T.replace(old, new)
    N_EDITS[0] += 1


def line_of(prefix):
    ms = list(re.finditer(r'^' + re.escape(prefix) + r'.*$', T, re.M))
    assert len(ms) == 1, ('anchor', len(ms), prefix[:90])
    return ms[0]


def repl_line(prefix, new):
    global T
    m = line_of(prefix)
    T = T[:m.start()] + new.rstrip('\n') + T[m.end():]
    N_EDITS[0] += 1


def append_line(prefix, extra):
    global T
    m = line_of(prefix)
    T = T[:m.end()] + extra + T[m.end():]
    N_EDITS[0] += 1


def ins_after(prefix, new):
    global T
    m = line_of(prefix)
    T = T[:m.end()] + '\n' + new.rstrip('\n') + T[m.end():]
    N_EDITS[0] += 1


def block(start_prefix, end_prefix, new):
    global T
    m = line_of(start_prefix)
    e = re.search(r'^' + re.escape(end_prefix), T[m.start():], re.M)
    assert e, ('block end', end_prefix)
    T = T[:m.start()] + new.rstrip('\n') + '\n\n' + T[m.start() + e.start():]
    N_EDITS[0] += 1


# FA-1 tables from the snippets of fa1_tables_v2p4a.py (fa1_tables_v2p4a.json 677fd9ccd297fdf4)
S = open(SNIP, encoding='utf-8').read().split('\n')
iT1, iT2, iT3 = S.index('T1'), S.index('T2'), S.index('T3')
TAB_T1 = '\n'.join(S[iT1 + 1:iT2])
TAB_T2 = '\n'.join(S[iT2 + 1:iT3])
assert TAB_T1.count('\n') == 5 and TAB_T2.count('\n') == 9

# ---------------------------------------------------------------- front matter
repl_line('Version 2.4, 2026-10-13. Owner: Combustion and Propulsion.',
          'Version 2.4a, 2026-10-13. Owner: Combustion and Propulsion. Interface: `interfaces/combustion.json` v2.4a (sha256/16 `@@IFACE_SHA@@`); v2.4 (`469727032124329f`) is kept as `data/v2/combustion_interface_v2p4_as_published.json` and v2.3 (`d9ec54fbf450e243`) as `data/v2/combustion_interface_v2p3_as_published.json`. Status: targeted revision v2.4a in answer to the independent re-review `reviews/REVIEW-COMBUSTION-R2.md` (REV-COMB-2, REVISE (targeted)) and to the lead decisions to CHANGELOG line 177. v2.4 of this report (`32e366bd78437dc0`), which answered REV-COMB-1, REV-GNC-1 and the Electronics SIL items, is archived as `02-combustion/superseded/v2p4/REPORT.md`. Digital only, *Por revisar*: the v2.4a changes await re-review. Companion files: `02-combustion/CF-4-SPEC.md` v2.0, `02-combustion/T1-T4-REGRESSION-SPEC.md` v2 and the item-by-item answer `02-combustion/REVISION-RESPONSE-R2.md`.')

rep('v2.4 adds or replaces the following, each with its evidence:',
    'v2.4 added or replaced items 1-11 below, each with its evidence; v2.4a amends them in place and item 12 lists the patch (REV-COMB-2):')

rep('A5 is deleted and replaced by the LIGHT_SPIKE record; A4 trips at 30 bar raw for 5 ms; A14-A16 cover the bleed valves, the purge and the torch.',
    'On an A1 relight with the bleed fitted, E1 also needs [closure confirmed OR the closure deadline reached], the deadline being <= the torch gate (LEAD line 166 (3)). A5 is deleted and replaced by the LIGHT_SPIKE record; A4 trips at 30 bar abs on the FILTERED channel for 5 ms (LEAD line 166 (4)); A14-A16 cover the bleed valves, the purge and the torch.')

rep('A **fuel-assisted** fast part at a relight reaches 48.9-75.5 bar at a 1 ms burn time (<= 55.5 bar at 5 ms, <= 41.4 bar at 10 ms; SIM on ASSUMED burn time and fuel fraction): MEOP is NOT shown for it. It is FMEA item FA-1, a single-control hazard accepted by the lead for design continuation only (§9.1).',
    'A **fuel-assisted** fast part at a relight (FA-1) is published in v2.4a as an envelope over O/F 3-12 and burn times of 1-7 ms (896 cases; SIM on an ASSUMED construct; §7.6): head peak 83.0 bar abs (baseline: vapour once, rounded entrance) to 88.0 bar abs (upper bracket), aft 0.95-1.00 of the head, above MEOP 45 bar for <= 3.65 ms (4.45 ms), above proof 67.5 bar for <= 1.0 ms (1.3 ms), never above 90 bar abs. The v2.4 figure 48.9-75.5 bar (O/F 8 only) is superseded. MEOP is NOT shown for FA-1. The structural load is 90 bar abs quasi-static at head and aft for every part, 92 / 102 bar abs for parts with periods of 0.25-1 ms, and a 1.8 kN x 4 ms thrust spike (LEAD line 173). FA-1 is an FMEA item, a single-control hazard accepted by the lead for design continuation only (§9.1).')

rep('so the 0.81 s plan holds (SIM, `rg01_line_states_v2p4.json`). The claim is gated by CF-4 (founders; `CF-4-SPEC.md`).',
    'so the 0.81 s plan holds (SIM, `rg01_line_states_v2p4.json`). The claim is gated by CF-4 (founders; `CF-4-SPEC.md`). v2.4a: the PURGE commit rule of LEAD line 175 (3) and Combustion\'s check of an unpurged start are in item 12 and §2.8.')

rep('proof 67.5 bar keeps >= 21.9 bar (SIM).',
    'proof 67.5 bar keeps >= 21.9 bar (SIM). v2.4a: the interlock thresholds sit below 24 C / 55.28 bar abs by the total channel uncertainty, and CF-1 / CF-3 accept only a full-stroke Cd <= 0.80 and a line loss >= the model (LEAD line 172 (4); §3.6).')

rep('Relief on every lockable volume; stored energy',
    'Relief on every lockable volume, with the set points in the interface block `relief_v2p4a` (LEAD line 172 (6)); stored energy')

rep('"85 m covers 62 m" is withdrawn; B1 flies only under the lead\'s gating rule after T1-T4.',
    '"85 m covers 62 m" is withdrawn; B1 flies only under the lead\'s gating rule after T1-T4. v2.4a: the burden of proof is reversed (LEAD line 172 (3)); the T1-T4 specification v2 sets the law stations, the σ target and the errs-safe check (§10.4).')

rep('eta_cf band 0.95-0.975 (RC-09);',
    'eta_cf band 0.95-0.975 (RC-09; decided by LEAD line 170 (1): the 25 bar cap stays);')

rep('Proposal J1: a 2.0 mm carbon-phenolic flange with a 0.5 mm flexible-graphite seal at the lip face.',
    'Joint J1, CONFIRMED by the lead (CHANGELOG line 146): a 2.0 mm carbon-phenolic flange with a 0.5 mm flexible-graphite seal at the lip face.')

ins_after('11. **Nozzle joint (§6.5).**', '''12. **v2.4a patch (REV-COMB-2; LEAD lines 166-177).**
    - E1 and A14 follow LEAD line 166 (3): closure confirmed OR the closure deadline (<= the torch gate) reached; at the deadline in flight BLEED_FAULT goes to the FC, V2 is commanded closed and the lift proceeds; on the stand it is an abort. A4 runs on the filtered channel for 5 ms (line 166 (4)) (R2-01; §7.3-7.4).
    - One stand safing rule after a no-light (LEAD line 172 (1); R2-02; §7.6, §10.2).
    - The FA-1 envelope and the line-173 load (item 2; R2-03; §7.6, §9.1).
    - The T1-T4 specification v2: reversed burden, law stations x/L 0.80-0.90, σ(S) <= 1.5 %, systematic terms and the errs-safe check on 78 B1 records (R2-04; §10.4).
    - Superseded interface values tagged and the `relief_v2p4a` block added (R2-05); vented-mass sentences corrected and CF-4 P4 defined per tap and per phase (R2-06); interlock guard band (R2-07); Table 2.15 rows relabelled (R2-08); J1, the lip goal, the segment heat and RC-09 aligned (R2-09); stand dynamic Pc channel, with flight LIGHT_SPIKE values at 1 kHz as lower bounds (R2-10); the FA-1 outflow-form sensitivity (R2-11).
    - **PURGE commit rule (LEAD line 175 (3), PROVISIONAL): PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge.** Line 164's "the FC delays T_fire" is withdrawn. Combustion's check (§2.8, `unpurged_start_check_v2p4a.json`, SIM/DERIVED): the branch "the relight proceeds unpurged" carries a hazard outside the abort model. In the PURGE NOT RUN LO worst state every light (P 0.758) is followed by the 23.4 cm3 vapour gap, 0-0.19 s after E2; the drogue-release term is already true at E2, and A3 then aborts in 0.712 of the starts (H20). Proposal: no commit by the deadline -> no relight on that pass. The lead decides (OI-31).
    - Tank outlet coverage during PURGE: covered quasi-statically, with a large margin, if the outlet is on the aft bulkhead of an axial tank; the outlet geometry is MISSING (§2.4 note).
    - GNC rev2 gives a specific-force angle of up to 2.71 deg during the purge flow, above the 2 deg purge basis: OPEN (OI-35; §2.8).''')

rep('lead decisions to CHANGELOG line 164 (Mechanical bleed path line 162).',
    'lead decisions to CHANGELOG line 177 (Mechanical bleed path line 162; Mechanical FA-1 margins line 176; GNC rev2 line 174, SIM, staged and under review REV-GNC-3). Mechanical status to line 179 (CAD v3.5 run 6 with TC-09 in Inconel 718 and the bleed modelled, line 178; mechanical.json v2.1 `e4d3e7c9df529171`, line 179) is quoted for status only: the v2.4a analyses stay on CAD v3.4.1. GNC `purge_outlet_inputs.json` (`47b4deb96ea22043`) for the v2.4a checks. mechanical.json v2.1 still has no MEOP, MAWP or rounded-entrance keys and quotes the tank relief as "<= 7.5 MPa", and electronics.json v2 keeps points the decisions have overtaken (REV-COMB-2 R2-13, a configuration item for the lead).')

rep('Material data quoted "as recalled" are marked TO-VERIFY.',
    'Material data quoted "as recalled" are marked TO-VERIFY. v2.4a adds Lubin and Springer (1967) for the tank-drain dip screening (LITERATURE, applicability to N2O TO-VERIFY) and the GNC rev2 records.')

rep('the CF-4 specification `CF-4-SPEC.md`, and §14 here.',
    'the CF-4 specification `CF-4-SPEC.md` (v2.0), the T1-T4 specification `T1-T4-REGRESSION-SPEC.md` (v2), the v2.4a data in `data/v2p4a/` (`HASHES.txt`), and §14 here.')

rep('the 44.9 bar figure, the A5 abort and others.',
    'the 44.9 bar figure, the A5 abort and others. v2.4a: the FA-1 envelope script reproduces the v2.4 late-light case to 1e-6 bar before it extends the grid; the unpurged-start check reproduces six published P_abort values of `rg01_line_states_v2p4.json` before it follows the voids after a light; the T1-T4 law model reproduces the grain_q1d web on DC-D (14.25 against 14.24 mm). A first T1-T4 pass read the wrong DC-D file and let the analytic model burn past burn-through; both were corrected before any value was used (§13).')

rep('graphite erosion kinetics; the joint materials at temperature.',
    'graphite erosion kinetics; the joint materials at temperature. v2.4a: the fuel-vapour inventory at an A1 light (FA-1); the tank outlet geometry; the purge at the 2.7 deg specific-force angle; whether a light inside a liquid slug survives the vapour gap behind it.')

repl_line('**Next closure** (§12). Founders: CF-4, IGN-1',
          '**Next closure** (§12). Lead: the PURGE commit rule after Combustion\'s unpurged-start finding (OI-31); the configuration items of R2-13. Founders: CF-4 v2.0 (with 3 deg and per-tap flow), IGN-1 (>= 30 lights with photodiode false-positive tests, on the stand dynamic Pc channel), B-PNT-1, CF-1 to CF-3, then T1-T4 per specification v2. Electronics: the channel uncertainty behind the interlock guard band, the stand dynamic Pc channel, the closure deadline (E0 + 0.15 s), A4 on the filtered channel, A7, A14-A16, LIGHT_SPIKE. GNC: the 500-run specific-force angle during PURGE and a slosh bound (tank outlet); the bleed-valve mass trigger (> 0.30 kg, LEAD line 175 (2)). Mechanical: the gimbal bearing selection (line 179), the TC-02 head margin in LC-TB70 (line 179, OPEN), the tank outlet in CAD, the measured dP-flow curve of the FD-01 element, the joint FE re-run. Combustion: the purge at 2.7 deg (OI-35), a 1-D gas-dynamic run of the worst FA-1 row (OI-36), and the reduction of CF-4, IGN-1 and T1-T4.')

ins_after('- §11 Unknowns; §12 Open items with owners',
          '- v2.4a changes are marked "v2.4a" in place: §0 item 12; §2.4 tank outlet; §2.8 the PURGE commit rule, the unpurged start (Table 2.16) and the 2.7 deg note; §3.6 guard band; §7.3-7.4 the E1 and A14 closure term, A4 filtered; §7.6 the FA-1 envelope (Tables 7.6a and 7.6b); §8 the dynamic Pc channel; §9 H20, the vented mass and the FA-1 FMEA; §10 the v2.4a test-plan amendments, safing, CF-4 v2.0 and the T1-T4 specification v2; §11-§14.')

# ---------------------------------------------------------------- §2
rep('The conditioning requirement is 15-25 C (ENG-12, REQUIREMENTS rev 2; RC-13 b), with the 24 C liquid-line interlock (§2.8) and the arm limits of §7.3.',
    'The conditioning requirement is 15-24 C at ARM (ENG-12 as amended; RC-13 b; REV-COMB-2 R2-05), with the 24 C liquid-line interlock (§2.8), its guard band (§3.6) and the arm limits of §7.3. Values quoted at 25 C are bounds, not operating points.')
rep('holds 2.00 kg in 3.17 L, conditioned to 15-25 C.',
    'holds 2.00 kg in 3.17 L, conditioned to 15-24 C at ARM (ENG-12 as amended; 25 C is kept as a bound).')
rep('self-pressurised N2O conditioned to 15-25 C with a heater blanket',
    'self-pressurised N2O conditioned to 15-24 C at ARM (ENG-12 as amended) with a heater blanket')
rep('over the 15-25 C and A1 starts.',
    'over the 15-25 C bound (ARM window 15-24 C) and the A1 starts.')

repl_line('**v2.4 note (sequence v2.8 and the A1 purge).**',
          '''**v2.4 note (sequence v2.8 and the A1 purge).** On an A1 relight the liquid must cover the tank outlet from the PURGE command, E0 - 2.90 s, not only from T_fire: the purge is sized for liquid at both taps (15.62 g/s per tap) and vents vapour at 4.25 g/s per tap. The settling condition above therefore applies from E0 - 2.90 s - t_settle. Under the drogue the axial specific force at RELIGHT is 0.94-1.14 g (GNC records), so the condition is expected to hold. If the outlet uncovers during PURGE, the vented mass falls and the segment may not clear: the relight then rests on the line-state tables of §2.8 for an incomplete purge. [v2.4a: the T_fire delay of LEAD line 164, which v2.4 cited here, is withdrawn by line 175 (3).] That case is listed in §11.

**v2.4a: tank outlet coverage during PURGE** (lead request after GNC rev2; `unpurged_start_check_v2p4a.json` part D; DERIVED with CoolProp densities and the GNC SIM inputs of `purge_outlet_inputs.json` `47b4deb96ea22043`; quasi-static).
- Geometry used: the baseline tank of mechanical.json v1, a 6061-T6 tube 101.6 x 3.175 mm (ID 95.25 mm), internal length 0.4449 m, flat bolted bulkheads. It is a concept, not yet in CAD (DATASHEET tube size, DESIGN concept).
- Liquid at the purge in the six re-flown records: 766-1170 g at 0.89-1.12 g axial. Depth over the aft bulkhead: 126-133 mm at 766 g and 193-202 mm at 1170 g (283.15-289.5 K).
- The free surface drops at the wall by 2.3 mm at the largest specific-force angle in the records (2.71 deg), 5.7 mm at the largest tilt (6.86 deg) and 47.6 mm at an illustrative 45 deg. The lowest liquid height at the wall stays >= 120 mm (78.6 mm at 45 deg). The wall uncovers only beyond 69.3 deg.
- Screening: the Lubin-Springer dip height for a non-swirling drain is 7.9 mm (LITERATURE; applicability to near-saturated N2O TO-VERIFY). Roll spin-up of the liquid (Ekman) takes >= 359 s at <= 35.4 deg/s with an ASSUMED kinematic viscosity of 0.5-2e-7 m2/s, so no drain vortex develops in the 2.9 s. First slosh mode 2.92 Hz.
- **Verdict:** covered quasi-statically, with a large margin, IF the outlet sits on the aft bulkhead of an axial tank. This is not a final verdict.
- MISSING: the outlet position and diameter; any dip tube, sump, anti-vortex plate or screen; the tank orientation in the vehicle and which bulkhead is aft; the bulkhead face near the outlet (bosses, protrusions); a slosh amplitude (sim6 carries the liquid as a lumped mass); the specific-force angle over the 500 runs (six records were given). Owners: Mechanical (CAD), GNC (OI-32).''')

repl_line('| Tank relief set pressure |',
          '| Tank relief set pressure | 6.9 MPa, below the 7.0 MPa tank MEOP (ENG-09) | Combustion proposal, CONFIRMED by LEAD line 172 (6) with fire relieving at 8.35 MPa, MAWP >= 8.42 MPa, proof >= 10.5 MPa, the back-relief check (Cv >= 0.1) and the 9.5 MPa +/- 5 % disc. Interface block `relief_v2p4a`; it supersedes the v1 trapped-liquid relief "<= 7.5 MPa" |')

rep('6. Design attitude at RELIGHT is theta <= 2 deg.',
    '6. Design attitude at RELIGHT is theta <= 2 deg [v2.4a: GNC rev2 gives a specific-force angle of up to 2.71 deg to the body axis during the purge flow, above this basis; OPEN (OI-35), see the note under Table 2.14].')

rep('   - if closure is not confirmed before E1, the relight proceeds and BLEED_FAULT goes to the FC.',
    '   - if closure is not confirmed by the closure deadline (<= the torch gate; Electronics E0 + 0.15 s), E1 is declared at the deadline, BLEED_FAULT goes to the FC, V2 is commanded closed and the relight proceeds; on the stand it is an abort (amended by LEAD line 166 (3); item 15).')

rep('if T_fire would cut the flow below 1.9 s, the FC delays T_fire. The 0.81 s plan holds.',
    'if T_fire would cut the flow below 1.9 s, the FC delays T_fire [SUPERSEDED: withdrawn by LEAD line 175 (3); item 18]. The 0.81 s plan holds.')

rep("14. RG-01 stays BLOCKING until GNC re-flies on Combustion's re-routed-coil tables and CF-4 (line 161).",
    """14. RG-01 stays BLOCKING until GNC re-flies on Combustion's re-routed-coil tables and CF-4 (line 161). [v2.4a: GNC rev2 re-flew it (line 174; SIM, staged; REV-GNC-3 running); CF-4 remains.]
15. Line 166 (v2.4a): E1 = torch confirmed (2oo2) AND [closure confirmed OR the closure deadline reached], the deadline <= the torch gate; at the deadline in flight the lift proceeds, BLEED_FAULT goes to the FC and V2 is commanded closed; on the stand it stays an abort (3). The 30 bar abort runs on the filtered channel with 5 ms persistence (4). A second re-zero ends before the PURGE command (5).
16. Lines 172 and 173 (v2.4a): one stand safing rule (172 (1)); the FA-1 load restated as an envelope, then fixed at 90 bar abs quasi-static at head and aft for every part, 92 / 102 bar abs for parts with periods of 0.25-1 ms, and a 1.8 kN x 4 ms thrust spike (172 (2), 173); the relief set points confirmed (172 (6)); RG-16 miss side: GNC flies the published vented-mass table (172 (8)).
17. Line 175 (1)-(2) (v2.4a): A1 apogee target 285 m; the bleed-valve mass trigger is > 0.30 kg added by the selected pair.
18. Line 175 (3) (v2.4a), PROVISIONAL: **PURGE commits no later than the plain relight trigger - 1.7 s (T_fire delay <= 0.6 s); otherwise no purge.** Line 164's "the FC delays T_fire" is withdrawn. The rule's second branch, "the relight proceeds unpurged", is refuted by Combustion's check (v2.4a subsection after Table 2.15); the lead decides between no relight on that pass and a ride-through mode (OI-31).""")

rep('   - closure confirmed by E0 - 0.05 s;',
    '   - the flow stopped by E0 - 0.05 s, and closure confirmed by the closure deadline (<= the torch gate; LEAD line 166 (3));')

rep('The relight is never committed before a complete purge: if T_fire would cut the flow below 1.9 s, the FC delays T_fire | LEAD lines 153, 160, 161, 164 |',
    'Commit rule (LEAD line 175 (3), PROVISIONAL): PURGE commits no later than the plain relight trigger - 1.7 s, so that >= 1.9 s of flow fits with T_fire delayed by <= 0.6 s; otherwise no purge. The v2.4 rule "the FC delays T_fire" (line 164) is withdrawn. What follows a missed commit is open: Combustion\'s check refutes "the relight proceeds unpurged" (v2.4a subsection below) | LEAD lines 153, 160, 161, 164, 175 |')

repl_line('| Closure | Closure confirmed before E1',
          '| Closure | V1 first, confirmed on P_mid by the closure deadline (<= the torch gate; Electronics E0 + 0.15 s). E1 = torch confirmed AND [closure confirmed OR deadline reached]: at the deadline in flight BLEED_FAULT goes to the FC, V2 is commanded closed and the lift proceeds; on the stand it is an abort. The FC action is LOG-ONLY; closure from P_mid is a pad go/no-go on every flight with the bleed fitted | LEAD lines 160, 166 (3), 168 |')

rep("GNC's relight attitude (max 0.76 deg at RELIGHT; 0 of 500 above 1 deg) lies inside the 2 deg case.",
    "GNC's relight attitude (max 0.76 deg at RELIGHT; 0 of 500 above 1 deg) lies inside the 2 deg case. v2.4a: the angle that governs the liquid in the segment during PURGE is the specific-force angle to the body axis, not the attitude. GNC rev2 gives up to 2.71 deg raw (2.65 deg as a 0.1 s mean) in six re-flown records (`purge_outlet_inputs.json`), above the 2 deg basis. The purge model is not computed at 2.7 deg (OPEN, OI-35); CF-4 v2.0 adds 3 deg runs.")

rep('The 5 % quantiles of E0 -> E2 given a light are in the JSON.',
    'The 5 % quantiles of E0 -> E2 given a light are in the JSON (`E0_E2_given_light_quantiles_5pct_s`). v2.4a (R2-08): in the PURGE NOT RUN rows the last column is taken over all samples, a would-be time that W does not limit (A2 aborts beyond W); the given-light values are stated in the row.')

repl_line('| PURGE NOT RUN, LO worst (ARM LO wet) |',
          '| PURGE NOT RUN, LO worst (ARM LO wet) | 12.5, then an 11.2 slug and a 23.4 gap | 0.242 | All samples, would-be (A2 aborts beyond W): 0.510 / 1.281 / 1.318. Given a light: median 0.480, p95 0.576, max 0.628. Every such light is followed by the 23.4 cm3 gap (v2.4a subsection below) |')
repl_line('| PURGE NOT RUN, HI worst |',
          '| PURGE NOT RUN, HI worst | 51.8 (whole segment) | 1.0 | All samples, would-be (A2 aborts beyond W): 1.121 / 1.268 / 1.305. No light within W |')

rep('- "PURGE NOT RUN" is a failure state: a bleed valve fails closed, or the trigger gate never releases.',
    '- "PURGE NOT RUN" is a failure state: a bleed valve fails closed, the trigger gate never releases, or (v2.4a) the commit deadline of LEAD line 175 (3) passes without a commit.')

ins_after('- E0 -> E3 for the purged states:', '''
**v2.4a: unpurged start at the late-commit point** (LEAD line 175 (3) asks whether an unpurged start carries a hazard outside its abort model; `src/unpurged_start_check_v2p4a.py` `41fad4500f472bd4`, `data/v2p4a/unpurged_start_check_v2p4a.json` `4c745dcfbf09aef7`; SIM on the ASSUMED delays of the rg01 set, which the script reproduces before it extends it, plus DERIVED line states; no grid re-run).

The abort model behind Table 2.15 ends at E2: a light inside a liquid slug counts as a success, and the voids behind that slug are not followed. The check follows them.

Table 2.16. Post-light vapour gap (200 000 samples). Gap timing with the 2500 N/s start ramp to 200 N (volumetric flow scaled by mdot_ox(F) of the S230 map, DERIVED; ramp ASSUMED to start at E2) or with the flow held at the lift (an upper bound on times). Sequences P1 / S1 / C1 in cm3.

| State (0-2 deg) | P(light within W) | Lights followed by a vapour gap | Gap arrival after E2 [s]: ramp / lift flow | Gap duration [s]: ramp / lift flow | P(released, then A3): ramp / lift flow |
|---|---|---|---|---|---|
| PURGE NOT RUN, LO worst, unlined (12.5 / 11.2 / 23.4) | 0.758 | all | 0-0.091 (median 0.053) / 0-0.193 (median 0.094) | 0.139-0.156 / 0.365 | 0.712 / 0.717 |
| PURGE NOT RUN, LO worst, lined (15.6 / 12.4 / 19.2; lining dropped, line 164; reference) | 0.865 | all | 0-0.101 (median 0.058) / 0-0.220 (median 0.108) | 0.113-0.131 / 0.298 | 0.819 / 0.825 |
| PURGE NOT RUN, least, unlined (12.0 / 34.4 / 0.74) | 1.0 | all | 0.196-0.295 / 0.470-0.731 | 0.004 / 0.011 | 0 / 0 (dip shorter than the 22 ms A3 detection) |
| PURGE NOT RUN, HI worst (51.8, whole segment) | 0 | - | - | - | 0 (no light; A2 abort under the drogue) |
| PURGED 2.5 s, worst, unlined and lined; lined 2.2 s robust edge | 1.0 | none | - | - | 0 |

- **Release.** E2 in the latency model is Pc > 3 bar abs held 10 ms, so the drogue-release term (Pc valid AND >= 300 kPa abs, LEAD line 168 (1)) is already true at E2; the release follows within one 10 ms telemetry frame. On the 200 N ramp the unlined gap arrives before the 0.10 s hold of b7 in every sample, so b7 is never the first term.
- **A3 in the gap.** The oxidiser flow falls to 0.23 of the liquid flow (saturated vapour 128.2 against liquid 830.2 kg/m3 at 286.7 K, CoolProp). The A3 ratio in the gap is 0.008-0.030 at 62.5 N, 0.085-0.10 at 100 N, about 0.17 at 200 N and <= 0.24 at 500 N (CEA c*, n 0.35-0.68 ASSUMED, flame assumed to survive), below the 0.40 threshold, so A3 trips about 22 ms into the gap and aborts. A vapour light at the lift flow gives Pc 1.04-1.11 bar abs, below E2.
- **Consequence.** In 0.712 of the LO-worst starts (0.94 of its lights) the vehicle is released from the drogue and the engine then aborts. That is GNC's "dead vehicle released" class (touchdown about -32 m/s in GNC rev2, line 174), not the abort under the drogue that the model assumes (about -22 m/s). The same model leaves no successful relight in that state: P_total is about 0, not the 0.75 assumed in line 175 (3).
- **Population** (all PURGE NOT RUN records at 0 and 2 deg; bracket cases, not probability-weighted; first 20 000 samples): a light followed by a gap in 499 of 540 unlined LO records (mean P(released, then A3) 0.58), 477 / 540 lined LO (0.52), 180 / 540 unlined HI (0.22) and 270 / 540 lined HI (0.44).
- **Purged states:** no post-light gap. The 2.5 s purge removes the hazard. The HI worst unpurged state never lights within W and adds nothing new.
- **FA-1 interaction.** At 200 N the pintle seats before the liquid returns (no re-admission). On a 500 N ramp, 25 % of the trips re-admit liquid before the seat: <= 3.56 g with the flow held at the command point (above the 2.141 g FA-1 fast part) or <= 0.53 g with a linear closing. It matters only if the flame went out in the gap, which is not modelled.
- **Verdict (SIM/DERIVED, not physical).** The provisional rule is refuted as written: an unpurged start at the late-commit point carries a hazard outside its abort model (H20).
- **Proposal for the lead.** No commit by the plain trigger - 1.7 s -> no relight on that pass, as A14 does for a fail-closed bleed. A ride-through mode (drogue release held on unpurged starts; torch kept on and A3 adapted through the gap) is a research option only. Hypothesis: the flame survives a 0.14-0.37 s vapour gap. Comparator: the no-relight rule. Evidence needed: CF-4 optional run O-3 and IGN-1 on the dynamic Pc channel. Refutation: a flame-out or an A3 trip in the gap.
- **Limits.** Two-convention bracket of the trade (paused, restart; the larger result is kept); the ramp start at E2 is ASSUMED; flame survival through the gap is not modelled (if the flame goes out the ratio is lower and A3 trips sooner); no slosh or tilt above 2 deg.''')

# ---------------------------------------------------------------- §3.6
ins_after('- Unchanged: software Pc cap 25 bar;', '''- **Guard band (v2.4a; LEAD line 172 (4); R2-07).** The 0.67 bar margin on Pc equals about 0.92 K or 1.14 bar of P_tank (Table 3.8 slopes: +0.73 bar of Pc and +1.24 bar of P_sat per K, DERIVED). The interlock thresholds therefore sit below 24 C and 55.28 bar abs by the total channel uncertainty of T_tank and P_tank, which Electronics states (MISSING until then; interface `interlock_guard_band`).
- **CF-1 / CF-3 acceptance (LEAD line 172 (4)).** Full-stroke Cd <= 0.80 (the top of the ASSUMED band; Cd 0.85 alone adds about 1.4 bar, REV-COMB-2) and a line loss at the failure flow (about 0.38 kg/s) >= the modelled value. Otherwise MEOP is restated.''')

# ---------------------------------------------------------------- §6
rep('0.88-9.87 kJ into the valve-to-seat segment over the 18.67 s A1 coast in six heat cases (§2.8).',
    '0.83-9.0 kJ into the valve-to-seat segment over the 18.67 s A1 coast in six heat cases on CAD v3.4.1 (831-9011 J, `segment_heat_v341_v2p4.json`; §2.7-2.8). The 0.88-9.87 kJ printed here in v2.4 were Mechanical\'s totals on the superseded v3.4 route (875-9872 J) (R2-09).')
repl_line('**Proposal J1 (preferred;',
          '**Joint J1, CONFIRMED by the lead (CHANGELOG line 146; material data LITERATURE as recalled, TO-VERIFY).**')
rep('so the lip stays at or below its present 250 C in-burn;',
    'for the lip, 250 C was a goal, not a limit (CHANGELOG line 145); with J1 the lip runs at about 342 C in-burn (`nozzle_lip_melt_v2p4.json`);')
rep('- Alternative J2 (zirconia washer) is listed in the data file.',
    '- Alternative J2 (zirconia washer), not selected (J1 confirmed, line 146; Mechanical rejects J2 in line 179), is listed in the data file.')

# ---------------------------------------------------------------- §7.3
rep('At E1 the pintle is commanded to the ignition lift. From E1 to E2 the torch is supervised (A16) |',
    'On an A1 relight with the bleed fitted, E1 also needs [bleed closure confirmed OR the closure deadline reached]; the deadline is <= the torch gate (Electronics: E0 + 0.15 s). At the deadline without confirmation: in flight BLEED_FAULT goes to the FC (log-only), V2 is commanded closed and the lift proceeds; on the stand, abort (LEAD line 166 (3)). At E1 the pintle is commanded to the ignition lift. From E1 to E2 the torch is supervised (A16) |')
rep('If closure is not confirmed (BLEED_FAULT), the relight still proceeds (LEAD line 160).',
    'If closure is not confirmed by the closure deadline (<= the torch gate), E1 is declared at the deadline with BLEED_FAULT to the FC and V2 commanded closed, and the relight proceeds (LEAD line 166 (3)); on the stand it is an abort.')
ins_after('- A7 must therefore not set telemetered Pc invalid on a late-light plateau',
          '- v2.4a: LEAD line 175 (5) replaces the time-only 0xFFFF term in design by an accelerometer-gated term (with Pc invalid, release iff ECU RUN AND accelerometer thrust >= 37.16 N for 3 frames at 100 Hz; otherwise hold the drogue and command ABORT at t_E2 + 0.8 s; a PROPOSAL to be flown), and line 175 (4) makes Pc VALID a launch-commit condition. With Pc valid the release at E2 is unchanged; that is why an unpurged LO start is released before its vapour gap (§2.8, v2.4a).')
rep('The FC commands PURGE 2.90 s before T_fire, through the purge trigger gate (line 161).',
    'The FC commands PURGE 2.90 s before T_fire, through the purge trigger gate (line 161). **PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge** (LEAD line 175 (3), PROVISIONAL; T_fire delay <= 0.6 s; line 164\'s "the FC delays T_fire" is withdrawn). What follows a missed commit is for the lead: line 175 (3) says the relight proceeds unpurged; Combustion\'s check refutes that branch and proposes no relight on that pass (§2.8, v2.4a; H20).')
rep('If closure is not confirmed before E1, BLEED_FAULT goes to the FC and the relight proceeds (LEAD line 160).',
    'Closure (V1 first) is confirmed on P_mid by the closure deadline, <= the torch gate (Electronics: E0 + 0.15 s); E1 needs closure confirmed OR the deadline reached. At the deadline in flight BLEED_FAULT goes to the FC, V2 is commanded closed and the lift proceeds; on the stand it is an abort (LEAD line 166 (3)).')

# ---------------------------------------------------------------- §7.4
rep('Software: Pc > 30 bar abs on the raw channel for 5 ms (code 2 HARD_START during IGNITION, code 17 PC_OVERPRESSURE after; LEAD line 160, was 3 ms).',
    'Software: Pc > 30 bar abs on the FILTERED channel for 5 ms (code 2 HARD_START during IGNITION, code 17 PC_OVERPRESSURE after; LEAD line 166 (4), which amends "raw" in line 160 (2); was 3 ms).')
rep('A late-light spike trips neither: raw above 30 bar <= 1.9 ms; comparator RC peak <= 19.3 bar abs (§7.6).',
    'A late-light spike trips neither: filtered peak <= 21.4 bar abs (LEAD line 166 (4); raw above 30 bar <= 1.9 ms); comparator RC peak <= 19.3 bar abs (§7.6).')
repl_line('| A14 | Bleed valve fault',
          '| A14 | Bleed valve fault (two NC valves in series on the joined bleed path, downstream of the tee) | Position or current feedback per valve (Electronics sets): a valve not open within its command window, or closure not confirmed by the closure deadline (<= the torch gate; Electronics E0 + 0.15 s; LEAD line 166 (3)) | PURGE command to E1; run | One valve not opening: no purge flow at all (the taps share the pair). No commit or no flow means no purge (LEAD line 175 (3), PROVISIONAL). Combustion proposes no relight on that pass (H20; OI-31); the lead decides. If the relight proceeds unpurged, the line state is "PURGE NOT RUN" (P_abort 0.24 LO to 1.0 HI, Table 2.15), and in the LO state a vapour gap follows every light, so A3 aborts after the drogue release (§2.8, v2.4a). One valve not closing: its series partner holds; flag. Closure not confirmed by the deadline (both open, double or common-cause fault): in flight E1 is declared at the deadline, BLEED_FAULT goes to the FC (log-only, line 168), V2 is commanded closed and the relight proceeds; on the stand, abort (LEAD line 166 (3)) | Both valves open: up to 31.24 g/s liquid overboard (11.8 % of the 100 % flow; upper bound) for the rest of the flight, additive tank outflow (GNC S313, ADDITIVE governs, line 164). The injector loses <= 0.09 % at the lift and about 1.5 % at 100 % if open loop (§9.1). Jet 3.3-5.0 N through the balanced or axial vent. The series pair doubles the fail-closed probability of the purge; FMEA input (§9.1) |')

# ---------------------------------------------------------------- §7.6
append_line('- Decisions on these numbers (LEAD line 160):',
            ' [Amended by LEAD line 166 (4): the 30 bar abort runs on the FILTERED channel with 5 ms persistence; filtered light-spike peak <= 21.4 bar abs.]')

FA1 = f'''**Fuel-assisted fast part at a relight: FA-1 envelope (v2.4a; REV-COMB-2 R2-03; LEAD lines 172 (2) and 173).** `src/fa1_envelope_v2p4a.py` (`a6b71cb487c9642e`) re-runs the v2.4 construct of `late_light_spike_v2p4.py` (hot chamber, fuel vapour premixed with the arriving N2O), first reproducing the v2.4 case to 1e-6 bar. It runs at the A1 relight (32.2 mm port, products at the A1 tank state 286.7 K) over O/F 3-12 x burn time tf 1-7 ms (1 ms steps) x residence 0.02 / 0.06 s x pool none / q 2 MW/m2, for two readings of the chamber vapour ("vapour once", the baseline; "as written", the v2.4 double count, an upper bracket) and both entrances: 896 cases, each with head and aft histories (`data/v2p4a/fa1_envelope_v2p4a.json` `64b328150025fa1e`; summary CSV `86d764bc80ed1dd5`). SIM on an ASSUMED construct (burn time, fuel fraction); tables DERIVED (`fa1_tables_v2p4a.json` `677fd9ccd297fdf4`). It supersedes the v2.4 table at O/F 8 only (48.9-75.5 bar at 1 ms, <= 55.5 bar at 5 ms, <= 41.4 bar at 10 ms), which is kept in §13.

Table 7.6a. FA-1 envelope maxima over O/F 4-12, tf 1-7 ms, residence and pool (impulse above P0 = 1.071 bar over 25 ms).

{TAB_T1}

Table 7.6b. Head peak [bar abs] by O/F and burn time, maximum over residence and pool: baseline (vapour once, rounded entrance) / upper bracket (as written, sharp entrance).

{TAB_T2}

- **O/F.** The closed-volume pressure of the fast part (2.141 g N2O in 365.65 cm3) peaks at O/F 3.5-4 (about 89 bar) and falls at lower O/F (84.5 bar at 3, 61 bar at 2). The first-order fuel-vapour bound does not exclude O/F below 4 (minimum about 1.5-2.0), but within the construct the O/F 3.5-4 rows bound the peak. The fuel-vapour inventory at the light remains MISSING (IGN-1, T4).
- **Burn time.** At O/F 4 (baseline) the peak falls from 83.0 bar at tf 1 ms to 53.0 bar at 7 ms, while the time above 45 bar stays at 3.15-3.6 ms and the impulse at 718-721 bar ms: a slower burn trades peak for duration at about constant impulse.
- **Entrance and aft end.** The rounded entrance lowers the baseline peak by about 2 % at the 32.2 mm port (83.0 against 84.8 bar). The aft node carries 0.95-1.00 of the head peak, so the J1 lip and the aft closure take the same load.
- **Thrust.** Peak 1.63-1.70 kN (Cf 1.35) or 1.69-1.77 kN (quasi-steady, eta_cf 0.975). The SDOF equivalent is <= 3.05 kN at periods of 0.5-5 ms, against 3.48-3.60 kN for the interim 1.8 kN x 4 ms rectangle, which therefore bounds.
- **Pressure DLF.** <= 1.007 for periods <= 0.1 ms (shell and bonnet: quasi-static valid); 1.05-1.20 for periods of 0.25-1 ms, giving a head equivalent static of <= 89.0 bar abs (baseline, rounded) and <= 102.0 bar abs (upper bracket, sharp).
- **Fuel basis.** Styrene gas instead of the ABS card: +1.8-2.8 % on the peak (90.1 bar on the as-written sharp case; 85.0 bar baseline rounded).
- **Outflow model form (R2-11).** Frozen-gamma outflow vents about 4 % fast. Reducing the throat area by 3.7 % (8 %) raises the tf 1 ms peak by 0.5-0.6 % (1.1-1.3 %), the tf 3 ms peak by 1.4-1.6 % (3.0-3.5 %) and the time above 45 bar by 0.15-0.25 ms (0.35-0.55 ms) (`fa1_outflow_sens_v2p4a.json` `540a78f8b9634f76`; a first-order emulation, ASSUMED). The 92 bar design value (89.0 x 1.03) becomes about 92.2 bar with the 4 % form (92.9 bar at 8 %); the 102 bar sensitivity covers it.
- **Not modelled:** acoustic and wave peaks along the 230 mm port (lumped nodes; transit about 0.3 ms hot and 1 ms cold); equilibrium thermochemistry (kappa fitted at 40 kg/m3 overstates the pressure by about 3.7 % at 6.6 kg/m3, conservative); flame spread, heat loss and roughness; the torch contribution before the light. A 1-D gas-dynamic run of the worst row would close the model-form items (R2-11; OI-36).
- **Load (LEAD line 173).** FA-1 structural load: 90 bar abs quasi-static at head and aft for every part; parts with natural periods of 0.25-1 ms also at 92 bar abs (design: baseline rounded with DLF and the +3 % fuel basis) and 102 bar abs (sensitivity: upper bracket, sharp, DLF); thrust spike 1.8 kN x 4 ms, confirmed bounding. Mechanical's margins (line 176, SF 1.0, FE and hand results) led to the lead's actions (line 177): the TC-09 aft section changes to Inconel 718 (316L yields at 90 bar); J-FWD to yield MS >= 0 at 92 bar and ultimate MS >= 0 at 102 bar; seal S13 (-0.016 at 102 bar only) accepted as a sensitivity result; the gimbal 608 bearings reselected against a maker-datasheet C0 at Combustion's SDOF 3.05 kN with DLF 2.0. Status from Mechanical (lines 178-179, SIM/DERIVED): TC-09 Inconel 718 is in CAD v3.5; J-FWD moves to A4-80 screws (yield MS +0.29 at 92 bar, ultimate +0.61 at 102 bar); the bearing selection is OPEN (C0 >= 1.80 kN per bearing from a maker datasheet, not done).
- A pad start from a cold chamber has only the torch propane as fuel before main ignition (0.027 g over 0.30 s, enough to burn 0.27 g of N2O, 14-22 % of the fast part), so the fuel-assisted case does not apply to it.
- **MEOP is NOT confirmed for the fuel-assisted case.** The control is the torch-first gate alone: a single-control hazard, FA-1 in §9.1 (LEAD lines 160 and 164). Electronics is required to fit (a) E1 on P_torch AND photodiode and (b) torch supervision from E1 to E2 (A16). These limit the exposure; they do not remove it. FA-1 is accepted for design continuation only. Flight acceptance needs IGN-1 (>= 30 lights with photodiode false-positive tests, on the stand dynamic Pc channel) and Mechanical's margins against the line-173 load with the line-177 actions closed (LEAD lines 170 (2), 172 (2), 173, 177).'''
block('**Fuel-assisted fast part at a relight** (hot chamber', '**Stand relief options**', FA1)

append_line('- **Wait after a no-light:**',
            ' This is the one stand rule after a no-light (LEAD line 172 (1)); H9, §10.2 and the interface (`stand_safing_v2p4a`) carry the same text.')

# ---------------------------------------------------------------- §7.7
rep('The relight is never committed before a complete purge: if T_fire would cut the flow below 1.9 s, the FC delays T_fire (LEAD line 164; GNC quantifies the height cost).',
    'PURGE commits no later than the plain relight trigger - 1.7 s; otherwise no purge (LEAD line 175 (3), PROVISIONAL; it withdraws line 164\'s "the FC delays T_fire"). In GNC rev2 the T_fire delay is <= 0.6 s and costs no measurable P; the decided-path height cost is <= 3.04 m (line 174, SIM). After a missed commit see H20 (§2.8, v2.4a).')

# ---------------------------------------------------------------- §8
repl_line('- Test requirement: T2 and T3 with 1 kHz Pc logging',
          '- Test requirement: T2 and T3 log Pc on the stand dynamic channel (>= 10-20 kHz with an anti-alias filter, flush mount or a characterised short sense line; LEAD line 172 (5)) at every throttle level. Logging at 1 kHz would alias the 1.1-1.8 kHz modes.')
rep('- **Test requirement:** T2 and T3 log Pc at 1 kHz at every throttle level.',
    '- **Test requirement:** T2 and T3 log Pc on the stand dynamic channel (>= 10-20 kHz, anti-alias filter; LEAD line 172 (5)) at every throttle level.')

# ---------------------------------------------------------------- §9
rep('Arm window 15-25 C (ENG-12); 24 C liquid-line interlock (§2.8);',
    'Arm window 15-24 C at ARM (ENG-12 as amended); 24 C liquid-line interlock (§2.8) with the thresholds lowered by the channel uncertainty (guard band, §3.6);')
rep('No retry into a pooled chamber. Ground: >= 5 s wait, N2 purge, safing (§10.2).',
    'No retry into a pooled chamber. Ground: N2 purge >= 60 s at >= 10 g/s, then a hold of >= 15 min before approach with Pc at ambient and the head thermocouples falling, then safing (§7.6, §10.2; LEAD line 172 (1)).')
rep('A4 at 30 bar raw for 5 ms (§7.4)',
    'A4 at 30 bar abs on the filtered channel for 5 ms (§7.4; LEAD line 166 (4))')
rep('Fuel-assisted fast part at a relight: 48.9-75.5 bar at a 1 ms burn (§7.6) | Torch-first gate; rounded entrance REQUIRED; W per §7.3; LIGHT_SPIKE logging; FA-1 (a) and (b) REQUIRED (§9.1) |',
    'Fuel-assisted fast part at a relight (FA-1 envelope): head 83.0-88.0 bar abs, above MEOP for <= 3.65-4.45 ms, never above 90 bar abs (§7.6) | Torch-first gate; rounded entrance REQUIRED; W per §7.3; LIGHT_SPIKE logging (lower bounds at 1 kHz in flight; the stand dynamic channel measures); FA-1 (a) and (b) REQUIRED; structural load per LEAD line 173 (§9.1) |')
rep('| The relight is never committed before a complete purge (LEAD line 164): the FC delays T_fire or does not relight on that pass |',
    '| No commit by the plain trigger - 1.7 s -> no purge (LEAD line 175 (3), PROVISIONAL; the T_fire delay of line 164 is withdrawn). Proposal: no relight on that pass (H20) |')
rep('Seal layer of proposal J1;', 'Seal layer of joint J1 (CONFIRMED, LEAD line 146);')
ins_after('| H19 |',
          '| H20 (v2.4a) | Unpurged start after a missed PURGE commit or a fail-closed bleed (LEAD line 175 (3)) | PURGE NOT RUN LO worst: every light (P 0.758) is followed by a 23.4 cm3 vapour gap 0-0.19 s after E2; the drogue-release term is already true at E2, and A3 aborts in the gap: released, then A3, in 0.712 of starts (lined 0.819; population means 0.22-0.58) (§2.8, v2.4a; SIM/DERIVED) | Proposal: no relight on that pass (as A14). Research option: ride-through (release held on unpurged starts; torch kept on; A3 adapted) on CF-4 O-3 and IGN-1 evidence. The lead decides (OI-31) |')

rep('and closure not confirmed by E0 - 0.05 s)',
    'and closure not confirmed by the closure deadline, <= the torch gate, LEAD line 166 (3))')
repl_line('- Before 0.5 s: m(t) lies between',
          "- Before liquid reaches the taps, the minimum of the open-element bracket is the all-vapour line 8.49 t (g, with t in s) up to 1.0 s. The minimum of the barrier-element bracket lies below that line until 1.6 s (3.17 g at 0.5 s, 5.93 g at 1.0 s), because that model stalls the T4 tap behind a capillary barrier (bubble point about 0.7 kPa against 45.5 bar): a model construct that a real T4 will not reproduce (REV-COMB-2 R2-06; `vented_mass_brackets_v2p4a.json` `8e8ca9329c74a01f`). GNC flies the published table, which is conservative on the miss side (LEAD line 172 (8)); GNC rev2 reports that its RG-16 miss-side failure is not caused by these minima (line 174). The flow rate never exceeds 31.24 g/s.")
repl_line('- The minimum rises at about 6 g/s',
          '- The maximum is not all-liquid flow from the start: every record starts with vapour, so the maximum is 11.9 g at 0.5 s and 72.9 g at 2.5 s, against 15.6 g and 78.1 g on the all-liquid line 31.24 t. The barrier minimum rises at about 5.5 g/s until liquid reaches the taps, then at about 25 g/s after 1.6 s. [v2.4 wording corrected per R2-06.]')
repl_line('| B-5 | Purge truncated by T_fire |',
          '| B-5 | Purge truncated by T_fire, or not committed | P_abort up to 0.098 at 1.8 s, 1.0 at 1.0 s (truncated-purge table, §2.8); without a purge see B-6 | FC timing | PURGE commits no later than the plain trigger - 1.7 s, so >= 1.9 s of flow fits with T_fire delayed by <= 0.6 s; otherwise no purge (LEAD line 175 (3), PROVISIONAL; the T_fire delay of line 164 is withdrawn) |')
ins_after('| B-5 | Purge truncated by T_fire, or not committed |',
          '| B-6 (v2.4a) | Unpurged relight (no commit by the plain trigger - 1.7 s, or no flow) | H20: in the PURGE NOT RUN LO worst state every light is followed by a 23.4 cm3 vapour gap after the drogue release; A3 aborts: released, then A3, in 0.712 of starts (§2.8, v2.4a) | None in time: the release term is true at E2, before the gap | Proposal: no relight on that pass (OI-31); the lead decides |')

rep('**FA-1: fuel-assisted fast part at an A1 relight (single-control hazard; LEAD lines 160 (4) and 164 (8)).**',
    '**FA-1: fuel-assisted fast part at an A1 relight (single-control hazard; LEAD lines 160 (4), 164 (8), 172 (2) and 173).**')
rep('Head Pc 48.9-75.5 bar abs at a 1 ms burn time: above MEOP 45 bar for <= 3.0 ms, above proof 67.5 bar at a 60 ms residence time. At a 5 ms burn time <= 55.5 bar, at 10 ms <= 41.4 bar. The rounded entrance does not help at 32.2 mm. SIM on ASSUMED burn time and fuel fraction (`late_light_spike_v2p4.json`).',
    'Envelope over O/F 4-12 and burn times of 1-7 ms (v2.4a, §7.6): head peak 83.0 bar abs (baseline) to 88.0 bar abs (upper bracket), aft 0.95-1.00 of the head; above MEOP 45 bar for <= 3.65 ms (4.45 ms), above proof 67.5 bar for <= 1.0 ms (1.3 ms), never above 90 bar abs; thrust spike <= 1.77 kN, SDOF equivalent <= 3.05 kN. SIM on an ASSUMED construct (`fa1_envelope_v2p4a.json`); the fuel-vapour inventory at the light is MISSING.')
rep('The 30 bar abort (5 ms raw) and the comparator (RC 5.28 ms) cannot act within a 1-3 ms pulse. LIGHT_SPIKE records the event afterwards: evidence, not protection.',
    'The 30 bar abort (filtered channel, 5 ms; LEAD line 166 (4)) and the comparator (RC 5.28 ms) cannot act within a 1-4 ms pulse. LIGHT_SPIKE records the event afterwards: evidence, not protection; at the 1 kHz flight logging its values are lower bounds (LEAD line 172 (5)).')
rep('- Severity: catastrophic if the case or closures fail; critical otherwise.',
    '- Severity: catastrophic if the case or closures fail; critical otherwise. Consequence (LEAD line 172 (2)): yield possible and ultimate not demonstrated until the line-177 actions close. Status (Mechanical lines 178-179, SIM/DERIVED at SF 1.0): TC-09 Inconel 718 in CAD v3.5; J-FWD A4-80 (yield MS +0.29 at 92 bar, ultimate +0.61 at 102 bar); the gimbal bearing selection OPEN (C0 >= 1.80 kN per bearing from a maker datasheet).')
rep("Mechanical's check of the case and closures for a 75.5 bar abs, <= 3 ms head pulse (dynamic load factor, burst margin), added to the FEA scope.",
    "Mechanical's margins against the line-173 load (90 bar abs quasi-static at head and aft; 92 / 102 bar abs for parts with periods of 0.25-1 ms; 1.8 kN x 4 ms thrust spike), reported in line 176.")
rep('Flight acceptance needs IGN-1 and the Mechanical pulse check (LEAD line 164).',
    "Flight acceptance needs IGN-1 and Mechanical's margins against the line-173 load with the line-177 actions closed (LEAD lines 164, 170 (2), 173, 177).")
rep('Mechanical the pulse check;', 'Mechanical the margins and the line-177 actions;')

# ---------------------------------------------------------------- §10
rep('| Pc (1 kHz), F, roll torque',
    '| Pc on the stand dynamic channel (>= 10-20 kHz, LEAD line 172 (5)) and the 1 kHz control channel, F, roll torque')
append_line('- **IGN-1:** >= 30 lights including photodiode',
            ' v2.4a: Pc and P_torch on the stand dynamic channel (>= 10-20 kHz, LEAD line 172 (5)), so that 1-3 ms spikes are resolved; flight LIGHT_SPIKE values at 1 kHz are lower bounds.')
ins_after('- **T4:** relights with the flight PURGE sequence', '''
**v2.4a amendments to the test plan** (REV-COMB-2; LEAD line 172).
- **Stand dynamic Pc channel (LEAD line 172 (5); R2-10):** IGN-1 and T1-T3 log Pc (and P_torch at IGN-1) at >= 10-20 kHz behind an anti-alias filter, with a flush-mounted transducer or a characterised short sense line (resonance measured), and a range >= 100 bar abs to cover the FA-1 envelope. The 1 kHz control channel aliases the 1.1-1.8 kHz modes and under-reads 1-3 ms spikes; flight LIGHT_SPIKE values logged at 1 kHz are lower bounds.
- **CF-1 and CF-3 acceptance (LEAD line 172 (4); R2-07):** full-stroke Cd <= 0.80, and a line loss at the failure flow (about 0.38 kg/s) >= the modelled value; otherwise MEOP is restated (§3.6).
- **Stand safing after a no-light (LEAD line 172 (1)):** the one rule of §10.2.
- **CF-4 v2.0:** 3 deg runs, per-tap flow, P4 per tap and per phase, P6 per line 166 (3), optional run O-3 (§10.3).
- **T1-T4:** specification v2 (§10.4): law stations x/L 0.80-0.90, the T3 holds at 20 % and 12.5 % as the law firings, repeats to σ(S) <= 1.5 %, N2 quench, witness sectioning, a density map.''')
repl_line('- **No-light or abort on the stand:**',
          '- **No-light or abort on the stand** (LEAD line 172 (1), the one rule): no retry into a pooled chamber; N2 purge of the chamber >= 60 s at >= 10 g/s; then a hold of >= 15 min before anyone approaches, with Pc at ambient and the head thermocouples falling; then the post-test procedure. The v2.3 "wait >= 5 s" is withdrawn everywhere (§7.6).')
rep('### 10.3 CF-4 summary (full text in `CF-4-SPEC.md`)',
    '### 10.3 CF-4 summary (full text in `CF-4-SPEC.md` v2.0)')
rep('a 0 / 2 deg tilt fixture.',
    'a 0 / 2 / 3 deg tilt fixture (v2.0), per-tap flow instruments and a tank-outlet probe.')
rep('P4 each tap >= 80 % of the model flow;',
    'P4 each tap >= 80 % of the model flow, per tap and per phase (vapour, then liquid), against the open-element reading (the barrier reading\'s T4 stall is a model construct and cannot pass or fail P4);')
rep('P5 <= 76 g vented from IS-1 and IS-2;',
    'P5 <= 76 g vented from IS-1 and IS-2, read against the vented-mass brackets;')
rep('P6 both valves closed with the flow stopped by E0 - 0.05 s, and BLEED_FAULT raised with one valve held open;',
    'P6 (a) the flow stopped by E0 - 0.05 s, (b) closure confirmed (V1 first, on P_mid) by the closure deadline <= the torch gate (E0 + 0.15 s), (c) with one valve held open, BLEED_FAULT at the deadline, then V2 commanded closed and the lift (flight build) or an abort (stand build) (LEAD line 166 (3));')
ins_after('- **Pass criteria P1-P7.**',
          "- **v2.0 changes (v2.4a).** Tilt runs at 0, 2 and 3 deg (GNC rev2's 2.71 deg specific-force angle; 4 deg sensitivity); per-tap flow channels and a tank-outlet probe; P4 per tap and per phase; P5 against the vented-mass brackets; P6 per LEAD line 166 (3); optional run O-3, an unpurged start, which tests the post-light vapour gap of §2.8 (a sequence with no gap after the first slug refutes the finding for that state). CF-4 tests the purge, not the commit rule.")

TS = '''### 10.4 Regression-rate measurement at T1-T4 and the law form (RG-03; specification v2)

The full text is `02-combustion/T1-T4-REGRESSION-SPEC.md` v2 (REV-COMB-2 R2-04; LEAD line 172 (3)); the computation is `t1t4_law_resolution_v2p4a.json` (`05b5ae5c20e04bd8`; DERIVED from published SIM histories, no grain re-run). The v2.4 text of this section is superseded: its law decision could not resolve the signature at T1, and it defaulted to the less safe gate when nothing was detected.

- **Burden of proof reversed (LEAD line 172 (3)).** The B1 gate is "current rule OR a_meas >= 1.25 -> change the grain" by default. It is relaxed only if the oxidiser-flux law is positively shown at σ(S) <= 1.5 %.
- **Law stations.** x/L 0.80, 0.85 and 0.90 against the head reference x/L 0.10 (x/L 0.30 if the spray check fails). a_meas stays at x/L 0.97 for the gate (REQUIREMENTS line 117).
- **Signature.** S = r(0.85)/r(0.10) over a 0.6-1.5 and n 0.35-0.68: 1.014-1.072 at T1 100 %; 1.037-1.135 on the T3 holds at 20 % and 12.5 %. At a x1.0 the probability of showing the oxidiser-flux law at σ 1.5 % is 0.47-0.95 at T1 and 0.99-1.00 on the T3 holds, which carry the decision.
- **σ target and repeats.** σ(S) <= 1.5 %; N = ceil(s1^2 / (0.015^2 - s_s^2)) repeats for a single-firing scatter s1 and a residual systematic term s_s (both ASSUMED bands until measured). A practical count (N <= 8) needs s_s <= 1.0 %.
- **Systematic terms** with ASSUMED residual targets: post-shutdown melt and soak-back (N2 quench; two-duration differential), the char and melt layer (witness sectioning), ovality (>= 4 diameters), the print density along x (density map), start and tail-off transients, head-end spray, aft-end flow, station position.
- **Errs safe (DERIVED; 78 B1 grain_q1d records: 30 on the 85 m band, 48 on the 62 m records; O/F down to 1.78).** Under a total-flux truth the gate keeps its 10 % allowance only if ρ = E_B1 / E_cal <= 1. A T1-only calibration gives ρ_max 1.068 (3.0 % of the allowance left). With a T3 hold, ρ_max is 1.004 (9.6 % left) at 20 % and 0.990 (11.2 %) at 12.5 %. Proposal for the lead: a_meas,gate = max(1, ρ_max) x a_meas whenever the oxidiser-flux law is not shown; a calibration set with a T3 hold makes the correction negligible.
- **Measurements.** Grain mass (<= 0.1 g, dried); >= 4 diameters per station (bore gauge <= 0.02 mm, or a 3-D scan) at x/L 0.10, 0.30, 0.50, 0.70, 0.80, 0.85, 0.90 and 0.97; Pc on the stand dynamic channel and the control channel; the oxidiser flow from the load cell and P_feed; the N2 quench at shutdown; witness sectioning; a density map of the printed grain.
- The burn limit for GNC is recomputed with 1.1 x a_meas and the declared law form (§4.6). O/F is not a gnc.json quantity: the B1 O/F histories come from Combustion's grain model run on the gnc.json duty cycles.
- **Limits.** The analytic signature model reproduces the grain_q1d record on DC-D to about 0.5 % (E at x/L 0.97 1.0607 against 1.0664; web 14.25 against 14.24 mm; regression-weighted O/F 8.37 against 8.17). A first pass of the computation read the wrong DC-D file, counted start rows as run rows, let the analytic model burn past burn-through and counted the 62 m records in the 85 m group; all were corrected before any value was used (§13).'''
block('### 10.4 Regression-rate measurement at T1-T4', '## 11. Unknowns', TS)

# ---------------------------------------------------------------- §11
append_line('17. The real late-light burn time and fuel fraction (FA-1)',
            ' v2.4a: also IGN-1 on the stand dynamic Pc channel.')
repl_line('21. Tank outlet coverage from the PURGE command',
          '21. Tank outlet coverage from the PURGE command (§2.4 notes): covered quasi-statically if the outlet is on the aft bulkhead of an axial tank (v2.4a); the outlet geometry (Mechanical, CAD), the slosh amplitude and the 500-run specific-force angle (GNC) are MISSING; then flight data.')
ins_after('24. The tail-off rows of §3.7', '''25. The fuel-vapour inventory in the warm 32.2 mm port at the moment of an A1 light (FA-1 basis; MISSING): IGN-1 and T4 on the stand dynamic Pc channel.
26. The FA-1 wave peaks along the port and the equilibrium outflow (R2-11): a 1-D gas-dynamic run of the worst row (Combustion, OI-36).
27. Whether a light inside a liquid slug survives the vapour gap that follows it (unpurged start, H20): CF-4 optional run O-3, IGN-1.
28. The purge at the 2.7 deg specific-force angle of GNC rev2 against the 2 deg basis: Combustion model run (OI-35), then CF-4 at 3 deg.
29. The total channel uncertainty of T_tank and P_tank behind the interlock guard band: Electronics, then CF-1 / CF-3.
30. The single-firing scatter s1 and the residual systematic term s_s of the law signature: T1-T3 repeats (T1-T4 specification v2).''')

# ---------------------------------------------------------------- §12
rep('## 12. Open items with owners (v2.4)', '## 12. Open items with owners (v2.4, updated in v2.4a)')
rep('the nozzle joint adds H19 and proposal J1 (§6.5)', 'the nozzle joint adds H19 and joint J1, CONFIRMED by line 146 (§6.5)')
repl_line('| OI-17 |',
          '| OI-17 | FA-1 load | Margins against the line-173 load (90 bar abs quasi-static at head and aft for every part; 92 / 102 bar abs for parts with periods of 0.25-1 ms; 1.8 kN x 4 ms): reported in line 176. Line-177 actions: TC-09 Inconel 718 in CAD v3.5 (line 178) and J-FWD A4-80 (line 179) done on paper; open: the gimbal bearing selection (C0 >= 1.80 kN per bearing from a maker datasheet) | Mechanical |')
rep('A4 at 30 bar raw for 5 ms; A7 bands',
    'A4 at 30 bar abs on the filtered channel for 5 ms (line 166 (4)); the E1 closure term and A14 per line 166 (3); A7 bands')
rep('| OI-21 | Seat face | <= 800 K from MECO to E1 in the FE | Mechanical |',
    '| OI-21 | Seat face | <= 800 K from MECO to E1 in the FE (line 179: base case < 800 K; adiabatic case OPEN) | Mechanical |')
repl_line('| OI-22 |',
          '| OI-22 | Nozzle joint | J1 CONFIRMED (line 146); FE re-run with the two-layer stack; the 316L lip at about 342 C against the 10.6 MPa bearing; leak criterion | Mechanical, Combustion |')
rep('the height cost and the floor of the T_fire delay rule;',
    'the height cost of the PURGE commit timing (the T_fire delay rule of line 164 is withdrawn by line 175 (3));')
rep('tank outlet coverage from PURGE (§2.4) | GNC |',
    'tank outlet coverage from PURGE (§2.4; v2.4a screening done; the 500-run angle and slosh remain). Status: re-flown in GNC rev2 (line 174, SIM, staged), under REV-GNC-3 | GNC |')
repl_line('| OI-27 |',
          '| OI-27 | HANDBACK-SUMMARY lines 79-80 | Done (line 170); the remaining wording (R2-12) was done by the lead (line 172 (7)) | Done |')
repl_line('| OI-28 |',
          '| OI-28 | ENG-01 at the 25 bar cap (RC-09) | Decided (line 170 (1)): the 25 bar software cap stays; at the eta_cf low end the rated thrust is about 487 N at 25 bar; T1 measures eta_cf, and the measured k feeds GNC\'s cap rule | Decided; T1 |')
repl_line('| OI-29 |',
          '| OI-29 | Regression law form (RG-03) | Specification v2 (§10.4): reversed burden (line 172 (3)), law stations x/L 0.80-0.90, σ(S) <= 1.5 %, T3 holds, systematic terms; errs-safe correction proposed | Founders, Combustion; lead (correction) |')
ins_after('| OI-30 |', '''| OI-31 | PURGE commit rule (H20) | Line 175 (3) is PROVISIONAL; Combustion's check refutes "the relight proceeds unpurged" (§2.8, v2.4a). Decide: no relight on that pass, or a ride-through mode on evidence | Lead (GNC, Combustion) |
| OI-32 | Tank outlet | Outlet position and diameter, dip tube or sump, anti-vortex device, orientation and bulkhead face in CAD; a slosh bound; the 500-run specific-force angle during PURGE | Mechanical, GNC |
| OI-33 | Interlock guard band | Total channel uncertainty of T_tank and P_tank; thresholds lowered by it; CF-1 / CF-3 acceptance (Cd <= 0.80, line loss >= model) | Electronics, founders |
| OI-34 | Stand dynamic Pc channel | >= 10-20 kHz, anti-alias filter, flush mount or a characterised short sense line, range >= 100 bar abs, for IGN-1 and T1-T3; price TO-QUOTE (Sønderborg DK-6400) | Electronics, founders |
| OI-35 | Purge at 2.7 deg | Re-run the decided-path purge at the GNC rev2 specific-force angle (2.71 deg raw) and at 3 deg; CF-4 v2.0 adds 3 deg | Combustion |
| OI-36 | FA-1 model form | A 1-D gas-dynamic run of the worst FA-1 row (R2-11) | Combustion |
| OI-37 | Interface configuration (R2-13) | mechanical.json v2.1 (line 179) adds the bleed topology and the FA-1 per-part tables, but has no MEOP, MAWP or rounded-entrance keys and quotes the tank relief as <= 7.5 MPa; electronics.json v2 (as reviewed) shows A5 OPEN, the 2.0 s hold and the Burkert 6027 HP | Lead |''')

# ---------------------------------------------------------------- §13
rep('| NZ-03 mica/vermiculite gasket | 1595 C against a 900 C rating | Proposal J1 (§6.5) |',
    '| NZ-03 mica/vermiculite gasket | 1595 C against a 900 C rating | J1 (§6.5), CONFIRMED by line 146 |')
ins_after('| Run-1 files: late_light_spike', '''
v2.4a failures and superseded evidence (kept; the v2.4 report and specifications are archived under `superseded/v2p4/`):

| Item | What happened | Consequence |
|---|---|---|
| A4 "raw" (v2.4 §0, §7.4, §8, §9.1, §12) | Line 166 (4) moved the 30 bar abort to the filtered channel; v2.4 kept "raw" (R2-01) | Filtered, 5 ms, everywhere; the line-160 record in §7.6 kept with an amendment note |
| E1 / A14 closure "before E1" and "by E0 - 0.05 s" | Three different deadlines (R2-01); E0 - 0.05 s is the scheduled flow end | Closure deadline <= the torch gate (line 166 (3)); E0 - 0.05 s kept only as the flow end |
| Stand rule "wait >= 5 s" in H9, §10.2 and the interface | Withdrawn in §7.6 but live elsewhere (R2-02) | One rule (line 172 (1)) |
| FA-1 "48.9-75.5 bar at 1 ms" and the "75.5 bar, <= 3 ms" pulse check | One O/F (8) at an ASSUMED fuel fraction (R2-03) | FA-1 envelope 83.0-88.0 bar abs; load per line 173 |
| T1-T4 specification v2.4 | Could not resolve the signature at T1; non-detection defaulted to the less safe gate (R2-04) | Specification v2, reversed burden |
| T1-T4 computation, first pass | Wrong DC-D file (not the S230 record); start rows read as run rows; the analytic model burned past burn-through (web 25.6 mm); the 62 m records counted in the 85 m group | Corrected before any value was used; the model check reproduces the q1d web (14.25 against 14.24 mm) |
| §9.1 vented-mass sentences | Contradicted their own table (R2-06) | Corrected; the barrier-bracket minimum stated as a model construct |
| Table 2.15 PURGE NOT RUN rows | All-sample would-be times under a given-light caption (R2-08) | Relabelled; given-light values stated |
| §6.4 segment heat 0.88-9.87 kJ | Mechanical's totals on the superseded v3.4 route | 0.83-9.0 kJ on CAD v3.4.1 |
| J1 "pending agreement"; lip "<= 250 C" as a requirement | J1 confirmed (line 146); 250 C a goal (line 145) | Text aligned (R2-09) |
| Line 164 "the FC delays T_fire" | GNC rev2: P 0 for commits at the plain trigger (line 174) | Withdrawn by line 175 (3) |
| Line 175 (3) "the relight proceeds unpurged (P_total ~0.75)" | Combustion's check: a light in a slug, a vapour gap, A3 after the release (§2.8) | Refuted as written (SIM/DERIVED); OI-31 for the lead |
| Purge basis theta <= 2 deg | GNC rev2 gives a 2.71 deg specific-force angle during the flow | OPEN (OI-35); CF-4 at 3 deg |
| Unpurged-start population scan, first run | Stopped after more than 600 s on the shared CPU | Re-run on a 20 000-sample subset (resolution 5e-5) |
| Interface v2.4 live values (42.85 bar, 1.0-4.3 flights per insert, 0.039 g/s, <= 7.5 MPa, 0-69 bar, 15-25 C, "valve left open", 0.28-0.29 s) | Withdrawn in the report but live in the JSON (R2-05) | Tagged SUPERSEDED or replaced in v2.4a; the block `superseded_v2p4a` lists them |''')

# ---------------------------------------------------------------- §14
ins_after('Reproduction: each script states its usage and asserts its input hashes', '''
v2.4a additions (scripts in `02-combustion/src/`; data in `02-combustion/data/v2p4a/` with `HASHES.txt`; sha256/16):

| Script | Data | Use |
|---|---|---|
| `fa1_envelope_v2p4a.py` (`a6b71cb487c9642e`) | `fa1_envelope_v2p4a.json` (`64b328150025fa1e`), `fa1_envelope_summary_v2p4a.csv` (`86d764bc80ed1dd5`), log | FA-1 envelope (§7.6) |
| `fa1_tables_v2p4a.py` (`cd4f66e9b5a5a52b`) | `fa1_tables_v2p4a.json` (`677fd9ccd297fdf4`) | Tables 7.6a and 7.6b |
| `fa1_outflow_sens_v2p4a.py` (`eb487c6139c7f72a`) | `fa1_outflow_sens_v2p4a.json` (`540a78f8b9634f76`) | R2-11 outflow sensitivity |
| `vented_mass_brackets_v2p4a.py` (`114108a9807a86d3`) | `vented_mass_brackets_v2p4a.json` (`8e8ca9329c74a01f`) | §9.1, CF-4 P5 |
| `t1t4_law_resolution_v2p4a.py` (`3701b74681de700b`) | `t1t4_law_resolution_v2p4a.json` (`05b5ae5c20e04bd8`), log | §10.4 and the T1-T4 specification v2 |
| `unpurged_start_check_v2p4a.py` (`41fad4500f472bd4`) | `unpurged_start_check_v2p4a.json` (`4c745dcfbf09aef7`), log | §2.8 (Table 2.16), §2.4 tank outlet |
| `build_cf4_v2.py` (`77151ba0c7e9712f`) | `CF-4-SPEC.md` v2.0 | §10.3 |
| `write_interface_v2p4a.py` (`bb72351d5719b99e`) | `interfaces/combustion.json` v2.4a (`@@IFACE_SHA@@`) | every v2.4 key kept |
| `build_report_v2p4a.py` | this report, from v2.4 by asserted edits | - |

Reproduction (v2.4a): each script asserts its input hashes; run with `/opt/engine-venv/bin/python -I`.''')

# ---------------------------------------------------------------- v2.4a addendum: LEAD line 181 (2), (4), (10) (coordinator after REV-GNC-3)
# data: unpurged_outcomes_v2p4a.json 18a639d61b58ce8a; cold_flow_thrust_v2p4a.json a226dfacf494cb2c / .csv e094c4be80d12f66
rep('12. **v2.4a patch (REV-COMB-2; LEAD lines 166-177).**',
    '12. **v2.4a patch (REV-COMB-2; LEAD lines 166-177; the line-181 requests (2), (4) and (10)).**')
rep('Proposal: no commit by the deadline -> no relight on that pass. The lead decides (OI-31).',
    'Proposal: no commit by the deadline -> no relight on that pass. The lead decides (OI-31). **Line 181 (2):** LO or HI is not settled by '
    'analysis (both are ends of Mechanical\'s ASSUMED wall heat-transfer bracket; CF-4 generation runs and T4 measure it), and L* does not need '
    'it: at the worst PURGE NOT RUN states an unpurged start succeeds with P = 0 under LO (no light 0.242, A3 before the release 0.046, '
    'released then A3 0.712) and under HI (no light). Combustion recommends L* = 1.3 s (§2.8, Table 2.17).')
ins_after('    - Tank outlet coverage during PURGE: covered quasi-statically', '''    - Tank outlet coverage on liquid depletion (line 181 (10)): the check already used the liquid left at the END of the PURGE flow (766.4 g minimum; 79.8-81.8 g depleted in the flow window, consistent with the 81.6 g liquid depletion), not the 73.0 g vented. Quasi-static coverage needs 13.6 mm of liquid, 78.6-82.5 g: about 9x below the minimum (§2.4).
    - **Cold-flow apparent thrust under the drogue (line 181 (4); §7.3, Table 7.3a; DERIVED).** After an undetected flame-out with Pc invalid, the open-loop pintle keeps N2O flowing. Bound (Cd <= 0.80, no line loss, isentropic equilibrium expansion to 1 atm, adiabatic; tank 283.15-289.5 K): 12.5-13.3 N with the command held at the 62.5 N start level, 35.6-37.5 N at 200 N, 117.7-119.9 N at 500 N and 181.5-206.5 N at the 4.0 mm stroke. Nominal HEM (Cd 0.70): 0.8-0.9 / 12.5-13.2 / 69.1-70.6 / 105.8-122.4 N. The cold flow alone exceeds the 37.16 N R2 threshold above about 200 N of command (bound) or 310-350 N (nominal), and heat pick-up from the hot chamber is excluded. PROPOSAL: hold the open-loop command at the start level while the drogue is attached with Pc invalid (OI-38).''')
append_line('**Configuration.** CAD v3.4.1',
            ' v2.4a addendum: LEAD line 181 (REV-GNC-3 decisions; requests (2), (4) and (10) are answered here) and line 182 (Mechanical handback: '
            'TC-02 classification, 608 bearings with C0 >= 1.80 kN, bleed valves 2 x 0.30 kg ASSUMED, the NZ-04 flexible-graphite seal treated as '
            'FAIL at a 577 C soak until a datasheet shows >= 627 C, the bay-wall clearance) are quoted for status; line 182 changes no v2.4a analysis.')
rep('whether a light inside a liquid slug survives the vapour gap behind it.',
    'whether a light inside a liquid slug survives the vapour gap behind it; which end of the wall heat-transfer bracket (LO or HI) governs '
    'the coast flashing; the cold-flow thrust of the engine, above all with a hot chamber.')
rep("Lead: the PURGE commit rule after Combustion's unpurged-start finding (OI-31);",
    "Lead: the PURGE commit rule after Combustion's unpurged-start finding (OI-31; L* = 1.3 s recommended); R2 with the cold-flow term and "
    "the command hold (OI-38);")
rep('GNC: the 500-run specific-force angle during PURGE and a slosh bound (tank outlet); the bleed-valve mass trigger (> 0.30 kg, LEAD line 175 (2)).',
    'GNC: the 500-run specific-force angle during PURGE and a slosh bound (tank outlet); the cold-flow term in the sim6 V flame-out case and '
    'the command trace there (OI-38); the re-fly at the actual mass ledger (LEAD line 181 (5) replaced the 0.30 kg trigger by >= 0.10 kg).')
append_line('11. **Nozzle joint (§6.5).**',
            ' [v2.4a: LEAD line 182 (4) treats the NZ-04 flexible-graphite seal as FAIL (577 C soak against a 450 C oxidising-service limit, '
            'as recalled) until a maker datasheet shows >= 627 C; otherwise Mechanical selects a datasheet-rated seal and re-checks the joint (OI-39).]')
rep('§2.8 the PURGE commit rule, the unpurged start (Table 2.16) and the 2.7 deg note;',
    '§2.8 the PURGE commit rule, the unpurged start (Tables 2.16 and 2.17) and the 2.7 deg note;')
rep('§7.3-7.4 the E1 and A14 closure term, A4 filtered;',
    '§7.3-7.4 the E1 and A14 closure term, A4 filtered, the cold-flow thrust under the drogue (Table 7.3a);')

# §2.4: liquid basis (line 181 (10))
ins_after('- **Verdict:** covered quasi-statically, with a large margin, IF the outlet sits on the aft bulkhead of an axial tank.',
          '- **Liquid basis (LEAD line 181 (10)).** The check uses the liquid in the tank at the END of the PURGE flow: GNC gives m_liq as '
          '[start, end] pairs and the minimum end value, 766.4 g, is the one used above. The depletion in the flow window is 79.8-81.8 g, '
          'consistent with the 81.6 g liquid depletion of line 181 (10) (8.6 g boils into the ullage; 73.0 g is the vented, vehicle-level '
          'mass). Quasi-static coverage with the outlet anywhere on the aft bulkhead needs a depth of 13.6 mm (h_c 7.9 mm plus the 5.7 mm wall '
          'drop at 6.86 deg), that is 78.6-82.5 g of liquid at 289.5-283.15 K: about 9x below the 766 g minimum (DERIVED; '
          '`tank_outlet_coverage_v2p4a` in the interface).')

# §2.8: outcome classes, LO or HI, L*
ins_after('- **Limits.** Two-convention bracket of the trade', '''
**v2.4a: outcome classes, LO or HI, and L\\* (LEAD line 181 (2))** (`src/unpurged_outcomes_v2p4a.py` `8256face5bcf7b27`, generated by `gen_unpurged_outcomes_v2p4a.py` as a verbatim copy of the parent check's code; `data/v2p4a/unpurged_outcomes_v2p4a.json` `18a639d61b58ce8a`; it reproduces the parent's P(light), P(light then gap) and P(released, then A3) to 1e-12 before it classes the starts). Line 181 (2) sets the PURGE deadline as a P_total-maximising rule: L* = 1.7 s if an unpurged start is LO (break-even against P_total ~0.75) and 1.3 s if HI (P_abort 1.0), and asks which applies.

Table 2.17. Outcome of an unpurged start (each start in exactly one class; Pc valid; A3 per §7.4; values: 2500 N/s start ramp / flow held at the lift). Population rows: mean over all PURGE NOT RUN records at 0 and 2 deg (540 each; bracket records, not probability-weighted).

| State | No light (A2, drogue held) | A3 before the release | Released, then A3 | Success |
|---|---|---|---|---|
| PURGE NOT RUN, LO worst, unlined (12.5 / 11.2 / 23.4) | 0.242 | 0.046 / 0.040 | 0.712 / 0.717 | 0 |
| PURGE NOT RUN, LO worst, lined (reference) | 0.135 | 0.046 / 0.040 | 0.819 / 0.825 | 0 |
| PURGE NOT RUN, HI worst (51.8) | 1.0 | 0 | 0 | 0 |
| PURGE NOT RUN, least, unlined and lined | 0 | 0 | 0 | 1.0 (unlined: a dip shorter than the A3 detection) |
| PURGED 2.5 s worst, unlined and lined; lined 2.2 s robust edge | 0 | 0 | 0 | 1.0 |
| Population, LO, unlined | 0.012 | 0.005 | 0.58 / 0.80 | 0.40 / 0.18 |
| Population, LO, lined | 0.003 | 0.003 | 0.52 / 0.77 | 0.47 / 0.23 |
| Population, HI, unlined | 0.771 | 0.008 | 0.22 / 0.22 | 0 / 0 |
| Population, HI, lined | 0.516 | 0.006 | 0.44 / 0.48 | 0.04 / 0 |

- **LO or HI.** Not settled, and not settleable by analysis. LO and HI are the two ends of Mechanical's wall heat-transfer bracket (segment heat cases isothermal, hw+5K and ARM_bay45C_liq24C, each at h LO and h HI) that sets how much liquid in the segment flashes during the coast. Both ends are ASSUMED; no evidence supports or excludes either. CF-4 optional generation runs and T4 measure it (§11 item 32).
- **The decision does not need it.** At the worst states an unpurged start succeeds with P = 0 under both ends: HI because it never lights, LO because every light is followed by the vapour gap and A3. GNC's LO premise (P_total ~0.75 = 1 - P_abort) counted every light as a success, which the abort model never checked. In the population, P(success) per record is bimodal (0 or 1): 0 in 82 % of the unlined and 77 % of the lined LO records, and in every HI record. The released-then-A3 hazard is present under both ends (population means 0.52-0.80 LO, 0.22-0.48 HI).
- **Recommendation (SIM/DERIVED; the lead decides, OI-31).** FSW L* = 1.3 s (the HI value): PURGE commits whenever the lead to the plain trigger is >= 1.3 s. Below 1.3 s, no unpurged relight on that pass (no purge -> no relight, as A14), unless GNC shows that holding the drogue release on unpurged starts to >= E2 + 0.22 s (gap arrival <= 0.193 s with the flow held at the lift, plus 0.022 s A3 detection) gains P. With that hold the light-gap-A3 sequence aborts with the drogue attached.
- **Hazard (evidence class SIM on ASSUMED delays + DERIVED line states).** RELEASED_THEN_A3: light, drogue release at E2 (Pc >= 3 bar abs), post-light vapour gap, A3 abort: a dead vehicle released (GNC's class, about -32 m/s at touchdown against about -22 m/s on the drogue). Per start: 0.712 (unlined) and 0.819 (lined) at the LO worst states.''')
append_line('17. Line 175 (1)-(2) (v2.4a): A1 apogee target 285 m;',
            ' [Replaced by LEAD line 181 (5): GNC re-flies at the actual ledger for any confirmed landing-mass growth >= 0.10 kg summed over all changes.]')

# §6.5: line 182 (4)
ins_after('### 6.5 Nozzle joint: hot layer, seal and hazard H19 (v2.4)',
          '\n**v2.4a status (LEAD line 182 (4)).** The flexible-graphite seal of J1 (Mechanical NZ-04) sees a 577 C soak against a 450 C '
          'oxidising-service limit (as recalled) and is treated as FAIL until a maker datasheet for the chosen grade shows an oxidising-gas '
          'limit >= 627 C; otherwise Mechanical selects a datasheet-rated seal material and re-checks the joint (OI-39). The hot-layer and '
          'leak numbers below are unchanged.')

# §7.3: cold-flow apparent thrust under the drogue
ins_after('- v2.4a: LEAD line 175 (5) replaces the time-only 0xFFFF term', '''
**v2.4a: cold-flow apparent thrust under the drogue after a flame-out (LEAD line 181 (4))** (`src/cold_flow_thrust_v2p4a.py` `b4cbf147753ecc7c`; `data/v2p4a/cold_flow_thrust_v2p4a.json` `a226dfacf494cb2c`; table for GNC `cold_flow_thrust_v2p4a.csv` `e094c4be80d12f66`). GNC's R2 releases on an accelerometer thrust >= 37.16 N; its undetected flame-out at E2 peaks at 33.0 N (29.92 N on A1_none) over 0.5 s with no cold-flow term (20.85 N inside W10 < 6 m/s). With Pc invalid the ECU runs the pintle open loop on the P_feed map (A7) and A3 is blind, so nothing closes the pintle on a flame-out: N2O keeps flowing through the injector and the nozzle at the lift the thrust command sets.

- **Bound (DERIVED).** F <= mdot_max x v_iso,eq. mdot_max: Cd 0.80 (the CF-1 / CF-3 acceptance limit, line 172 (4)) x pintle area x Dyer flux with P1 = P_tank (no line loss), saturated liquid at T_tank, downstream at 1 atm. v_iso,eq: isentropic equilibrium expansion of the tank liquid to 1 atm (CoolProp): 289.7 / 301.0 / 310.2 m/s at 283.15 / 286.7 / 289.5 K. For steady adiabatic quasi-1D flow dF = (P_e - P_a) dA_e, so the thrust is largest at P_e = P_a, and every irreversibility (injector throttling, slip, non-equilibrium, friction) raises the entropy and lowers it. The bound holds for any adiabatic flow; it does not cover heat pick-up.
- **Nominal (DERIVED on ASSUMED inputs).** Quasi-steady HEM: the Dyer injector at Cd 0.70 (0.80 variant) with the grain_q1d line loss, an adiabatic chamber at the tank-liquid enthalpy, an HEM nozzle (A_t 147.9 mm2 x 0.98, eps 2.0), choked or as a venturi, optimum-expansion thrust (the eps 2.0 exit would lie below the triple point, 0.88 bar, so the full-flowing value is not evaluated). Cross-check: at the 0.2039 mm ignition lift and the A1 state the model gives 34.8-35.0 g/s against the published 35.0 g/s.
- At low lift the bound is about 15 times the nominal. The bound credits the whole tank-to-ambient expansion as axial momentum, as if the pintle were an ideal nozzle pointed aft. In the nominal model the radial pintle spray is throttled into a chamber at 1.02-1.3 bar (lifts <= 0.5 mm), and almost all of that work is lost. Only a measurement can place the truth between the two.

Table 7.3a. Cold-flow apparent thrust with the pintle at the open-loop map lift of the command (ranges over the tank states 283.15 / 286.7 / 289.5 K, 40.0 / 43.5 / 46.5 bar; drive 16.7 mm/s, 10 ms lag).

| Open-loop command | Lift [mm] | Bound [N] | Nominal, Cd 0.70 [N] | Nominal, Cd 0.80 [N] |
|---|---|---|---|---|
| 62.5 N (start level) | 0.213-0.228 | 12.5-13.3 | 0.8-0.9 | 1.1 |
| 100 N | 0.311-0.333 | 18.2-19.3 | 2.0-2.1 | 2.9-3.3 |
| 150 N | 0.453-0.488 | 26.4-28.0 | 6.2-6.7 | 8.7-9.3 |
| 200 N | 0.611-0.662 | 35.6-37.5 | 12.5-13.2 | 16.3-17.1 |
| 250 N | 0.787-0.859 | 45.8-47.9 | 20.0-20.7 | 24.6-25.5 |
| 375 N | 1.319-1.481 | 76.5-78.2 | 41.7-42.1 | 49.3-49.9 |
| 500 N | 2.059-2.431 | 117.7-119.9 | 69.1-70.6 | 80.1-81.2 |
| Any command: pintle at the full drive rate to the 4.0 mm stroke (reached 0.24 s after E2) | 4.0 | 181.5-206.5 | 105.8-122.4 | 118.9-139.2 |

- **Window 0-0.8 s after E2.** The plant is quasi-steady, so the thrust follows the lift. Holding at the start level: <= 12.5-13.3 N over the whole window (bound). On a 2500 N/s ramp to 500 N the bound passes 37.16 N 0.065-0.070 s after E2, the nominal 0.125 s after; with the pintle at the full drive rate, 0.035-0.040 s and 0.070-0.078 s.
- **Command at which the cold flow alone reaches** the 4.16 N all-winds margin (33.0 against 37.16 N): the start level (bound), 125-130 N (nominal; 108-112 N at Cd 0.80). The 16.31 N margin inside W10 < 6 m/s: 81-88 N (bound), 221-225 N (nominal; 195-200 N). The 37.16 N threshold by itself: 198-208 N (bound), 346-348 N (nominal; 309-312 N).
- **Heat pick-up (excluded; sensitivity).** With heat added at tank pressure (the largest work per joule), v_iso rises to 355 / 402 / 483 m/s at +50 / +100 / +200 kJ/kg (A1 state). The start-level bound then rises from 13.0 to 15.3 / 17.3 / 20.8 N. It reaches 16.31 N at 66-85 kJ/kg, that is 2.8-3.7 kW at the start-level flow. The nominal at the start level stays <= 1.9 N with 200 kJ/kg; at 200 N it rises from 12.9 to 24.5 N. The thermal state of the chamber, grain and nozzle at the relight is MISSING. The hot gas in the chamber at the flame-out holds about 0.55-0.80 kJ (365.65 cm3 at 3-4.4 bar).
- **Also excluded:** N2O decomposition or re-ignition on the hot grain (then the engine is not dead); the hot-gas blowdown at the flame-out (GNC's t_off decay: add the two, do not replace one with the other); vapour in the line (it lowers the thrust: HEM vapour flux 15 450 against Dyer liquid 56 843 kg/m2s); nozzle separation (it lies between the eps 2.0 and the optimum values).
- **Consequence for R2 (DERIVED; GNC re-flies).** With the command held at the start level the dead engine stays within the inside-W10 < 6 m/s margin (13.3 N against 16.31 N) unless the heat pick-up exceeds about 2.8 kW. It does not stay within the all-winds margin (4.16 N). Above about 200 N of command (bound) or 310-350 N (nominal), the cold flow alone satisfies R2 and a dead vehicle is released. The sim6 V result "R2 holds the drogue in 1000/1000" has no cold-flow term and does not cover such commands. With the engine dead the descent does not slow, so the guidance command is expected to rise; sim6 V does not record that command.
- **PROPOSAL (for GNC R2 v2 and the lead; OI-38).** While the drogue is attached and Pc is invalid, hold the open-loop command at the start level, or cap the lift at the start-level lift, until R2 confirms; GNC adds F_cold(lift, P_tank) from the CSV, bound and nominal, to the sim6 V truth thrust and re-flies. Alternative: a ratio test of the accelerometer thrust against the open-loop expected thrust. Hypothesis: the hold keeps the dead-engine apparent thrust within the margin while a lit engine still releases (62.5 N x pcf_k 0.875 = 54.7 N; GNC's release estimate >= 48.4 N). Comparator: R2 as flown. Evidence: CF-3 with a thrust load cell at the start-level, 200 N and 500 N lifts (cold chamber); a post-burn N2O pulse at the start-level lift in the T series (hot chamber; it also shows whether the grain re-ignites). Refutation: a measured cold-flow thrust above 16.3 N at the start-level lift, or a GNC re-fly in which the hold loses P.''')

# §9: H20, B-6, B-7
rep('on CF-4 O-3 and IGN-1 evidence. The lead decides (OI-31) |',
    'on CF-4 O-3 and IGN-1 evidence. The lead decides (OI-31). Line 181 (2): worst-state P(success) 0 under LO and under HI; '
    'Combustion recommends L* = 1.3 s (Table 2.17) |')
rep('| Proposal: no relight on that pass (OI-31); the lead decides |',
    '| Proposal: no relight on that pass (OI-31); the lead decides. L* = 1.3 s recommended (line 181 (2), Table 2.17) |')
ins_after('| B-6 (v2.4a) | Unpurged relight',
          '| B-7 (v2.4a) | Undetected flame-out after E2 with Pc invalid (R2 branch, line 181 (4)) | The open-loop lift keeps N2O flowing: '
          'cold-flow thrust <= 12.5-13.3 N at the start level and, by itself, above 37.16 N beyond about 200 N of command (bound; nominal '
          '310-350 N); R2 may release a dead vehicle (§7.3, Table 7.3a; DERIVED) | None in the engine: A3 is blind without Pc | PROPOSAL: '
          'command hold at the start level while the drogue is attached; GNC re-flies R2 with the cold-flow term (OI-38) |')

# §10: test-plan amendments
ins_after('- **T1-T4:** specification v2 (§10.4): law stations x/L 0.80-0.90',
          '- **Cold-flow thrust (LEAD line 181 (4); OI-38):** CF-3 adds a thrust load cell and logs the cold-flow thrust at the start-level '
          '(about 0.22 mm), 200 N and 500 N lifts (cold chamber). The T series adds, at the end of one firing, a short N2O pulse at the '
          'start-level lift with the igniter off (hot chamber); it measures the thrust and shows whether the grain re-ignites. Safing per §10.2.')

# §11 unknowns
ins_after('30. The single-firing scatter s1 and the residual systematic term s_s',
          '31. The cold-flow thrust after a flame-out, cold and with a hot chamber, grain and nozzle (heat pick-up MISSING): CF-3 with a '
          'load cell; a post-burn N2O pulse in the T series (§10, v2.4a).\n'
          '32. Which end of the wall heat-transfer bracket (LO or HI) governs the coast flashing in the segment: CF-4 optional generation runs, T4.')

# §12 open items
rep('Decide: no relight on that pass, or a ride-through mode on evidence | Lead (GNC, Combustion) |',
    'Decide: no relight on that pass, or a ride-through mode on evidence. Line 181 (2): LO/HI not settled; worst-state P(success) 0 under '
    'both; Combustion recommends L* = 1.3 s and, below it, no unpurged relight unless a release hold on unpurged starts (>= E2 + 0.22 s) '
    'gains P (Table 2.17) | Lead (GNC, Combustion) |')
ins_after('| OI-37 | Interface configuration (R2-13)',
          '| OI-38 | Cold-flow thrust and R2 (line 181 (4)) | GNC adds F_cold(lift, P_tank) (`cold_flow_thrust_v2p4a.csv`) to the sim6 V '
          'flame-out case, records the command trace there and re-flies R2 with the command hold at the start level; CF-3 load-cell '
          'measurement; post-burn N2O pulse (T series) | GNC, lead; founders (tests); Combustion (model) |\n'
          '| OI-39 | J1 seal material (line 182 (4)) | NZ-04 flexible graphite FAIL at the 577 C soak until a datasheet shows >= 627 C; '
          'Mechanical re-checks the joint with a datasheet-rated seal; the §6.5 hot-layer inputs are unchanged | Mechanical |')

# §13 failures and superseded evidence
ins_after('| Interface v2.4 live values (42.85 bar',
          '| GNC\'s LO premise for L* (line 181 (2)): an unpurged LO start at P_total ~0.75 | Outcome classes: worst-state P(success) 0 under LO '
          'and HI (Table 2.17) | Refuted (SIM/DERIVED); L* = 1.3 s recommended |\n'
          '| sim6 V flame-out case "R2 holds the drogue in 1000/1000" | No cold-flow term; the open-loop lift keeps N2O flowing and the cold '
          'flow alone exceeds 37.16 N above about 200 N of command (bound) | Not supported for such commands (DERIVED); OI-38 |\n'
          '| First cold-flow thrust run | The heat and cross-check outputs were added before any value was used; the CSV is unchanged | '
          'Second run published |')

# §14 file index
rep('| `unpurged_start_check_v2p4a.py` (`41fad4500f472bd4`) | `unpurged_start_check_v2p4a.json` (`4c745dcfbf09aef7`), log | §2.8 (Table 2.16), §2.4 tank outlet |',
    '| `unpurged_start_check_v2p4a.py` (`41fad4500f472bd4`) | `unpurged_start_check_v2p4a.json` (`4c745dcfbf09aef7`), log | §2.8 (Table 2.16), §2.4 tank outlet |\n'
    '| `unpurged_outcomes_v2p4a.py` (`8256face5bcf7b27`), generated by `gen_unpurged_outcomes_v2p4a.py` (`394bd079a3b50f92`) | '
    '`unpurged_outcomes_v2p4a.json` (`18a639d61b58ce8a`), log | §2.8 (Table 2.17), line 181 (2) |\n'
    '| `cold_flow_thrust_v2p4a.py` (`b4cbf147753ecc7c`) | `cold_flow_thrust_v2p4a.json` (`a226dfacf494cb2c`), `cold_flow_thrust_v2p4a.csv` '
    '(`e094c4be80d12f66`), log | §7.3 (Table 7.3a), line 181 (4) |')
rep('| `write_interface_v2p4a.py` (`bb72351d5719b99e`) |', '| `write_interface_v2p4a.py` (`5c06eb0a06e09daf`) |')
append_line('**Tests (digital).** Every v2.4 script asserts its input hashes.',
            ' Line-181 addendum: the outcome-class script is a verbatim copy of the parent check\'s code and reproduces its P(light), '
            'P(light then gap) and P(released, then A3) to 1e-12, plus the parent\'s population means, before it classes the starts; the '
            'cold-flow model reproduces the published ignition-lift flow at the A1 state (34.8-35.0 g/s against 35.0 g/s) and the map lifts at '
            '4.5 MPa.')

# ---------------------------------------------------------------- v2.4a addendum: LEAD line 183 (FEA negatives; NZ-01 throat insert), status and one contradiction
append_line('**Configuration.** CAD v3.4.1',
            ' Line 183 (lead read of the max-thrust FEA tables) is also quoted for status: TC-02 DESIGN CHANGE mandatory; TC-03 (Inconel 718 seat '
            'insert) passes primary and P+Q, LCF to be shown; NZ-01 graphite throat insert MS -0.44 (thermal) accepted TEST-BASED if captured, '
            'refuted by fragment loss or a throat-area change > 2 % (see OI-40: erosion alone can exceed 2 % per A1 flight).')
ins_after('- A single A1 flight can exceed the 5 % rule:',
          '- v2.4a (LEAD line 183 (2)): the NZ-01 cracked-but-contained acceptance is refuted by "fragment loss or a throat-area change > 2 %". '
          'Erosion alone changes the throat area by 1.9 % (nominal), 8.0-8.5 % (conservative) or 8.4-13.6 % (literature) in one A1 flight, so '
          'that criterion cannot tell a crack from erosion. Combustion proposes that the post-firing inspection compare the measured bore with '
          'the erosion expected for the firing (pre/post bore, duty cycle), and count as refutation any area change > 2 % beyond that '
          'expectation, any non-axisymmetric step or any missing fragment (contradiction kept for the lead, OI-40).')
ins_after('| OI-39 | J1 seal material (line 182 (4))',
          '| OI-40 | NZ-01 acceptance criterion (line 183 (2)) | "Throat-area change > 2 %" is below the erosion expected in one A1 flight '
          '(1.9-13.6 %, §5.4); proposal: > 2 % beyond the expected erosion, a non-axisymmetric step or a missing fragment | Lead; Mechanical; '
          'founders (inspection) |')
ins_after('| First cold-flow thrust run |',
          '| Line 183 (2) refutation "throat-area change > 2 %" | Combustion\'s erosion per A1 flight: 1.9 % nominal, 8.0-8.5 % conservative, '
          '8.4-13.6 % literature (§5.4) | Contradiction kept; criterion relative to the expected erosion proposed (OI-40) |')

# ---------------------------------------------------------------- finish
iface_sha = h16(IFACE)
assert T.count('@@IFACE_SHA@@') == 2
T = T.replace('@@IFACE_SHA@@', iface_sha)
open(OUT, 'w', encoding='utf-8').write(T)
print('edits', N_EDITS[0], 'lines', T.count('\n') + 1, 'sha256/16', h16(OUT))

# stale scan (prints only hits)
PAT = [r'30 bar raw', r'raw for 5 ms', r'5 ms raw', r'E0 - 0\.05 s', r'before E1', r'delays T_fire', r'T_fire delay', r'wait >= 5', r'75\.5',
       r'15-25 C', r'pending agreement', r'250 C', r'0\.88-9\.87', r'1 kHz', r'[Pp]roposal J1', r'J1 or J2', r'line 164']
L = T.split('\n')
for pat in PAT:
    hits = [i + 1 for i, s in enumerate(L) if re.search(pat, s)]
    print(f'{pat!r}: {len(hits)} lines {hits[:40]}')
