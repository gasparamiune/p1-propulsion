# GNC simulation package (`gncsim`): Space/GNC, ARGOS H1 engine team

Version: sim v2.4 (2026-10-12): 6-DOF `sim6 v2.4` + `run6 v2.4`, with the 1-D `sim1d v1.2` kept as an
independent reference. Owner: Space/GNC (`01-systems-gnc`). Units are SI. Environment: `/opt/engine-venv`
(Python 3.13, numpy, scipy, numba, CoolProp, RocketCEA, python-control, matplotlib). The v1.2 README is kept as
`README_v1.2.md`.

Everything here is simulation or derivation. None of it is hardware validation. Every parameter carries a
tag (REQ/DATASHEET/LITERATURE/SIM/DERIVED/ASSUMED), in one of these places:
- `gncsim/params.py` or `gncsim/vehicle.py`
- `run6.build(...)[5]["tags"]`
- the interface JSON it was read from

Scripts read the interface JSON at run time and never hard-code another discipline's numbers. During the
2026-10-12 mount outage, `GNC_IFACE` points to the lead's fallback hub.

Combustion v2 relay (2026-10-12). The lead relayed combustion v2 performance before `combustion.json` v2 was
published. `data/relay/lead_relay_combustion_v2_20261012.json` records the message. `scripts/m2_engine_relay.py`
turns combustion's S230 duty-cycle runs into thrust-binned mass-flow factors k_ox(F), k_f(F) on the v1 map
(`data/relay/engine_correction_v2.json`). `run6` applies them, with the S230 grain and the +0.11 kg engine growth,
while the hub still carries `combustion.json` v1 (`cfg engine="relay"`, default; `engine="v1"` is the comparator).
When `combustion.json` v2 is published, the correction stops applying by itself and its map is used.

Lead decisions 2026-10-12 (logged in `interfaces/CHANGELOG.md`). The N2O load is 2.00 kg in a 3.17 L tank. The roll
RCS is a provision only, deleted if T1 measures a roll torque of at most 0.02 N m. ENG-07 slew is at least 100 deg/s
across +/-7 deg. Gimbal parts are designed to the 26.5 N m stall load. Case `AD_prov_2kg` flies that configuration:
RCS not fitted, load fixed at 2.00 kg (`m_fixed`). `AD_fins_f20` (RCS fitted, sized load x 1.15 = 2.00 kg) stays the
reference for the paired comparisons.

## Layout

| Path | Content |
|---|---|
| `gncsim/tables.py` | CEA (RocketCEA) Pc x O/F tables; N2O saturation table (CoolProp) |
| `gncsim/propulsion.py` | numba engine/tank kernels: equilibrium self-pressurised N2O tank, map interpolation |
| `gncsim/engine_v2.py` | engine map from `combustion.json` v1 (throttle-map CSV: F, mdot_ox, mdot_f, Pc vs port diameter), tank-pressure ceiling; relay correction (combustion v2 S230) |
| `gncsim/params.py` | tagged default parameters and interface-JSON readers |
| `gncsim/vehicle.py` | reference vehicles RV-1 (v1), RV-1b (v2) and RV-1c (ledger v3c): geometry, tagged mass ledgers, mass properties vs propellant state (numba) |
| `gncsim/aero.py` | all-attitude (0-180 deg) component build-up aero: nose-first and tail-first, legs, fins, flaps, drogue |
| `gncsim/sim6.py` | **6-DOF flight simulator** (model summary below) |
| `gncsim/run6.py` | parameter-vector builder from the interface JSON and tagged assumptions; sizing; MC draws; Wilson CI; Spearman sensitivity |
| `gncsim/sim1d.py`, `run1d.py`, `mc1d.py`, `sizing.py` | independent 1-D vertical reference (M1), unchanged |
| `gncsim/tvc_analytic.py` | M1 analytic TVC sizing (pivot options, tail-wags-dog, hinge budget) |
| `scripts/m2_engine_relay.py` | relay correction of the engine map from combustion's S230 runs (factors, validation, S230 grain) |
| `scripts/m2_mc6.py` | M2 Monte Carlo, 500 runs per case: baseline, floors, hoverslam/ballast, IMU/GNSS/LiDAR classes, guidance laws (ZEM/ZEV, convex-lite), roll RCS and roll-torque sweep, pintle plant, structural filter, slew limit, gimbal limit, upwind bias, v1 engine map, RV-1b, A-F, B |
| `scripts/m2_verify6.py` | verification: torque-free and vacuum-ballistic invariants, dt convergence, zero-dispersion landings, comparison with sim1d and with the lead's seed |
| `scripts/m2_csi.py` | linear control-structure interaction: rigid/flexible engine mount, slosh, bending, delay; margins with and without the structural command filter |
| `scripts/m2_csi_timedomain.py` | nonlinear check of the CSI finding in the 6-DOF (mount stiffness/damping x actuator bandwidth, filter on/off) |
| `scripts/m2_duty_cycles.py` | duty-cycle CSVs v2: (a) full flights, (b) hops, (c) tethered hover, (d) static-fire qualification |
| `scripts/m2_vehicle.py` | RV-1c outputs: ledger, mass properties vs propellant state and events, CG range, aero tables with uncertainty sets, tail-wags-dog table, figures |
| `scripts/m2_trade.py` | descent-attitude trade quantities: hop to 300 m, flap area for tail-first stability, cold-gas RCS impulse and tank cooling, drogue |
| `scripts/m2_imu_sweep.py` | landing success vs residual gyro bias (IMU requirement) |
| `scripts/m2_failure_forensics.py` | re-flies every failed MC run (same draw) with full recording and classifies the failure |
| `scripts/m2_analysis.py` | case table, paired McNemar comparisons, failure drivers, loads, plots |
| `scripts/m2_fin_roll.py` | hand calculation: fin-misalignment roll torque vs the roll-RCS torque (fin alignment tolerance) |
| `scripts/m2_gnc_json.py` | assembles `interfaces/gnc.json` v2 from all of the above |
| `scripts/m1_*.py` | M1 scripts (1-D closure, sweeps, duty cycles v1, gnc.json v1), kept as the record of v1 |
| `data/iface_snapshot/` | copies of the interface files used by the v2 runs + `manifest.json` (sha256) |
| `data/lead_seed/` | local verified copy of the lead's point-mass seed (provenance in `PROVENANCE.txt`) |
| `data/relay/` | record of the lead's combustion v2 relay and the derived engine correction (sha256 of combustion's work files inside) |

## Running (in this order; about 40 min on one core)

```
cd 01-systems-gnc/sim
export GNC_IFACE=/mnt/project-files/engine/interfaces      # or the fallback hub
export GNC_SUFFIX=v2 GNC_OUT=/home/claude/work/space/out/m2 GNC_DC_OUT=/home/claude/work/space/out/duty_cycles_v2 \
       GNC_RES=/home/claude/work/space/out/results_v2 GNC_VEH_OUT=/home/claude/work/space/out/vehicle NUMBA_NUM_THREADS=1
PY="nice -n 10 /opt/engine-venv/bin/python"
$PY scripts/m2_engine_relay.py   # needs combustion's work files (paths in data/relay); skip to reuse the committed correction
$PY scripts/m2_mc6.py            # GNC_CASES=a,b selects cases; GNC_APPEND=1 adds them to an existing summary
$PY scripts/m2_verify6.py
$PY scripts/m2_csi.py
$PY scripts/m2_csi_timedomain.py
$PY scripts/m2_duty_cycles.py
$PY scripts/m2_vehicle.py
$PY scripts/m2_trade.py
$PY scripts/m2_imu_sweep.py
$PY scripts/m2_failure_forensics.py
$PY scripts/m2_analysis.py
$PY scripts/m2_fin_roll.py
$PY scripts/m2_gnc_json.py
$PY scripts/m2_report_tables.py  # markdown tables for REPORT.md, transcribed by script
```
`run_m2_all.sh` (in `01-systems-gnc/sim/`) runs the same chain with the environment above.
The first call of each process compiles the numba kernels, which takes about 30 s. A 500-run case then
takes about 30 s.

## 6-DOF model summary (sim6 v2.4)

**Truth model**
* Rigid body with variable mass, CG and inertia (ledger plus tank liquid/vapour plus grain), quaternion
  attitude, flat Earth, ISA density.
* Rotation (v2.4): each step applies the torque kick w += (M/I) dt, then the exact torque-free motion of the
  axisymmetric body over dt. That motion is two exponential-map attitude updates and a rotation of the transverse rates.
* Wind: power-law shear plus MIL-F-8785C low-altitude Dryden turbulence.
* Jet damping.

**Engine**
* Command → floor/ceiling clamp → deadband → 1 % quantisation → slew limit → first-order thrust lag.
  The open-loop pintle option adds the fuel lag.
* Thrust, mdot_ox, mdot_f and Pc come from the `combustion.json` v1 throttle map against the port diameter, with
  the mass flows scaled by the combustion v2 relay factors (S230 straight-port grain) in the default `engine="relay"`.
* The tank-pressure ceiling follows the blowdown.
* Ignition delay and tail-off are modelled.
* A tank equilibrium solve runs every 10 ms.

**Gimbal**
* The command is delayed (electronics.json delays).
* Servo: 2nd order with a torque-speed limit (datasheet stall and no-load) and the crank nonlinearity of
  mechanical.json (engine rate × cos ψ, torque / cos ψ).
* Deadband, backlash and an 8 deg conical stop.
* Flexible engine mount: axis stiffness from mechanical.json, ASSUMED damping. It is driven by base
  excitation (v2.2).
* Hose spring, friction, tail-wags-dog reaction −J_twd δ̈.

**Other truth-model elements**
* Slosh: first lateral mode, spring-mass.
* Legs: 4 spring-damper feet with stroke limit and friction.
* Aero: component build-up at the local velocity, including ω × r. Nose drogue, fins and flaps.

**Flight software**
* Sensors:
  * IMU classes ADIS16470, BMI088 and ICM-42688: residual bias, scale factor, noise density, vibration.
  * GNSS: standalone or RTK, with bias, noise and latency.
  * LiDAR (range-limited), barometer.
* Estimator: gyro-propagated attitude with no in-flight attitude aiding, plus three 3-state Kalman
  filters (position, velocity, accel bias) at 100 Hz.
* Guidance:
  * MECO on the predicted apogee.
  * Drogue at apogee (A-D).
  * Relight planned on the latest ignition (0.6 s).
  * Vertical landing: velocity-tracking reference + PI, or ZEM/ZEV (v2.3: time-to-go re-estimated every step from
    the planned deceleration, hand-over to the terminal law at tgo < 0.5 s).
  * Thrust-effectiveness estimator.
  * Autonomous hoverslam selection (T_floor > 0.9 W).
  * Lateral: PD, ZEM/ZEV or convex-lite (box-constrained QP), each to a reachable target with a divert
    clip.
  * Lateral disturbance feed-forward.
  * 8 m terminal gate with a tilt limit tapering to 4.5 deg.
* Control:
  * Attitude PD+I, gain-scheduled on thrust and moment arm, with integrator-freeze anti-windup.
  * Circular (vector-norm) gimbal limit.
  * Command shaping: 100 deg/s slew limit and a 2nd-order 50 rad/s structural low-pass.
  * Roll RCS (bang-bang).
* After the loop deactivates, the command returns to neutral through the shaping chain.

## Known limitations (v2.4)

* No in-flight attitude aiding in the estimator: the IMU result is specific to this assumption.
* Drogue: quasi-steady tension at the nose tip (massless canopy). No inflation transient and no line dynamics.
* Tail-first aero is unknown to about ×2 (no CFD or tunnel data yet). The MC draws the uncertainty set.
* Rocking damping, servo stiffness, hose stiffness and the leg spring/damper are ASSUMED ranges.
  They need bench measurement.
* RCS vapour draw is not removed from the tank. A bound is in the report: ≤ 0.02 kg, about 1 % of the load.
* The vehicle never fails structurally in the sim. Hinge torques far above the actuator stall (e.g. the
  unfiltered case) flag hardware damage that the sim does not model.
* Relight is assumed to succeed. Ignition reliability is a test item; a failed relight means vehicle loss
  under the drogue.
* No aerodynamic roll moments: fin misalignment and roll damping are not in sim6 (`m2_fin_roll.py` estimates them).
* The engine map is the v1 map with relay factors until `combustion.json` v2 is published; the factors are averages
  over the port diameters of combustion's runs.

## Change history

* sim1d v1.0–v1.2 (M1): see `README_v1.2.md`.
* sim6 v2.0: first 6-DOF on RV-1b.
* sim6 v2.1: mechanical.json v1 engine module (RV-1c, 146 mm body, CG pivot), crank nonlinearity,
  conical stop, flexible mount, command shaping, lateral disturbance feed-forward, 8 m gate,
  nominal-drag guidance model.
* sim6 v2.2: base excitation of the flexible mount; loads split into flight and touchdown; the inactive
  loop returns the gimbal to neutral through the shaping chain instead of stepping.
  * The v2.1 step produced hinge spikes at MECO and touchdown: up to 20 N·m after touchdown in 12 test
    runs, against 2–4.5 N·m with v2.2.
  * Roll-RCS hardware item P14 was added to the ledger (v3b).
* sim6 v2.3: ZEM/ZEV vertical law fixed. v2.2 used a fixed final time from burn start with a 0.3 s floor, which has
  an equilibrium hover about 0.5 m above the gate; the nominal flight hovered until the load was exhausted
  (P 0.836, sized 4.81 kg; kept as evidence). Load metrics in g use standard gravity, because test mode 1 has
  g = 0 and the verification script failed with a division by zero. The baseline path is bit-identical to v2.2
  (12 runs each of AD_fins_f20 and B_f20 reproduced exactly).
  * run6 v2.3: combustion v2 relay engine model, ledger v3c (+0.11 kg engine growth), S230 grain, residual roll
    torque amplitude `roll_amp` (straight port, 0.02 N m ASSUMED), `run_cfg` shared with the forensics.
* sim6 v2.4: rotational integrator. v2.3 updated the body rates with explicit Euler, including the gyroscopic term.
  * Symptom: the transverse rate amplitude of a spinning body grew as exp(T b^2 dt / 2).
  * The torque-free kernel test failed: |H| drift 8.9 % over 20 s at a 3 rad/s spin, dt 1 ms; first order in dt.
  * v2.4 integrates the free motion exactly: drift about 1e-13 at all step sizes. `rot_int 0` reproduces v2.3.
  * The v2.3 torque-free runs also left the roll RCS on. It despun the body; that is a control torque, not a defect.
    The kernel test now turns off the RCS, slosh and the flexible mount.
  * The baseline MC is unchanged at the printed precision (P 0.984, same failures and percentiles).
  * All results were re-run on v2.4. The v2.3 outputs are kept in `results/history/v2.3/`.
  * run6 v2.4: `rot_int` (default 1), fixed-load cases (`m_fixed` in m2_mc6), comparators for the lead decisions
    (rate80, norcs_r03/r04, bw8/bw6, slowPc, q2) and the lead baseline `AD_prov_2kg`.
* Failures and superseded runs are kept in the `results/` history files (`results/history/`).
