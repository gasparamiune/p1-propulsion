# Electronics v2.11 working log (not a report)
Task: coordinator relay of LEAD CHANGELOG line 203 (CHANGELOG 204 lines, 60190e33f21480b6 at start). Handback between
BEGIN ELEC-V211-HANDBACK / END ELEC-V211-HANDBACK. Hub v2.10 tree and interfaces/electronics.json are FROZEN (REV-ELEC-2 reviewing);
stage only at the end in hub 06-electronics/staging_v2.11/. CHANGELOG result line at the end (assert the count first).
Rules: tags on everything; nice; <= 2 processes; kill by PID only; new SIL results < 1 GB; compress superseded results.

## 2026-10-13 17:30 start
- v2.10 sources snapshot: firmware_v2p10_src/ (55 files, list v2p11_notes/v2p10_src_snapshot.sha256); v2.10 binaries copied to
  firmware/build/v2p10/ (sil 986f77d935ef9f8c, sil_bpc1 12fde7c8e52daa08, test_core 9baa6a63eb144e2e) for the v2.10 comparisons.
- combustion.json still v2.4a (5237d4584bad38c4): lift reconciliation and gen_tables on v2.4b PENDING.
- Scope: (1a) non-sticky over-range bit + above-FS flag (flight; stand as built); (1b) CANDIDATE ride-through in the relight light
  window, compile/config option, sized from FA-1 (time above 45 bar <= 4.45 ms), S6/S9 + harness re-run case by case vs v2.10;
  (3) cap <= 2.55 s + no truncation of the 2.5 s flow under valve tolerances; (4) V1 stuck open / V2 closed detect <= 0.5 s or FMEA
  residual with vented mass; (5) S13 B per class + class occurrence on the A1 relight population; (7) unpurged RELIGHT guard, lift
  (pending v2.4b), gen_tables (pending), fallback IEPE conditioner, stale labels (spike_chain, test_core), per-sample ADC limit;
  re-record (manifest v1.3), electronics.json v3.1 staged + self-check, CHANGELOG line.

## 2026-10-13 17:45 new scope from LEAD CHANGELOG line 205 (hub CHANGELOG 205 lines, 1e4fe2bf201f7563)
- 070BG cannot meet <= 1 ms transducer-path period on v3.5.1 head (Mechanical v351/pc: pc_line_period_v1.json 7f5d8950516d98f2,
  pc_space_v1.json b336b6abf9821b68, pc_transducer_temperature_v1.json 774519536f26c762). Free envelope above 1/8-27 NPT seat
  dia 12 x 30 mm. RESELECT flight Pc transducer: miniature seat-mounted, body within dia 12 x 30 (state thread), front dead volume
  <= 20 mm3 (<= 60 if CC-2), proof >= 112 bar abs, range covers 45 bar MEOP with 30 bar abort / 25 bar cap resolvable, operating
  >= 120 C (B1 soak 118.3 SIM) + stated margin for MISSING diaphragm gas-side transient, bandwidth + rise time, N2O/O2 compat,
  vibration rating, output vs ADC chain (or conditioning change). 1-3 candidates, DATASHEET, mass, TO-QUOTE DK-6400.
  Then rerun Pc-chain studies (over-range harness, S5/S6/S9) with the new characteristics; update B-PC-1 bench rows.
  FA-1 period domain close-coupled seat T <= 1 ms -> 93 bar yield / 102 bar ultimate. Keep 070BG as stand static-level ref if useful.
  Sense line deleted (BOM PROVISION ENG-PC-01). Seat temp SIM: A1 33.8 C at RELIGHT, soak max 83.8 C; B1 soak 118.3 C.

## 2026-10-13 18:10 line 206 (3) + results so far (hub CHANGELOG 208 lines, b7cb9beffb51a310; 207/208 = GNC review, nothing for ELEC)
- LEAD 206 (3): miniature P_mid (BL-08) / P_feed (EL-11) transducers alongside the Pc reselection; Mechanical carries 2 x 50 g ASSUMED,
  expects ~ -0.07 kg; proof >= 1.5 x tank-side MEOP seen (state basis), N2O/O2 compat, location temperature, DATASHEET mass/envelope,
  TO-QUOTE DK-6400; one family welcome.
- COORDINATOR 18:05: load 7.2 on 4 cores -> at most ONE heavy process at a time, nice 15 (GNC P2 and FEA 3D on critical path).
- calc/v2p11/pc_transducer_v3.py -> results/pc_transducer_v3.json 161982ca107d83a7: C1 Kulite XTL-190SM-2000A PREFERRED (one family
  Pc/P_feed/P_mid), C2 Kistler 4007D-100 ALTERNATE, C3 Endevco 8530B-1000 NOT FOR FLIGHT (121 C rating). INA333 G 79.7 conditioning;
  U330 47.5k/47.5k/220nF (5.225 ms), 174k/29.4k -> 32.59 bar abs +/-1.51; U570 806k, 10.50k/2.05k -> 11.08/10.07 bar abs; mass -0.074 kg.
- calc/v2p11/fa1_chain_v2p11.cpp + fa1_chain_summary.py -> results/fa1_chain_v2p11.json eea3b964e41f0afe (896 cases x 6 chains x
  4 phases): v210_line 494 / v210_noline 362 (= published v2.10); C1 chains 0 over-range, as-built 376-379 aborts (low band, ~42 %
  of the grid); ride sizing pers 15 ms, tau_w 10 ms grid (10.44 ms hw), X 15 ms after E2, T45 7 ms -> 0 aborts on all C1 chains.
- Face peaks 104-125 bar abs vs Combustion SDOF 102 bar ultimate (construct 1.1->25.1 bar step in 0.1 ms, case 743): CONTRADICTION.
- Ride-through comparator switch: no free Teensy pin / decoder output -> DESIGN: series R334 23.7k shorted by a low-leakage switch,
  long RC enable = SPI-latched D-FF (D = SPI0 MOSI, CLK = a MAX31856 CS rising edge, CLR_N = ARM_REQ) AND a 0.75 s LTC6993-1 bound.
