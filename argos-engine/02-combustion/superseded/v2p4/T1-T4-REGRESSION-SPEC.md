# T1-T4 regression-rate measurement and law form (RG-03)

Combustion v2.4, 2026-10-13. Same text as 02-combustion REPORT v2.4 §10.4, published standalone for the founders (coordinator after CHANGELOG 168). Physical execution: the founders; reduction: Combustion. Digital specification only.

Why it matters: the B1 gate uses a measured a. If the true law is the total-flux form, the reviewer finds 19 of 500 runs ending below 1 mm of web with the burn limit active (truth k = 1.149 a), and the lead's rule becomes "current rule OR a_meas >= 1.25 -> change grain" (CHANGELOG line 168). Which law applies is decided by this measurement.

**What is measured** (founders execute; Combustion reduces):
- Grain mass before and after each firing (balance resolution <= 0.1 g), dried to constant mass.
- Port diameter at six stations, x/L = 0.10, 0.30, 0.50, 0.70, 0.90 and 0.97 from the head end, on two orthogonal diameters (bore gauge, resolution <= 0.02 mm), or a 3-D scan of the bore with the same stations extracted. x/L 0.97 is where the total-flux law burns through first (§4.6, `b1_axial_law_v2p4.json`).
- Time histories: Pc at 1 kHz, oxidiser mass flow from the tank load cell and P_feed, thrust, burn time from the Pc rise and fall (E2 to the tail-off at 10 % of the run Pc).
- At least two oxidiser fluxes: T1 at 100 % and the T2 throttle steps, so that n is fitted rather than assumed.

**Reduction.**
- Mean regression per station: r_i = (D_after,i - D_before,i) / (2 t_burn); the mass loss checks the integral (sum over stations against the weighed loss, within 5 %, ASSUMED).
- Both laws are fitted to the station data with the measured oxidiser-flux history: oxidiser-flux r = a G_ox^n (nearly uniform along x) and total-flux r = a G^n with G = (mdot_ox + mdot_f(x)) / A_port (rising toward the aft end). At O/F 4-6 and n 0.5 the total-flux form predicts an aft-to-head ratio r(0.97)/r(0.10) of about 1.08-1.12 against about 1.0.
- Law decision: the total-flux form is declared when the measured aft-to-head ratio exceeds the oxidiser-flux prediction by more than twice its measurement uncertainty, on at least two firings. The head-end station (x/L 0.10) is checked for injector-spray effects against x/L 0.30; if they differ by more than the uncertainty, x/L 0.30 is used as the head reference.
- a_meas for the B1 gate: the multiplier on the nominal model law (anchored at r(300 kg/m2 s) = 1 mm/s, §4.1) that reproduces the regression measured at x/L 0.97. Evaluated at the aft station, a total-flux truth shows up as a larger a_meas (about x1.10-1.15), so the gate errs on the safe side whichever law holds. The head-station multiplier is reported beside it.
- The burn limit for GNC is recomputed with 1.1 x a_meas and the declared law form (§4.6).

Uncertainty to report with every a_meas: bore-gauge and station-position error, burn-time definition, and the oxidiser-flux history from the load cell (TO-VERIFY at T1).
