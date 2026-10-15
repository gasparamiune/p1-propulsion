# Combustion v2.4a patch - PROGRESS (restart file)
Session start 2026-10-13 (new Combustion engineer, takes over from v2.4 author).
Brief: REV-COMB-2 (e6bf189fb271e652) REVISE (targeted). LEAD decision CHANGELOG line 172.
Workdir: /home/claude/work/combustion/v2p4a/ (scripts, staging). Hub: /home/claude/work/shared-fallback/engine/
Inputs verified: REPORT.md v2.4 32e366bd78437dc0; combustion.json v2.4 469727032124329f; review e6bf189fb271e652.

## Steps
1. [x] FA-1 envelope script fa1_envelope_v2p4a.py -> data/v2p4a/fa1_envelope_v2p4a.json ; SendMessage to main
2. [ ] v2.4a text + interface patch (R2-01, 02, 05, 06, 07, 08, 09, 10)
3. [ ] T1-T4-REGRESSION-SPEC v2 (R2-04)
4. [ ] Publish: archive v2.4 -> superseded/v2p4/, REPORT v2.4a, combustion.json v2.4a, CF-4 v2, T1-T4 v2, REVISION-RESPONSE-R2.md, one CHANGELOG line

## Log
- 12:35 Read review §0/§3/§4/§5/§10, CHANGELOG 159-172, REQUIREMENTS amendments. Author model = late_light_spike_v2p4.py (constant-cv, kappa@40 kg/m3). A1 P0 = 1.071 bar.
- Probe: closed-volume UV pressure of the fast part (2.141 g N2O, 365.65 cm3, ABS 298 K) peaks at O/F 3.5-4 (89.2 bar), falls to 84.5 at O/F 3, 61 at O/F 2 -> adding O/F 3, 3.5 rows to the envelope (beyond brief) to show O/F 4 end is near the max.
- Decisions: script at /home/claude/work/combustion/src/fa1_envelope_v2p4a.py (imports author modules, hash-asserted); ig 0.30 (v2.4 FA-1 basis) + flight_latest/early-light checks; pool form fixed to rate (qA/hev)(1+1/OF) (reviewer form) with v2.4 regression check; products at A1 T_tank 286.70 K; vapour once = init gas x0.05 (reviewer reading).
- Fuel bound inputs: r_MECO 0.70 mm/s (DC-A1dispp99 grain run, mf 16.7 g/s at D 33.2 mm); kappa 1.2e-7, rho c 1.5e6, dT 350 K (soakback_v2); coast 18.67 s (CHANGELOG 106); flush tau = V/Qv (cold-flow A1 vapour 6.24 L/s); bleed vents overboard (no chamber flush).
- 13:05 STEP 1 DONE. fa1_envelope_v2p4a.py (a6b71cb487c9642e) -> hub 02-combustion/data/v2p4a/fa1_envelope_v2p4a.json 64b328150025fa1e, CSV 86d764bc80ed1dd5, log 848fbc4ec1da7e33, HASHES.txt. Regression v2.4 reproduced 1e-6 bar.
  Maxima: head 83.0/84.8 (vo rounded/sharp), 88.0 (aw sharp); aft 81.7/85.2; >45 3.65/4.45 ms; >67.5 1.00/1.30; >90 0; imp 726/757 bar.ms; F 1.70 kN (Cf1.35) / 1.77 (QS); SDOF <=3.05 kN vs rect 3.48-3.60; DLF 0.25-1 ms up to 1.20 (equiv 102 bar bracket, 89 baseline rounded); styrene basis +2-3% -> 90.1 bracket. Fuel bound: O/F not excluded <4 but P max at O/F 3.5-4.
  SendMessage to main SENT ~13:05.
- 13:20 CHANGELOG now 173 lines: line 173 = LEAD decision on my envelope (FA-1 load 90 bar abs QS head+aft all parts; parts with period 0.25-1 ms also 92 bar design / 102 bar sensitivity; 1.8 kN x 4 ms confirmed bounding; fuel datum TO-VERIFY). Fold into v2.4a (config line "to 173"). Line 172 (6) calls the block "relief_v2p4"; brief says relief_v2p4a -> use relief_v2p4a + note.
- STEP 2 prep (reductions, no re-runs): src/vented_mass_brackets_v2p4a.py -> data/v2/v2p4a/vented_mass_brackets_v2p4a.json (R2-06: open-element min = all-vapour line 8.49 t until 1.0 s; barrier min 3.17 g @0.5 s, below vapour line until 1.6 s; max 11.87/72.93 g vs liquid line 15.62/78.10). src/fa1_tables_v2p4a.py -> fa1_tables_v2p4a.json (report tables). src/fa1_outflow_sens_v2p4a.py -> fa1_outflow_sens_v2p4a.json (R2-11: At x0.963 -> peak +0.5-0.6 % tf1, +1.4-1.6 % tf3; x0.92 -> +1.1-1.3 % / +3.0-3.5 %; >45 bar +0.15-0.25 ms / +0.35-0.55 ms). Finding: 92 bar design value (89.0 x 1.03) becomes ~92.2 with the 4 % outflow form (92.9 at 8 %); 102 bracket covers.
- Segment heat reconcile: §2.7 0.83-9.0 kJ = v3.4.1 (segment_heat_v341_v2p4.json 831-9011 J); §6.4 0.88-9.87 kJ = Mechanical segment_heat_budget_v1 totals (875-9872 J) on the v3.4 route -> fix §6.4.
- E1 closure deadline value: electronics.json v2 head_end_bleed_provision.purge: "V1-first closure confirmed by P_mid, else BLEED_FAULT at E0 + 0.15 s" (<= torch gate 0.16 s).
- Order decided: T1-T4 v2 computation next (feeds §10.4 + interface), then CF-4 v2, interface v2.4a, REPORT v2.4a, REVISION-RESPONSE-R2, publish, CHANGELOG.
- 13:45 Coordinator mid-task ask (GNC rev2, LEAD line 175 (3)): two checks + commit wording. CHANGELOG now 177 lines (176 mechanical FA-1 margins; 177 lead on TC-09/J-FWD/bearings, cites Combustion SDOF 3.05 kN).
  CHECK 1 src/unpurged_start_check_v2p4a.py (41fad4500f472bd4) -> data/v2/v2p4a/unpurged_start_check_v2p4a.json 4c745dcfbf09aef7 (log 899dfa49731836ca), 27 s.
  Reproduces rg01 set (asserts 6 published P_abort). RESULT: PURGE NOT RUN LO worst [12.49,11.21,23.44]: every light (0.7576) is in slug S1 and is followed by the 23.44 cm3 vapour gap:
  arrival after E2 lift-flow median 0.094 max 0.193 s, ramp-to-200 N 0-0.091 s; gap 0.365 s (lift) / 0.139-0.156 s (ramp). A3 ratio in gap <= 0.238 (CEA c*, n 0.35-0.68) < 0.40 -> A3 trips.
  E2 (latency model) = Pc>3 bar abs -> release term true at E2 -> P(released then A3) 0.712 of starts (0.94 of lights). Lined LO worst 0.819. Population 0-2 deg: unlined LO 499/540 records light-then-gap, mean P 0.58; lined LO 0.52; HI 0.22/0.44.
  Purged states: no post-light gaps. Least state 0.74 cm3 gap: 11 ms/4 ms < A3 detection (dip only). Liquid re-admission after A3: none at 200 N; ramp-500 bound <=3.6 g upper / 0.53 g linear (vs FA-1 2.141 g).
  => provisional rule REFUTED as written (hazard outside the abort model: post-release A3 abort = GNC "dead vehicle released" class). Options: no purge -> no relight (as A14); or hold release on unpurged starts; or torch-on + A3 change (research).
  CHECK 2 (same script, part D): depth 126-133 mm at 766 g (283-289.5 K), 193-202 mm at 1170 g; surface drop at wall 2.3 mm (sf 2.71 deg), 5.7 mm (tilt 6.86); wall uncovers at 69 deg; Lubin-Springer dip h_c 7.9 mm; Ekman spin-up >= 359 s; slosh 2.92 Hz.
  Verdict: quasi-statically covered IF outlet on aft bulkhead of an axial tank; outlet position/diameter/dip tube/sump/anti-vortex/orientation/bulkhead face MISSING (tank not in CAD); slosh MISSING (sim6 lumped).
- 13:47 T1-T4 fix: DC-D -> engine_S230/DC-D-S230_ground_reg1.csv, 'run' rows; analytic stops at burn-through. Model check web 14.241 vs 14.25 mm, E 1.0664 vs 1.0607, OF 8.17 vs 8.37.
  t1t4_law_resolution_v2p4a.py d892751f3f5104e9 -> json a96c82763ab4512a (log 506e3fac161d43c9). rho_max: T1_100 1.0677 (allow 3.0 %), T1_50 1.043, T2 1.045, T3_20 1.004, T3_12p5 0.990, T4_DCD 1.042. Run-rows-only B1 same to 1e-4.
  Signature 0.85/0.10 over band: T1_100 1.014-1.072 (P_show 0.24-1.0), T3_20 1.037-1.120 (0.79-1.0), T3_12p5 1.046-1.135 (0.92-1.0). B1 O/F min 1.78, p05 2.24.
- 13:58 iface v2.4a built: write_interface_v2p4a.py bb72351d5719b99e -> v2p4a/iface/combustion.json 7d1cef9b912eef4d (2831 v2.4 keys kept, 175 added). CF-4 v2 a94211a295fe0224 (build_cf4_v2.py). T1-T4 spec v2 drafted. Next: build_report_v2p4a.py.
- 14:3x PUBLISHED v2.4a to hub (REPORT 97815f01af417804, iface 7d1cef9b912eef4d, R2 resp 9a6dfe5477d89160, CF-4 a94211a295fe0224, T1-T4 bbf0ea642453dc7a, superseded/v2p4/, data/v2p4a/HASHES.txt). CHANGELOG line NOT yet appended.
- Coordinator NEW ask (CHANGELOG line 181 items (2),(4),(10)): fold into v2.4a. Line 182 (Mechanical handback; NZ-04 flexible graphite 577 C vs 450 C -> FAIL until datasheet) quoted for status.
  ITEM 1 src/unpurged_outcomes_v2p4a.py 8256face5bcf7b27 (generated by src/gen_unpurged_outcomes_v2p4a.py from parent 41fad4500f472bd4) -> data/v2/v2p4a/unpurged_outcomes_v2p4a.json 18a639d61b58ce8a, 25 s.
    Worst LO unlined: noL 0.242, A3pre 0.046/0.040, relA3 0.712/0.717, success 0. Lined 0.135/0.046/0.819/0. HI worst noL 1.0. Population (unweighted) LO P_success 0.40/0.18 unlined, 0.47/0.23 lined (pool ramp / lift flow); relA3 0.58/0.80, 0.52/0.77; HI success 0-0.04, relA3 0.22-0.48. 77-82 % LO records P_success 0 (bimodal).
    => LO/HI not settled (ASSUMED Mechanical h bracket; CF-4 gen runs/T4). Decision independent: recommend L* = 1.3 s; below: no unpurged relight unless release hold >= E2+0.22 s on unpurged starts (GNC flies).
  ITEM 2 src/cold_flow_thrust_v2p4a.py -> data/v2/v2p4a/cold_flow_thrust_v2p4a.json (a226dfacf494cb2c) + .csv e094c4be80d12f66, 7 s.
    Bound (Cd 0.80, no line loss, isentropic eq. to 1 atm, adiabatic) at T 283.15-289.5 K: start level 62.5 N 12.5-13.3 N; 200 N 35.6-37.5; 500 N 117.7-119.9; stroke 181.5-206.5. Nominal HEM Cd0.70: 0.8-0.9 / 12.5-13.2 / 69-71 / 106-122 (Cd0.80: 1.1/16.3-17.1/80-81/119-139).
    Cmd where cold flow alone = 37.16 N: bound 198-208 N, nominal 346-348 (Cd0.8 309-312). W<6 margin 16.31 N: bound 81-88 N cmd. Heat +100 kJ/kg -> bound x1.33; 66-85 kJ/kg (2.8-3.7 kW) takes start-level bound past 16.31 N.
    Ignition-lift flow cross-check 35.0 g/s at A1 (REPORT 35.0) OK.
  ITEM 3: coverage already on end-of-flow liquid (766.4 g; window depletion 79.8-81.8 g); quasi-static coverage needs 7.9+5.7 = 13.6 mm = 79-83 g liquid.
  NEXT: interface writer (EXP + blocks) -> rebuild iface -> build_report EXPECT IFACE + addendum edits -> rebuild -> R2 response section -> republish (guard hub hashes) -> HASHES.txt -> CHANGELOG line -> handback.
- PUBLISHED ADDENDUM (line 181 (2)/(4)/(10) + line 182/183 status): hub REPORT 062e307a8d25e1ec (134 edits; builder f7aca226b3129283 now reads superseded/v2p4/REPORT.md), iface 5237d4584bad38c4 (writer 5c06eb0a06e09daf; 396 keys added), R2 resp e99595103ee17214; first v2.4a publish archived in superseded/v2p4a-first/ (HASHES 3f8279e38251ef86); data/v2p4a/HASHES.txt 16 OK (b5e951a4864badd1); src: unpurged_outcomes 8256face5bcf7b27, gen 394bd079a3b50f92, cold_flow b4cbf147753ecc7c.
  Hub-copy reproduction: cold_flow -> a226dfacf494cb2c, outcomes -> 18a639d61b58ce8a (identical).
  Line 183 (2) contradiction: NZ-01 '>2 % throat-area change' vs erosion 1.9-13.6 %/A1 flight -> OI-40.
- CHANGELOG: line 184 = GNC rev2.1 (appeared before my append); MY LINE = 185 (len 2406). Re-read check pending.
- NEXT: re-read CHANGELOG line 185; final SubagentHandback.

## v2.4b (REV-COMB-3 REVISE targeted; fold lead lines 186 + 194) -- started 2026-10-13
- Inputs verified: REVIEW-COMBUSTION-R3 a786101f28d45d6f (507 l), CHANGELOG f3dd884de680e626 (194 l), REQUIREMENTS 1199b94ea5682cde, reviewer MANIFEST a8ddc0f9854683d4 (16/16 OK; comparator only).
- Plan: (A) release_hold_v2p4b.py (R3-01: per-record classes vs hold H, 3 profiles, all 2160 PURGE NOT RUN records, latest trip + 10 ms)
  (B) fa1_spectra_v2p4b.py (R3-02/03/04: re-run of FA-1 grid storing solver-resolution histories to t_end; head/aft pressure spectra to >=50 ms; thrust spectrum to >=200 ms; impulse; resolution study 0.1/0.05/0.025/0.0125 ms on governing cases)
  (C) cold-flow start-lift conditional + CF-3 acceptance + grain_q1d start-level lit thrust history CSV at 0.2039 mm (R3-05/14)
  (D) T1-T4 v3 + CF-4 v2.1 specs (R3-06/07/08/10), budgets from S230 map
  (E) REPORT v2.4b edits (stale scan list from REV-COMB-3 §7 + R3-09), H19 IN718 lip melt; (F) iface v2.4b; (G) REVISION-RESPONSE-R3; (H) publish + data/v2p4b HASHES (2-col sha256sum); (I) CHANGELOG line.
- 16:39 (A) DONE release_hold_v2p4b.py 57be93ba115fd649 (gen 18894 B) -> release_hold_v2p4b.json a926426da0e6e436 + records CSV 59e7f44e44fbfeef. Latest trip (MC = det. sup): LO unl 0.2822/0.1775/0.7267 (ramp200/ramp500/lift); HI unl 0.1532/0.1336/0.3216; LO lined 0.2902/0.1725/0.7309; HI lined 0.2693/0.1773/0.6270. Holds (+10 ms): unlined 0.30/0.19/0.74; all 0.31/0.19/0.75.
- 16:44 (B) DONE fa1_spectra_v2p4b.py -> json 372b8078d7a90e75, P csv 55df65344f35759b, F csv 288a2294151e3760, NPZ 399bf43d1c09de24 (896/896 v2.4a reproduced). FINDING: undamped spectrum lobes in 0.1-1 ms: baseline 101.7 @0.75 ms, all-case 119.2 @0.75, 113.2 @0.4; 91.7 @0.1 ms > 90. v2.4a 89.0/'<=1.007' = sampled-max artefacts. -> contradiction to 194 (1) 93/102.
- 16:48 NEXT: dense-period spectra from NPZ (no re-run) + damping + ODE check; then run cold_flow_start_lift, start_level_lit_thrust, test_budgets, nozzle_lip_melt_in718 (written, not run).
- 17:2x (B2) DONE fa1_spectra_dense_v2p4b.py -> json 7468996959538d0f, P csv 4a4ebb65b38a9a03, F csv 072f2e0f2987fda5 (571 s). Dense: T<=0.1 head base 88.6/all 93.6 (0.095 ms); 0.1-1 head base 102.5 (0.71)/all 120.3 (0.705), aft base 98.5/all 102.5; 1-20 all 146.9 head (3.5 ms) <151 FA1S.
  Parts: TC-02 (0.272-0.385, head) base 99.5/all 111.7 (zeta .02 105.8, .05 99.8); TC-09 (aft 0.33-0.467) 91.1/94.4; TC-01/TC-04 87.0/91.6. Thrust rect bounds T<=20 ms (min ratio 1.08-1.22); exceed at 23.25 (QS whole)/25.0/27.0/29.75 ms.
  ODE check |diff| <= 4e-4 bar; coarse consistency 3.6e-5 bar; ringing 480 Hz, 1.33 kHz (0.75 ms), 2.07 kHz, 2.73 kHz (0.366 ms) = construct network modes.
  90.7 vs 89.0 decomposition: 88.98 sampled -> 90.02 continuous (0.05 ms) -> 89.86 published 0.1 ms grid -> 90.61 unclipped gauge (vapour_once start 0.054 bar) vs reviewer 90.66; 0.0125 ms 90.29.
- IN718 melting range: WebFetch read Special Metals SMC-045 (2007) Table 2: 1260-1336 C (2300-2437 F) = DATASHEET (PDF not archived; curl 403). Script updated.
- cold_flow_start_lift_v2p4b -> json 28ce48092f33da1b: factor 1.224-1.305; offset 0.048-0.070 mm; SPI/Dyer 1.511-1.524; mdot lim 52.58-56.31 g/s; heat 66.1-84.8 kJ/kg (2.84-3.66 kW).
- new script tank_outlet_dip_v2p4b.py (R3-17); test_budgets adds probe dropout + P1 lift basis.
