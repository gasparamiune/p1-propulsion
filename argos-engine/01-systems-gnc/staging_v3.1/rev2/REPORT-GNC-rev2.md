# GNC rev2: RG-01 re-fly on one flight FSW; sim6 v2.9-dev amendments G, K, V

## 0. Checkpoint

**Delivered / reviewed / date:** GNC (Senior Space/GNC) / independent reviewer to be assigned / 2026-10-13. Status "Por revisar". All results are simulation (SIM); none is physical validation.

**Configuration:**
- **Simulator:** sim6/run6 v2.9-dev = rev1 amendments M, W, F, P, R, S plus G (purge sequence and trigger gate), K (freeze on Pc invalid) and V (Pc invalid inside [E2, release]).
  - Changed files: sim6.py f90e0ba8e993ad60, run6.py b054a222eff38b6e, engine_v2.py f8f6a70289cbf180, tailoff.py 7ac146f91b11bc5e.
  - Every other file is identical to rev1. The rev1 copy was not edited.
  - Every new option is off by default and bit-identical when off.
- **FSW-R2, the only flight FSW (N1):**
  - stored v2.8 base (ENG-03 rate map, k_est_asc 2);
  - flown mass estimator tot_cal_comp;
  - decided release predicate (rel_mode 1, rel_to 0.10 s);
  - fct_comp 1, with FC_THRUST not armed on A1;
  - decided purge sequence G73: PURGE committed at T_fire − 2.90 s, MV ramp 0.35 s, 2.5 s of flow (ECU cap) ending E0 − 0.05 s, 29.2 g/s, 73.0 g booked, gate plus constant-velocity commit predictor, T_fire never before 1.9 s of flow.
  - K is not part of FSW-R2.
- **Inputs:** strict mode (GNC_STRICT 1). An unreadable interface file is an error, every input is checked against the pin list (sim/pins/pins_rev2.sha256, 4c97768d53b57eef, 16 files), and versions are asserted.
  - Interfaces: combustion.json hub v2.4 469727032124329f; mechanical v2 4f024ed4ccb4618c; ENGINE-BASELINE 508faa652ccbd539; throttle_map_v2 4f2e6d846f7253da; actuator_rate_check_v2 2e1341e06b9e3968.
  - electronics.json stays on the v1 pin (42fe12e15baa6e3e): hub v2 (da067408c1594814) has no dynamics_for_GNC (N5 dependency).
  - Combustion hub v2p4 tables: rg01 2939549811d4c381, purge_vented_mass 0038561f71a51502, purge_duration 1ff6bfcd7d2f454c, purge_table 79880ab51139ff99, late_light 57fce738164fd571 / 7baa4f6fa76bfdd3, burn_limit_proxy bc95a09b083e45ae, drogue_hold_check 70820e0038be39a7.
  - Electronics: tvc_supply_budget_v1 3ee9d60ad039ed45. Mechanical: coil_o3b_v34_v1 1c45d4ed2485d25e.
- **Draws and pairing:** seed 101, 500 runs per arm. Bases A1_none and A1J_pc ("main2"), plus A1_pc and A1J_none for the core states.
  - Start delays come from the rg01 quantile tables, with the same u in every arm, so all comparisons are paired.
  - E2 is placed at the 6-DOF light.
- **Statistics:** Wilson 95 % intervals and exact McNemar. "Loses" means lower P with p < 0.05.
  - P_total = P|lit × (1 − P_abort) × (1 − p_nl), with p_nl ∈ {0, 0.5, 2, 5} %.
  - No state-weighted mean is formed, because the state probabilities are unknown.

**Claim to check:**
1. On FSW-R2 with the purge at the ECU cap, the decided purged states have P_abort 0 and P|lit 0.982–0.990, and none loses against the liquid plan.
2. The 0.81 s plan holds.
3. The only reserve failures come from the purge mass on the liquid table, and the 285 m apogee target removes them.
4. The decided sequence has no spurious purge starts (P30 fixed).
5. The K freeze and the time-only 0xFFFF term are inferior to the alternatives stated in §5 and §6.

**Verdict and permitted use:** none yet; an independent reviewer records the verdict in supervision.json (not me). Use as simulation evidence for design decisions only.

## 1. RG-01 re-fly (task 1)

### P|lit per state

Each cell gives P|lit, exhausted runs and the minimum usable reserve, for A1_none / A1J_pc / A1_pc / A1J_none. Usable reserve = liquid left − 3 % of the loaded N2O (ASSUMED residual). The last column is the pooled main2 pair against the liquid plan without a purge.

| State | A1_none | A1J_pc | A1_pc | A1J_none | Pooled vs liquid, no purge |
|---|---|---|---|---|---|
| liquid, no purge | .994 / 0 / 56.0 g | .982 / 0 / 65.8 g | .988 / 0 / 67.2 g | .986 / 0 / 55.9 g | reference |
| liquid + G73 | .986 / 2 | .980 / 2 | .976 / 2 | .980 / 2 | −9/+4, p .27. Four-base pool −21/+7, p .0125: **LOSES** |
| purged worst + G73 | .986 / 1 | .984 / 0 | .982 / 0 | .988 / 1 | −7/+4, p .55 |
| purged least + G73 | .990 / 1 | .982 / 0 | .988 / 0 | .990 / 1 | −3/+1, p .63 |
| Tp1.9 edge + G73 | .990 / 0 | .986 / 0 | .984 / 0 | .984 / 0 | −5/+5, p 1.0 |

- **Prep path (UNKNOWN = UNPRIMED, plan 1.41 s):**
  - liquid .982/.978 (2/2 exhausted): pooled −12/+4, p .077; A1_none alone −6/+0, p .031 (loses);
  - purged worst .988/.974: −11/+4, p .12;
  - against liq|G73 neither loses (−8/+5, −10/+8);
  - largest E0→E2 is 1.059 / 1.186 s, inside the 1.41 s plan.
- **P_total:** P_abort is 0 for these states (Combustion), so P_total = P|lit × (1 − p_nl). Example: purged worst A1_none 0.986 at p_nl 0, 0.937 at 5 %.

### Purge bracket (pooled main2 against the liquid plan)

| Purge | Liquid | Purged worst | Liquid exhausted (A1_none / A1J_pc) |
|---|---|---|---|
| G73 | −9/+4 | −7/+4 | 2 / 2 |
| G76 | −10/+4, p .18 | −7/+4 | 3 / 2 |
| PS10 | −6/+1, p .13 | −8/+4 | 2 / 2 |

### Reserve tail and apogee trim

- **Runs 14 and 108:** liquid without purge 56.0 / 74.8 g (A1_none). With G73: liquid −0.6 / −0.0 g; purged worst −0.9 / 10.4 g. The next lowest run is 490.
- **Trim adopted under line 168 (4):** h_target 300 → **285 m**; apogee p50 goes from 304.5–304.9 m to 289.4–289.9 m.
  - At 285 m: liq|G73 and pw|G73 have 0 exhausted runs on both bases.
  - Minimum usable reserve 4.8 / 9.6 g (liquid table) and 15.0 / 19.3 g (purged worst).
  - P .990/.986 and .990/.988; pooled against the untrimmed arms liq −8/+13 (p .38), pw −7/+11 (p .48).
  - 290 m leaves 1 exhausted run (A1_none liquid). 280 m also clears, with reserve minima 9.5–27.7 g.
  - Cost: 15 m of apogee target.
  - The target is recorded in flight_profile of the staging JSON.
- **+0.60 kg (conditional):**
  - Exhausted runs per base: liq|G73|m60 6/7 at 300 m, 5/5 at 290, 3/4 at 280, 3/3 at 275; pw|G73|m60 6/7, 5/4, 3/3, 3/3.
  - liq|none|m60 already has 2/2 exhausted with no purge.
  - Runs 14, 108 and 490 end at the residual even at 275 m.
  - **Lead decision if the mass materialises:** a trim below 275 m, or another fix (propellant load or landing reserve).

### 0.81 s plan

The plan holds. Largest E0→E2 given light, with the margin to 0.81 s:

| State | Largest E0→E2 | Margin |
|---|---|---|
| liquid | 0.499 s | 0.311 s |
| purged worst | 0.626 s | 0.184 s |
| purged least | 0.573 s | 0.237 s |
| Tp1.9 edge | 0.730 s | 0.080 s |
| PURGE NOT RUN LO | 0.628 s | 0.182 s |

- **Not covered: Tp1.9 edge plus the 0.4 s plateau.** e19|G73|L400 gives .944/.950, −39/+3: LOSES.
- That state needs the flow cut below 2.5 s. On the decided path the flow was ≥ 2.387 s in every run, so it is not reached.

### Plateau and P0 offset

- **No plateau:** the Pc branch releases in 500/500 runs, 5–8 ms after light (p50), 12 ms max.
- **L400 (2.4 bar for 0.4 s):** the persistence branch releases at 100 ms in 500/500.
  - Purged worst .982/.974; against liq|G73|L400 −10/+4, p .18.
- **L400o (P0 offset +0.71 bar):** the absolute branch releases 1 ms after light.
  - Purged worst .976/.970; −17/+9, p .17.
  - The measured-P0 rule (line 166) shows no loss.

### Failure states (FMEA inputs)

| State | P\|lit (A1_none / A1J_pc) | P_abort | P_total (p_nl 0) | Notes |
|---|---|---|---|---|
| PURGE NOT RUN LO | .986 / .980 | .242 | .747 / .742 | — |
| Same, sequence and booking flown with no flow (NOT_VENTED as a flag) | .994 / .986 | .242 | .753 / .747 | — |
| PURGE NOT RUN HI | not flown | 1.0 | 0 | Combustion gives no delay quantiles |
| BLEED_FAULT (31.24 g/s stuck from E0, FC log-only) | .924 / .920 | 0 | .924 / .920 | 32 exhausted per base; bled 115–162 g in 3.7–5.2 s; −70/+4 |
| Both case TCs lost; ECU reset | not flown | — | 0 | Relight refused, drogue held. Drogue descent ≈ the R3 outcome (§6), touchdown ~22 m/s: vehicle loss |
| B1 stuck bleed from ignition | .368 (default gate .332) | — | — | 315/500 exhausted |

### Other line-166 (REV-ELEC-1) changes

- **E1 rule:** in the simulation the flow ends at E0 − 0.05 s, so E1 is never delayed.
- **Second re-zero window:** the gate opens 4.0 s (p01) before the commit (min 3.68 s); the second re-zero must end inside that window, before PURGE.

### Continuity with the stored FSW (N1)

- A1_none: .990 → .994 (−1/+3, p .63).
- A1J_pc: .984 → .982 (−2/+1, p 1.0).

### Code-change provenance

- The main RG-01 tables were flown before the last sim6 edit (the V flame-out option, 11:44Z).
- Bit-check RF re-flew subsets of three tables with the final code: 0 mismatches. Bit-check V1 (identity when the V option is off) also passed.

## 2. Amendment a: purge sequence, gate and late commit (sim6 G)

### API and hypotheses

- **API (run6 S-registry; full table in rev2.api_v29 of the staging JSON):**
  - pgg_Tc 2.90, pgg_ton 0.35, pgg_Tp 2.5, pgg_cap 2.5 (ECU cap), pgg_toff 0.05, pgg_tcl 0.077, pgg_Tmin 1.9;
  - gate: pgg_aqs 1.5 m/s², pgg_tqs 0.5 s, pgg_tau 0.2 s, pgg_tdmin 1.0 s;
  - predictor: pgg_cv 1, pgg_ant 2.90; overrides pgg_ovr, pgg_hfl.
- **Hypotheses:**
  - H-G1: no commit during the drogue transient. Refuted by a commit before the gate opens or with |a_z,f| > 1.5 m/s².
  - H-G2: the 1.9 s floor costs no P on the decided path.
  - H-G3: "delay T_fire instead" is safe.

### Decided path

- **Commit:** by the predictor in 2000/2000 runs (Tp1.9 edge state, four bases), at 88.8–129.6 m.
- **Gate:** opens at 219.5–255.3 m; gate to commit ≥ 3.68 s (p01 4.0 s); |a_z,f| after the gate opens p99 1.21 m/s², max 1.33 m/s².
- **Spurious starts:** 0.
- **E0 height:** p50 44.7 m, min 34.7 m.
- **Flow and mass:** flow ≥ 2.387 s; purge mass 69.7–73.0 g.
- **H-G1 and H-G2 are not refuted.**

### Height cost of the T_fire-delay rule (Combustion's request)

- In 158–166 of 500 runs per base the plain trigger fires before the planned T_fire. T_fire then moves to the plain trigger + 0.127 s (77 ms valve close + 50 ms).
- E0 comes p50 0.47–0.58 m, p99 2.87 m, max 3.04 m below the height at the plain trigger.
- The commit came ≥ 2.66 s before the plain trigger, so the 1.9 s floor never bound.

### P30 (bit-check G6, 500 runs per arm)

| Arm | Purge-start height | Starts above 200 m |
|---|---|---|
| Exact rev1 P30 arm on FSW-R2 | p50 123.5 m, p99 301.1 m, max 304.0 m | 6 |
| G with the gate off and constant-acceleration extrapolation | identical distribution; 6 flagged spurious | 6 |
| Decided G | p50 109.8 m, max 129.6 m | 0 (0 above 160 m, 0 spurious) |

### Late commit (H-G3 refuted)

State e19 (Tp1.9 edge, conservative), 500 runs per base:

| Commit rule | A1_none / A1J_pc | Pooled vs the decided commit |
|---|---|---|
| At the plain trigger (T_fire delayed 2.30 s; E0 p50 0.07 m) | 0.000 / 0.000 | all lost |
| Forced at 100 m (delay ≤ 0.64 s, E0 ≥ 37.3 m) | .992 / .986 | −3/+4, p 1.0 |
| Forced at 90 m (delay ≤ 1.02 s, E0 ≥ 30.0 m) | .946 / .932 | −51/+2, p 3e-13: LOSES |
| Forced at 80 m | .446 / .458 | LOSES |
| Forced at 70 m | .018 / .022 | LOSES |

- The 60 m floor was not flown.
- Nominal 1 ms record (bit-check G2): a commit at the plain trigger costs 42.8 m; E0 comes at 0.10 m.
- **Lowest safe forced commit:** about 100 m (DERIVED).
- **Time form:** a T_fire delay up to about 0.6 s costs no measurable P; about 1 s loses about 6 %.

**PROPOSAL (lead decision):**
- Commit no later than plain trigger − 1.7 s (0.35 + 1.9 + 0.05 − 0.6).
- If no commit by then, do not purge. That is the PURGE NOT RUN LO state, P_total about 0.75, against P about 0 for the delay rule.
- Comparator: the decided delay rule.
- Refuted if Combustion shows that an unpurged start at that point carries a hazard outside its abort model (TO-VERIFY).

### Tank outlet coverage inputs (Combustion's request; no coverage verdict)

- **Attitude during the flow (500 runs per base):**
  - tilt from vertical p50 1.6°, p99 5.2–5.3°, max 6.9°;
  - transverse rate p99 11.8–13.0 °/s, max 16.1 °/s;
  - roll rate up to 35.4 °/s.
- **10 ms re-flights:** run 0 and the largest-tilt and largest-rate runs of each base and state; 12/12 identity checks passed.
  - axial specific force 0.89–1.12 g;
  - angle between the body axis and the specific force ≤ 2.65° (0.1 s mean), i.e. the quasi-static free-surface tilt relative to the tank;
  - descent 21–25 m/s; flow from 95–115 m down to 43–54 m;
  - liquid 846–1170 g at flow start, 766–1089 g at flow end.
- **Vehicle mass drop:** exactly 73.0 g (G1). The liquid drops 81.6 g because of boil-off into the ullage.
- **Purge window:** identical in the purged worst and purged least states.
- **Not modelled:** slosh, canopy pendulum.
- **Verdict needs:** tank and outlet geometry and fill (Combustion / Mechanical).

## 3. +0.60 kg on the fixed engine module (task 5)

- **Placement:** point mass at ledger P07, z 0.158 m (DESIGN placement).
- **A1:**
  - liq|none|m60: .992 / .980, with 2/2 new exhaustions and no purge;
  - liq|G73|m60: .980 / .980 (6/7 exhausted); per base, A1_none −6/+0, p .031 (LOSES); pooled −11/+5, p .21;
  - pw|G73|m60: .984 / .978 (6/7 exhausted); pooled −11/+6, p .33.
  - Trim: §1.
- **B1 62 m (FSW-R2, W1p), all 500 engines:**
  - P .988 → .990 (−2/+3);
  - usable reserve shift p50 −10.7 g, min −39.2 g; 0 exhausted;
  - apex p50 62.78 → 62.72 m.
- **B1 on the default grain gate (line 172 (3)):**
  - 364/500 engines kept (72.8 %);
  - P .989 [.972, .996] → .989 (−2/+2); 0 exhausted;
  - fuel web at the end of the record ≥ 2.62 mm; burn limit acted in 1/364 runs (34/500 without the gate); 0/364 below 1 mm.

## 4. RG-16 on the decided purge path

- **Terms (flown as published, line 172 (1)):**
  - miss-side booking residual −45 g (bound 78.1 − 34.3 = 43.8 g);
  - not booked +73.0 g;
  - stuck bleed A1 +161.6 g, B1 +568.8 g;
  - smallest FC-window mass 12.87 kg.
- **Realised Monte Carlo (200 runs × 5 onsets per case):**
  - 670 N misses 0/1000, except Llo_cmd_pbk 1/1000 (comparator 0) and B1 H_cal bleed 1/1000;
  - held maximum ≤ 592.9 N (margin ≥ 57.1 N); 0 pre-onset alarms.
- **Adopted budget form, miss side (allowed 2.99 %):**
  - single-frame random term: H_cal 5.27 %, H_cal_comp (flown) **4.45 %: FAIL**;
  - per-flight form: H_cal 3.71 % FAIL, H_cal_comp 2.49 % PASS.
- **Over-read side:** passes in every form; worst estimate 585.1–589.8 N.
- **Barrier-element minima:** they do not cause the failure. The whole purge term is 0.35 pp; without it the total is still 4.10 %.
- **Consequence:** FC_THRUST stays not armed on A1. The definition of the random term is a lead decision.

## 5. Amendment b (K: freeze k_hat and the B apex predictor on Pc invalid; line 113 (2))

- **API:** kfz_on.
- **Hypothesis:** freezing loses neither P nor detections. Refuted by any McNemar loss, fewer detections or more false decisions.
- **Bit-check K:**
  - K1: Pc valid, identical (1730 values);
  - K2: Pc lost from t = 0, k_hat stays 1.000;
  - K3: Pc lost after the light, k_hat frozen.

**Re-fly, paired against the stored K-off rev1 tables. H-K is REFUTED.**

- **Mass-estimator Pc-lost arms (Pc lost from the pad):**

| Base and arm | K off → K on | Pair |
|---|---|---|
| A1_none low Cd end, re | .992 → .858 | −67/+0 |
| A1_none low Cd end, cmd | .994 → .840 | −79/+2 |
| A1_none low Cd end, re_comp | .996 → .860 | −68/+0 |
| B1_62 high Cd end, re | .986 → .704 | −145/+4 |
| B1_62 high Cd end, cmd | .994 → .690 | −154/+2 |
| B1_62 high Cd end, re_comp | .994 → .704 | −147/+2 |

  A1 at the high Cd end and B1 at the low end show no loss.
- **Fault arms (50 Pc-lost arms, 8000 runs):**
  - A1: identical.
  - B1 ascent: Lhi_blind .095 → .025 (−14/+0); MISS .110 → .030 (−8/+0); GEO .110 → .000, with 11 false geofence trips.
  - B1 floor GEO: 26 false trips.
  - B1 landing: Lhi_blind detections 200 → 179; GEO 82 false trips.
  - Total detections 5960 → 5918.
- **Mechanism:**
  - The freeze stops k_hat from learning the open-loop thrust error from the accelerometer.
  - The A1 landing then flies with a 12.5 % thrust error at the low Cd end.
  - The B apex predictor overshoots: B1 landing Lhi_blind apex p50 64.5 → 81.3 m, max 111 m, and the geofence trips before the fault.
- **What K-off means:** it learns against F/tsc. That equals the throttle-map thrust at the current pintle position, which the FSW can form from its command or encoder without Pc, apart from map error (not modelled).

**PROPOSAL:**
- Do not fly the freeze.
- With Pc invalid, re-reference k_hat and the apex predictor to the throttle-map thrust and keep learning. A freeze only for short dropouts (length TO-DEFINE).
- Make Pc valid a launch-commit condition.
- This is a new amendment, not flown. Comparator: K and K-off. Refuted by a loss against K-off once a map-error band is added.

## 6. Amendment c: Pc invalid inside [E2, release], including a flame-out (sim6 V)

- **API:** pcf_on, pcf_dt, pcf_k, pcf_rule (0 none, 1 interim, 2 accelerometer, 3 hold and abort), pcf_Facc 37.16 N, pcf_n 3, pcf_tmax 0.5 s, pcf_tbl, pcf_fo.
- **Mapping to the adopted predicate:** R1 is the adopted 0xFFFF term (release at t_E2 + 0.10 s with the ECU in RUN).
- **Monte Carlo:** purged worst + G73, Pc invalid from E2, 500 runs per base, paired with pw|G73 (.986/.984):

| Rule | Engine lit | Low Cd end (pcf_k 0.875) | With the L400 plateau | Undetected flame-out |
|---|---|---|---|---|
| R0, no Pc-free term | .392 / .396 | — | — | — |
| R1, interim (adopted) | .990 / .986; −1/+4; releases at 100 ms | .992 / .988 | .982 / .972 | releases a dead vehicle in 1000/1000; touchdown p50 −32.3 m/s (p01 −35.7) |
| R2, accelerometer | .990 / .984; −2/+4; releases 40–70 ms after light | .990 / .988; 0 aborts | .986 / .976; releases 440–470 ms after light; 0 aborts | holds the drogue in 1000/1000 (largest estimate 33.0 N < 37.16 N); touchdown p50 −21.8 m/s |
| R3, always hold and abort | 0 / 1000 | — | — | holds the drogue |

- On a flame-out both R1 and R2 lose the vehicle (P 0). R2 keeps it on the drogue with about 0.46 times the impact energy.

**RECOMMENDATION (lead):**
- Replace the time-only 0xFFFF term with R2: release on the accelerometer thrust ≥ 37.16 N for 3 frames at 100 Hz with the ECU in RUN; otherwise hold the drogue and abort at t_E2 + pcf_tmax.
- Widen the margins before adopting it:
  - flame-out estimate 33.0 N against a 37.16 N threshold (11 %);
  - plateau release at 470 ms against the 500 ms deadline. PROPOSAL pcf_tmax 0.8 s (not flown).

## 7. Bit-check v29

All parts PASS.

| Part | Content | Result |
|---|---|---|
| A0 (run 1) | options off against the stored v2.8 tables | 6660 + 6956 values, 0 mismatches |
| A1 (run 1) | differential against the rev1 simulator copy | 36 jobs, 5472 values, 0 mismatches |
| K (run 1) | K1–K3 | PASS |
| V (run 1) | V1–V7 | PASS |
| RF (run 1) | final code reproduces subsets of three re-fly tables | 4498 + 5017 + 9515 values, 0 mismatches |
| G (run 2) | G1–G6; G6 = 4 × 500 runs, P30_reproduced true | PASS |
| N (run 2) | N0–N5 (strict inputs; N5 = 692 values identical between combustion v2.3 and v2.4) | PASS |

- **Run 1 failure:** run 1 failed two test expectations: G1 compared the liquid drop instead of the vehicle-mass drop, and N4 expected a different KeyError name. Kept as `bitcheck_v29_run1_FAIL.*`.
- **Run 2:** tests corrected; the simulator was unchanged (file times). Run 2 records the code hashes, and they match the staged sim6, run6 and the tool.
- **Other checks:** purge-outlet re-flights 12/12.
- **Manifests:**
  - rev2 MANIFEST verified 280/280;
  - rev1 MANIFEST re-verified OK.
- **Not applicable:** npm test and build (no app change).

## 8. Text fixes to rev1 (staging JSON `rev2.text_fixes_rev1`)

1. Withdrawn: the igniter Unknowns row and the RG-12 drift note. Stated instead: electronics v2 breaks the run6 build (N5).
2. §2.8: W1p_tot (19/500 runs below 1 mm) was flown **with** the limit action.
3. §2.10: the per-arm bound for 0/200 is 1.49 % (exact one-sided 95 %).
4. The bit-check v1.5 claim covered parts A, C–F, P, R and S only.
5. start_transient: arm L400_te flew t_ign_est 1.11 s.
6. B1 is now carried on the default grain gate.

In the staging JSON, the drogue text of relight_conditions is replaced by the adopted predicate, and purge_bound is superseded by ≤ 76 g per purge (73.0 g at the ECU cap). The old values are kept.

## 9. Status per task

- **Done:**
  - RG-01 re-fly, including the failure states, plan check, reserve, trim (285 m adopted) and continuity.
  - Amendment a: ECU cap, 1.9 s floor, delay and height cost, lowest commit, P30 fixed. The late-commit rule is a PROPOSAL.
  - Amendment b: re-fly done; result REFUTED. The replacement is not done.
  - Amendment c: R0–R3, flame-out, low Cd end and plateau flown; recommendation R2.
  - +0.60 kg on A1 and B1.
  - gnc.json v3.1 rev2 staging: rev1_items, results, lead decisions to line 172, inputs_read with hashes.
  - REV-ELEC-1 items.
  - REV-GNC-2 N1, N4, N5, ECU cap, runs 14/108, RG-16 terms, restated predicate, text fixes.
  - Combustion v2.4 pins and the height-cost request.
  - REV-COMB-2: RG-16 statement, B1 default gate, B1 O/F export.
- **Partly done:**
  - Tank outlet coverage: inputs only; the verdict needs the geometry.
  - Amendment c margin widening (pcf_tmax 0.8 s) not flown.
  - Trim at 285 m flown only on the liquid table and purged worst.
- **Not done:**
  - RG-08 flag in the loop with a late flip.
  - K re-reference amendment.

## 10. Unknowns (not invented)

- **FMEA probabilities:**
  - the line-state probabilities;
  - PURGE NOT RUN;
  - BLEED_FAULT.
- **Inputs from other subsystems:**
  - tank outlet geometry and fill;
  - real FC frame noise (the RG-16 random term);
  - accelerometer noise and bias, drogue snatch and pendulum (R2 margins).
- **Not modelled:**
  - flame-out cold flow;
  - throttle-map error under Pc loss;
  - the Pc-lost specification for the MECO predictor, attitude thrust estimate and disturbance estimator.
- **Pending confirmation:**
  - Combustion's unpurged-start hazard at the late-commit point;
  - whether the barrier-element stall is physical;
  - the other states at 285 m.

## 11. Next closure

1. Independent review of this checkpoint and of amendments G, K and V.
2. Lead decisions:
   - late-commit rule (§2);
   - K replacement (§5);
   - R2 and pcf_tmax (§6);
   - RG-16 random-term definition;
   - +0.60 kg trim below 275 m.
3. Combustion: unpurged-start hazard; coverage verdict from §2 inputs.
4. GNC:
   - fly the K re-reference amendment;
   - R2 with pcf_tmax 0.8 s;
   - the remaining states at 285 m;
   - RG-08 amendment.

## 12. Files (staging_v3.1/rev2/, sha256/16)

- **Manifest:** MANIFEST_rev2.sha256 cb5d2c48e8d8fa27 (280 files, 80 MB; CSV tables gzipped with -n).
- **Results:**

| File | sha256/16 |
|---|---|
| results/gnc_json/gnc_v3.1_staging_rev2.json | a5564b45ed7fb463 |
| results/rg01_refly/rg01_refly.json (plus 114 tables .csv.gz) | 8a3b34a08289d5b1 |
| results/bitcheck_v29/bitcheck_v29.json (run 2) | e945cc883b459701 |
| results/bitcheck_v29/bitcheck_v29_run1_FAIL.json | 187d4d6ac8d5848d |
| results/b1_m60/b1_m60.json | f9de38ee5e376774 |
| results/b1_of/b1_of_phases.json (B1 O/F export) | 2b92abbccbc80679 |
| results/b1_of/b1_of_phases.csv (B1 O/F export) | 6a624065305a23aa |
| results/rg16_v2/rg16_fct_terms_v2.json | 2ae2a6eedd90249a |
| results/kfz_pcl/kfz_pcl.json | 5f9193f628950610 |
| results/kfz_fault_f/kfz_fault_f.json | 1d50206be7a19cdb |
| results/purge_outlet/purge_outlet_inputs.json | 47b4deb96ea22043 |

- **Simulator and pins:** sim/gncsim_v2.9-dev_MWFPRSGKV/ (hashes in §0), sim/pins/pins_rev2.sha256 4c97768d53b57eef, sim/iface_v3d/.
- **Scripts:**

| Script | Version | sha256/16 |
|---|---|---|
| m2_rg01_refly.py | v1.3 | 73004f1fd6ffbf21 |
| m2_bitcheck_v29.py | v1.1 | ef1c8bd71339687a |
| m2_bit29_runner.py | — | 4c24129aba762f1e |
| m2_gnc_json_v31_rev2.py | v1.1 | faff9f0c14fcc296 |
| m2_kfz_pcl.py | — | 71aa66d8a36de7cc |
| m2_kfz_fault_f.py | — | 6f19529337d716b5 |
| m2_b1_m60.py | v1.2 | 8e2276483da45bc9 |
| m2_b1_of_phases.py | — | 509cd5eddbe12023 |
| m2_purge_outlet_inputs.py | v1.1 | 6937ae463ce049a2 |
| m2_rg16_fct_terms_v2.py | v2.1 | 9e46f9e79b98c5d4 |
| m2r2_env.sh | — | 86b4d8b92dade4b7 |

- **Logs:** logs/ (22 logs).
- **Elsewhere:**
  - interfaces/CHANGELOG.md line 174 (gnc result);
  - working notes /home/claude/work/space/rev2_notes/PROGRESS.md.
