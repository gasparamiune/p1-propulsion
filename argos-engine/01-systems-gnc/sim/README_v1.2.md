# GNC simulation package (`gncsim`) - Space/GNC, ARGOS H1 engine team

Version: sim v1.2 (2026-10-11). Owner: Space/GNC (01-systems-gnc). Units SI. Python 3.13, numpy, scipy,
numba, CoolProp, RocketCEA, python-control (environment `/opt/engine-venv`).

Everything here is simulation or derivation. None of it is hardware validation. Every parameter
carries a tag (REQ/DATASHEET/LITERATURE/SIM/DERIVED/ASSUMED) in `gncsim/params.py`, `gncsim/vehicle.py`
or the interface JSON it was read from.

## Layout

| Path | Content |
|---|---|
| `gncsim/tables.py` | CEA (RocketCEA, N2O/ABS card of the lead) Pc x O/F tables; N2O saturation table (CoolProp) |
| `gncsim/propulsion.py` | numba engine/tank kernels: steady throttle point (regression law, CEA), injector ceiling, equilibrium self-pressurised N2O tank (bisection on internal energy) |
| `gncsim/params.py` | tagged default parameters and interface-JSON readers (`load_interfaces`) |
| `gncsim/vehicle.py` | RV-1 reference vehicle: geometry, tagged mass ledger, mass properties vs propellant state (numba) |
| `gncsim/aero.py` | all-attitude (0-180 deg) component build-up aerodynamics, nose-first and tail-first, legs, flaps, drogue |
| `gncsim/sim1d.py` | 1-D vertical flight simulator (profiles A ballistic+relight, B continuous-burn hop), landing guidance, engine/tank dynamics |
| `gncsim/run1d.py` | parameter-vector builder (`make_par`) and runner (`fly`) |
| `gncsim/sizing.py` | propellant/tank sizing by bisection on the nominal flight |
| `gncsim/mc1d.py` | 1-D Monte Carlo (dispersions per brief C.7), Wilson intervals, Spearman sensitivity |
| `gncsim/tvc_analytic.py` | first-pass TVC sizing: pivot options, tail-wags-dog zero, trim, aero moments, hinge-moment budget |
| `scripts/m1_duty_cycles.py` | duty-cycle CSVs (full flight, hop, tethered hover, static-fire qualification) |
| `scripts/m1_landing_mc.py` | M1 landing-closure MC v1 (kept as evidence; superseded) |
| `scripts/m1_landing_mc_v1p1.py` | landing closure v1.1/v1.2: floors 12.5/20/25/40 %, auto / forced hover / forced hoverslam / hover-with-ballast, sized loads |
| `scripts/m1_sweeps.py` | throttle 10-90 %, slew, resolution, ignition latency sweeps; ballast/payload trade; sensitivity |
| `scripts/m1_requirements.py` | assembles `interfaces/gnc.json` v1 from the results above |

## Running

```
cd 01-systems-gnc/sim
nice -n 10 /opt/engine-venv/bin/python scripts/m1_duty_cycles.py
GNC_SUFFIX=v1p2 nice -n 10 /opt/engine-venv/bin/python scripts/m1_landing_mc_v1p1.py
GNC_SUFFIX=v1p2_m115 GNC_LOAD_MARGIN=1.15 nice -n 10 /opt/engine-venv/bin/python scripts/m1_landing_mc_v1p1.py
GNC_SUFFIX=v1p2 nice -n 10 /opt/engine-venv/bin/python scripts/m1_sweeps.py
GNC_SUFFIX=v1p2 nice -n 10 /opt/engine-venv/bin/python scripts/m1_requirements.py
```
Outputs go to `GNC_OUT` (default `/home/claude/work/space/out/...`); curated copies are in
`01-systems-gnc/results/`, `01-systems-gnc/duty_cycles/` and `01-systems-gnc/vehicle/`.
`data/*.npz` are caches (CEA, N2O saturation, engine tables); delete them to rebuild.

## Model summary (1-D, sim v1.2)

* State: altitude, vertical velocity, tank (mass, internal energy), fuel mass, thrust. RK1/semi-implicit Euler, dt 1 ms
  (time-step convergence check in the 6-DOF verification set).
* Engine: command -> clamp [floor, ceiling(P_tank, port)] -> deadband -> quantisation -> slew limit -> first-order lag;
  ignition delay, rise, exponential tail-off (tau 35 ms). Mass flow from the steady throttle map (O/F shift and Isp vs throttle),
  Isp dispersion scales the mass flow.
* Tank: equilibrium self-pressurised N2O with 50 % wall heat-capacity participation, updated every 10 ms; thrust ceiling
  falls with blowdown; flow stops when liquid <= 3 % residual.
* Aero: axial drag with direction-dependent C_A (nose-first, tail-first, engine-on retropropulsion factor, legs), drogue.
* Guidance: profile A MECO on predicted apogee; B throttle-down on predicted apex then floor-coast with apex trim;
  landing burn = velocity-tracking reference (braking parabola to a gate at 4 m, terminal curve to 1 m/s),
  feed-forward + PI with anti-windup, drag feed-forward; accelerometer thrust-effectiveness estimator (v1.2);
  autonomous mode selection hover-capable vs Falcon-9-style hoverslam (T_floor > 0.9 W_est); hoverslam cuts the
  engine when the vehicle stops before contact.
* Navigation errors: constant altitude/velocity biases, mass-estimate error, accelerometer bias (per run).

## Known limitations (v1.2)

* Vertical only: no attitude, lateral motion, wind, slosh, TVC (the 6-DOF in v2 covers them).
* Engine map is the GNC placeholder built from ENGINE-BASELINE v0 (eps 3, 30 mm port, fixed-K injector ceiling);
  combustion.json v1 (eps 2, helical port, pintle) is integrated in v2.
* Touchdown is "h <= 0"; leg dynamics and contact in the 6-DOF.

## Change history

* v1.0: first landing closure (proportional loop) - failures kept in `results/m1/landing_closure_mc1d_v1.*`.
* v1.1: flown-mode recording fixed; per-case sized propellant loads.
* v1.2: accelerometer thrust-effectiveness estimator; hoverslam terminal margin 3 m/s2; hoverslam stop-cut no longer
  requires h_nav > 3 cm (a negative altimeter bias made the vehicle stop aloft, climb at floor thrust and fall).
