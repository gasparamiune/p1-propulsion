## C. 6-DOF simulation: method

### C.1 Scope and status

`sim6` is a numba-compiled, fixed-step (1 ms) 6-DOF simulator of the vehicle, the engine, the gimbal and the flight
software. It is an engineering model for requirement derivation and comparison of options. It is not validated
against hardware. The 1-D simulator `sim1d v1.2` (M1) stays as an independent reference; the two share only the
engine tables.

### C.2 Truth model

| Element | Model | Basis / tag |
|---|---|---|
| Rigid body | Variable mass, CG and inertia from the tagged ledger plus tank liquid/vapour and grain regression; Euler rotational equations; jet damping | DERIVED (ledger v3c) |
| Attitude | Quaternion, exact exponential-map update per step, renormalised | numerical |
| Translation | Semi-implicit Euler, flat Earth, ENU | numerical |
| Atmosphere | ISA density, site density dispersed U(1.10, 1.25) kg/m3 | LITERATURE + ASSUMED |
| Wind | Power-law shear (alpha 0.14) + MIL-F-8785C low-altitude Dryden turbulence (first-order forms), gust scale dispersed | LITERATURE |
| Aero | Component build-up at the local air velocity incl. omega x r: nose (Barrowman), blunt-base leading term, Allen-Perkins/Jorgensen crossflow, legs, Barrowman fins with interference, nose drogue (quasi-steady tension at the nose tip); tail-first terms dispersed | DERIVED + ASSUMED |
| Engine | Command -> floor/ceiling clamp -> deadband 0.5 % -> 1 % quantisation -> slew limit -> first-order lag (closed-loop Pc); ignition delay; tail-off 35 ms; mass flows from the throttle map against the port diameter; thrust ceiling vs tank pressure | combustion.json v1 map x relay factors |
| Tank | Equilibrium self-pressurised N2O (CoolProp), wall heat capacity, solved every 10 ms | DERIVED |
| Thrust line | Along the gimballed nozzle axis through the pivot; misalignment U(+/-0.25 deg); lateral CG offset N(0, 2 mm) per axis (roll moment from lateral thrust included) | ASSUMED |
| Gimbal | Transport delay (ring buffer), 2nd-order servo with torque-speed limit, crank nonlinearity (rate x cos psi, torque / cos psi), deadband, backlash, 8 deg conical stop, flexible mount (stiffness from mechanical.json, damping ASSUMED) with base excitation, hose spring, friction, tail-wags-dog reaction -J_twd d'' | electronics.json + mechanical.json + ASSUMED |
| Slosh | First lateral mode as a spring-mass (Abramson, NASA SP-106) while the liquid is settled | LITERATURE |
| Legs | 4 spring-damper feet, stroke limit, regularised Coulomb friction | ASSUMED |
| Roll | Engine roll torque proportional to thrust (straight port: residual only), RCS couple | ASSUMED |

### C.3 Flight-software model

* Sensors: IMU classes (ADIS16470, BMI088, ICM-42688) with residual bias, scale factor, noise density and
  thrust-proportional vibration; GNSS standalone or RTK with per-run bias, white noise and 20 ms latency; LiDAR
  (range-limited, tilt < 30 deg); barometer with bias; pad alignment error.
* Estimator: attitude propagated from the gyros with no in-flight aiding; three decoupled 3-state Kalman filters
  (position, velocity, accelerometer bias) per world axis at 100 Hz.
* Guidance:
  * ascent lateral-velocity hold, optional upwind bias, MECO on the predicted apogee;
  * drogue at apogee (A-D);
  * relight planned on the latest ignition (0.6 s) from the predicted stopping distance;
  * landing burn vertical: velocity-tracking reference + PI (baseline) or ZEM/ZEV (comparator);
    accelerometer thrust-effectiveness estimator; automatic hoverslam when T_floor > 0.9 W;
  * lateral: PD, ZEM/ZEV or convex-lite (box-constrained QP re-solved at 10 Hz), each to a reachable target with a
    divert clip, plus disturbance feed-forward;
  * 8 m terminal gate: lateral-velocity nulling, tilt limit 10 deg at the gate tapering to 4.5 deg below 1 m.
* Control: attitude PD+I on the thrust-direction error, gain-scheduled on the estimated thrust and moment arm;
  circular (vector-norm) gimbal limit with integrator freeze; throttle = |T_cmd| / k_eff with saturation and
  integrator freeze; ECU command shaping (100 deg/s slew limit, 2nd-order 50 rad/s low-pass); roll RCS bang-bang
  with a 5 deg/s deadband. After the loop deactivates, the command returns to neutral through the shaping chain.

### C.4 Hypotheses that limit the results

1. No in-flight attitude aiding: the IMU requirement holds for this estimator only.
2. Tail-first aerodynamics are unknown to about x2; the MC draws the whole band but the band itself is ASSUMED.
3. The drogue is quasi-steady (massless canopy, no inflation transient, no line dynamics).
4. Rocking damping, servo and hose stiffness, legs: ASSUMED ranges until bench data exist.
5. Relight always succeeds; ignition reliability is a test item.
6. No aerodynamic roll moments (fin misalignment, roll damping): hand estimate in `fin_roll_v2.json`.
7. The engine map is the v1 map scaled by relay factors until `combustion.json` v2 is published.
8. The vehicle never fails structurally in the sim; hinge torque above actuator stall flags damage that is not modelled.

## B.5 Research proposals (hypotheses, not claims)

Each proposal is a research item. None is claimed better or new until the refutation test has been run.

**R-a. Landing legs as the aft fin panels.**
* Hypothesis: four leg panels, stowed flush along the aft body for the ascent and the coast, give the nose-first
  static margin that the separate fins give (>= 0.5 cal at 2 deg). The fins (0.30 kg, ledger A10) are then deleted,
  and the vehicle does not tumble before the drogue opens.
* Comparator: AD_fins_f20 (separate fins) and AD_nofins_f20 (no fins), same 500 draws.
* Evidence so far:
  * Landing success with and without fins differs by less than the MC noise (table C.6).
  * The fins set the coast attitude: the finless coast tumbles, and a drogue opened during a tumble is a
    line-wrap risk the sim does not model.
* Refuted if any of these holds:
  * the leg-panel geometry gives a nose-first static margin below 0.5 cal at 2 deg in `aero.py`;
  * the paired 6-DOF MC with leg-panel aero loses landings (McNemar p < 0.05);
  * leg deployment at ~22 m/s under the drogue exceeds the leg hinge loads Lauty can carry.

**R-b. Floor-thrust relight high under the drogue (backup-parachute window).**
* Hypothesis: lighting the engine at the floor thrust at ~100 m, while the drogue still holds the attitude and
  settles the liquid, then releasing the drogue only after Pc is confirmed, leaves enough height to deploy a
  backup main parachute if the relight fails. The cost is <= 0.3 kg N2O, with no loss of landing success.
* Comparator: baseline A-D (relight at the latest feasible point, ~40 m, no backup window).
* Evidence so far: the baseline relight height (table C.6) gives under 2 s of fall before impact if ignition
  fails. A floor-thrust phase of ~3 s at 100 N costs ~0.15-0.3 kg N2O (map flow at 100 N x time, DERIVED).
* Refuted if any of these holds:
  * a 6-DOF implementation needs more than 0.4 kg extra N2O;
  * the paired MC loses landings;
  * the height after a failed-relight detection (Pc < 50 % at t_ign + 0.2 s) is below the backup parachute's
    deployment-to-safe-speed height (Lauty/recovery to supply).

**R-c. Aided GNSS/INS attitude estimator to admit low-cost MEMS IMUs.**
* Hypothesis: an error-state EKF that fuses GNSS position/velocity with the IMU bounds the gyro-bias attitude drift
  well enough that a BMI088 or ICM-42688 class IMU lands within 2 % of the ADIS16470 baseline. Attitude is
  observable through the specific force in the powered phases and the drogue deceleration.
* Comparator: AD_fins_f20_BMI088 / _ICM42688 (gyro-only attitude) and the baseline.
* Evidence so far:
  * Success falls monotonically with the residual gyro bias (IMU sweep).
  * BMI088 noise with the ADIS16470 bias recovers most of the loss, so the bias is the driver. Bias is what
    aiding estimates.
* Refuted if either holds:
  * the EKF in sim6 with the BMI088 model does not reach the target in a paired MC;
  * attitude is unobservable for long enough in the low-specific-force phases (coast, drogue) to fail the landing.

## B.6 Staged test campaign (entry and exit criteria derived from this analysis)

| Stage | Content | Exit criteria (numbers from section D) |
|---|---|---|
| T0 bench | Gimbal + servos + ECU shaping; IMU; LiDAR/GNSS; RCS valves; drogue release | rocking mode >= 25 Hz with damping >= 0.02; engine-side slew >= 100 deg/s within +/-5 deg; backlash and resolution <= 0.1 deg; ECU filter frequency response as specified; IMU residual gyro bias <= 0.03 deg/s after pad calibration over 60 s; RCS couple torque within 20 % of 0.073 N m |
| T1 static fires (DC-D) | Ignition latency distribution (>= 30 starts), throttle map, Pc loop, 3 starts per run, gimbal sweeps under thrust, thrust-vector alignment, engine roll torque, rocking mode under thrust | latency p99 <= 0.5 s and planning value 0.6 s holds; t10-90 <= 0.15 s; floor 20 % stable; resolution <= 2 %; alignment <= 0.25 deg; roll torque measured to +/-0.005 N m at 4 throttle settings |
| T2 tethered hover (DC-C) | 0.5-2 m hover on a tether; doublets; attitude hold; thrust-effectiveness estimator; roll RCS | attitude hold within +/-2 deg; estimated vs measured thrust within 5 %; roll held within the deadband; link-loss policy demonstrated |
| T3 low hops (profile B) | 5-50 m then 100 m, legs fixed, landing guidance and divert | touchdown within the success criteria on 3 consecutive hops; telemetry matches the 6-DOF within its dispersion band |
| T4 drogue drop tests | Dummy vehicle of the landing mass, no engine | descent speed 21 +/- 3 m/s; swing <= 10 deg; release works under load |
| T5 relight hop | A-D mini: MECO ~60-100 m, drogue, relight ~30-40 m | relight within the planned window; landing within the criteria |
| T6 full A-D, 300 m | ACEMA 2027-09-01 | mission success |
