# F4 secondary-structure joints, CAD v3.5.1 (fea3d 2026-10-19; DERIVED hand calcs, J-PD01 loads SIM from the F1 FE)

Minimum margin per joint over all cases (limit loads x SF per 188 (9); preload K 0.2 and +/-25 % scatter ASSUMED; mu 0.20 ASSUMED).

Bounding: Phi 0 for separation/slip, Phi 1 for screw and host thread; second set with load factor Phi 0.2 (ASSUMED typical).

| joint | screws | governing case (bounding) | P N | V N | MS min (bounding) | criterion | MS sep | MS slip | MS bolt y | MS bolt u | MS host thread | MS bolt shear | MS min (Phi 0.2) | criterion | hot preload util. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| J-PD01 | 4x M3 A2-70 / G11 / TC-02 | FA1S / bounding |k2| + soak-back thermal preload / A1_22.2 / PDFOOT_PD-01S_p | 74.4 | 13.2 | +0.15 | bolt_y | +9.09 | +9.21 | +0.15 | +0.80 | +1.24 | +119.08 | +0.20 | bolt_y_phi02 | 0.83 |
| J-FD01 | 2x M3 A4-70 / TC-02 | LC3 hard-landing envelope (10 g) / bounding R7 (as the F1 PM cap) | 646.4 | 51.6 | -0.41 | bolt_y | +0.29 | -0.28 | -0.41 | -0.17 | +0.21 | +13.54 | -0.20 | bolt_y_phi02 | 1.15 |
| J-FD09 | 2x M4 A4-70 / GM-09 | LC3 hard-landing envelope (10 g) / 0.5 | 757.7 | 47.4 | -0.17 | bolt_y | +0.69 | +1.21 | -0.17 | +0.19 | +0.49 | +30.41 | +0.05 | bolt_y_phi02 | 0.89 |
| J-FS15 | 2x M4 module->FS-15 | FA-1 spike (equipment bound) | 269.2 | 3.2 | +0.04 | bolt_y | +6.14 | +101.89 | +0.04 | +0.62 | +1.36 | +925.97 | +0.11 | bolt_y_phi02 | 0.89 |
| J-FS15 | 2x M5 FS-15->wall (ICD-2) | LC3 hard-landing envelope (10 g) | 182.6 | 53.4 | +0.07 | bolt_y | +10.37 | +6.09 | +0.07 | +0.64 | - | +44.68 | +0.11 | bolt_y_phi02 | 0.89 |
| J-BL05 | 4x M3 valve->BL-07 | LC3 hard-landing envelope (10 g) / V1 az 26 | 45.1 | 6.5 | +0.09 | bolt_y | +15.27 | +20.28 | +0.09 | +0.68 | +1.61 | +131.91 | +0.12 | bolt_y_phi02 | 0.89 |

Worst case per joint with the load factor Phi 0.2 (ASSUMED):

| joint | screws | case | P N | V N | MS min (Phi 0.2) | criterion |
|---|---|---|---|---|---|---|
| J-PD01 | 4x M3 A2-70 / G11 / TC-02 | FA1S / bounding |k2| + soak-back thermal preload / A1_22.2 / PDFOOT_PD-01S_p | 74.4 | 13.2 | +0.20 | bolt_y_phi02 |
| J-FD01 | 2x M3 A4-70 / TC-02 | LC3 touchdown (5.43 g SIM) / bounding R7 (as the F1 PM cap) | 640.9 | 46.2 | -0.20 | bolt_y_phi02 |
| J-FD09 | 2x M4 A4-70 / GM-09 | LC3 hard-landing envelope (10 g) / 0.5 | 757.7 | 47.4 | +0.05 | bolt_y_phi02 |
| J-FS15 | 2x M4 module->FS-15 | FA-1 spike (equipment bound) | 269.2 | 3.2 | +0.11 | bolt_y_phi02 |
| J-FS15 | 2x M5 FS-15->wall (ICD-2) | LC3 hard-landing envelope (10 g) | 182.6 | 53.4 | +0.11 | bolt_y_phi02 |
| J-BL05 | 4x M3 valve->BL-07 | LC3 hard-landing envelope (10 g) / V1 az 26 | 45.1 | 6.5 | +0.12 | bolt_y_phi02 |

Assembly utilisation nu = sigma_vM(tension + thread torsion) / Rp0.2,min at the specified torque (K 0.2; VDI 2230 guide <= 0.9 at nominal, AS RECALLED):

| joint | T N m | F_nom N | mu implied | nu nominal | nu at +25 % |
|---|---|---|---|---|---|
| J-PD01 | 0.6 | 1000 | 0.138 | 0.57 | 0.71 |
| J-FD01 | 1.0 | 1667 | 0.138 | 0.94 | 1.18 |
| J-FD09 | 2.05 | 2562 | 0.140 | 0.84 | 1.05 |
| J-BL05 | 0.88 | 1467 | 0.138 | 0.83 | 1.04 |
| J-FS15 M4 | 2.05 | 2562 | 0.140 | 0.84 | 1.05 |
| J-FS15 M5 | 4.15 | 4150 | 0.143 | 0.84 | 1.05 |

Torque window (N m) keeping every case MS >= 0 (same K 0.2 and +/-25 % scatter; DERIVED, scan 0.3-1.6 x specified):

| joint | specified | window, bounding | window, Phi 0.2 | window, Phi 0.2 without slip |
|---|---|---|---|---|
| J-PD01 | 0.6 | [0.18, 0.72] | [0.18, 0.751] | [0.18, 0.751] |
| J-FD01 | 1.0 | none | none | [0.62, 0.774] |
| J-FD01 sealOD | 1.0 | none | [0.662, 0.815] | [0.351, 0.815] |
| J-FD09 | 2.05 | [0.653, 2.024] | [0.615, 2.252] | [0.615, 2.252] |
| J-FD09 EI0.5 | 2.05 | none | [1.357, 2.166] | [0.977, 2.166] |
| J-FS15 M4 | 2.05 | [0.615, 2.138] | [0.615, 2.271] | [0.615, 2.271] |
| J-FS15 M5 | 4.15 | [1.245, 4.443] | [1.245, 4.617] | [1.245, 4.617] |
| J-BL05 | 0.88 | [0.264, 0.959] | [0.264, 0.987] | [0.264, 0.987] |

J-PD01 thermal preload change at soak-back (G11 CTE 30/50/70e-6): +170 N, +335 N, +499 N (DERIVED, G11 data TO-VERIFY).
ICD-14 bleed cluster: 0.740 kg at [12.4, 33.0, 303.0] mm; limit inertial resultants per case in f4_secondary.json.
FA-1 equipment bound: 26.85 g axial (DLF 2.0 x 1.8 kN / 13.671 kg dry, DERIVED).
