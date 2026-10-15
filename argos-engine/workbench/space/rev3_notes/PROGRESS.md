# GNC rev2.1 / rev3 (response to REV-GNC-3 and lead CHANGELOG line 181) - PROGRESS (append-only)

Successor note: read this file top to bottom, then interfaces/CHANGELOG.md lines 174-181 and reviews/REVIEW-GNC-R2.md.
Task list = lead line 181 as relayed by the engine lead (P1 publication only; P2-P9 flights). Write only under
/home/claude/work/space/ and hub 01-systems-gnc/staging_v3.1/{rev2p1,rev3}/. Never edit staging rev1/rev2 (evidence).

## 0. Orientation (2026-10-13 ~14:25Z, clock of this box)
- Read CHANGELOG 155-181 (file 181 lines), REVIEW-GNC-R2.md (REV-GNC-3, fabfc81fa1d70327), REPORT-GNC-rev2.md (2edf0360cbc975e5),
  REQUIREMENTS amendments (00-requirements/REQUIREMENTS.md ef308e24783cba0e, now carries the l.181 amendment line).
- Verified: staging rev2 MANIFEST_rev2.sha256 cb5d2c48e8d8fa27 280/280 OK; reviewer MANIFEST_REV-GNC-3 d3bca19f1fdb1ca2 61/61 OK.
- Combustion v2.4a in the hub (02-combustion/data/v2p4a, REPORT.md v2.4a): unpurged_start_check_v2p4a.json 4c745dcfbf09aef7
  (H20, OI-31): PURGE NOT RUN LO worst -> every light (P 0.758) followed by a 23.4 cm3 vapour gap; released then A3 in 0.712
  (ramp) / 0.717 (flow held). Combustion proposes "no commit by deadline -> no relight on that pass". NOT yet decided by the
  lead (no CHANGELOG line). Relevant to P6 (L* table: add the H20 bracket as a third case) and to rev2.1 (record as pending).
- Work tree: /home/claude/work/space/gnc_dev3 = copy of gnc_dev29 (gncsim hash-identical to staged rev2 sim v2.9-dev:
  sim6 f90e0ba8e993ad60, run6 b054a222eff38b6e); data -> gnc_dev/data (symlink, shared; never modified).
  Env: gnc_dev29/scripts/m2r2_env.sh (strict mode, pins_rev2). Outputs: /home/claude/work/space/out/rev3/.
- Runtime: ~40-130 s per 500-run arm (1 process). 4 cores; another agent's make_all.py uses ~1 core. Disk: ~1.7 GB free:
  gzip tables (-n) as soon as an eval is done.

## 1. P1 rev2.1 DONE (2026-10-13 ~14:59Z)
- Staged hub 01-systems-gnc/staging_v3.1/rev2p1/ MANIFEST_rev2p1.sha256 02c554a2f0fe68fa (12 files, verified);
  gnc_v3.1_staging_rev2p1.json c2860bd89c1e5920 (builder m2_gnc_json_v31_rev2p1 v1.0, deterministic, self-check 32 hits 0 unmarked).
- CHANGELOG line 184 appended (read back, no interleaving). SendMessage "GNC rev2.1 staging ready for document check" sent to main.
- Harness REFUSED writing REPORT-*.md from this subagent (Write tool): checkpoint carried in JSON key checkpoint_rev2p1 and in the
  final handback. Same will apply to REPORT-GNC-rev3.md (carry checkpoint in rev3 JSON + handback).
## 2. Mass (coordinator, line 182 (7)) DONE as derivation
- m2_mass_v35 v1.0 -> out/rev3/mass_v35/mass_v35_vs_v3d.json ee89a8c0dff34d89: v3.5 vs v3d +1.168 kg (gimballed +0.237, fixed +0.931);
  v35t (valves 0.15 each) +0.868; v35g (gimballed+ring+P07 only) +0.341. iface_v35a (derived mechanical.json 3edda3aa...) +
  pins_rev3/pins_rev3_v35a.sha256. Closure check vs R.build ledger OK.
## 3. P2/P3 flights running: queue run_rev3_queue.sh (PID 22826 script; python child changes per step). Kill by PID only.
- Repro: A1_none liq|G73|h285 byte-identical to staged rev2 table.
- v35a at 285 m: liq|G73 P 0.940/0.942 ex 24/24; pw|G73 0.950/0.954 ex 19/19 (A1_none/A1J_pc) -> re-exhausts; options needed.
## 4. P2 flights DONE (eval rev3_fly.json aa3eb0b976f3b93d, log out/rev3/logs/rev3_fly_eval_P2.log), 2026-10-13 ~15:20Z
- Sweep +0.1..+0.45 kg at P07 (285 m): no significant pooled loss (p 0.12-1.0); exhaustions 1-3 per base from +0.1 kg; reserve
  p01 84 -> 23-30 g at +0.45 kg; W<6 -6..-12 at +0.45 kg (liq).
- v35a (+1.168 kg) LOSES liq -56/+9 (p 2e-9), pw -46/+9 (p 4e-7), ex 19-24. v35t (+0.868) LOSES liq -30/+10 (p 0.002), pw -25/+9
  (p 0.009), ex 7-12. v35g (+0.341, gimballed+ring+P07) n.s. -10/+8 (ex 2-3). -> P2opt needed for v35a and v35t.
- Tank is full (m_n2o 2.0 kg): no propellant lever; only trim (275-245 m) and landing-reserve levers (kd 0.7, ht 5 m).
## 5. Coordinator line 186 -> sim6 v2.10-dev amendment V2 in /home/claude/work/space/gnc_dev4 (copy of gnc_dev3, data symlink)
- patch_sim6_v210 / patch_run6_v210: sim6 1f92061d41db894a, run6 8719591fd6f8cafb. V2 = command hold 62.5 N (pv2_hold), 4 R2
  baseline modes (0 E0 / 1 E2 / 2 E0+drag comp / 3 E2+drag comp) with window stats (pv2_s5_*, pv2_s8_*), cold flow from the
  pinned Combustion CSV/JSON (pv2_cold 1 bound / 2 HEM, pv2_ck), release hold pv2_rh. Pin list pins_rev3/pins_rev3.sha256
  (= rev2 + cold-flow CSV/JSON).
- m2_bitcheck_v210: OFF and pv2_on-neutral bit-identical to v2.9 (173 common results + 73 record columns, 8 cases x 2);
  functional: hold trace 62.5 N, F_cold = table at Pt0 (12.5-13.35 N), release hold 0.22 s, stats mode. out/rev3/bitcheck_v210/.
- NOTE sim6 relight start level is 100 N (floor 0.2, relight_start_frac 0.2) vs the decided ignition lift 62.5 N (Combustion
  F_lift): the hold flies 62.5 N per lead 186 (2); the pre-onset start command stays 100 N in sim6 (record as a discrepancy).
## 6. Queue 2 (run_rev3_queue2.sh PID 23486, waits for queue 1): P4s stats -> r2v2 eval -> P6/P8 -> P2opt v35a -> eval v2.0
- m2_rev3_fly v2.0 (gnc_dev4): groups P4s (12 stats arms), P6 (rh220, rh250, e19 L400 ant13/17/21/25), P8 (liqF, pwF).
- Gate-failure probability for P6: DERIVED from recorded commit times (commit 2.97-7.7 s after the gate opens; nominal lead
  2.67-3.20 s) -> class fractions for an injected gate-opening delay; gate never opens -> plain-trigger commit, lead 0.
## 7. rev2.2 DONE (coordinator, REV-GNC-4 C1-C5) - 2026-10-13 ~16:05Z
- staging_v3.1/rev2p2 MANIFEST_rev2p2.sha256 db9237eeaa3a739e (8 files); gnc_v3.1_rev2p2.json 4f3209323b0e0ed4; t10 --publication
  exit 0. CHANGELOG line 191 (mine), lead PUBLISHED v3.1 at line 192. v3 archived at 01-systems-gnc/superseded/.
## 8. Lead line 194 (REV-COMB-3) folded into rev3 without restarting finished runs (~16:10-16:40Z)
- (1) E2 + 0.22 s hold WITHDRAWN: rh220/rh250 tables kept as SUPERSEDED evidence (flown on the sim's ~100 N guidance profile).
  New sim6 v2.12-dev amendment V3 (pv2_rhF: ECU command during the held release) in /home/claude/work/space/gnc_dev6 (copy of
  gnc_dev5): sim6 b0d9d8a0ded64e28, run6 a1df28f35a2576f1. m2_bitcheck_v212: part A ALL IDENTICAL vs v2.11 (200 results, 76
  record columns, 12 cases); part B v1.0 FAIL = criterion defect (guidance commands exactly 500 N on ascent and quantised
  200 N on landing records); v1.1 (6c24a695159f6ba1) ALL PASS: hold blocks 15/9-10/20 records = 0.30/0.19/0.40 s; V2 (i)
  precedence holds (0 records at 200 N with Pc invalid).
- P6c arms (m2_rev3_fly v2.2 gnc_dev6): rh300c200, rh190c500, rh400c200, rh300 (natural); P6 eval v1.1 (comparator() with the
  reviewer per-H table r3_unpurged_classes.json c162cde0363c4917).
- (2) R2 v2 lit model 62.5 N x pcf_k WITHDRAWN -> P4c NOT flown; lit side PENDING Combustion v2.4b CSV; P4s fo side stands.
  Command-hold trace: m2_rev3_hold_trace v1.0 -> out/rev3/fly/hold_trace.json 6aa0cb6acec996da (hold 0.80 s at 62.5 N;
  F_cold max 12.5-12.9 N with the hold, 71.5-75.2 N without; R2 max 17-20 N vs 50-63 N).
- (3) R3-17 dip onset: m2_rev3_reserve_dip v1.0 -> reserve_dip.json (onsets 62/69/80 g; every P2/P3 table used the 60 g
  ASSUMED residual).
## 9. Queues
- queue 3c (gnc_dev4, PIDs 32451/32452): P6b DONE (nominal start ant13 P 0.000/0.012, ant17 0.758/0.780, ant21 0.990/0.990,
  ant25 0.996/0.990) -> P6 eval v1.0 DONE (p6_late_commit.json afd7b24ff0e254ef) -> P5 latency (running 16:31Z) -> eval v2.1
  -> rg16w.
- queue 4 stopped in its wait loop; queue 4b (gnc_dev6, PIDs 4820/4822): P6c -> P2opt v35t (gnc_dev3) -> P6 eval v1.1 ->
  reserve dip -> eval v2.2.
## 10. 16:39-16:50Z
- queue 3c DONE: P5 latency (p5_latency.json c3ada252722a7a9d; A1 flown at the 300 m comparator target), eval v2.1, rg16w
  (rg16w.json f8d296ecca36f542: A1 comp 2.973 % PASS +0.012 pp, A1 non-comp 4.015 % FAIL - both reproduce the reviewer; B1
  comp 2.083 % / non-comp 2.385 % PASS on white; AR(1) at same RMS fails all; B1 9-10 % of FC segments < 0.52 s).
- P6c DONE (gnc_dev6): rh300c200 0.986/0.980, rh190c500 0.984/0.970, rh400c200 0.986/0.972, rh300 natural 0.994/0.990
  (ref nrLO|none 0.994/0.990).
- queue 4b now in P2opt v35t (gnc_dev3); then P6 eval v1.1, reserve dip, eval v2.2. queue 5 (PIDs 7160/7163/7165) waits
  for 4b, then the full m2_bitcheck_v29 v1.2 on gnc_dev6 -> out/rev3/bitcheck_v29_rev3 (scratch scratch_bit29_rev3).
- Tables gzipped (-n) in out/rev3/fly and out/rev3/p5 (all loaders read .csv.gz). Disk ~0.8 GB free.
- New: m2_rev3_hold_trace v1.0, m2_rev3_results v1.0 (builder of out/rev3/rev3_results.json), m2_rev3_stage v1.0 (hub copy +
  MANIFEST_rev3.sha256; dry run 395 files / 120 MB).
- P7 NOT RUN (needs a sim amendment, dropout length TO-DEFINE, map error band; SIL/HIL gate).
## 11. 16:50-17:20Z (close-out)
- Coordinator: lead freed disk (~1.9 GB reported; 9.1 GB free at 17:10Z); staging may proceed; 200 MB hold rule kept (built
  into m2_rev3_stage v1.2: refuses to copy if < 200 MB would remain).
- queue 4b DONE 17:02:25Z: P2opt v35t complete (liq h275 0.976/0.980, h265 0.976/0.974, h255 0.990/0.986, h245 0.984/0.982,
  kd70 0.982/0.972, ht5 0.868/0.848; pw h275 0.978/0.972, h265 0.984/0.984, h255 0.992/0.988, h245 0.986/0.986, kd70
  0.990/0.980, ht5 0.870/0.828); P6 eval v1.1 (same hash as the preview, ddcf6eb9e599a7a1), reserve dip, eval v2.2
  (missing = the 40 P4c arms only).
- 32 new rf_*.csv gzipped (-n); P6 eval, reserve dip and eval v2.2 re-run on the .gz files (logs *_gz.log): only the table
  references changed (64 / 16 / 64 path+hash entries), no value changed (compared field by field against copies).
- P3 285 m duty-cycle record DONE: m2_rev3_dc_record v1.0 (gnc_dev3) -> out/rev3/dc_record_285 (dc_record_285m.json
  27932a7e9d59b5a7): liq|G73|h285 p99 runs re-flown with the recorder, both reproduce their MC rows field by field.
  A1_none run 380: counter 8.375 s (> A1 sizing 8.258 s), thrust-on 8.52 s, 2911 N s, apex 288.2 m, liquid left 155 g;
  A1J_pc run 472: counter 8.189 s (inside), 8.33 s, 2684 N s. Staged under rev3/duty_cycles/ (published index untouched).
- m2_rev3_reserve_dip v1.1: paired re-test of the P2 options vs st|G73|h285 with the same onset on both tables (60 g column
  reproduces the eval). With 69/80 g: liq v35t h275 and kd70 lose; pw v35a h255 loses at 80 g; remaining n.s.: v35a 245 m
  (both states), v35t <= 255 m (liq) / <= 265 m (pw) (+ pw kd70). Per-arm section unchanged vs v1.0 (checked).
- queue 5 (v2.9 full suite on gnc_dev6): A0, A1, G, K, V PASS at 17:15Z; N, RF running.
- builder: v29 section reads the real keys (all_passed, parts{p: passed}, part_wall_s, code_unchanged_during_run); F11
  (duty-cycle record) and the dip-adjusted option lists added; F4 reading: bands, not thresholds (liq v35t non-monotone).
## 12. 17:08-17:13Z: DELIVERED (staged, CHANGELOG line 202)
- queue 5 DONE 17:08:00Z: m2_bitcheck_v29 v1.2 full suite on gnc_dev6 ALL PASS (A0 7.7 s, A1 119 s, G 157 s, K, V, N 27 s,
  RF 9 s; code unchanged during run; 88 inputs hashed) -> out/rev3/bitcheck_v29_rev3/bitcheck_v29.json 5c03053a5ad87605.
  Observation kept: run6 strict-mode error texts still say 'run6 v2.9-dev:' (lines 87/107/129), text only.
- builder m2_rev3_results v1.0 (62a706e465292652) -> rev3_results.json e0f6e7611fe523b5: v29 section on the real keys,
  F11 duty-cycle record, dip-adjusted option lists, P4 incoming Electronics 198 (6), proposal for the 198 (1) purge_bound
  wording (11 proposals, none applied).
- m2_rev3_stage v1.2 (881dee094f3dd820): 486 files / 160.6 MB incl. the npz streams (disk recovered) and duty_cycles/ ->
  hub 01-systems-gnc/staging_v3.1/rev3/; MANIFEST_rev3.sha256 79c2c8cd5d10e3c4 (487 entries), sha256sum -c OK; free
  9.25 GB after. NOT_STAGED_rev3.txt = only the v29 scratch.
- CHANGELOG: re-read (201 lines, last = electronics archive), appended line 202 at 17:11:57Z, read back 17:12:14Z: 202
  lines, no other writer between.
- Disk monitor stopped; no rev3 process running. Next: independent check of rev3 (not by GNC); handback to main.
