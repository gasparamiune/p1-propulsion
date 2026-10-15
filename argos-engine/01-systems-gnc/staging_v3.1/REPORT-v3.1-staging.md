# GNC v3.1 STAGING: FC_THRUST closure item 1, Combustion data items, T_tank note (2026-10-13)

## Status
- This is a staging set and is not published. Nothing in v3 changed:
  - `interfaces/gnc.json` v3 (sha256/16 3e97c378cfebee95);
  - `01-systems-gnc/REPORT-v3.md` (2d79920b8cc1537d).
- New outputs are in `01-systems-gnc/staging_v3.1/`. MANIFEST_staging_v3.1.sha256 lists 28 files.
- One line was appended to `interfaces/CHANGELOG.md`.
- Number tags used: SIM (sim6/run6 v2.7.1-dev), DERIVED, ASSUMED and REQ (lead). Nothing here is a bench or flight validation. A matching hash, a passing check or a correct table is not physical approval.

## 1. FC_THRUST: the four questions

### Q1. Review and run of m2_fc_thrust.py
v1 was reviewed before its first run and replaced by v1.1. The unchanged v1 stays in `01-systems-gnc/sim/scripts`.

Review fixes in v1.1:
1. A1 relight planning value 0.81 s (REQ lead). v1 used 0.65 s.
2. D_model now uses the FSW-estimated vertical speed (v1 used the true one). The leg term follows the profile's leg state. This now matches the k_est_asc 2 model exactly.
3. A second arming window, "fc" = airborne AND lit AND drogue released. This is the proposed valid flag. The v1 "air" window is kept for comparison.
4. Four filter variants at 100 Hz frames, with a random frame phase per run:
   - raw (the 1 kHz sample at the frame instant);
   - frame mean (the 10 samples of the frame);
   - first-order τ 10 ms;
   - first-order τ 20 ms.
5. Per-run held maximum: the highest level exceeded on 3 consecutive frames (20 ms). An abort at threshold T happens if and only if the held maximum exceeds T, so one statistic answers every threshold.
6. Latency from noise-free step and ramp responses.
7. Stuck-pintle detection timed from the failure onset and from the true threshold crossing, over a threshold sweep.
8. 500 runs per branch and profile.

Error statistics skip the first 0.1 s of each window segment, to exclude filter settling. In a first test, the drogue tension carried over in the filter after release inflated the A1 τ 20 ms 3σ to 16.7 %. Held maxima and false aborts still use every frame.

Run size:
- 2000 sim6 flights: A1 at 0.81 s with the liquid-line start-delay table, and B1 85 m. Each has a healthy branch (H) and a Pc-lost branch (L, thrust_scale 1.143 from ignition).
- 4000 synthetic stuck-pintle cases per filter variant.

The healthy branch reproduces the published landing success: A1 0.992, B1 0.978.

### Q2. 3σ error and latency

Healthy branch, A1 and B1 pooled, fc window, thrust ≥ 450 N. 3σ = p0.135 / p99.865. All latencies are on the flight-computer side.

| Variant | 3σ | Absolute error [N] | 3σ without mass error | Step 50 % (mean / max) | Ramp lag | Abort decision after a step (mean / max) |
|---|---|---|---|---|---|---|
| raw | 22.5 % | −104 / +114 | ±19.4 % | 4.5 / 9 ms | 0 | 24.5 / 29 ms |
| frame mean | 11.8 % | −50 / +59 | ±6.2 % | 8.5 / 13 ms | 4.5 ms | 29.5 / 34 ms |
| τ 10 ms | 10.6 % | −44 / +53 | ±4.3 % | 11.5 / 16 ms | 10 ms | 31.5 / 36 ms |
| τ 20 ms | 10.1 % | −41 / +50 | ±3.1 % | 18.5 / 23 ms | 20 ms | 38.5 / 43 ms |

- Over all burning frames (above 0.15 F_max), the τ 20 ms 3σ is 10.3 %. The τ 20 ms step reaches 90 % in 51.5 ms (mean) / 56 ms (max).
- The latencies include 0–9 ms of frame staleness. They exclude the IMU's internal filter and sample delay (part not chosen; datasheet needed), FC scheduling, CAN transport, ECU scheduling, and airframe axial dynamics (sim6 treats the airframe as rigid).
- The per-flight bias (standard deviation 3.1 %) comes from the assumed N(0, 3 %) FSW mass-estimate error. It dominates every filtered variant.

### Q3. Pc-lost Monte Carlo branch and stuck-pintle detection

**Pc lost, 650 N held 20 ms, fc window:**
- **τ 20 ms:**
  - False aborts: 0/500 (A1) and 0/500 (B1). The one-sided upper 95 % bound is 0.30 % per flight.
  - A normal fit of the held maxima gives 7.9e-5 per flight (A1) and 5.1e-5 (B1).
  - Held maxima p99 / max: 627 / 634 N (A1), 622 / 636 N (B1). The true thrust is 571.5 N.
- **Frame mean and τ 10 ms:** 0/1000.
- **Raw:** 29/1000 Pc-lost false aborts (20 A1, 9 B1), plus 1/1000 in the healthy branch. Raw is not usable at the assumed 2 m/s² vibration level.
- **Window comparison:** the "air" window (any engine state) gives the same held maxima. The maximum always occurs while the engine is lit (2000/2000). A1 coast and drogue readings stay ≤ 462 N.

**Stuck full-stroke pintle**, τ 20 ms, threshold 650 N. Ramps of 2.5 or 3.6 kN/s, starting from 500 N (ascent) or 150 N (landing). Times from the failure onset, p50 / p99 / max.
- **876 N:** detected in 4000/4000 cases.

  | Start | 2.5 kN/s | 3.6 kN/s |
  |---|---|---|
  | 500 N | 104 / 126 / 132 ms | 85 / 100 / 105 ms |
  | 150 N | 245 / 265 / 271 ms | 183 / 198 / 203 ms |

  Detection comes at most 72 ms after the true thrust crosses 650 N (p50 43–45 ms).
- **670 N:**
  - Missed (no abort within 2 s) in 252/4000 cases (6.3 %): 59–66 per 1000 in each ramp case.
  - The misses come from runs whose estimate under-reads by more than about 3 %.
  - Detected cases: p50 94–250 ms, p99 0.91–1.07 s.
- **Sample size:** the 4000 cases reuse the 1000 healthy-run error sets (4 ramp cases each). For a bias-driven miss the effective sample is about 1000, with an upper 95 % bound of 0.30 % when none is observed.

**Threshold trade-off at the assumed 3 % mass error** (τ 20 ms):

| T [N] | Pc-lost false aborts (of 1000) | 670 N missed (of 4000) |
|---|---|---|
| 620 | 19 | 0 |
| 625 | 11 | 0 |
| 630 | 7 | 8 |
| 635 | 1 | 42 |
| 640 | 0 | 75 |
| 645 | 0 | 136 |
| 650 | 0 | 252 |

At 3 %, no threshold clears both failure modes.

**Sensitivity to the mass-estimate error** (`m2_fc_thrust_mest` v1, τ 20 ms):
- Method: a paired re-evaluation of the same 2000 flights and 4000 stuck cases, with the same noise samples. The run's mass error e becomes c·e in the flight-computer estimate only, so the flights themselves are unchanged.
- The correction is exact: F_acc_c = (F_acc − D_model)(1 + c·e)/(1 + e) + D_model. |D_model| at the held maximum is up to 15 N, so it cannot be neglected.

| Mass sd (1σ) | 3σ at ≥ 450 N | Observed window [N] | At 650 N: false aborts / 670 N missed | Normal-fit tails (false abort / miss) | Band top tolerated at 650 N |
|---|---|---|---|---|---|
| 0.5 % | 3.5 % | 600–665 | 0/1000 / 0/4000 | 6e-59 / 8e-12 | 1.245 |
| 1 % | 4.4 % | 605–660 | 0 / 0 | 2e-25 / 2e-5 | 1.229 |
| 1.5 % | 5.7 % | 615–650 | 0 / 0 | 7e-14 / 2e-3 | 1.214 |
| 2 % | 7.1 % | 620–640 | 0 / 43 | 8e-9 / 1.4e-2 | 1.198 |
| 3 % (assumed) | 10.1 % | none (640 > 625) | 0 / 252 | 8e-5 / 6.5e-2 | 1.169 |

- The observed window runs from the lowest threshold with zero false aborts to the highest with zero 670 N misses.
- The band-top tolerance is DERIVED by scaling the held maxima linearly.
- With 1 %, 670 N is detected in 4000/4000 cases, p50 / p99 / max 0.18 / 0.29 / 0.44 s from the onset. 876 N takes 0.15 / 0.25 / 0.26 s.

### Q4. Threshold proposal (DESIGN, GNC, on SIM evidence; the lead decides)
1. **Threshold:** keep 650 N held for 3 consecutive 100 Hz frames (20 ms).
   - The estimate uses a first-order τ 20 ms filter at the IMU rate. The frame mean is an alternative: about 15 ms faster, with slightly more noise.
   - Raw samples are not used.
2. **Valid flag:** FC_THRUST is valid only while airborne (h_est > 1 m, before touchdown), the engine is lit and the drogue is released. Invalid means flag only (lead rule).
   - In sim6 this window does not change any result.
   - It is proposed for loads sim6 does not model: drogue snatch, touchdown impact before the touchdown flag, and the pad ground reaction (where F_acc reads the weight, not the thrust).
3. **New GNC requirement proposal:** flight-computer mass-estimate error ≤ 1 % (1σ) at every instant of the burn.
   - Criterion (GNC choice; the lead may set another): no false abort and no miss in the Monte Carlo, and normal-fit tails ≤ 1e-4.
   - 1.5 % is the edge; 2 % fails.
   - The assumed 3 % leaves 6.3 % of 670 N cases undetected.
4. **Lower thresholds are not proposed.** At 3 % they only trade misses for false aborts. With the required mass estimate, a balanced threshold of about 627 N would clear both, but it would tolerate a band top of only 1.19, against 1.23 at 650 N, while 1.143 is still an assumed value.

Refutation criteria (the claims above fail if any of these happens):
- On the DC-C / DC-D bench, F_acc against the load cell at ≥ 450 N falls outside the published 3σ band.
- Measured IMU vibration exceeds 2 m/s² at F_max.
- Any false over-thrust abort occurs at a true thrust ≤ 571.5 N.
- A commanded full-stroke pintle on the stand is not aborted within the published detection time.
- The mass estimate, once verified, is worse than 1 %. The 3 % figures then apply.

Decision owners:
- Lead: threshold and mass-estimate requirement.
- Electronics: ECU implementation, CAN timing, and whether the check also runs with Pc valid.
- GNC: mass estimator and the FC_THRUST frame.
- Combustion: open-loop band top and the stuck-pintle range.

## 2. Combustion data items (sent earlier and relayed by the lead; now in v3.1 staging)
**(1) A1 coast acceleration, MECO to the relight command** (500 runs plus the nominal; `coast_accel_a1` and `staging_v3.1/results/a1_coast_accel/`):
- The coast up lasts 6.31 s [p01 6.08, p99 6.54] with f_z < 0, so vapour is driven toward the seat.
  - f_z is the body-axis specific force; positive means apparent gravity toward the engine end.
  - Mean −0.38 m/s²; minimum −1.18 m/s² (p01 −1.46) just after tail-off.
- Drogue descent: 13.1 s, mean 8.18 m/s², last second 9.83 m/s².
- Drogue turnover at apogee: f_z ≤ 0 for 0.11 s (max 0.27 s), dipping to −1.90 m/s². Rates reach up to 194 deg/s. The drogue model is quasi-steady, so this is indicative only.
- f_z stays continuously positive for 13.0 s [p01 11.7, min 11.4] before the relight command.
- GNC makes no claim about venting. The judgement and the 19 cm³ requirement belong to Combustion.

**(2) B1 62 m duty cycles** (`staging_v3.1/duty_cycles/`):

| Record | Run | Thrust-on | Outcome |
|---|---|---|---|
| p99 | 159 | 18.63 s | lands |
| max | 211 | 20.65 s | fails landing |
| tg711 p99 | 264 | 18.28 s | lands |
| tg711 max | 211 | 20.15 s | fails landing |

- All four records lie inside the 85 m sizing cycles.
- Against Combustion's corner a ×1.5 / n 0.35, which burns through at 17.0–17.8 s: 7.2 % of the 62 m runs burn longer than 17.0 s, and 2.0–2.4 % longer than 17.8 s (engine-on counter).

## 3. T_tank ARM range
- 44 of 500 runs per case are drawn above 24 C.
- The difference is small and not conservative for every output:
  - Fisher p ≥ 0.43;
  - success in range differs by ≤ 0.3 points;
  - the B1 p99 engine-on counter in range is 0.0–0.2 s higher.
- Lead decision: recorded, no re-run. The next GNC baseline draws U(15, 24) C.

## 4. Other findings
- **Low thrust in fast B1 descents:** the relative error grows to −10 to −15 % at 105–150 N in a few runs. These are under-reads from the drag-model term. They do not affect the over-thrust check, but would matter if FC_THRUST were used for anything else.
- **Cross-check against sim6's own thrust-scale estimator (k_hat):** the median ratio is 0.986 for A1 (p01–p99 0.977–0.997) and 0.999 for B1. Agreement is within 1.5 %; the A1 offset is not explained.
- **Known issue in the v3 builder:** `m2_gnc_json_v3` v5 fails (NameError) when `fc_thrust.json` exists. The published v3 was built without it and is not affected. v3.1 is built by `m2_gnc_json_v31` v1 from the published v3 bytes, with their hash checked.

## 5. Checkpoint
**Claim.** On simulation evidence, 650 N / 20 ms on a τ 20 ms estimate is supported:
- 0/1000 Pc-lost false aborts;
- 876 N detected in 4000/4000 cases, p99 ≤ 0.27 s;
- 670 N missed in 6.3 % at the assumed 3 % mass error, and 0/4000 with ≤ 1 %.

GNC proposes the ≤ 1 % mass-estimate requirement. This is not a physical validation.

**Configuration.**
- sim6/run6 v2.7.1-dev (numba, 1 ms); FSW v2.7 provisional (k_est_asc 2, ratchet).
- iface_v3c: combustion.json v2.3, mechanical.json v2, electronics.json v1.
- A1 at planning value 0.81 s with the liquid-line E0→E2 table; B1 at 85 m. pc2 bases, no throat growth.
- Seeds:
  - 101 for the draws;
  - 20261019 + run (offset 100000 for L, 200000 for B1) for the flight-computer noise;
  - 20261020 for the stuck cases.
- Run commands:
  - Environment: NUMBA_NUM_THREADS=1, GNC_IFACE=/home/claude/work/space/iface_v3c, GNC_ACT_RATE=.../actuator_rate_check_v2.json, `nice -n 10`, 2 processes.
  - Main study: `GNC_FCT_PARTS=fly GNC_FCT_PROFILES=A1` and `=B1` in parallel, then `GNC_FCT_PARTS=eval`.
  - Sensitivity: `GNC_FCM_PARTS=fly` per profile, then `eval`.

**Sources.**
- REQ: the lead's FC_THRUST specification (gnc.json v3 `lead_decisions over_thrust_abort`: CAN 0x024, ≥ 100 Hz, 0.1 N, τ ≤ 20 ms, 650 N held 20 ms, stale or invalid = flag only).
- REQ: the lead's relay of the stuck-pintle case (670–876 N, 2.5 / 3.6 kN/s, from 500 or 150 N).
- ASSUMED: band factor 1.143 (lead), mass error N(0, 3 %) (run6), vibration 2 m/s² at F_max.

**Files** (staging_v3.1, sha256/16):

| File | sha256/16 |
|---|---|
| gnc_v3.1_staging.json | 695a069e8fc8dc53 |
| results/fc_thrust/fc_thrust.json | 0726d6197d341cbd |
| results/fc_thrust/fc_thrust_v1.1.png | 0524133876784c6b |
| results/fc_thrust/fc_thrust_mest.json | 37a82ed93a25ebfa |
| results/fc_thrust/fc_thrust_mest_v1.png | 1d95333eda793427 |
| sim/scripts/m2_fc_thrust.py (v1.1) | d6364936bf727494 |
| sim/scripts/m2_fc_thrust_plot.py (v1) | c47cbfe969a1150a |
| sim/scripts/m2_fc_thrust_mest.py (v1) | 786665d8f8eb69ec |
| sim/scripts/m2_gnc_json_v31.py (v1) | e260732a3b4d2134 |
| sim/scripts/m2_stage_hub_v31.py (v1.1) | c6684d227e38bd56 |

The Combustion and T_tank files staged earlier are unchanged; their hashes are in the manifest (19 earlier entries, of which only the stage script was re-staged as v1.1).

**Tests and verification.**
- All 2000 re-flown flights reproduce v1.1's held maxima and frame phases exactly.
- 136/136 stuck-pintle miss counts reproduce, and the 3 % 3σ reproduces (0.10075).
- Healthy landing success matches the published Monte Carlo runs.
- All 28 staged files match the manifest 10 s after writing; the sources are byte-identical; the JSONs parse; no temporary files remain.
- All 20 hash references inside gnc_v3.1_staging.json match the hub files.
- The CHANGELOG line was read back.
- v3 is untouched.

**Unknowns.**
- The flight-computer mass estimator is not specified. In the model the error is a constant fraction per run; a real pad-weighed, flow-integrating estimate drifts through the burn.
- The vibration level is assumed.
- The IMU filter delay is unknown (datasheet needed).
- CAN, flight-computer and ECU timing are unknown.
- Axial airframe dynamics are not modelled.
- The 1.143 band top is assumed.
- Throat growth with Pc lost is not modelled.
- The stuck cases are synthetic ramps, not 6-DOF failure flights. What the vehicle does after a missed 670 N pintle is not evaluated.
- It is not known whether the ECU runs the check only with Pc lost. This makes no difference at 650 N: healthy false aborts are 0/1000 at ≥ 610 N.

**Next closure.**
1. **Lead:** decide on 650 N and the ≤ 1 % mass-estimate requirement.
2. **GNC:** specify the mass estimator and its error budget.
3. **Founders:** say whether the loaded vehicle can be weighed at ARM, and with which scale (range, resolution, accuracy). Log F_acc against the load cell, and IMU vibration, on DC-C / DC-D.
4. **Electronics:** CAN/ECU latency, the valid-flag meaning, whether the check runs with Pc valid, and the IMU datasheet delay.
5. **GNC, optional:** add a stuck-pintle fault mode to sim6 to see the closed-loop consequence of a missed 670 N pintle.
6. **Closure item 2** (the 44 cm³ re-runs): waits for Combustion's re-check and Electronics' fault-path time.
7. **Reviewer:** a reviewer other than the author should review the v3.1 staging set.
