# GNC rev2 (RG-01 re-fly + amendments a/b/c) - PROGRESS (append-only)

## 0. Orientation (2026-10-13 ~11:00Z)
- Read CHANGELOG 111-164 (lead 111,113,126,142,154,156,160,161,164; comb 155,159,163; mech 162; gnc 157,158) and rev1 report s1, 2.1-2.3, 2.12, RG-01/RG-15.
- Combustion RG-01 file /home/claude/work/combustion/data/v2/v2p4/rg01_line_states_v2p4.json 2939549811d4c381:
  part2_line_states_for_gnc.v[state] = {P_abort_W0p65, E0_E2_all_s, E0_E2_given_light_quantiles_5pct_s (21), seq}; truncated_purge_worst_by_Tp (P_abort vs flow Tp, lin0.0/lin1.0, no quantiles).
  liquid 0 / max .499; purged unlined worst 0 / .626 (8.15 cm3); least 0 / .573 (4.77); Tp1.9 edge 0 / .730 (14.88); NOT RUN LO .242 / q to .628; HI 1.000 (no q); bleed_fault = purged worst + 31.2 g/s additive from E0.
  Truncated unlined P_abort: Tp1.7 .2405, 1.8 .0977, >=1.9 0.
- rg01 liquid table differs from the v2.8 base liquid table (RC03 relight_latency_sup_v2p4 f0ea1eb9905919ce) by max 9.1 ms (q0), <=0.2 ms elsewhere -> re-fly the liquid reference with the rg01 table.
- Dev tree: /home/claude/work/space/gnc_dev29 = copy of gnc_dev28 (all sim files hash-identical to rev1 sim, sim6 f9094b63e64f2324). Outputs go to /home/claude/work/space/out/rev2/.
- Run cost ~70 s per 500-run arm per process (rev1 logs).
- sim6 relight: phase 3 trigger go_ with lag = t_ign_est + t_rise (const accel extrapolation); amendment P purge = trigger re-evaluated with lag + prg_T + prg_lead (const accel) -> P30 spurious starts at drogue deployment. Lift (=E0 in sim) = relight command; light at E0 + t_ign (E2 at light).

## 0b. Coordinator inputs (REV-ELEC-1 / lead CHANGELOG l.166), received mid-task
- v3.1 fixes: relight_conditions drogue text -> adopted predicate (l.161: RUN AND b4 AND [(Pc valid AND >= 300 kPa abs) OR b7 filtered], latched); purge_bound 14.5 g -> <= 76 g per purge (Comb <= 73.0 g at 2.5 s).
- Fly/handle: E1 = 2oo2 torch AND [closure confirmed OR deadline <= torch gate] (in flight lift proceeds + BLEED_FAULT): in sim the flow ends E0-0.05 so E1 never delayed; BLEED_FAULT arm = purged-worst delays + 31.2 g/s additive from E0.
  P0 high offset keeps measured P0 -> E2 (relative rise) unchanged; the absolute 3.0 bar branch then fires at true 3.0 - offset (2.29 bar at +0.71): fly as a plateau-bracket arm (rel_Pc 2.29e5 + L400).
  NOT_VENTED = flag (no sim change). Both case TCs lost -> relight refused, drogue held (FMEA failure state, P=0). ECU reset -> SAFE, drogue held (FMEA). l.166 (5) second re-zero must END before the PURGE command: report gate-open-to-commit interval as the window.
- Dev: sim6/run6 v2.9-dev in gnc_dev29 with amendments G (pgg_*), K (kfz_on), V (pcf_*) coded; smoke test running (log logs/r2_smoke1.log).

## 0c. REV-GNC-2 (CONDICIONADO, reviews/REVIEW-GNC-R1.md a5c6b147c830b67e) + lead l.168 -> re-plan (coordinator, in order)
1 N1: ONE flight FSW for every RG-01 base/arm (A1_none + A1J_pc): FSW-R2 = stored v2.8 base + decided rule (rel_mode 1, rel_to 0.10) + flown mass estimator tot_cal_comp (m2_mass_est_v2.run_cfg_case, mest_mode 1, kest_comp 1) + fct_comp 1 + purge booked. Continuity: liq/none on FSW-R2 vs stored rel1 tables (paired).
2 N4: pin all inputs (iface pin, actuator_rate_check_v2, sim data/, Comb purge_table_v2p4 + burn_limit_proxy_v2p4, Mech coil_o3b_v34_v1; hub copies), run6 FAILS on GNC_IFACE fallback + asserts version; electronics.json v2 breaks build (KeyError dynamics_for_GNC) -> keep v1 pin for TVC dynamics, state dependency (N5).
3 Purge at ECU cap: 2.5 s flow, <= 73.0 g (G73 = 29.2 g/s) primary; G76/PS10 bounds; reserve tail per draw (runs 14, 108); +0.60 kg; size A1 apogee trim removing new exhaustions (>= 275 m auto-adopted, lower -> lead).
4 RG-16 terms at ~31 g/s path both sides (miss side with ~45 g booking residual; Comb vented-mass table pending). FC_THRUST not armed on A1 until it passes. Budget form (3 sigma RSS random + sum bias bounds) ADOPTED.
5 Restated predicate l.168: RELEASE iff RUN AND b4 AND [(Pc valid AND >= 300 kPa) OR b7 OR (0xFFFF AND t >= t_E2+0.10)], latched; late invalidity releases on first invalid frame; b7 valid filtered only; BLEED_FAULT FC action LOG-ONLY. Fly ECU changes (E1 rule, case TC, NOT_VENTED).
- Text fixes for v3.1 report: withdraw igniter Unknowns row + RG-12 drift note; s2.8 W1p_tot flown WITH limit action; s2.10 bounds per arm 0/200 = 1.49 %; list bit-check parts run; start_transient L400_te t_ign_est 1.11 s.
- Amendments a/b/c (+ flame-out under Pc invalid; flag-in-loop late flip RG-08) AFTER the re-fly; if context tight hand back RG-01 first, list these open.

## 0d. Coordinator: Combustion v2.4 published (pin from hub) + l.170 (25 bar Pc cap stays, no arm change) - 2026-10-13 ~11:40Z
- New pinned GNC_IFACE /home/claude/work/space/iface_v3d: combustion.json = hub v2.4 469727032124329f; mechanical v2 4f024ed4ccb4618c and ENGINE-BASELINE 508faa652ccbd539 = hub; electronics.json = v1 pin 42fe12e15baa6e3e (hub v2 da067408c1594814 has no dynamics_for_GNC -> N5 dependency); throttle_map_v2.csv 4f2e6d846f7253da, actuator_rate_check_v2.json 2e1341e06b9e3968.
- Pin list gnc_dev29/data/pins/pins_rev2.sha256 (16 files, full sha256): iface set + tvc_supply_budget_v1 (hub 06-electronics copy, 3ee9d60ad039ed45) + Comb hub v2p4 tables (rg01 2939549811d4c381, purge_duration 1ff6bfcd7d2f454c, purge_table 79880ab51139ff99, purge_vented_mass 0038561f71a51502, late_light_spike 57fce738164fd571, late_light_tables 7baa4f6fa76bfdd3; all = HASHES.txt) + burn_limit_proxy bc95a09b083e45ae + drogue_hold_check 70820e0038be39a7 + Mech coil_o3b_v34_v1 1c45d4ed2485d25e.
- run6 v2.9-dev strict mode: unreadable GNC_IFACE file -> RuntimeError (no snapshot fallback); pinned sha256 checked; versions asserted (combustion v2.4, electronics v1, mechanical v2).
- v2.4 rewrote igniter.sequence (only key change the sim could see): run6/engine_v2 do not read it; m2_meco_mc.nc_sequence() crashed on a None step -> made tolerant, NCS flagged 'NOT the v2.3 meaning' (unused by the re-fly; legacy NCS arms not re-run).
- Re-fly driver smoke OK (7 arms x 3 runs). Full re-fly launched 2 procs (logs/r2_refly_mc_{0,1}.log), 58 jobs x 500 runs.
- Added arm nrLO|G73z: PURGE NOT RUN LO flown with the decided sequence + booking but zero flow (FC commanded, valve failed); nrLO|none kept.
- +0.60 kg mass risk placed at ledger P07 'fixed TVC module' z 0.158 m (DESIGN placement).

## 1. RG-01 re-fly (task 1) - main set DONE 2026-10-13 ~12:55Z (late arms pending: trim, amendment a/c)
- Ran: m2_rg01_refly v1.0 mc (58 jobs x 500 runs, seed 101, 2 procs), eval v1.1 -> out/rev2/rg01_refly/rg01_refly.json 2f0672ee793895e7 (+ rf_<base>_<arm>.csv).
- FSW-R2 on every arm (stored v2.8 base + flown estimator tot_cal_comp + rel_mode 1 rel_to 0.10 + fct_comp 1); purge G73 = decided sequence, 29.2 g/s x 2.5 s cap = 73.0 g (flown 69.7-73.0 g); comb hub v2.4 pinned, strict mode.
- Continuity (N1): liq|none FSW-R2 vs stored v2.8 rel1: A1_none 0.990->0.994 (-1/+3 p .625), A1J_pc 0.984->0.982 (-2/+1 p 1) = immaterial.
- P|lit (A1_none / A1J_pc; P_abort 0 for liq/pw/pl/e19): liq|none .994/.982; liq|G73 .986/.980; pw|G73 .986/.984; pl|G73 .990/.982; e19|G73 .990/.986. Pooled main2 vs liq|none: pw -7/+4 p .549; pl -3/+1; e19 -5/+5; liq|G73 -9/+4 p .267 (all4 -21/+7 p .0125 LOSES = purge-mass cost on the liquid line).
- Exhausted: liq|none 0; liq|G73 2 per base (runs 14, 108; usable -0.6/-0.03 g); pw|G73 A1_none 1 (run 14 -0.9 g), A1J_pc 0 (run14 +4.3, run108 +9.2 g); G76 3/2; PS10 2/2. m60: liq|none 2 (14,108), liq|G73 6/7, pw|G73 6/7 -> trim arms next.
- Failure states: nrLO P|lit .986/.980 (none) or .994/.986 (sequence flown, no flow), P_abort .242 -> P_total ~.75; nrHI P_total 0; BLEED_FAULT bf|G73 .924/.920 (32 exhausted each; -70/+4 p 1e-16 vs liq|none).
- Plateau bracket: L400 pw .982/.974 (no loss vs liq|G73|L400); L400o (P0 +0.71 bar) pw .976/.970; e19|G73|L400 .944/.950 LOSES (-39/+3 p 6e-9): Tp1.9 edge + 0.4 s plateau exceeds the 0.81 s plan (evidence; e19 only reachable with a late commit).
- Plan 0.81 s: max E0->E2 | light liq .499 (margin .311), pw .626 (.184), pl .573 (.237), e19 .730 (.080), nrLO .628 (.182). Prep path (liqP/pwP, plan 1.41 s): .982/.978, .988/.974 (no loss vs liq|G73).
- Sequence G (decided): commit src 1 in 500/500, commit h 88.8-129.6 m, E0 h p50 44.7 min 34.7 m, gate open 224-240 m, gate-open->commit >= 4.0 s (p01), spurious 0, |az_f| p99 1.21 m/s2. Plain trigger fired before T_fire in 161/166 runs -> T_fire delay vs plain p50 .02-.03 s max .127 s, height cost p50 .5 m max 3.0 m; 1.9 s floor never bound (flow >= 2.387 s). Tilt in PURGE p99 5.2-5.3 max 6.9 deg; rate p99 12-13 dps.
- Next: late arms (apogee trim liq/pw h290/h280 (+m60), amendment a ant0/hf, amendment c pcfR0-3 + fo), B1 m60 + blf31 running, bit-check v29 running.

## 5. Mass sensitivity +0.60 kg (task 5) - DONE (A1 in the re-fly; B1 here) 2026-10-13 ~13:10Z
- Ran: m2_b1_m60 v1.0 (B1 62 m W1p FSW-R2, 500 runs paired; mass at P07 z 0.158 m) -> out/rev2/b1_m60/b1_m60.json 04a76593abd9f698.
- B1: ref P .988 [.974,.995]; +0.60 kg .990 (-2/+3 p 1.0); usable reserve shift p50 -10.7 g (p01 -28.0, min -39.2); reserve p01 215 -> 194 g, min 110 -> 101 g; 0 exhausted; apex p50 62.78 -> 62.72 m (p99 68.6 -> 67.5).
- A1 (rg01_refly, pooled main2): liq|none|m60 .992/.980 with 2 exhausted per base (runs 14, 108) = NEW exhaustions without any purge; liq|G73|m60 .980/.980 (6/7 exhausted); pw|G73|m60 .984/.978 (6/7 exhausted); vs liq|none|m60 -11/+5 p .21 and -11/+6 p .33 (no McNemar loss, but the tail exhausts) -> apogee trim arms running.
- B1 stuck-open bleed 31.24 g/s from first ignition (blf31, FMEA / RG-16 bound): P .368 [.327,.411], 315/500 exhausted, bled 379-569 g (p50 483 g).

## 0e. Coordinator: REV-COMB-2 outcomes, lead line 172 (received ~13:20Z)
- RG-16 miss side: fly the vented table as published (done, conservative); report separately if the miss side fails only because of the barrier-element minimum records -> it does NOT: the purge term is 0.35 pp of the 4.45 % (comp) total; without any purge term the single-frame form is still 4.10 % > 2.99 %.
- B1 on the DEFAULT grain gate (lead rule OR a_meas >= 1.25): b1_m60 v1.1 eval -> 364/500 kept (72.8 %): ref .989, +0.60 kg .989 (-2/+2 p 1), blf31 .332 (243 exhausted).
- B1 O/F per phase export: m2_b1_of_phases v1.0 -> out/rev2/b1_of/b1_of_phases.json 2b92abbccbc80679, .csv 6a624065305a23aa (9 records: gnc.json v3 85 m x5 + v3.1 staging 62 m x4, hashes match listings). Mass-weighted O/F: ascent 9.8-10.1, apex/floor 5.0-5.3, descent 4.8-5.1, landing 8.3-9.3, terminal 5.3-5.9; instantaneous min 2.06 (start transient samples).

## 4. RG-16 on the decided purge path (coordinator item 4) - DONE (budget form result = FAIL on the miss side)
- Ran: m2_rg16_fct_terms_v2 v2.0 fct (18 cases x 200 runs) + v2.1 eval -> out/rev2/rg16_v2/rg16_fct_terms_v2.json 2ae2a6eedd90249a.
- Terms: booking bound 31.24 g/s x 2.5 s = 78.1 g - vented min 34.3 g = 43.8 g (FSW-R2 books 73.0 g: 38.7 g); flown -45 g (coordinator bound); not booked +73.0 g; bleed A1 +161.6 g, B1 +568.8 g (31.24 g/s); m_FC_min 12.87 kg.
- Realised MC (A1 decided path, 1000 stuck onsets each): miss side -45 g: 670 N misses 0/1000 in H_cal, H_cal_comp, Llo_re; 1/1000 in Llo_cmd_pbk (comparator 0/1000); 0 pre-onset alarms everywhere; held max 574.2-592.9 N (margin >= 57.1 N); bleed A1 581.8 N (margin 68.2); B1 bleed 589.1 N, 670 N miss 1/1000 (H_cal), 0/1000 with comp.
- ADOPTED budget form (3 sigma RSS random + sum bias), miss side allowed 2.99 %: single-frame random -> H_cal 5.27 %, H_cal_comp (flown, fct_comp 1) 4.45 % = FAIL; form B (per-flight random only, frame noise left to the 3-frame hold) -> H_cal 3.71 % FAIL, H_cal_comp 2.49 % PASS. Over-read side passes in every form (worst estimate 585.1-589.8 N < 650 N).
- Consequence: FC_THRUST stays NOT armed on A1 at this path (lead rule); the random-term definition is a lead decision.

## 2. Amendment (a) purge trigger gate / late commit (task 2) - MC DONE 2026-10-13 ~13:50Z (eval pending)
- Arms on state e19 (Tp1.9 robust-edge delay table, conservative for a flow cut to 1.9 s), A1_none / A1J_pc, seed 101, 500 runs:
  ant0 (commit at the plain trigger, T_fire delayed to t_go + 2.30 s) P .000/.000; height floor hf100 .992/.986; hf90 .946/.932;
  hf80 .446/.458; hf70 .018/.022 (hf60 not flown: monotone, hf70 already fails).
- Bit-check G2 (1 ms nominal, late commit): T_fire delay 2.30 s -> height cost 42.8 m, E0 at 0.10 m, fails (expected).
- Reading: the "delay T_fire" rule is safe only for commits at >= ~100 m (>= ~2.3 s ahead of the plain trigger). PROPOSAL:
  below that floor, skip the purge (PURGE NOT RUN state, P_total ~.75) instead of delaying T_fire (P ~0). Lead decision.
## 3. Amendment (c) Pc invalid inside [E2, release] (task 4) - MC DONE except pcf_k 0.875 sensitivity (queued, chain4)
- pw|G73, Pc invalid from E2 (pcf_dt 0), A1_none / A1J_pc (baseline pw|G73 .986/.984):
  R0 no release .392/.396; R1 interim (= 0xFFFF branch of the adopted predicate) .990/.986; R2 accelerometer-gated .990/.984
  (1 exhausted); R3 hold+abort .000/.000 (all abort); flame-out undetected: R1fo .000/.000, R2fo .000/.000, R3fo .000/.000.
  Release vs hold counts and touchdown speeds -> eval (pc_invalid block).
## Apogee trim (lead l.168 (4)) - partial
- liq|G73 exhausted (A1_none/A1J_pc): nominal 2/2, h290 1/0, h280 0/0; pw|G73: nominal 1/0, h290 0/0, h280 0/0.
- +0.60 kg: liq|G73|m60 6/7 -> h290 5/5 -> h280 3/4; pw|G73|m60 6/7 -> h290 5/4 -> h280 3/3. Queued (chain3): m60|h275, h285.
## Bit-check v29 run 2 (G, N; tool v1.1 + code hashes) - running; G1-G5 PASS; G6 P30 arm reproduced (6 starts > 200 m;
  gate-off CA h3.5 reproduces the identical start-height distribution, 6 spurious flagged).
## Amendment (b) K re-fly (task 3) - fault arms DONE 2026-10-13 ~14:20Z; MV PCL arms running (chain1)
- m2_kfz_fault_f v1.0 (50 Pc-lost arms, 8000 runs, K on, paired with stored K-off out/fault_f): totals det arms 6000 runs:
  detected 5960 -> 5918, fault onsets 5960 -> 5946, false 0 -> 0, McNemar -28/+0.
  A1 (asc, land; 20 arms): identical detections and P (0 change).
  B1: asc Lhi_blind P .095 -> .025 (-14/+0) both levels; asc MISS .110 -> .030 (-8/+0); asc GEO .110 -> .000 (-11/+0), false
  geofence 0 -> 11; floor GEO false 0 -> 26; land Lhi_blind detected 200 -> 179 (onsets 200 -> 194); land GEO false 0 -> 82.
- Mechanism (checked in the tables): the stored Pc-lost arms lose Pc FROM THE PAD (mest_pcl_t 0, open-loop Cd factor from t 0).
  With K on, kz_Fp never gets a valid sample -> the B apex predictor uses Fcmd; at the high Cd end (x1.143) the hop overshoots:
  B1land Lhi_blind h_max p50 64.5 -> 81.3 m, max 67.5 -> 111.1 m; geofence (h_target + 15 m) trips before the fault onset.
  K off used the truth-implied F/tsc (not available to the FSW with Pc lost) -> rev1 B1 Pc-lost results were optimistic (RG-18).
- H-K REFUTED on B1 for the pad-loss construct; not refuted on A1. In-flight loss (open-loop factor from an onset) is not
  representable in sim6 except at the A relight (V) -> open; PROPOSAL: Pc valid as a launch-commit condition + a
  command-referenced effectiveness hold for in-flight loss (new amendment, to fly against K).
## Final late results (eval rg01_refly v1.3, 2026-10-13 ~15:00Z)
- Bit-check v29 run 2 (G, N; tool v1.1 + code hashes sim6 f90e0ba8e993ad60, run6 b054a222eff38b6e): ALL PASS. G6 P30_reproduced
  true (old P: 6 starts > 200 m; G gate-off CA h3.5 identical distribution, 6 spurious flagged; G decided: 0 > 160 m, 0 spurious).
  Combined latest per part (run1 A0 A1 K V RF + run2 G N): all PASS.
- Trim: h285 clears all nominal-mass exhaustions (liq|G73 0/0, pw|G73 0/0; reserve min 4.8/9.6 and 15.0/19.3 g; apogee p50
  289.4-289.9 m; pooled vs untrimmed liq -8/+13 p .38, pw -7/+11 p .48) -> ADOPTED h_target 285 m (rule >= 275 m). m60: 3/3
  exhausted remain at 275 m (runs 14, 108, 490) -> lead.
- Amendment K: MV PCL arms with K on LOSE: A1 pcllo -67/+0, -79/+2, -68/+0; B1 pclhi -145/+4, -154/+2, -147/+2 -> H-K refuted;
  PROPOSAL re-reference to the throttle-map thrust instead of freezing. FSW-R2 does not include K.
- Amendment c: R1 (adopted 0xFFFF term) = R2 on lit engines (pooled .988 / .987; k875 .990/.989; L400 .977/.981, R2 releases
  440-470 ms, deadline 500 ms); flame-out R1 releases dead vehicle (td p50 -32.3 m/s), R2 holds drogue (td p50 -21.8 m/s,
  Facc max 33.0 < 37.16 N); R3 0/1000 lit. RECOMMEND R2 + pcf_tmax 0.8 s (not flown).
- Late commit: hf100 no loss (delay <= 0.64 s), hf90 -51/+2 -> PROPOSAL commit >= 1.7 s before the plain trigger else no purge.
- Height cost (Combustion ask): decided path delay 0.127 s, cost p50 0.47-0.58, p99 2.87, max 3.04 m; commit >= 2.66 s ahead.
- Purge outlet inputs v1.1 (12/12 re-flight checks): tilt p99 5.2-5.3, max 6.9 deg; transverse rate p99 11.8-13.0, max 16.1
  deg/s; roll up to 35.4 deg/s; axial 0.89-1.12 g; specific-force angle to axis <= 2.65 deg (0.1 s mean).
- B1 default gate (b1_m60 v1.2 eval): 364 kept; P .989; web end >= 2.62 mm; limit acted 1/364; m60 .989 (-2/+2).
- gnc_v3.1_staging_rev2.json built (builder v1.1, refuses unfilled texts), A1 h_target 285 m recorded in flight_profile.
## 6. Staging + CHANGELOG - DONE 2026-10-13 ~13:10Z (clock of this box)
- staging_v3.1/rev2/ (280 files, 80 MB; CSV gzipped -n): MANIFEST_rev2.sha256 sha256/16 cb5d2c48e8d8fa27 (sha256sum -c OK).
  gnc_v3.1_staging_rev2.json a5564b45ed7fb463; rg01_refly.json 8a3b34a08289d5b1; rev1 MANIFEST re-verified OK (388 lines);
  interfaces/gnc.json untouched (mtime 03:24Z).
- CHANGELOG line 174 appended (gnc result) and read back after 10 s (6 fields).
- Open: RG-08 flag-in-loop late flip (not started); K re-reference amendment; pcf_tmax 0.8 s; trim at 285 m flown on liq/pw only.
