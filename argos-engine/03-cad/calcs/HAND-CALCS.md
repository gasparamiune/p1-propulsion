# Hand calculations v2 (DERIVED, `calcs/hand_calcs.py`, 2026-10-12)

Chamber MEOP **45 bar** (lead decision 2026-10-12, Combustion pintle full-stroke failure case), proof **67.5 bar**, blocked-nozzle bound **63.1 bar** (no yield at temperature). CAD v3 geometry. v1 (31 bar, CAD v2) kept as `hand_calcs_v1.json`.

MS = allowable/(SF x applied) - 1. Allowables from `04-fea/src/engmat.py` (spec minimums; temperature knock-down via T_allow). LC4/BN rows: SF 1.0 on yield (no yield); '-' = not applicable. **T_allow** = highest part temperature at which the row keeps MS >= 0; the LC5 thermal FEA must show the part below it.

| Check | Applied | Allow. yield | Allow. ult | SF y/u | MS y (20 C) | MS u (20 C) | T_allow C | Note |
|---|---|---|---|---|---|---|---|---|
| Case full wall 63.50/57.15 [LC1 25.0 bar]: von Mises at bore (Lame + end load) | 22.8 MPa | 240 | 260 | 1.5/2.0 | 6.02 | 4.71 | 256 | hoop 23.8, axial 10.7, radial -2.5 MPa; wall 3.175 mm |
| Case fwd seal land 57.25 bore [LC1 25.0 bar]: von Mises at bore (Lame + end load) | 23.1 MPa | 240 | 260 | 1.5/2.0 | 5.92 | 4.62 | 255 | hoop 24.2, axial 10.9, radial -2.5 MPa; wall 3.125 mm |
| Case collar groove 62.50 (pivot plane) [LC1 25.0 bar]: von Mises at bore (Lame + end load) | 26.4 MPa | 240 | 260 | 1.5/2.0 | 5.06 | 3.92 | 250 | hoop 28.0, axial 12.8, radial -2.5 MPa; wall 2.675 mm |
| Case aft seal land 61.0 (above the gland) [LC1 25.0 bar]: von Mises at bore (Lame + end load) | 35.5 MPa | 240 | 260 | 1.5/2.0 | 3.51 | 2.66 | 236 | hoop 38.4, axial 20.4, radial -2.5 MPa; wall 1.925 mm |
| Case aft thread root M63x1.5 d3 61.16 [LC1 25.0 bar]: von Mises at bore (Lame + end load) | 34.2 MPa | 240 | 260 | 1.5/2.0 | 3.68 | 2.8 | 238 | hoop 36.9, axial 19.6, radial -2.5 MPa; wall 2.005 mm |
| Case full wall 63.50/57.15 [LC2 45.0 bar]: von Mises at bore (Lame + end load) | 41 MPa | 240 | 260 | 1.5/2.0 | 2.9 | 2.17 | 227 | hoop 42.9, axial 19.3, radial -4.5 MPa; wall 3.175 mm |
| Case fwd seal land 57.25 bore [LC2 45.0 bar]: von Mises at bore (Lame + end load) | 41.6 MPa | 240 | 260 | 1.5/2.0 | 2.84 | 2.12 | 226 | hoop 43.6, axial 19.5, radial -4.5 MPa; wall 3.125 mm |
| Case collar groove 62.50 (pivot plane) [LC2 45.0 bar]: von Mises at bore (Lame + end load) | 47.6 MPa | 240 | 260 | 1.5/2.0 | 2.36 | 1.73 | 216 | hoop 50.4, axial 23.0, radial -4.5 MPa; wall 2.675 mm |
| Case aft seal land 61.0 (above the gland) [LC2 45.0 bar]: von Mises at bore (Lame + end load) | 63.9 MPa | 240 | 260 | 1.5/2.0 | 1.5 | 1.03 | 192 | hoop 69.1, axial 36.8, radial -4.5 MPa; wall 1.925 mm |
| Case aft thread root M63x1.5 d3 61.16 [LC2 45.0 bar]: von Mises at bore (Lame + end load) | 61.6 MPa | 240 | 260 | 1.5/2.0 | 1.6 | 1.11 | 196 | hoop 66.5, axial 35.3, radial -4.5 MPa; wall 2.005 mm |
| Case full wall 63.50/57.15 [LC4 67.5 bar]: von Mises at bore (Lame + end load) | 61.5 MPa | 240 | 260 | 1.0/None | 2.9 | - | 230 | hoop 64.3, axial 28.9, radial -6.8 MPa; wall 3.175 mm |
| Case fwd seal land 57.25 bore [LC4 67.5 bar]: von Mises at bore (Lame + end load) | 62.5 MPa | 240 | 260 | 1.0/None | 2.84 | - | 229 | hoop 65.4, axial 29.3, radial -6.8 MPa; wall 3.125 mm |
| Case collar groove 62.50 (pivot plane) [LC4 67.5 bar]: von Mises at bore (Lame + end load) | 71.3 MPa | 240 | 260 | 1.0/None | 2.36 | - | 221 | hoop 75.6, axial 34.6, radial -6.8 MPa; wall 2.675 mm |
| Case aft seal land 61.0 (above the gland) [LC4 67.5 bar]: von Mises at bore (Lame + end load) | 95.9 MPa | 240 | 260 | 1.0/None | 1.5 | - | 200 | hoop 103.7, axial 55.2, radial -6.8 MPa; wall 1.925 mm |
| Case aft thread root M63x1.5 d3 61.16 [LC4 67.5 bar]: von Mises at bore (Lame + end load) | 92.4 MPa | 240 | 260 | 1.0/None | 1.6 | - | 202 | hoop 99.7, axial 52.9, radial -6.8 MPa; wall 2.005 mm |
| Case full wall 63.50/57.15 [BN 63.1 bar]: von Mises at bore (Lame + end load) | 57.5 MPa | 240 | 260 | 1.0/None | 3.17 | - | 234 | hoop 60.1, axial 27.0, radial -6.3 MPa; wall 3.175 mm |
| Case fwd seal land 57.25 bore [BN 63.1 bar]: von Mises at bore (Lame + end load) | 58.4 MPa | 240 | 260 | 1.0/None | 3.11 | - | 233 | hoop 61.1, axial 27.4, radial -6.3 MPa; wall 3.125 mm |
| Case collar groove 62.50 (pivot plane) [BN 63.1 bar]: von Mises at bore (Lame + end load) | 66.7 MPa | 240 | 260 | 1.0/None | 2.6 | - | 225 | hoop 70.7, axial 32.3, radial -6.3 MPa; wall 2.675 mm |
| Case aft seal land 61.0 (above the gland) [BN 63.1 bar]: von Mises at bore (Lame + end load) | 89.6 MPa | 240 | 260 | 1.0/None | 1.68 | - | 204 | hoop 96.9, axial 51.6, radial -6.3 MPa; wall 1.925 mm |
| Case aft thread root M63x1.5 d3 61.16 [BN 63.1 bar]: von Mises at bore (Lame + end load) | 86.4 MPa | 240 | 260 | 1.0/None | 1.78 | - | 206 | hoop 93.2, axial 49.5, radial -6.3 MPa; wall 2.005 mm |
| Fwd closure 8xM5 A4-70 [LC1 25.0 bar]: screw shear at thread root (d3=4.019 mm) | 72.9 MPa | 260 | 420 | 1.5/2.0 | 1.37 | 1.88 | - | V/screw=925 N incl. x1.15 sharing; F_end=6434 N |
| Fwd closure 8xM5 A4-70 [LC1 25.0 bar]: bearing in case wall | 59.2 MPa | 336 | 416 | 1.5/2.0 | 2.78 | 2.51 | 350 | e/D=2.40 (>=2 for the bearing ratios used) |
| Fwd closure 8xM5 A4-70 [LC1 25.0 bar]: shear-out of case to tube end | 15.6 MPa | 138 | 156 | 1.5/2.0 | 4.93 | 4.01 | 350 | e=12.0 mm [R4] |
| Fwd closure 8xM5 A4-70 [LC1 25.0 bar]: case net section at inboard screw row (8 holes, axial) | 14.1 MPa | 240 | 260 | 1.5/2.0 | 10.3 | 8.2 | 350 | net axial 14.1 MPa; upper bound with full hoop superposed (not physical, row is outboard of seals): VM 21.0 MPa |
| Fwd closure 8xM5 A4-70 [LC1 25.0 bar]: bearing of screw on closure thread (Le=6.0 mm) | 30.8 MPa | 336 | 416 | 1.5/2.0 | 6.27 | 5.75 | 350 |  |
| Fwd closure 8xM5 A4-70 [LC2 45.0 bar]: screw shear at thread root (d3=4.019 mm) | 131 MPa | 260 | 420 | 1.5/2.0 | 0.318 | 0.599 | - | V/screw=1665 N incl. x1.15 sharing; F_end=11584 N |
| Fwd closure 8xM5 A4-70 [LC2 45.0 bar]: bearing in case wall | 107 MPa | 336 | 416 | 1.5/2.0 | 1.1 | 0.952 | 350 | e/D=2.40 (>=2 for the bearing ratios used) |
| Fwd closure 8xM5 A4-70 [LC2 45.0 bar]: shear-out of case to tube end | 28 MPa | 138 | 156 | 1.5/2.0 | 2.29 | 1.78 | 350 | e=12.0 mm [R4] |
| Fwd closure 8xM5 A4-70 [LC2 45.0 bar]: case net section at inboard screw row (8 holes, axial) | 25.4 MPa | 240 | 260 | 1.5/2.0 | 5.29 | 4.11 | 350 | net axial 25.4 MPa; upper bound with full hoop superposed (not physical, row is outboard of seals): VM 37.8 MPa |
| Fwd closure 8xM5 A4-70 [LC2 45.0 bar]: bearing of screw on closure thread (Le=6.0 mm) | 55.5 MPa | 336 | 416 | 1.5/2.0 | 3.04 | 2.75 | 350 |  |
| Fwd closure 8xM5 A4-70 [LC4 67.5 bar]: screw shear at thread root (d3=4.019 mm) | 197 MPa | 260 | 420 | 1.0/None | 0.318 | - | - | V/screw=2498 N incl. x1.15 sharing; F_end=17376 N |
| Fwd closure 8xM5 A4-70 [LC4 67.5 bar]: bearing in case wall | 160 MPa | 336 | 416 | 1.0/None | 1.1 | - | 350 | e/D=2.40 (>=2 for the bearing ratios used) |
| Fwd closure 8xM5 A4-70 [LC4 67.5 bar]: shear-out of case to tube end | 42.1 MPa | 138 | 156 | 1.0/None | 2.29 | - | 350 | e=12.0 mm [R4] |
| Fwd closure 8xM5 A4-70 [LC4 67.5 bar]: case net section at inboard screw row (8 holes, axial) | 38.2 MPa | 240 | 260 | 1.0/None | 5.29 | - | 350 | net axial 38.2 MPa; upper bound with full hoop superposed (not physical, row is outboard of seals): VM 56.7 MPa |
| Fwd closure 8xM5 A4-70 [LC4 67.5 bar]: bearing of screw on closure thread (Le=6.0 mm) | 83.3 MPa | 336 | 416 | 1.0/None | 3.04 | - | 350 |  |
| Fwd closure 8xM5 A4-70 [BN 63.1 bar]: screw shear at thread root (d3=4.019 mm) | 184 MPa | 260 | 420 | 1.0/None | 0.411 | - | - | V/screw=2334 N incl. x1.15 sharing; F_end=16238 N |
| Fwd closure 8xM5 A4-70 [BN 63.1 bar]: bearing in case wall | 149 MPa | 336 | 416 | 1.0/None | 1.25 | - | 350 | e/D=2.40 (>=2 for the bearing ratios used) |
| Fwd closure 8xM5 A4-70 [BN 63.1 bar]: shear-out of case to tube end | 39.3 MPa | 138 | 156 | 1.0/None | 2.52 | - | 350 | e=12.0 mm [R4] |
| Fwd closure 8xM5 A4-70 [BN 63.1 bar]: case net section at inboard screw row (8 holes, axial) | 35.7 MPa | 240 | 260 | 1.0/None | 5.73 | - | 350 | net axial 35.7 MPa; upper bound with full hoop superposed (not physical, row is outboard of seals): VM 53.0 MPa |
| Fwd closure 8xM5 A4-70 [BN 63.1 bar]: bearing of screw on closure thread (Le=6.0 mm) | 77.8 MPa | 336 | 416 | 1.0/None | 3.32 | - | 350 |  |
| Aft closure M63x1.5 x 14 [LC1 25.0 bar]: external thread (case) stripping, A_s 1551 mm2 | 4.71 MPa | 138 | 156 | 1.5/2.0 | 18.6 | 15.6 | 350 | F 7304 N, Le 14 mm, uniform load share assumed (first-thread peak in FEA) |
| Aft closure M63x1.5 x 14 [LC1 25.0 bar]: internal thread (closure) stripping, A_n 2007 mm2 | 3.64 MPa | 138 | 156 | 1.5/2.0 | 24.4 | 20.4 | 350 |  |
| Aft closure M63x1.5 x 14 [LC2 45.0 bar]: external thread (case) stripping, A_s 1551 mm2 | 8.48 MPa | 138 | 156 | 1.5/2.0 | 9.88 | 8.2 | 292 | F 13151 N, Le 14 mm, uniform load share assumed (first-thread peak in FEA) |
| Aft closure M63x1.5 x 14 [LC2 45.0 bar]: internal thread (closure) stripping, A_n 2007 mm2 | 6.55 MPa | 138 | 156 | 1.5/2.0 | 13.1 | 10.9 | 314 |  |
| Aft closure M63x1.5 x 14 [LC4 67.5 bar]: external thread (case) stripping, A_s 1551 mm2 | 12.7 MPa | 138 | 156 | 1.0/None | 9.88 | - | 292 | F 19727 N, Le 14 mm, uniform load share assumed (first-thread peak in FEA) |
| Aft closure M63x1.5 x 14 [LC4 67.5 bar]: internal thread (closure) stripping, A_n 2007 mm2 | 9.83 MPa | 138 | 156 | 1.0/None | 13.1 | - | 314 |  |
| Aft closure M63x1.5 x 14 [BN 63.1 bar]: external thread (case) stripping, A_s 1551 mm2 | 11.9 MPa | 138 | 156 | 1.0/None | 10.6 | - | 298 | F 18435 N, Le 14 mm, uniform load share assumed (first-thread peak in FEA) |
| Aft closure M63x1.5 x 14 [BN 63.1 bar]: internal thread (closure) stripping, A_n 2007 mm2 | 9.19 MPa | 138 | 156 | 1.0/None | 14.1 | - | 350 |  |
| Aft lip t 6.0 [LC2 45.0 bar] UPPER bound: uniform gasket pressure, bending at r 24.0 | 33.7 MPa | 240 | 260 | 1.5/2.0 | 3.74 | 2.85 | 239 | F 7477 N (firing: P x pi (r_bore^2 - r_t^2), divergent relief ignored); Kirchhoff plate a 24 clamped, b 15 free; t/span 0.69 (thick: FEA governs) |
| Aft lip t 6.0 [LC2 45.0 bar] LOWER bound: rigid insert, load at the lip root: peak shear | 12.4 MPa | 138 | 156 | 1.5/2.0 | 6.45 | 5.29 | 258 | 1.5 x mean shear F/(2 pi a t) |
| Aft lip t 6.0 [LC4 67.5 bar] UPPER bound: uniform gasket pressure, bending at r 24.0 | 55.1 MPa | 240 | 260 | 1.0/None | 3.36 | - | 236 | F 12215 N (proof with a solid dummy insert: P x pi r_bore^2); Kirchhoff plate a 24 clamped, b 15 free; t/span 0.69 (thick: FEA governs) |
| Aft lip t 6.0 [LC4 67.5 bar] LOWER bound: rigid insert, load at the lip root: peak shear | 20.2 MPa | 138 | 156 | 1.0/None | 5.84 | - | 254 | 1.5 x mean shear F/(2 pi a t) |
| Aft lip t 6.0 [BN 63.1 bar] UPPER bound: uniform gasket pressure, bending at r 24.0 | 51.5 MPa | 240 | 260 | 1.0/None | 3.66 | - | 240 | F 11415 N (throat blocked: P x pi r_bore^2); Kirchhoff plate a 24 clamped, b 15 free; t/span 0.69 (thick: FEA governs) |
| Aft lip t 6.0 [BN 63.1 bar] LOWER bound: rigid insert, load at the lip root: peak shear | 18.9 MPa | 138 | 156 | 1.0/None | 6.32 | - | 256 | 1.5 x mean shear F/(2 pi a t) |
| Graphite insert top edge (bore r 16.0) [LC1 25.0 bar] DESIGN (vented OD gap): |compressive| hoop | 2.5 MPa | - | 78 | None/2.0 | - | 14.6 | - | 4 vent grooves keep the sleeve gap at chamber pressure: hoop = -P |
| Graphite insert top edge (bore r 16.0) [LC1 25.0 bar] BOUND (OD gap not pressurised): hoop tension | 8.11 MPa | - | 25 | None/2.0 | - | 0.541 | - | not the design condition (vent grooves); kept as the bound if the grooves char-block; start-transient thermal stress governs (FEA LC5) |
| Graphite throat section [LC1 25.0 bar] DESIGN (vented OD gap): |compressive| hoop | 2.5 MPa | - | 78 | None/2.0 | - | 14.6 | - | 4 vent grooves keep the sleeve gap at chamber pressure: hoop = -P |
| Graphite throat section [LC1 25.0 bar] BOUND (OD gap not pressurised): hoop tension | 3.04 MPa | - | 25 | None/2.0 | - | 3.11 | - | not the design condition (vent grooves); kept as the bound if the grooves char-block; start-transient thermal stress governs (FEA LC5) |
| Graphite shoulder bearing on the Grafoil ring [LC1 25.0 bar] | 5.76 MPa | - | 78 | None/2.0 | - | 5.77 | - | F 4523 N (upper bound P pi r_bore^2) on 785 mm2 (sleeve share neglected) |
| Graphite insert top edge (bore r 16.0) [LC2 45.0 bar] DESIGN (vented OD gap): |compressive| hoop | 4.5 MPa | - | 78 | None/2.0 | - | 7.67 | - | 4 vent grooves keep the sleeve gap at chamber pressure: hoop = -P |
| Graphite insert top edge (bore r 16.0) [LC2 45.0 bar] BOUND (OD gap not pressurised): hoop tension | 14.6 MPa | - | 25 | None/2.0 | - | -0.144 | - | not the design condition (vent grooves); kept as the bound if the grooves char-block; start-transient thermal stress governs (FEA LC5) |
| Graphite throat section [LC2 45.0 bar] DESIGN (vented OD gap): |compressive| hoop | 4.5 MPa | - | 78 | None/2.0 | - | 7.67 | - | 4 vent grooves keep the sleeve gap at chamber pressure: hoop = -P |
| Graphite throat section [LC2 45.0 bar] BOUND (OD gap not pressurised): hoop tension | 5.47 MPa | - | 25 | None/2.0 | - | 1.29 | - | not the design condition (vent grooves); kept as the bound if the grooves char-block; start-transient thermal stress governs (FEA LC5) |
| Graphite shoulder bearing on the Grafoil ring [LC2 45.0 bar] | 10.4 MPa | - | 78 | None/2.0 | - | 2.76 | - | F 8143 N (upper bound P pi r_bore^2) on 785 mm2 (sleeve share neglected) |
| Graphite insert top edge (bore r 16.0) [LC4 67.5 bar] DESIGN (vented OD gap): |compressive| hoop | 6.75 MPa | - | 78 | None/1.0 | - | 10.6 | - | 4 vent grooves keep the sleeve gap at chamber pressure: hoop = -P |
| Graphite insert top edge (bore r 16.0) [LC4 67.5 bar] BOUND (OD gap not pressurised): hoop tension | 21.9 MPa | - | 25 | None/1.0 | - | 0.141 | - | not the design condition (vent grooves); kept as the bound if the grooves char-block; start-transient thermal stress governs (FEA LC5) |
| Graphite throat section [LC4 67.5 bar] DESIGN (vented OD gap): |compressive| hoop | 6.75 MPa | - | 78 | None/1.0 | - | 10.6 | - | 4 vent grooves keep the sleeve gap at chamber pressure: hoop = -P |
| Graphite throat section [LC4 67.5 bar] BOUND (OD gap not pressurised): hoop tension | 8.2 MPa | - | 25 | None/1.0 | - | 2.05 | - | not the design condition (vent grooves); kept as the bound if the grooves char-block; start-transient thermal stress governs (FEA LC5) |
| Graphite shoulder bearing on the Grafoil ring [LC4 67.5 bar] | 15.6 MPa | - | 78 | None/1.0 | - | 4.01 | - | F 12215 N (upper bound P pi r_bore^2) on 785 mm2 (sleeve share neglected) |
| Graphite insert top edge (bore r 16.0) [BN 63.1 bar] DESIGN (vented OD gap): |compressive| hoop | 6.31 MPa | - | 78 | None/1.0 | - | 11.4 | - | 4 vent grooves keep the sleeve gap at chamber pressure: hoop = -P |
| Graphite insert top edge (bore r 16.0) [BN 63.1 bar] BOUND (OD gap not pressurised): hoop tension | 20.5 MPa | - | 25 | None/1.0 | - | 0.221 | - | not the design condition (vent grooves); kept as the bound if the grooves char-block; start-transient thermal stress governs (FEA LC5) |
| Graphite throat section [BN 63.1 bar] DESIGN (vented OD gap): |compressive| hoop | 6.31 MPa | - | 78 | None/1.0 | - | 11.4 | - | 4 vent grooves keep the sleeve gap at chamber pressure: hoop = -P |
| Graphite throat section [BN 63.1 bar] BOUND (OD gap not pressurised): hoop tension | 7.67 MPa | - | 25 | None/1.0 | - | 2.26 | - | not the design condition (vent grooves); kept as the bound if the grooves char-block; start-transient thermal stress governs (FEA LC5) |
| Graphite shoulder bearing on the Grafoil ring [BN 63.1 bar] | 14.5 MPa | - | 78 | None/1.0 | - | 4.36 | - | F 11415 N (upper bound P pi r_bore^2) on 785 mm2 (sleeve share neglected) |
| Liner hoop, gap pressurised [LC2 45.0 bar] (balanced) | 1e-06 MPa | - | 60 | None/2.0 | - | 3.000e+07 | - | pressure on both faces: net hoop ~0; collapse only from a transient gap over-pressure (see note) |
| Tank tube MEOP 35C: von Mises at bore (Lame) | 100 MPa | 238 | 257 | 1.5/2.0 | 0.583 | 0.283 | - |  |
| Tank seal land MEOP 35C: von Mises at bore (Lame) | 102 MPa | 238 | 257 | 1.5/2.0 | 0.559 | 0.263 | - |  |
| Tank seal land at proof (no yield): von Mises at bore (Lame) | 153 MPa | 240 | 260 | 1.0/1.0 | 0.574 | 0.705 | - |  |
| Tank bulkhead screws STEEL-12.9 35C: screw shear at thread root (d3=4.773 mm) | 134 MPa | 635 | 610 | 1.5/2.0 | 2.16 | 1.28 | - | V/screw=2395 N incl. x1.15 sharing; F_end=49984 N |
| Tank bulkhead screws STEEL-12.9 35C: bearing in case wall | 128 MPa | 333 | 411 | 1.5/2.0 | 0.737 | 0.609 | - | e/D=2.00 (>=2 for the bearing ratios used) |
| Tank bulkhead screws STEEL-12.9 35C: shear-out of case to tube end | 42.6 MPa | 137 | 154 | 1.5/2.0 | 1.15 | 0.81 | - | e=12.0 mm [R4] |
| Tank bulkhead screws STEEL-12.9 35C: case net section at inboard screw row (12 holes, axial) | 69.1 MPa | 238 | 257 | 1.5/2.0 | 1.29 | 0.858 | - | net axial 69.1 MPa; upper bound with full hoop superposed (not physical, row is outboard of seals): VM 96.5 MPa |
| Tank bulkhead screws STEEL-12.9 35C: bearing of screw on closure thread (Le=9.0 mm) | 44.4 MPa | 333 | 411 | 1.5/2.0 | 4 | 3.63 | - |  |
| Tank bulkhead screws at proof (no yield): screw shear at thread root (d3=4.773 mm) | 201 MPa | 635 | 610 | 1.0/1.0 | 2.16 | 2.04 | - | V/screw=3593 N incl. x1.15 sharing; F_end=74976 N |
| Tank bulkhead screws at proof (no yield): bearing in case wall | 192 MPa | 336 | 416 | 1.0/1.0 | 0.754 | 1.17 | - | e/D=2.00 (>=2 for the bearing ratios used) |
| Tank bulkhead screws at proof (no yield): shear-out of case to tube end | 63.9 MPa | 138 | 156 | 1.0/1.0 | 1.17 | 1.44 | - | e=12.0 mm [R4] |
| Tank bulkhead screws at proof (no yield): case net section at inboard screw row (12 holes, axial) | 104 MPa | 240 | 260 | 1.0/1.0 | 1.31 | 1.51 | - | net axial 103.7 MPa; upper bound with full hoop superposed (not physical, row is outboard of seals): VM 144.8 MPa |
| Tank bulkhead screws at proof (no yield): bearing of screw on closure thread (Le=9.0 mm) | 66.5 MPa | 336 | 416 | 1.0/1.0 | 4.05 | 5.25 | - |  |
| Tank bulkhead: plate bending (simply supported), a=47.7 t=14.0 mm | 101 MPa | 238 | 257 | 1.5/2.0 | 0.563 | 0.267 | - |  |
| Tank bulkhead at proof: plate bending (simply supported), a=47.7 t=14.0 mm | 152 MPa | 240 | 260 | 1.0/1.0 | 0.578 | 0.71 | - |  |

## Forward-closure screw trade at LC2 (20 C, min MS)

8xM5: 0.32, 10xM5: 0.65, 12xM5: 0.98, 8xM6: 0.86, 12xM6: 1.79

Forward-closure joint (Al rows) keeps MS >= 0 at LC2 up to **189.0 C**.

## Retaining-lip thickness trade (BN 63.1 bar, upper bound = uniform gasket pressure)

| t mm | BN sigma MPa | T_allow BN C | LC2 sigma MPa |
|---|---|---|---|
| 4 | 115.8 | 189.0 | 75.9 |
| 5 | 74.1 | 218.0 | 48.6 |
| 6 | 51.5 | 239.5 | 33.7 |
| 8 | 29.0 | 262.5 | 19.0 |

## Liner

Unsupported long-tube collapse [R5] 3.5 bar (E 7 GPa ASSUMED), 2.5 bar at 150 C: far below MEOP. The liner relies on (i) the grain web supporting it and (ii) the case gap venting to the chamber at both liner ends (no seals on the liner). A trapped-gap over-pressure at shutdown (chamber tau ~3 ms) is a credible collapse mode near burnout when the web is thin; mitigation: 2 axial vent grooves 1 x 0.3 mm on the liner OD (CAD v3.1 note) and inspection after every firing. Not resolvable by the static FEA.

## O-ring glands [R2]

- Fwd closure piston glands 2x AS568-226 FKM 75A at proof 67.5 bar (alternative, marginal gap): depth 2.800-2.848 mm, squeeze 16.9-22.9 %, stretch 1.5-3.4 %, fill max 76 %, gap 0.156 mm (limit 0.16) -> **PASS**
- Fwd closure piston glands 2x AS568-226 FKM 90A at proof 67.5 bar (v3.1 design): depth 2.800-2.848 mm, squeeze 16.9-22.9 %, stretch 1.5-3.4 %, fill max 76 %, gap 0.156 mm (limit 0.26) -> **PASS**
- Aft closure rod gland AS568-229 FKM 75A, groove 66.7 H9, on the 61.0 f7 land at proof 67.5 bar (v3.0 groove): depth 2.865-2.917 mm, squeeze 14.9-21.1 %, stretch 0.6-2.8 %, fill max 75 %, gap 0.106 mm (limit 0.16) -> **FAIL**
- Aft closure rod gland AS568-229 FKM 75A, groove 66.5 H9, on the 61.0 f7 land at proof 67.5 bar (v3.1 design): depth 2.765-2.817 mm, squeeze 17.8-23.9 %, stretch 0.6-2.8 %, fill max 77 %, gap 0.106 mm (limit 0.16) -> **PASS**
- Aft closure rod gland AS568-233 FKM 75A, groove 66.7 H9, on the 61.0 f7 land at proof 67.5 bar (v3.0 CAD label: error): depth 2.865-2.917 mm, squeeze 14.9-21.1 %, stretch -16.8--15.3 %, fill max 75 %, gap 0.106 mm (limit 0.16) -> **FAIL**
- Aft closure rod gland AS568-233 FKM 75A, groove 66.5 H9, on the 61.0 f7 land at proof 67.5 bar (v3.0 CAD label: error): depth 2.765-2.817 mm, squeeze 17.8-23.9 %, stretch -16.8--15.3 %, fill max 77 %, gap 0.106 mm (limit 0.16) -> **FAIL**
- Tank bulkheads (AS568-238 FKM 90A) at proof: depth 2.800-2.852 mm, squeeze 16.8-22.9 %, stretch 0.6-2.2 %, fill max 76 %, gap 0.164 mm (limit 0.18) -> **PASS**

## Verification

Annular-plate integrator vs clamped solid plate: M_r(a) -112.50 vs exact -112.50 N m/m (rel. error 2.1e-09); small-hole edge M_t 146.25 vs 2 x solid centre 146.25.

Minimum MS over all rows (20 C): **0.26**

Failing rows: none

Bound rows below zero (not design conditions, listed for transparency): Graphite insert top edge (bore r 16.0) [LC2 45.0 bar] BOUND (OD gap not pressurised): hoop tension

Failing glands: Aft closure rod gland AS568-229 FKM 75A, groove 66.7 H9, on the 61.0 f7 land at proof 67.5 bar (v3.0 groove); Aft closure rod gland AS568-233 FKM 75A, groove 66.7 H9, on the 61.0 f7 land at proof 67.5 bar (v3.0 CAD label: error); Aft closure rod gland AS568-233 FKM 75A, groove 66.5 H9, on the 61.0 f7 land at proof 67.5 bar (v3.0 CAD label: error)
