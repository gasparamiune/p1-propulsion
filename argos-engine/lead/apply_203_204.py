# Save Electronics v2.10 and GNC rev3 handbacks to the hub; append CHANGELOG 203/204; REQUIREMENTS bullets.
import hashlib, shutil

HUB = '/home/claude/work/shared-fallback/engine'
SP = '/tmp/claude-0/-home-claude-ARGOS-H1/05bcfa66-42da-580c-a72f-ba0b32235147/scratchpad'
CL = f'{HUB}/interfaces/CHANGELOG.md'
REQ = f'{HUB}/00-requirements/REQUIREMENTS.md'


def h16(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]


assert h16(CL) == 'd19869387f220320', h16(CL)
assert h16(REQ) == '1199b94ea5682cde', h16(REQ)

ER = f'{HUB}/06-electronics/REPORT-v2.10-HANDBACK.md'
GR = f'{HUB}/01-systems-gnc/staging_v3.1/rev3/REPORT-GNC-rev3.md'
for p in (ER, GR):
    try:
        open(p)
        raise SystemExit(f'exists: {p}')
    except FileNotFoundError:
        pass
shutil.copyfile(f'{SP}/ELEC-v2.10-REPORT.extract.md', ER)
shutil.copyfile(f'{SP}/GNC-rev3.extract.md', GR)
he, hg = h16(ER), h16(GR)

lines = open(CL).read().split('\n')
if lines[-1] == '':
    lines = lines[:-1]
assert len(lines) == 202, len(lines)

l203 = (
    "2026-10-13 | lead | (decision) | On Electronics v2.10 (lines 195-201; handback saved as 06-electronics/REPORT-v2.10-HANDBACK.md "
    f"{he}, lead-extracted, outside SHA256SUMS-v2.10; SHA256SUMS-v2.10 674eef94498822dd 502/502 and archive/v2.9 5f5f9a172b41339d "
    "406/406 re-verified by the lead; SIM/DERIVED/DATASHEET, not yet reviewed). interfaces/electronics.json v3 (38bf149f368c1d4c) is the "
    "working interface, author-published and unreviewed until REV-ELEC-2. "
    "(1) OI-FA1-PC-OVERRANGE: as built, v2.10 aborts the A1 relight in 362-494 of the 896 FA-1 grid cases (grid counts, SIM), turning a "
    "fault the structure is sized to survive into a vehicle loss, and it neither keeps Pc valid nor flags over-range. Decision: the stand "
    "keeps the as-built abort. Flight, v2.11: (a) ADOPTED: a non-sticky over-range bit (PC_VALID 0 only while over range) and an "
    "above-full-scale flag in LIGHT_SPIKE and the 1 kHz log; (b) CANDIDATE: ride-through of a FA-1-length transient by lengthening the "
    "filtered 30 bar persistence, the 4.75 V IGNITION rule and the comparator RC only inside the relight light window, sized from the "
    "FA-1 envelope (time above 45 bar <= 4.45 ms bracket). (b) is adopted for flight only if the S6/S9 re-run shows every genuine "
    "over-pressure and sensor-fault case still aborts and none gains peak Pc or time above 45 bar beyond what Mechanical has accepted "
    "(MEOP 45 bar; LC-TB70 for the blocked throat). Otherwise the as-built abort stays and the FA-1 abort fraction enters GNC's relight P "
    "as a loss term. "
    "(2) 070BG port: with the ASSUMED 0.30 m sense line (period about 6 ms, SIL linear model) the port is in the T > 1 ms domain of 194 (1), "
    "at up to about 151 bar abs (FA1S) against a 141.0 bar abs proof (DATASHEET): DESIGN CHANGE. The Pc port is close-coupled so the "
    "transducer path period is <= 1 ms (then 102 bar ultimate < 141 bar proof), shown by Mechanical with geometry and period; if that cannot "
    "be met, Electronics selects a flight transducer with proof >= the spectrum value at the line period and states the resolution cost. "
    "070BG saturation, recovery and post-over-range shift stay MISSING: founder B-PC-1 over-range row on a spare unit (70-100 bar g, below "
    "the 140 bar g proof) and an inquiry to TE. "
    "(3) OI-PURGE-CAP: the ECU both-open cap is set to <= 2.55 s (Combustion basis 75.9 g <= 76 g). Electronics shows the 2.5 s scheduled "
    "flow is not truncated under the valve timing tolerances; if it would be, the lead re-opens the 76 g allowance instead. The flow-basis "
    "difference (SIL 32.0 vs Combustion 29.8 g/s, +7 %) goes to Combustion v2.4b; until CF-4/B-BLEED-1 measure it, GNC carries the purge "
    "at the higher basis (about 80 g for the 2.5 s schedule) as a sensitivity. gnc.json purge_bound wording is corrected in v3.2. "
    "(4) S12 OI-BLEED-DETECT (V1 stuck open with V2 closed: undetected on the stand, 5.05 s late in flight, 104 g): v2.11 design item, "
    "detection <= 0.5 s on stand and flight, or an FMEA residual with its vented mass given to GNC. "
    "(5) RE-02 / S13 B criteria restated per class: lit start with a valid baseline and torch confirmed -> RUN, 0 failures; BASE_HIGH -> "
    "refuse with its reason code, MV never opened; torch gate not reached -> abort with the gate reason. Electronics reports each refusal "
    "class's occurrence on the A1 relight population for GNC. "
    "(6) RE-24 accepted as test-based: B-TVC-1 measures the undetected-jam bound and GNC shows a jam at that bound does not lose a landing. "
    "RE-12 (flight extension of the A7 blank) waits for REV-ELEC-2. "
    "(7) Unpurged RELIGHT guard in the ECU ADOPTED for v2.11 (baseline 186 (1); see line 204 (2)). Start/hold lift: Combustion v2.4b "
    "defines the start-level lift, the ECU hold lift equals it, CF-3 measures at the commanded lift with the encoder recorded. gen_tables "
    "is re-run on v2.4b. 113B22 excitation (20-30 V) vs NI 9234 compliance (19 V) is TO-VERIFY; Electronics names a fallback IEPE "
    "conditioner. "
    "(8) Independent re-review REV-ELEC-2 (max) of v2.10 and of this line is launched; Electronics v2.11 (max) starts in parallel and takes "
    "the REV-ELEC-2 findings as a delta. Nothing here is physical approval | lead"
)

l204 = (
    "2026-10-13 | lead | (decision) | On GNC rev3 (line 202; staging_v3.1/rev3 MANIFEST 79c2c8cd5d10e3c4 487/487 re-verified by the "
    f"lead; handback saved as staging_v3.1/rev3/REPORT-GNC-rev3.md {hg}, lead-extracted, outside the manifest; SIM/DERIVED). "
    "(1) F1 late commit: L* = 1.3 s stays the commit rule (purging after it is never worse than no relight), but a commit lead below about "
    "2.1 s is not counted as a landing (P about 0 at 1.31 s, 0.76-0.78 at about 1.7 s, 0.99 at about 2.1 s with the nominal start; 0.64-0.72 "
    "at 2.1 s with L400). Nominal leads are >= 2.65 s in every table, so the band arises only after a gate fault (gate delay >= 3.465 s); "
    "the gate-delay tolerance replaces a gate-failure probability until canopy data exist. "
    "(2) Unpurged alternative of 186 (1), line-194 comparator P6c: with a hold >= 0.30 s on the 200 N ramp it leaves no released-then-A3 "
    "residual and gives P_total LO 0.39-0.46, HI 0-0.036, 0 at the worst states, only in the below-L* branch and only with Pc valid. NOT "
    "ADOPTED: the gain is confined to a fault branch of unquantified probability and would add a flight-software and ECU path (the ECU "
    "guard of line 203 (7) excludes it). Revisit if the gate-failure probability is shown >= 1 % per flight, or if CF-4/T4 settle the "
    "unpurged start as LO and Combustion's per-record classes confirm the 0 residual. "
    "(3) Mass and apogee (F4/F5): the v3.5-class landing mass re-exhausts propellant at 285 m. With the R3-17 dip onset on both arms, no "
    "significant loss remains only at 245 m (v35a, ASSUMED 0.30 kg valves) or <= 255-265 m (v35t, 0.15 kg valve target). The A1 apogee "
    "target is decided on the v3.5.1 ledger (0.20 kg hardware allowance, real valve mass, outlet geometry) by the rule: highest 5 m band "
    "with no significant pooled loss against the v3d reference, dip onset on both arms. Planning value for the other teams: 250 m "
    "PROVISIONAL. Gaspar is told at the decision that his 300 m default would drop to about 250 m unless mass comes down; Mechanical's "
    "ranked reduction list is the lever. "
    "(4) Recorded as found: F6 285 m coverage (e19|G73|L400 loses); F7 R2 v2 flame-out side (W10 margin +5.30 N, all winds -2.29 N in "
    "4/2072, hold load-bearing); F8 RG-16 (A1 non-comp 4.015 % FAIL, AR(1) vibration fails everywhere: FC_THRUST stays NOT armed on A1, "
    "B1 arming waits for a measured IMU spectrum); F9 late UNPRIMED flip loses (line 161 'UNKNOWN = UNPRIMED from the start' stands, "
    "T_fire re-plan stays a research proposal); F10 sim start level 100 N vs 62.5 N is an open model item; F11 285 m duty records are "
    "records, not sizing (A1_none p99 8.375 s > 8.258 s A1 cycle noted to Mechanical and Combustion; B1 still governs). Old values "
    "(0.22/0.25 s holds, 60 g residual, 62.5 N x pcf_k) are SUPERSEDED evidence. "
    "(5) The 11 v3.2 proposals wait for the independent check REV-GNC-5 (max) of staging rev3, launched now. "
    "(6) GNC rev4: 188 (7) ENG-11 loop robustness over K 3133-7406 N m/rad now; the P2 re-fly on massprops v3.5.1 when Mechanical "
    "freezes; P4c on Combustion v2.4b; P7 before the SIL/HIL freeze. Nothing here is physical approval | lead"
)

lines += [l203, l204]
open(CL, 'w').write('\n'.join(lines) + '\n')

req = open(REQ).read()
if not req.endswith('\n'):
    req += '\n'
req += (
    "- Electronics v2.10 decisions (CHANGELOG 203): Pc over-range bit non-sticky and an above-full-scale log flag; FA-1 ride-through in "
    "flight only if S6/S9 show genuine over-pressure still aborts (stand keeps the abort); Pc port close-coupled (transducer path period "
    "<= 1 ms) or a flight transducer with proof >= the spectrum value at its period; ECU purge both-open cap <= 2.55 s; bleed V1-stuck "
    "detection <= 0.5 s or FMEA residual; ECU refuses an unpurged RELIGHT.\n"
    "- GNC rev3 decisions (CHANGELOG 204): L* = 1.3 s commit rule unchanged, commit leads below ~2.1 s not counted as landings; unpurged "
    "relight alternative NOT ADOPTED; A1 apogee target set on the v3.5.1 ledger by the no-significant-loss rule (planning value 250 m "
    "PROVISIONAL); FC_THRUST not armed on A1.\n"
)
open(REQ, 'w').write(req)
print('ER', he, 'GR', hg, 'CL', len(lines), h16(CL), 'REQ', h16(REQ))
