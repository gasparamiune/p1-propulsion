# ICD-AIRFRAME: engine to airframe interface (draft 0.2)

Issued by the engine lead on 2026-10-13 for Lauty, who owns the airframe, structure, recovery and legs.

**Status:** DRAFT 0.2 (0.1 corrected the same day with Mechanical's routing and module notes). It is compiled from these sources:
- interfaces/gnc.json v3, icd_inputs_for_airframe (3e97c378cfebee95);
- interfaces/mechanical.json v2 (2026-10-12);
- the lead decisions in interfaces/CHANGELOG.md up to 2026-10-13.

Mechanical v2.1 (CAD v3.4) will replace every value marked **(v2.1)**: the bolt pattern, the main-valve module envelope, the mass properties and the vent line routes. This is an interface definition. It is not a fabrication drawing or a tolerance stack. Every value carries its evidence tag. A value marked TO-DEFINE is unknown; it is not zero.

## 1. Frames and units

- **Units:** SI (m, kg, s, N, Pa).
- **Vehicle stations** z [m] are measured from the airframe aft datum (base plane), with +z toward the nose.
- **Engine frame:** origin at the gimbal pivot. +Z points forward along the engine axis, +X is the outer gimbal axis and +Y the inner axis.
- **Reference vehicle RV-1:** the pivot is at station z = 0.203 m and the nozzle exit at z = −0.030 m (DERIVED+ESTIMATE).
- **CAD:** STEP in mm with +Z forward. GLB in m with +Y up, for visualisation only.

## 2. Engine bay geometry

| Item | Value | Tag / source |
|---|---|---|
| Engine bay inner diameter | ≥ 140 mm over the whole engine zone | REQ, founder decision 2026-10-12 |
| Engine zone, engine frame | z = −0.2377 to +0.252 m about the pivot (aft closure at the 8° stop to the top of the pintle stack) | DERIVED+ESTIMATE, mechanical.json v2; closing sweep in CAD v3.4 (v2.1) |
| Engine zone, RV-1 stations | about −0.035 to +0.455 m | DERIVED from the line above |
| Nozzle exit below the pivot | 0.233 m; exit protrudes about 0.03 m below the aft datum | DERIVED+ESTIMATE |
| Gimbal range | ±7° on the vector norm; 8° conical mechanical stop | REQ ENG-07 |
| Airframe attachment | Thrust rings GM-09 (upper, thrust path) and GM-10 (lower: stop ring, TVC servo base) | DERIVED, CAD v3.3 |
| Ring fit | Ring outer radius 69.75 mm in the 140 mm bore; 0.25 mm radial gap | DERIVED, CAD v3.3 |
| Ring fasteners | 16 × M5 radial screws. Bolt pattern, edge distance and wall bearing check: **(v2.1)** | ESTIMATE |
| Main-valve module (MV-P, balanced poppet) | Fixed module above the gimbal zone: occupies the bay from +0.252 m to about +0.355 m (engine frame; ESTIMATE). FS-01 axis at r 10 mm, az 219.5°, from z 259.5 mm up; FS-15 fixes it with 2 × M5 radial screws into the wall. Envelope and mass: **(v2.1)** | LEAD 2026-10-13 / Mechanical |
| N2O tank | 6061-T6 tube, 101.6 × 3.175 mm, two bolted bulkheads, 3.17 L internal (2.00 kg at 85 % fill), cylinder length about 0.445 m. Located forward of the engine zone. Station and mounting: TO-DEFINE with Lauty | DERIVED / LEAD |
| Feed across the gimbal | Option A/O3b: coil on the engine case; fixed 3/8 in wall line at az 219.5°, r 64.2 mm, from z 71 to 249.5 mm (engine frame), held by 3 P-clips on the airframe wall at z 110 / 170 / 230 mm. The coil fixed end is being re-routed (retained-vapour fix): it needs an **airframe-wall clamp or GM-09 standoff near az 219.5°, z ≈ 71 mm**. Criterion: hose K_max ≤ 17.2 N·m/rad at 7.4 V, wall clearance ≥ 3 mm at the 8° stop, bend radius per the hose maker | REQ ENG-08, amended 2026-10-13 |

## 3. Loads from the engine into the airframe

All values are SIM or DERIVED. None of them is a test result.

| Case | Value | Tag / source |
|---|---|---|
| Rated thrust | 500 N (Pc 25 bar, software cap) | REQ ENG-01 |
| Over-thrust abort | 650 N held for 3 frames on a 20 ms filter. Valid airborne, lit and with no drogue load | LEAD 2026-10-13, provisional (REV-GNC-1 RG-16 to RG-19 open) |
| Physical worst-case thrust | 876 N at Pc 42.9 bar (pintle stuck at full stroke, 30 °C tank, Cd 0.80). Use it as the ultimate axial load case for the thrust rings | SIM, Combustion v2.3 |
| Chamber MEOP / proof | 45 bar / 67.5 bar | LEAD ENG-09 |
| Lateral thrust at 7° | 61 N at 500 N; 107 N at 876 N | DERIVED (F sin 7°) |
| TVC design moment | 35.3 N·m engine moment. Rod forces 441 / 552 / 609 N react into the TVC brackets on GM-10 | LEAD 2026-10-12 |
| Peak axial specific force in flight | 35.8 m/s² (B1 dispersed max), 33.7 m/s² (B1 p99), 27.7 m/s² (A1 p99) | SIM, duty cycles v3 |
| Touchdown, leg contact | 50.3 m/s² (B1 p99), 40.3 m/s² (A1 p99). The 530–673 m/s² values in the "disp_max" files are failed-landing impacts, not design loads | SIM, duty cycles v3 |
| Drogue steady line load | 150 N at apogee mass; 158 N upper bound. The opening (snatch) load is not computed: it belongs to the recovery designer | DERIVED, gnc.json |
| Airframe first bending mode | ≥ 10 Hz, goal 15 Hz | DERIVED, gnc.json |
| Axis stiffness, structure plus rods | ≥ 3,100 N·m/rad at every pose, goal 5,200. The airframe side of the ring mounts is part of this path | LEAD 2026-10-12 |

## 4. Mass, CG and inertia

GNC's reference vehicle RV-1c is ASSUMED. The real airframe is checked against the bands below. If it falls outside them, GNC re-runs the Monte Carlo; being outside is not automatically a failure.

| Item | Value | Tag |
|---|---|---|
| Liftoff mass | 16.07 kg for A1 (drogue + fins); 15.42 kg for B hops | SIM, ledger v3d |
| Dry mass / N2O / grain | 13.67 kg / 2.00 kg / 0.404 kg | DERIVED ledger |
| Landing mass, nominal A1 | 14.77 kg. Hover window at the 20 % floor: 11.33–16.0 kg | DERIVED |
| CG station in flight | 0.6534–0.6585 m. Verified band 0.6135–0.7035 m (1σ flown 15 mm) | SIM / DERIVED |
| CG above the pivot | ≥ 0.216 m at the 20 % floor, ≥ 0.343 m at 12.5 % (flown: 0.448 m) | DERIVED (tail-wags-dog rule) |
| Lateral CG offset | ≤ 6 mm | DERIVED |
| Thrust-axis misalignment | ≤ 0.25° | DERIVED |
| Dry mass and transverse inertia bands | ±15 % about RV-1c (I_transverse about 4.3 kg·m² at liftoff) | DERIVED |
| Engine hardware mass and CG | **(v2.1)**: CAD v3.4 re-issues the gimballed and fixed masses. The main-valve module and tank bulkheads are not yet in CAD | OPEN |

## 5. Thermal, venting and bay temperature

- **Upper-bay vent: REQUIRED** (lead decision 2026-10-13; this supersedes "recommended" in gnc.json v3). Conductance ≥ 0.3 W/K, goal 1.0 W/K, from Mechanical's servo-mount thermal network. Vent area and station: Lauty with Mechanical **(v2.1)**. Conditions:
  - Barometer static ports must sit outside the vent outflow and its wake. Vent-induced static error at the ports ≤ 12 Pa.
  - No vent inside the aft keep-out cone (section 7).
  - No drogue line or lanyard across a vent.
- **Bay temperature at ARM:** ≤ 45 °C, enforced by a firmware inhibit. The launch-site limit is TO-DEFINE, and it matters for Argentina in September.
- **Tank temperature at ARM and ignition:** 15–24 °C (ENG-12 interlock). Tank heater and insulation: interface TO-DEFINE.
- **Hot parts in the bay:** the case over-temperature abort is set at 448.15 K (175 °C). Keep airframe materials clear of the chamber case. Clearance and radiation shielding: **(v2.1)** thermal FEA.

## 6. Pressure relief and overboard vents

Each discharge path needs an airframe port. Port size and routing: **(v2.1)** with Lauty.

| Device | Setting | Discharge |
|---|---|---|
| Tank passive relief (valve and/or burst disc) | below proof; trapped-liquid relief ≤ 7.5 MPa; tank MEOP 7.0 MPa | overboard, away from the plume and the baro ports |
| Secondary rupture disc on the valve-outlet block FS-01 | 9.5 MPa ±5 % | overboard |
| N2O fill and vent | ground interface, TO-DEFINE | overboard; remote vent on the pad (founder decision pending) |
| Roll RCS provision | 4 nozzle bosses on the body wall (2 tangential couples) and a tank ullage port. Valves fitted only if T1 measures more than 0.02 N·m of roll torque | LEAD 2026-10-12 |
| Head-end bleed (A1 provision, lead 2026-10-13) | forced purge of the valve-to-seat segment before an in-flight relight, <= 76 g N2O per purge (2.5 s of flow at about 31 g/s, 1.0 mm equivalent; CHANGELOG 160, 164); two NC valves in series | overboard port RESERVED in the airframe (size and station (v2.1)), clear of the drogue line, baro ports and the aft keep-out cone; fitted for A1 unless the CF-4 cold flow shows it is not needed. The vent must be BALANCED (opposed pair) or AXIAL: a single lateral jet (about 2 N) tilts the vehicle 1.2-1.9 deg at relight and adds trapped vapour |

The stand-only aft TC-09S DN32 burst disc is a test-cell item and does not fly. The S1 vent is internal to the module.

## 7. Keep-out zones

- **Aft plume cone:** no leg, foot, fin, line or antenna inside the cone r(x) = 0.010 + x·tan(44.57°) aft of the nozzle exit plane, for x ≤ 0.194 m (DERIVED, gnc.json; it is a layout keep-out, not a thermal result).
- **Ground plume impingement:** NOT COVERED. There is no ground-plane plume case yet, and the hover wall jet onto the feet is open (Combustion / plume CFD request).
- **Gimbal sweep:** the engine zone of section 2 must hold the 140 mm bore over the whole sweep. No airframe stringers, harness or brackets may intrude into it.

## 8. Recovery (A1)

| Item | Value |
|---|---|
| Drogue | ASSUMED 0.9 m class, CdA 0.5 m² (verified band 0.425–0.575 m²). Nose bay, ejected forward along the axis at apogee |
| Line | Single line at the nose tip on the vehicle axis. A swivel is REQUIRED; the 6-DOF assumes no roll torque. No bridle leg, line or lanyard runs toward the engine bay |
| Release | On Pc-confirmed relight, under the full steady line load. Released mass ≤ 0.78 kg (0.35 kg budgeted), so the released parts fall slower than the vehicle |
| Descent at relight | About 22 m/s |
| Canopy oscillation | The angle between the body axis and the specific force at relight must stay ≤ 2° (retained-vapour design attitude, lead 2026-10-13). The 6-DOF models a quasi-steady canopy (p99 0.63°); real pendulum swing adds directly. Choose a low-oscillation canopy (cross or ribbon class ASSUMED) and provide swing data (drop test or literature) |
| Backup parachute | Ledger item 0.5–1.0 kg; design TO-DEFINE |
| Deployment-to-inflation delay, opening load, bay volume, ejection method | Recovery / airframe (Lauty) |

## 9. Fins

- **Fin set:** 4 aft fins, span 0.12 m, root chord 0.20 m, tip chord 0.10 m, 3 mm GF/PETG, about 0.30 kg.
- **Static margin rule:** Lauty's fins must give at least the verified nose-first static margin of 0.725 cal at the liftoff CG. Otherwise GNC re-checks the coast.
- **Cant:** same-sense fin cant ≤ 0.162°.

## 10. Legs and touchdown

- **Touchdown envelope:** vertical ≤ 2 m/s, lateral ≤ 0.5 m/s, tilt ≤ 5°, tilt rate ≤ 10°/s (REQ).
- **Leg values as simulated (ASSUMED):**
  - 4 legs, stroke ≥ 0.10 m;
  - k 2,500 N/m and c 120 N·s/m per leg;
  - foot radius 0.40 m;
  - ground friction μ 0.3–0.7;
  - deployed at the relight command on A1, fixed on B hops.
  - Lauty designs the legs; GNC re-runs on the real values.
- **Pad slope: TO-DEFINE.** With the assumed legs at the criteria corner, a 3.4° downhill slope uses up the tip-over margin (5.1° with the stroke-lowered CG). With lateral speed alone the limit is 9.3° (REV-GNC-1 RG-14, rigid-body energy check). The landing pad and leg design must state the slope they accept.

## 11. Electrical

- **ARM rule:** ARM only if the predicted both-servo-stall plug voltage is ≥ 6.6 V and the battery at rest is ≥ 8.1 V (LEAD 2026-10-12).
- **Harness resistances:** source and branch resistance against the 15 / 20 mΩ assumptions, verified in B-PWR-1/2.
- **Harness across the gimbal:** routing TO-DEFINE (ICD-13). Connector locations: Electronics v2.

## 12. Open items for this ICD

| # | Item | Owner |
|---|---|---|
| ICD-1 | Thrust-ring bolt pattern, wall bearing and pull-out at 876 N plus lateral and moment loads | Mechanical (v2.1) / Lauty |
| ICD-2 | Main-valve module envelope and mass at the zone top | Mechanical (v2.1) |
| ICD-3 | Upper-bay vent area and station; baro-port placement | Lauty with Mechanical |
| ICD-4 | Relief and vent port routing (tank relief, 9.5 MPa disc line, fill/vent) | Mechanical / Lauty |
| ICD-5 | Tank station and mounting; heater and insulation interface | Mechanical / Lauty |
| ICD-6 | Launch-site bay temperature limit | Founders |
| ICD-7 | Pad slope specification and leg design | Lauty |
| ICD-8 | Drogue opening load, bay volume, ejection method, swivel and release fitting | Lauty |
| ICD-9 | Ground plume impingement on the feet | Combustion |
| ICD-10 | Airframe first bending mode ≥ 10 Hz on the real tube | Lauty, then GNC re-check |
| ICD-11 | Engine hardware mass and CG from CAD v3.4 | Mechanical (v2.1) |
| ICD-12 | Wall-line P-clips (3, at z 110 / 170 / 230 mm engine frame) and the coil fixed-end clamp near az 219.5°, z ≈ 71 mm: clamp type, wall fastening, loads (hose end reaction up to 32 N and 1.3 N·m at the 8° stop for EI 0.25) | Lauty with Mechanical |
| ICD-13 | Harness routing across the gimbal | Electronics / Mechanical, TO-DEFINE |
| ICD-14 | Head-end bleed overboard port (A1 provision): size, station, routing; balanced or axial vent | Mechanical (v2.1) / Lauty |
| ICD-15 | Drogue canopy type and oscillation data at the relight condition (≤ 2° design attitude) | Lauty |
