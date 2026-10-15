# ENG-03 throttle rate with the HV69 rate map (GNC, 2026-10-13)

Author: Space/GNC specialist. This is the text handed back to the lead on 2026-10-13, with formatting added by the lead.

**Simulator.** sim6 v2.8-dev. With the new options off it is bit-identical to v2.7.1-dev (m2_bitcheck_v28, parts A–F all pass).

**Evidence status.** Every result here is a simulation (SIM). The HV69 torque-speed line under load has not been measured: it comes from retailer copies of MKS data. This is not physical validation.

## Map and method

- **Rate map.** Electronics pintle_rate_map_v1.json (sha256/16 411b0573d604364e).
- **Lookup.** Bilinear in tank pressure P_tank (true value) and in delivered thrust divided by thrust_scale. Outside the 3.5–5.5 MPa grid the edge values are held.
- **Pairing.** Each run is paired with the stored baseline on the same draws: seed 101, 500 runs per base, each base flown with its own N2O load.
- **Bases.**
  - A1_none, A1_pc, A1J_none and A1J_pc, all on the v3 liquid plan of 0.81 s.
  - B1 62 m, rbl and tgl.
- **Statistic.** Exact McNemar test: a two-sided binomial test on the discordant pairs.

## R1, decision arm

Settings: corner opening map capped at 2500 N/s; closing 2500 N/s; closed-loop tau as in the baseline.

| Pool | P change | lost/gained | p | n |
|---|---|---|---|---|
| A1 | +0.00 % (0.9870 vs 0.9870) | −17/+17 | 1.0 | 2000 |
| B1 | −0.20 % (0.9940 vs 0.9960) | −4/+2 | 0.688 | 1000 |
| All | −0.07 % | −21/+19 | 0.875 | 3000 |

## Other arms

**R3, HV69 corner map both ways, uncapped.** Opening reaches up to 2757 N/s and closing about 2635 N/s. Result over all bases: +0.10 %, −13/+16, p 0.711.

**R1n, nominal map.** All bases: −0.20 %, p 0.263. B1 alone: −0.6 %, −9/+3, p 0.146. The nominal map is never slower than the corner map, so this arm shows the noise floor of the B1 paired flips.

**R2, lag bound.** Electronics model B is put in series with the loop: 4 ms latency plus the 8.5 / 8.0 ms two-state model. This double-counts the drive lag that already sits inside the closed-loop tau, so it is an upper bound.
- A1: +0.00 %, −21/+21, p 1.
- B1: −1.20 %, −13/+1, p 0.0018.
  - All 13 lost B1 runs have mean wind 5.9–7.8 m/s.
  - They fail on touchdown horizontal velocity at about 0.5–1.0 m/s.
- B1 with wind ≥ 6 m/s (n 272):
  - R2: −4.0 %, −12/+1, p 0.0034.
  - R1: −1.1 %, −4/+1, p 0.375.

**Rate-aware feed-forward.** Tested on the landing trigger with +20 ms and +40 ms of planning lag.
- It does not recover R2: still −13/+1.
- R1 stays at −0.2 % / −0.1 %.
- No feed-forward is proposed.

## Where the opening rate binds (R1)

Bound time per run, given as p50 / p99 / max.

| Phase | Bound time [s] | Runs affected |
|---|---|---|
| Ascent: engine-start rise from 0 to about 500 N, where the ECU kStartRamp of 2500 N/s also applies | 0.102 / 0.175 / 0.182 | 496 of 500 |
| Coast, drogue and relight command | never | — |
| A1 relight rise | 0 / 0.022 / 0.029 | 157 of 500 |
| B1 throttle-up at the landing trigger | 0 / 0.066 / 0.098 | 122 of 500 |

**Tank pressure at the landing trigger.** p01 3.89–3.95 MPa; p50 4.35–4.42 MPa.

**Runs below the map grid.** In some runs P_tank fell below the 3.5 MPa row; the edge value was held and the run flagged. A1: 1–3 runs per base. B1: none.

## GNC conclusion

The R1 loss is within about 1 %. Under the lead's logged rule:
- ENG-03 becomes the state-dependent map: opening at or above the corner map, closing at or above 2500 N/s, closed-loop t10-90 ≤ 100 ms.
- The HV69 stays. No actuator change needs sizing.

**Condition carried to B-PNT-1.** Measure t10-90 closed loop, under load, with the drive in the loop. If the drive lag adds on top of the Monte Carlo tau draw, B1 loses about 1.2 % (arm R2), all of it in winds of 6–8 m/s. This links to the launch-commit wind and gust criterion (RG-06).

## Not modelled

- Per-run draws of the drive state. The corner map is used on every run, which is conservative.
- The HV69 torque-speed line under load (unmeasured).
- Start and shutdown models: unchanged from the baseline.

## Files

All in the hub under 01-systems-gnc/staging_v3.1/. The lead verified five of the hashes.

| File | sha256/16 |
|---|---|
| results/eng03_rate/eng03_rate_v1.1.json | ec1a5f1ce12fff4c (verified) |
| results/eng03_rate/eng03_paired_runs_v1.1.csv.gz | 7bf6c1e7f04811d5 (verified) |
| results/v28_checks/bitcheck_v28_v1.json | 7961e16e62ee0846 (verified) |
| sim/scripts/m2_eng03_rate.py v1.1 | 37b25a4594edc2e3 (verified) |
| sim/scripts/m2_bitcheck_v28.py | 4b50663e29074bd5 |
| sim/gncsim_v2.8-dev/sim6.py | 07de1f97f7e14a31 (verified) |
| sim/gncsim_v2.8-dev/run6.py | 1cbb70bd40ab3be5 |

These files are not yet in the MANIFEST; GNC will add them at close-out.
