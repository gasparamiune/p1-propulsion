# Combustion handback summary (2026-10-12)

SUMMARY: Combustion and Propulsion, ARGOS H1 engine, 2026-10-12 (handback; the two report texts follow below the summary)

Interface: interfaces/combustion.json v2.3 (sha256/16 d9ec54fbf450e243; CHANGELOG line 45) at this handback; current interface v2.4 469727032124329f (CHANGELOG 169). Plume wording (RC-10, RC-11, RC-19) corrected by the lead on 2026-10-13 to match plume REPORT v2.2b. Nothing in this handback is MEASURED. Every number carries a tag in the reports (SIM, CEA, DERIVED, ASSUMED, LITERATURE or LEAD).

**Gas path** at 500 N sea level, 20 C tank, initial port (SIM):
- Pc 25.0 bar.
- mdot 0.264 kg/s (oxidiser 0.241, fuel 0.0231).
- O/F 10.4; the A1 mean is 8.9 and the 12.5 % floor is 4.1.
- Isp_SL 193.1 s delivered (eta_c* 0.92 and eta_cf 0.975, both ASSUMED); c* 1401 m/s; T0 2757 K.

**Pressure limits** (LEAD):
- Software cap 25 bar; abort about 30 bar.
- Chamber MEOP 45 bar; a pintle stuck full open gives 30.7-42.9 bar.
- Proof 67.5 bar; tank MEOP 70 bar.

**Nozzle:** Dt 13.72 mm, De 19.41 mm, eps 2.0 (45 deg convergent, 15 deg cone, lambda 0.983). pe/pa is 3.2 at 100 %. Insert is fine-grain graphite of at least 1.80 g/cm3; grade TO-QUOTE (Sønderborg DK-6400).

**Grain:** FDM ABS at 100 % infill, OD 53.5 x L 230 mm (S230), centred straight 25 mm port, web 14.25 mm, 0.404 kg; L* 1.92 m.
- Regression law r = 5.77e-5 Gox^0.5 is ASSUMED, band x0.6-1.5. No verified N2O/ABS law exists.

**Injector:** servo pintle, 5.5 mm seat, 15 deg needle, 4 mm stroke, 3 mm stem.
- Cd 0.70 ASSUMED (range 0.6-0.8); Dyer NHNE flow model.
- Lift 1.92 mm at 100 % and 0.21 mm at 12.5 %; dP/Pc 0.91 at 100 % to 10.4 at 12.5 %.

**Feed:**
- NC isolation valve, Cv >= 3, off the gimbal; -6 hose.
- Filter <= 15 um at Cv >= 2.2; line drop 117 kPa against a 270 kPa budget.
- Trapped-liquid relief <= 7.5 MPa.
- Priming rule: 0.10 mm pintle bleed lift before the isolation valve opens.

**Throttle floor:**

| Level | dP/Pc | Chug gain margin |
|---|---|---|
| 25 % (required): met | 5.8 | 23.7 at 10 ms delay |
| 20 % (target): met | 7.1 | 27.2 |
| 12.5 % (stretch): met in the model | 10.4 | 38.6 at 10 ms / 172 at 1 ms |

- At 12.5 %: Pc 4.37 bar, 62.5 N, incipient lip separation, side load about 0 N.
- Not modelled: hybrid low-frequency (thermal-lag) modes at 0.3-2 Hz, and combustion efficiency at the low oxidiser flux of the floor (G_ox 25-74 kg/m2s). Static fire T3 with 1 kHz Pc logging settles both.

**Throttle choice:** variable-area pintle at the head end plus a separate NC isolation valve. In the trade, upstream throttle valves leave vapour quality 0.27-0.36 at <= 25 % throttle.
- Plant: gain K_h 7.6 -> 20.1 bar/mm (x2.7 down to the floor), tau_c 4 ms.
- A slow fuel mode of 5-9 % has tau_f 0.11-0.53 s. The Pc loop must be closed and gain-scheduled.

**Pintle v2.3** (adopted by the lead):
- The seat gap meters at every lift, so a closing pressure force persists: +115 N seated at 70 bar; -38 to +82 N in hot fire.
- The S3 spring on the PTFE guide (mu 0.20) failed the opening check C2 (1.28-1.47 against 1.5).
- Rolling guide with 0.25 N m + 0.12 N m/rad: C2 1.62 under L1 and 1.62 under L2; closing assist at MEOP 0.108 N m.
- Seat: 17-4PH, needle H900 / seat H1150. Land pressure <= 331 MPa (46 % of Fty, elastic). Blued contact band >= 0.24 mm; PFPE film.
- The 15 deg seat self-locks if seat friction exceeds 0.27; a break-out test is required. A polymer seat is infeasible.
- Rod seal: spring-energised PTFE class (vendor classes TO-VERIFY). Leak rate only by test; NC valve closed during coasts.

**Ignition:** spark-ignited N2O/propane torch at 3 bar, O/F 5.5, 3.0 kW.
- Per start: 0.055 g propane, 0.30 g N2O, 15 J; >= 3 starts.
- The ignition lift is held until Pc > 3 bar. Arc-ABS remains a bench research option.
- Model relight reaches 10 % / 90 % thrust at 0.10 / 0.29 s.

**Tank:** self-pressurised, 2.00 kg / 3.17 L at 15-25 C; N2 supercharge not baselined.
- From full, 500 N is held for 4.1-7.0 s.
- Settling before relight is met: A2 has 2.2 s settled against 0.5 s needed.

**Throat erosion per flight** (gnc v1 cycles):
- Nominal 0.020-0.057 mm (dAt/At 0.6-1.7 %); conservative 0.12-0.24 mm (3.6-7.2 %); literature-scaled 0.03-0.40 mm.
- Replace the insert at dAt/At 5 %: 1-4 A1 flights per insert.

**Heat flux:**
- Peak 21.9 MW/m2 at the throat (Bartz, Tw 600 K, h_g 10.3 kW/m2K, T_aw 2737 K, uncertainty x0.7-1.3).
- Cold-wall start 27-32 MW/m2. Gas and soot radiation 0.12-0.49 MW/m2 (emissivity 0.05-0.2 ASSUMED).

**Plume CFD:** own two-species HLLC/MUSCL solver plume2s, plus OpenFOAM rhoCentralFoam. Domain 45 x 12 De. Runs at the v1 point (O/F 7.76) and the v2 point (O/F 10.4).
- The jet is under-expanded (pe/pa 3.24) with Mach reflection. A small Mach disk sits at x 2.68 De (CFD band 2.58-2.77 De); the Lewis-Carlson value, 2.66 De, lies inside that band.
- Shock cells are 3.96 De (first) to 4.10 De (mean of three). Prandtl-Pack/Tam gives 4.82 De (-15 to -18 %), but that correlation is used here outside its weak-shock range.
- Potential core 14.9 De. It changes to 5.7-30 De with eddy viscosity x2 / x0.5, so it depends on the turbulence model.

**CFD validation:**
- Thrust 500.8 N against 505.8 N from 1-D theory (-0.98 % fine grid; -1.08 % coarse, -1.09 % at the v2 point: about 1 %); mdot -0.65 %. All levels at the v1 point (Pc 24.99 bar, O/F 7.76).
- Three levels (20k/80k/320k cells, all at 3.25 ms): thrust grid-insensitive within +/-0.15 % with no observed convergence (R 1.09; 3x deviation bound, not a GCI); mdot GCI 0.11 %. The fine level restarts from the medium state, so it is not independent beyond about 8-10 De.
- Every other quantity lies inside the 2-sigma temporal scatter of the unsteady jet; bands are reported instead.
- OpenFOAM inviscid differs by -1.2 % in exit-plane thrust. Code-to-code comparison is valid only upstream of about 8 De, because the OpenFOAM runs stopped at the 2 h limit.
- A single-gas model leaves thrust unchanged but gives axis temperature -15 % at 20 De and -30 % at 40 De.

**Afterburning** (fast-chemistry bound):
- 172-182 K at O/F 7.76 (extrapolated f_ext 181.8 K; not resolvable against the time scatter).
- About 0 K at the v2 point, O/F 10.4 (oxidiser-rich exhaust); stream-B bound: plume maximum 3011 K against 2705 K.
- 1322-1476 K at the fuel-rich 12.5 % floor. The floor CFD gives 61.8 N with a strong normal shock at 0.65 De.

**Images and animations:**
- Synthetic Abel-projected photo (QUALITATIVE); Blender renders (ARTISTIC).
- startup_500N_medium and sweep_100_20_12p5_coarse, as MP4 and GIF. The sweep is time-compressed.

**Files** (hub /home/claude/work/shared-fallback/engine/):
- 02-combustion: src (42 scripts); data (thermo, v2 maps, duty-cycle histories, thermal BC CSVs, as-published interfaces); figs/v2 (26 PNG).
- 05-plume-cfd: ownruns, openfoam_cases, fluent-crosscheck, validation, anim, blender, scripts (458 files, 202 MB).
- interfaces/combustion.json v2.3. Heavy runs live in /home/claude/work/combustion.

**Failures kept as evidence:**
- The v1 helical grain burned through on B1 (web -3.12 mm at 15 s); replaced by the straight S230 grain.
- eps 3 separates at <= 20 %.
- Mechanical's v2-v2.2 needle force law is unconservative for opening; under the corrected law S3 failed C2, hence the rolling guide.
- The 0.08 s pintle stroke time was retired (no basis). Head-end thermal run 1 and actuator run 1 are superseded; afterburn models v1 and v2 are superseded.
- FAILURE-CFD-01 (OpenFOAM function objects) and FAILURE-CFD-02 (mixing length with local time stepping).
- Validation v2.0 compared grid levels at different times, and the first v2.1 run gave a negative GCI.
- Runs were lost on the broken mount. OpenFOAM stopped at 2 h with the jet front at 11-18 De. The v2.0 exit-plane integral read 2.6 % low.

**Open issues:**
- OI-1: gnc v2 A2/B1 need 2.54/2.44 kg of N2O against the 2.00 kg tank.
- OI-2: GNC Monte Carlo still to run on the v2 map.
- OI-4: post-chamber case reaches 220-426 C against the 192 C aft-land limit.
- OI-5: retainer soak. A 0.15 kg aluminium retainer reaches 588-920 K, above the 240 C aluminium lip allowable at 51 MPa. Steel needs its own temperature-dependent allowable.
- OI-6: Pc transducer range 34.5 bar is below MEOP.
- OI-7: CAD still shows a 40 um screen.
- OI-10: B1 web is 1.31 mm at x1.5 regression.
- OI-15: the head is 37-66 C at relight against the 50 C servo-mount limit.
- Pintle rework after the thermal FEA (Mechanical v2.3).
- Internal mismatch in v2.3: igniter.sequence.relight says the isolation valve may stay open between burns. The lead rule (closed during coasts, pintle_actuator.lead_decision_v2p3) governs; fix in the next revision.

**Unknowns:**
- Regression law (a, n).
- Two-phase Cd.
- eta_c*, including the 1-2 % liquid-N2O c* penalty.
- Low-flux combustion at the floor.
- Ignition delay.
- Graphite kinetics and grade.
- Roll torque and thrust misalignment.
- Needle force versus lift.
- Seat friction, leak rate and break-out.

**Review:** no independent review yet (Por revisar). The reviewer's criteria and verdict go to public/engineering/supervision.json.
