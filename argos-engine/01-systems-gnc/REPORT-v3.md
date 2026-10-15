GNC CHECKPOINT. Space Systems / GNC, ARGOS H1. 2026-10-13, evening.
Subject: gnc.json v3 publication; v2.8 relight with option (c) and the stale-flag rule; B1 at the 62 m cap.

1. CLAIM (everything here is simulation; nothing is physical acceptance)
C1. v2.8 relight at the planning value 0.81 s (REQ, lead decision 2026-10-13; the GNC Pc-confirm-deadline rule).
- 4 A1 bases × 3 line states, 500 runs each, paired by draw (SIM).
- P liquid / vapour U01 / full vapour:

  | Base | Liquid | Vapour U01 | Full vapour |
  |---|---|---|---|
  | A1 | 0.992 | 0.992 | 0.994 |
  | A1 + growth | 0.988 | 0.994 | 0.992 |
  | ENG-07d | 0.988 | 0.992 | 0.990 |
  | ENG-07d + growth | 0.980 | 0.988 | 0.990 |

- The withdrawn 1.41 s rule on a primed line gives 0.900–0.976.

C2. Option (c) is verified paired on the same draws: 1.37 s fault path, planned 0.81 s vs 1.41 s.

  | Base | P at 0.81 s | P at 1.41 s | Runs lost / gained |
  |---|---|---|---|
  | A1 | 0.270 | 0.992 | 0 / 361 |
  | A1 + growth | 0.360 | 0.992 | 0 / 316 |
  | ENG-07d | 0.272 | 0.992 | 0 / 360 |
  | ENG-07d + growth | 0.356 | 0.994 | 0 / 319 |

- Exact McNemar p ≤ 1.9e-95 on every base.
- Fault-path spread: start delay = line-state E0→E2 + 0.56 s prep (0.69–1.37 s); bases without growth. P liq / vapU / vapF:

  | Base | Planned 1.41 s | Planned 0.81 s |
  |---|---|---|
  | A1 | 0.990 / 0.992 / 0.994 | 0.978 / 0.872 / 0.708 |
  | ENG-07d | 0.992 / 0.992 / 0.990 | 0.978 / 0.876 / 0.714 |

C3. Cost of a wrong UNPRIMED flag (primed line planned at 1.41 s), paired:

  | Line state | Loss |
  |---|---|
  | Liquid | −0.056 to −0.080 |
  | Vapour U01 | −0.042 to −0.046 |
  | Full vapour | −0.016 to −0.020 |

- Significant (p < 0.05) everywhere except A1 + growth full vapour (p 0.057).
- Worst P over the four line states (maximin): 0.270–0.360 when planned at 0.81 s; 0.900–0.936 when planned at 1.41 s.
- Break-even prior of an unreported UNPRIMED line: q* = 0.022–0.111. Per-state 95 % intervals from a joint bootstrap span 0.003–0.146.

C4. Stale or missing flag (the decision the lead asked GNC to make):
- Flag fresh (age ≤ 0.3 s, ASSUMED): PRIMED → 0.81 s; UNPRIMED → 1.41 s.
- Flag stale or missing at T_fire: hold the last valid flag received since the MECO valve closure. If none was received, plan 0.81 s.
- The plan is evaluated every frame and latched at T_fire. A flip to UNPRIMED after the 1.41 s trigger point fires at once.
- Why this is the safer plan:
  - A stale flag is one fault. Holding PRIMED is wrong only if a second, independent fault coincides: an emptying of the segment that the ECU did not report.
  - A held UNPRIMED errs only toward the false-UNPRIMED outcome (P ≥ 0.90). The segment can re-prime only through the NC valve.
  - Maximin (1.41 s on any stale flag) pays the C3 loss on every primed flight with a stale flag in order to cover a double fault. It is preferable only if the probability of an unreported emptying exceeds q*.
- Conditions:
  - The ECU publishes UNKNOWN (P_feed invalid), or UNPRIMED whenever it will run the prep; the FC treats UNKNOWN as UNPRIMED.
  - The flag is valid only after MECO.
  - Electronics confirms the rate and the staleness limit.
  - If a seat leak can empty the segment inside the staleness limit, the maximin plan must be reconsidered.

C5. B1 at the lead's 62 m cap (REQ, provisional until T1–T4). Band a ×0.6–1.5, n 0.35–0.68, uniform × uniform (ASSUMED), plus growth 7–11 %; 500 runs.
- Nominal flight at the worst corner (a 0.6, n 0.68, growth 0.11) closes the +25 % rule with 25.8 % reserve. Every other corner caps at 62.9 m or above.
- Monte Carlo: P 0.996 [0.986, 0.999], against growth only 0.996 (−2/+2, p 1).
- 0 runs exhaust the liquid; usable liquid p01 0.188 kg (growth only 0.261 kg).
- Engine-on counter p50/p99/max 15.81/18.25/20.16 s. All 500 runs are below the four 85 m dispersed sizing cycles (21.61, 21.73, 23.93, 24.09 s). The 85 m cycles therefore cover 62 m, and the lead keeps them as the conservative thermal and erosion sizing cases.
- For comparison, at 85 m with the band: P 0.966, 12 runs exhausted, usable p01 ≈ 0.

C6. Duty-cycle index rev d adds "records": the A1 p99 cycles of the v2.8 liquid-line lights at 0.81 s.
- `DC-A1_full_flight_disp_p99_kest2_v28liq_v3`: run 101, start delay 0.490 s, counter 8.53 s, thrust-on 8.68 s.
- `..._tg711_v3`: run 360, start delay 0.343 s, counter 8.35 s, thrust-on 8.49 s.
- Both re-flown runs reproduce their Monte Carlo rows field by field, and both landed.
- Both counters exceed the A1 sizing cycle (8.26 s). They are records; B1 governs thermal and erosion (lead).

Not claimed:
- physical validity;
- an in-flight simulation of the flag logic (option (c) is flown as a fixed planning value per case);
- an FC_THRUST error budget (OPEN, not run);
- acceptance of FSW v2.7/v2.8 (independent GNC review pending).

2. CONFIGURATION
- Simulator: sim6/run6 v2.7.1-dev (start-delay quantile option t_ign_q; regression band reg_band). The sim6/run6 headers were updated (docstrings only) after the runs; the code is identical by syntax-tree comparison.
- Flight software: v2.7 PROVISIONAL (k_est_asc 2, ratchet), with the v2.8 relight trigger at t_ign_est = planning value. N2O 2.00 kg.
- Interface set iface_v3c, identical to the hub files at publication: combustion.json v2.3 (d9ec54fbf450e243), mechanical.json v2 (4f024ed4ccb4618c), electronics.json v1 (42fe12e15baa6e3e).
- Seeds: main 101; growth 20261013; band 20261017; start delay 20261018; bootstrap 20261019. 500 runs per case.
- Start-delay model: the light occurs at a delay drawn from the line state's E0→E2 table.
  - Tables built from Combustion RC-03, with Combustion's p95 and max reproduced within 3 ms. Ranges: liq 0.126–0.499 s; vapU 0.148–0.801 s; vapF 0.436–0.809 s.
  - Fault point: fixed at 1.37 s.
  - Fault spread: table + 0.56 s. The 0.56 s offset is DERIVED (1.37 − 0.81); the shape of the spread after the prep is ASSUMED.
- B1 at 62 m: J_ref of the no-band 62 m flight. Growth U(0.07, 0.11) with the ECU Pc loop. +25 % reserve rule with 3 % trapped.

3. SOURCES
- interfaces/CHANGELOG.md, lead decisions 2026-10-13:
  - v2.8 design accepted;
  - correction: planning value 0.81 s, option (c) provisional, option (a) research, B1 cap 62 m, 85 m cycles kept;
  - MV-P/FS-01 Option A with the ~44 cm³ segment (arrived after the runs).
- Electronics v2.8 sequence (CHANGELOG): flight worst case 0.81 s = torch gate 0.16 s (PROVISIONAL) + W 0.65 s; fault path 1.37 s.
- Combustion RC-03 `relight_latency_sup_v2p4.json` (f0ea1eb9905919ce). Combustion RC-07 band runs `summary_v2p4.json` (53c2f1d137f9c7cb; Combustion work area, not in the hub).
- GNC comparators: relight_181 (1.81 s late runs), throat_growth, the regband cap scan, duty cycles rev c.

4. FILES (hub, `/home/claude/work/shared-fallback/engine/`)
- `interfaces/gnc.json` v3: sha256/16 3e97c378cfebee95, 608,266 B.
- `interfaces/CHANGELOG.md`: lines 96–99 appended.
- `01-systems-gnc/sim/`:
  - `README.md` v3 (v2.5 kept as `README_v2.5.md`);
  - `gncsim/` v2.7.1-dev;
  - `scripts/`: m2_relight_v28 v1.2, m2_regband_mc v1.1, m2_gnc_json_v3 v5, m2_stage_hub_v3 v1.3, m2_changelog_1013b v2, m2_dc_a1_v28_record v1, m2_fc_thrust v1 (not run), and the others;
  - `data/`;
  - `history/gncsim_hub_v2/` and `history/scripts_hub_v2/` (the v2 versions, unchanged).
- `01-systems-gnc/results/`: 22 GNC subfolders, including
  - `relight_v28/`: relight_v28.json with the option_c block, and 68 run tables (.csv.gz);
  - `regband/`: regband_mc.json including the 62 m cases;
  - `v271_checks/`;
  - `duty_cycles_v3_checks/`.
- `01-systems-gnc/duty_cycles/`:
  - `duty_cycles_index_v3.json` rev d (4a07d68946bd0dc9);
  - `DC-A1_full_flight_disp_p99_kest2_v28liq_v3.csv` (c0aeff3ee3866562);
  - `..._v28liq_tg711_v3.csv` (4c1fdefc3495e17e);
  - `history/duty_cycles_index_v3_revb.json` (416e4c351a705d65).
- GNC work area (not in the hub): `/home/claude/work/space/` (gnc_dev, out, logs, scratch, stage_hub).

5. TESTS / VERIFICATION
- Statistics: paired exact McNemar and Wilson 95 % intervals on every case; joint bootstrap (2000 resamples) for q*.
- m2_bitcheck_v271 v2, parts A–E: passed earlier. Bit-identical with the options off; start-delay option checks E1–E4.
- Docstring patch of sim6.py and run6.py: syntax trees with docstrings removed are identical.
- Records: re-flown runs equal their Monte Carlo rows. Index diff rev c → d: all cycle files identical by sha; only 'records' and the revision changed.
- gnc.json:
  - 0 NaN, 0 'nan'/'None' strings, 0 absolute paths;
  - 81 of 81 `01-systems-gnc` references resolve in the hub;
  - 1 Combustion path cited by the lead (`02-combustion/data/v2/dc_gncv3_band/summary_v2p4.json`) is not in the hub. This is flagged in the file.
- Hub copy: 351 files byte-identical to staging. gnc.json, the index and the CHANGELOG were read back at least 10 s after writing.
- Not applicable or not done: npm test/build (no app files in my scope); an independent reviewer verdict in supervision.json (the author cannot approve).

Failures kept as evidence:
- m2_relight_v28 v1: the fault cases returned no Monte Carlo because of the nominal sizing gate. Fixed in v1.1.
- The first v3 write (6140117a56b0ddb3) rounded the option (c) p-values to 0.0. Replaced by a3031093524171d6 (p kept as 2-significant-digit text) and then by 3e97c378cfebee95 (adds the 44 cm³ open item). Only the last sha is cited.
- Staging v1.2 filed two v3 scripts as v2 history. Removed from the hub; fixed in v1.3 with an mtime cutoff.
- The first build carried a Combustion work-area absolute path. It now reads as a work-area-relative description.
- An old sweep waiter shell had a wrong exit count (expected 40 lines, the sweep writes 30) and stopped at its time limit. No work was lost.
- Electronics' firmware file `engine_ecu.cpp` changed hash between builds (they are editing it). inputs_read records the hash at build time.
- I did not use SIGSTOP; solver processes never exceeded 2.

6. UNKNOWNS
- Probability that the segment empties without being reported: no seat-leak rate and no drain time. This is the quantity q* is compared against.
- The ECU flag (rate, staleness limit, UNKNOWN state) is not in electronics.json. 0.3 s is ASSUMED.
- The ~44 cm³ MV-to-seat segment (lead, after the runs). It invalidates:
  - the 21.4 cm³ abort tail-off bracket;
  - the 1.37 s fault path, the 0.56 s prep and the RC-03 tables, which may shift.
  - Option (c)'s 1.41 s has only 0.04 s of margin over 1.37 s.
- RC-03 E0→E2 tables are SIM on ASSUMED delays. The torch gate 0.16 s is PROVISIONAL.
- The regression-law band and its distribution are ASSUMED until T1–T4.
- Only the start-delay model is flown; the flag dynamics are not simulated.
- FC_THRUST error budget: not computed.

7. NEXT CLOSURE (owner)
1. GNC: FC_THRUST (review and run m2_fc_thrust.py v1; publish the 3σ error, latency, false-abort rate, stuck-pintle detection time and a threshold proposal).
2. GNC: re-run the abort tail-off bracket and the option (c) fault and fault-spread cases once the 44 cm³ re-check and the new fault-path time are published. Re-confirm 1.41 s or propose a new value.
3. Electronics: v2.8 sequence and flag in electronics.json (PRIMED/UNPRIMED/UNKNOWN, ≥ 10 Hz, staleness limit, ECU action when P_feed is invalid); fault path on 44 cm³.
4. Electronics + Mechanical: drain time of the segment under the worst credible seat leak.
5. Combustion: band distribution; measured RC-03 latency; torch-gate confirmation; 44 cm³ inventory and purge re-check; whether the band web result at 85 m (< 1 mm at the high-a corners) is acceptable.
6. Independent GNC reviewer: FSW v2.7 k_est_asc 2, the v2.8 planning logic and the stale-flag rule (verdict in supervision.json).
7. Founders (physical): IGN-1, T1–T4 and CF data to replace the ASSUMED latency and regression distributions.
