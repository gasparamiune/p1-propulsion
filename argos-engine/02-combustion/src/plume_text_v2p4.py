"""05-plume-cfd REPORT wording revision for RC-10, RC-11 and RC-19 (Combustion v2.4 handback, 2026-10-13). Text only, no re-run.
Applies exact, asserted substitutions to the published 05-plume-cfd/REPORT.md and writes the revised text as a .txt draft.
New numbers quoted come from existing files: thrust and Mach-disk levels (Table 8.2), the afterburn grid study (Richardson
f_ext 181.8 K, reviewer), and the v2-point stream-B bound (ownruns/c_2s_100_v2op/fig/c2s_v2op_afterburn_stats.json).
usage: python -I plume_text_v2p4.py PLUME_REPORT_MD OUT_TXT
"""
import hashlib, sys
src, out = sys.argv[1], sys.argv[2]
s = open(src).read()
EXPECT = '7ce61efce1014e9f'   # 05-plume-cfd/REPORT.md v2.1a/v2.2 as reviewed
assert hashlib.sha256(s.encode()).hexdigest()[:16] == EXPECT, 'plume report changed since the review'
R = [
("Status: digital simulation only, *Por revisar*. A simulation is a prediction, not a measurement.",
 "Status: digital simulation only, *Por revisar*. A simulation is a prediction, not a measurement. Text revision v2.2b, 2026-10-13: wording changes for review findings RC-10, RC-11 and RC-19 (`reviews/REVIEW-COMBUSTION.md`, ACCEPT WITH COMMENTS); no case was re-run."),
("- a small Mach disk at x = 2.68 De, within 0.5 % of the Lewis-Carlson correlation;",
 "- a small Mach disk at x = 2.68 De on the fine grid; the Lewis-Carlson value, 2.66 De, lies inside the CFD band 2.58-2.77 De (medium and coarse temporal bands; the coarse run at the v2 point gives +1.6 %);"),
("Thrust and mass flow are grid-converged to 0.15 % and 0.11 % and agree with 1-D theory within 1 %.",
 "All grid levels use the v1 operating point (combustion.json v1: Pc 24.99 bar, O/F 7.76). At that point thrust is grid-insensitive within +/-0.15 %, with no observed convergence: e21 = 0.254 N and e32 = 0.233 N give R = 1.09, monotone divergence, for which GCI is undefined, so 0.15 % is a 3x deviation bound and not a GCI. The mass-flow GCI is 0.11 %. Thrust agrees with 1-D theory to about 1 % (-0.98 % fine, -1.08 % coarse, -1.09 % at the v2 point). The fine level restarts from the medium state (§8), so it is not an independent level beyond about 8-10 De."),
("- adds at most 179 K at O/F 7.76;",
 "- adds 172-182 K at O/F 7.76 (temporal band 172-178 K; time-matched fine maximum 179.2 K; Richardson extrapolation of the three levels 181.8 K);"),
("- adds nothing at the v2 point (O/F 10.4, oxidiser-rich);",
 "- adds nothing at the v2 point for an equilibrium exhaust (O/F 10.4, oxidiser-rich; 0.44 K). The stream-B upper bound, which releases the c* deficit by fast chemistry, raises the plume maximum from 2705 K to 3011 K at that point (difference of maxima, +306 K; `ownruns/c_2s_100_v2op/fig/c2s_v2op_afterburn_stats.json`);"),
("| v1 point, time-matched 3.25 ms (coarse / medium / fine) | 7.76 | 174.0 / 177.3 / 179.2 | x 5.9-6.3 De, r 0.67-0.70 De, Z 0.91 (near Z_st 0.93) | GCI 1.8 % (p 0.78). Grid differences lie inside the temporal band 172-178 K, so not resolvable.",
 "| v1 point, time-matched 3.25 ms (coarse / medium / fine) | 7.76 | 174.0 / 177.3 / 179.2 | x 5.9-6.3 De, r 0.67-0.70 De, Z 0.91 (near Z_st 0.93) | GCI 1.8 % (p 0.78); Richardson f_ext 181.8 K. Grid differences lie inside the temporal band 172-178 K, so not resolvable; quoted band 172-182 K."),
("| v2 point (S230) | 10.435 | 0.44 | n/a | Oxidiser-rich exhaust (no Z_st): nothing to burn. The v1 run post-processed with v2 composition gives 0.47 K |",
 "| v2 point (S230) | 10.435 | 0.44 | n/a | Oxidiser-rich exhaust (no Z_st): nothing to burn. The v1 run post-processed with v2 composition gives 0.47 K. Stream-B upper bound (c* deficit released): plume maximum 3011 K against 2705 K |"),
("(with `_raw` versions).", "(with `_raw` versions; the `_raw` files carry no burned-in caption and are kept out of publishable image sets)."),
("- Three grid levels at the same physical time (3.25 ms) with GCI and an oscillatory 3x bound.",
 "- Three grid levels at the same physical time (3.25 ms) with GCI and an oscillatory 3x bound. The fine level started from the medium state at 3.0 ms and ran 0.25 ms (`f_2s_100/run.json`): it is at the same physical time but has no independent history beyond about 8-10 De."),
("| Thrust [N] | 500.33 | 500.56 | 500.82 | -0.12 | 0.152 (3x bound) | yes |",
 "| Thrust [N] | 500.33 | 500.56 | 500.82 | -0.12 | not a GCI: 3x deviation bound 0.152; R 1.09, monotone divergence, no observed convergence | yes |"),
("| Mach disk x [De] | 2.775 | 2.676 | 2.676 | 11.4 | ~0 (asymptotic range not shown) | no |",
 "| Mach disk x [De] | 2.775 | 2.676 | 2.676 | 11.4 (degenerate: medium and fine agree to 3e-5 De) | not quoted | no |"),
("| Axis T at 10 De [K] | 2128 | 2207 | 2222 | 2.4 | 0.19 | no |", "| Axis T at 10 De [K] | 2128 | 2207 | 2222 | 2.4 | withdrawn (fine level not independent here) | no |"),
("| Axis T at 20 De [K] | 2061 | 2072 | 2058 | osc. | 2.1 | no |", "| Axis T at 20 De [K] | 2061 | 2072 | 2058 | osc. | withdrawn (far field) | no |"),
("| Core length, Z 0.95 [De] | 13.22 | 14.35 | 14.90 | 1.06 | 4.2 | no |", "| Core length, Z 0.95 [De] | 13.22 | 14.35 | 14.90 | 1.06 | withdrawn (far field inherited from the medium run) | no |"),
("- The grid effect is not resolvable against the scatter; report 172-179 K.",
 "- The grid effect is not resolvable against the scatter. The Richardson extrapolation of the three maxima is 181.8 K; report 172-182 K."),
("4. Static-fire high-speed video: shock-diamond spacing (expect about 4 De) and luminous plume. Compare with the QUALITATIVE synthetic image, not the ARTISTIC renders.",
 "4. Static-fire high-speed video: shock-diamond spacing (expect about 4 De) and luminous plume. Compare with the QUALITATIVE synthetic image, not the ARTISTIC renders.\n"
 "5. Any further grid study (RC-10): time means over at least 3-5 ms per level, with autocorrelation-corrected errors, and GCI applied to the means; each level run from its own initial state.\n\n"
 "Ground plane (RC-19 e): floor afterburning is fuel-rich, 1300-1500 K on the axis at 17-20 De (0.33-0.39 m from the exit). The landing case with a ground plane (item 3) is therefore the priority before any thermal use of the far-field results. RC-19 (d): the floor sweep uses v1 gas (O/F 3.11, T0 2108 K) against the v2.3 floor (O/F 4.06, T0 2500 K); the v2-composition sensitivity (1322 K) is in §4."),
]
for a, b in R:
    n = s.count(a)
    assert n == 1, (n, a[:80])
    s = s.replace(a, b)
open(out, 'w').write(s)
print('ok', len(s), hashlib.sha256(s.encode()).hexdigest()[:16])
