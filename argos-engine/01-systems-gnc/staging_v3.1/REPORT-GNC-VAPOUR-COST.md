# GNC vapour-start relight cost and drogue window (2026-10-13)

Author: Space/GNC specialist. Text as handed back to the lead on 2026-10-13 around 05:55Z, with formatting added by the lead.

All P values are SIM. The abort probabilities are Combustion SIM results on ASSUMED delays. The credit transfer is ASSUMED. Nothing here is physical validation.

## Basis

- sim6 6-DOF.
- Bases A1_none and A1J_none, 1000 runs per entry, paired on the same draws.
- Comparator: the liquid line planned at 0.81 s (v3), P 0.990.
- P_total = (1 − P_abort) × P|lit. An aborted relight counts as a lost landing (ASSUMED).
- The runs that survive the abort are taken to be the earliest lights (ASSUMED). Treating the abort as independent of outcome changes P by 0.001 or less.

## Abort probabilities

Source: Combustion relight_vapour_states_v2p4.json, re-issued at 05:31 ("void fix").

- The governing LO pocket is now 35.09 cm³ (was 29.28 cm³). The 16 LO cases were re-flown; the pre-fix runs are kept as superseded evidence.
- At W 0.93 s direct: LO 2.0 %, HI 9.8 %, 44 cm³ 22.8 %.
  - LO and HI come from a CDF fit to Combustion's W 0.85 s point (DERIVED). The 44 cm³ value comes from the seg44 curve.
- Prep path at W 0.76 s is taken as equal to direct at 0.93 s, using Electronics' 0.17 s purge credit (transfer ASSUMED).
- The minimum windows light Electronics' single nominal SIL trace. They do not light the whole delay distribution.

## P_total by option

Columns: liquid | LO 35.1 cm³ | HI 38.7 cm³ | whole 44 cm³

| Option | P_total | Notes |
|---|---|---|
| (a) prep path, W 0.76 s, plan 1.48 s | 0.990 / 0.974 / 0.892 / 0.766 | Liquid against its own plan: −6/+6, p 1.0, so no early-light cost. Over 4 bases (with growth): liquid 0.987, 44 cm³ 0.766 |
| (b) direct path, W 0.93 s, plan 1.09 s | 0.967 / 0.972 / 0.894 / 0.767 | Liquid early-light cost −27/+4, p 3.4e-5. Over 4 bases: liquid 0.971 (−46/+13, p 1.9e-5), 44 cm³ 0.767 |

(a) vs (b) on a liquid line, paired: 0.990 vs 0.967, −2/+25, p 5.6e-6. Over 4 bases: 0.9865 vs 0.9705, −10/+42, p 9.1e-6.

## Zero-abort comparators (GNC addition; P_abort = 0 in all)

| Option | P_total (liquid / LO / HI / 44 cm³) | Notes |
|---|---|---|
| (a-0) prep, W 0.88 s, plan 1.60 s | 0.975 / 0.991 / 0.990 / 0.990 | W 0.88 = 1.05 − 0.17 credit (ASSUMED). Liquid against its plan: −19/+4, p 0.0026 |
| direct, W 1.05 s, plan 1.21 s | 0.953 / 0.994 / 0.992 / 0.995 | |
| direct, W 1.05 s, plan 1.01 s | 0.975 / 0.993 / 0.993 / 0.993 | |
| direct, W 1.05 s, plan 0.91 s | 0.989 / 0.991 / 0.986 / 0.979 | Maximin over liquid / LO / HI (0.986) |
| v3 (W 0.65 s, direct) | 0.990 / 0.016 / 0 / 0 | Current baseline |

**Not assessed by GNC:**
- the unignited-flow and hard-start inventory of a liquid line at the longer windows. Combustion gives 36.8–40.3 g for direct W 1.05 s, against the 26.6 g accepted;
- the same inventory on the prep path at W 0.88 s.

## Option (d): drogue window

**Definition.** The window runs from drogue deployment to the relight command. Deployment is at the estimated apogee. sim6 uses a massless quasi-steady canopy, so inflation time is 0. The window from INFLATION is these numbers minus the real inflation time, which is UNKNOWN (TO-DEFINE).

Measured run by run on the same draws (s):

| Plan [s] | p01 | p50 | min |
|---|---|---|---|
| 0.81 | 11.80 | 13.10 | 11.51 |
| 0.91 | 11.71 | 12.99 | 11.40 |
| 1.09 | 11.53 | 12.82 | 11.20 |
| 1.21 | 11.39 | 12.70 | 11.08 |
| 1.48 (prep) | 11.11 | 12.43 | 10.82 |
| 1.60 (prep) | 10.99 | 12.31 | 10.71 |

**f_z history.** Measured at the seat; the MV station (ASSUMED) is within 1 %. A positive value drives liquid aft toward the seat. Values are p50 (p01) against time since deployment:

| t [s] | f_z [m/s²] |
|---|---|
| 0 | −0.15 (−1.14) |
| 0.5 | 0.89 (0.42) |
| 1 | 2.45 (1.52) |
| 2 | 5.07 (4.41) |
| 3 | 7.34 (6.70) |
| 4 | 8.64 (8.05) |
| 5 | 9.30 (8.85) |
| 6+ | 9.6–9.8 (9.2–9.3) |

- f_z ≤ 0 lasts p50 0.11 s and p99 0.23 s, right after deployment.
- Window mean f_z: p50 8.18 m/s².
- Continuous time above 0.5 g before the command: p01 9.60 s, p50 11.28 s.
- Continuous time above 0.9 g: p01 5.15 s, p50 8.86 s.
- Command height: p50 45 m, p01 37 m. Vertical speed at command: about −22 m/s.
- No opening shock is modelled, so the f_z history has no inflation transient.

## Files

All in the hub under 01-systems-gnc/staging_v3.1/. The lead verified the first three hashes.

| File | Version | sha256/16 |
|---|---|---|
| results/relight_seg44/relight_seg44_v1.5.json | v1.5 | 9164b346834a400f |
| results/drogue_window/drogue_window_v1.json | v1 | 3b3d789025c42b23 |
| results/drogue_window/drogue_window_envelope_v1.csv | v1 | 6eec7397f1b5dd48 |
| results/drogue_window/drogue_window_runs_v1.csv | v1 | — |
| sim/scripts/m2_relight_seg44.py | v1.5 | — |
| sim/scripts/m2_drogue_window.py | v1 | — |
