<!-- generado por 04_diseno/structural.py -->
| Pieza | Caso de carga | Modelo | σ [MPa] | Admisible | S [MPa] | FS | Obj. | OK |
|---|---|---|---|---|---|---|---|---|
| P1-MNT-01 | Apriete (sostenido) | M = F_apriete·brazo = 2083 N·36 mm; Z = b·t²/6 (esquina de la C) | 2.60 | sust | 8.4 | 3.23 | 3.0 | ✔ |
| P1-MNT-01 | LC5 impacto + apriete (corta) | (M_apriete + H_imp·h) / Z; H_imp = 0.5·F_pico = 501 N | 5.04 | short | 24.0 | 4.76 | 3.0 | ✔ |
| P1-MNT-01 | LC1 empuje avante (corta) | (M_apriete + T·h)/Z | 4.00 | short | 24.0 | 6.0 | 3.0 | ✔ |
| P1-MNT-01 | Apriete: apoyo de la placa de reparto (sostenido) | p = F_tornillo / (40×40 mm) | 0.65 | sust | 8.4 | 12.89 | 3.0 | ✔ |
| P1-MNT-02 | Apriete (sostenido, compresión) | p = F / (π·D²/4) | 0.83 | sust | 8.4 | 10.12 | 3.0 | ✔ |
| P1-MNT-03 | LC5 vuelco (corta) | M_vuelco=50.9 N·m → F_perno=605 N; flexión local brazo 20 mm, b=40, t=20.0 | 4.54 | short | 24.0 | 5.28 | 3.0 | ✔ |
| P1-MNT-04 | Tuerca cautiva M6 en mejilla: arranque por corte (corta) | τ = F_perno/(2·t·h), h = 18 mm; admisible 0.5·S | 1.20 | metal | 12.0 | 9.98 | 3.0 | ✔ |
| P1-MNT-04 | LC5 en el plano (corta) | M = (H/2)·h; Z = t·L²/6 (L=64) | 2.66 | short | 24.0 | 9.01 | 3.0 | ✔ |
| P1-MNT-04 | Golpe lateral 200 N (corta) | M=(F/2)·h; Z = L·t²/6 (fuera del plano) | 4.86 | short | 24.0 | 4.94 | 3.0 | ✔ |
| P1-MNT-04 | Apoyo del perno Ø12 (corta) | p = (H/2)/(d·t) | 1.49 | short | 24.0 | 16.08 | 3.0 | ✔ |
| P1-MNT-05 | LC5 dinámico (corta) | p = 6M/(d·L²), M = 0.19·F·L = 215 N·m | 1.74 | short | 24.0 | 13.76 | 3.0 | ✔ |
| P1-MNT-05 | LC5 cola trabada (corta) | p = 6M/(d·L²), M = F_fus·L = 338 N·m | 2.75 | short | 24.0 | 8.73 | 3.0 | ✔ |
| P1-MNT-05/06 | Tope de marcha (sostenido) | F = (T·e + M_grav)/r = 406 N sobre tope Ø25 | 0.83 | sust | 8.4 | 10.14 | 3.0 | ✔ |
| P1-MNT-05/06 | LC6 golpe de ola 3 g en el tope (corta) | F = 1053 N | 2.15 | short | 24.0 | 11.17 | 3.0 | ✔ |
| P1-MNT-05/06 | LC6 ola ±1 g (fatiga ~1e6 ciclos) | F_a = 351 N | 0.71 | lcf | 3.6 | 5.03 | 3.0 | ✔ |
| P1-MNT-05 | LC1 apoyo del buje del pivote (corta) | p = F/(d·w), POM Ø20 × ancho | 0.34 | short | 24.0 | 70.72 | 3.0 | ✔ |
| P1-MNT-05 | LC6 paso de pala ±20 % T lateral (fatiga 1e7–1e8) | p_a = 6M/(d·L²) | 0.36 | fat | 1.4 | 4.04 | 3.0 | ✔ |
| P1-MNT-05 | LC1 tuercas cautivas de la placa motriz: arranque por corte (corta) | τ = (T/4)/(2·12·18) (bolsillo a 18 mm de la cara) | 0.18 | metal | 12.0 | 65.38 | 3.0 | ✔ |
| P1-MNT-05 | LC6 tuercas de placa motriz ±amp·T (fatiga 1e7–1e8) | τ_a = (amp·T_cr/4)/(2·12·18) | 0.02 | metal | 0.7 | 31.92 | 3.0 | ✔ |
| P1-MNT-05 | LC2 marcha atrás: cartucho contra el fondo del rebaje (corta) | p = T_rev/A_anillo | 0.10 | short | 24.0 | 240.24 | 3.0 | ✔ |
| P1-MNT-06 | LC5 cola trabada: apoyo extremo (corta) | p = F_ext/(d·25), F_ext = 3111 N | 3.11 | short | 24.0 | 7.71 | 3.0 | ✔ |
| P1-MNT-06 | LC5: arandela Ø24 de perno pasante (corta) | p = (F_ext/2)/(π(24²−6.4²)/4) | 3.70 | short | 24.0 | 6.48 | 3.0 | ✔ |
| P1-HSG-01 placa Al | LC1 empuje bollard | franja cartucho→pernos: M = (T/2)·11 mm, Z = 30·t²/6 (t=6) | 9.68 | metal | 240.0 | 24.8 | 2.0 | ✔ |
| P1-HSG-01 placa Al | LC6 ±20 % empuje (fatiga) | σ_a = (amp·T/2)·11/Z | 1.19 | metal | 60.0 | 50.44 | 2.0 | ✔ |
| P1-HSG-01 placa Al | LC3 torque de rotor trabado en colisos M4 | p = Q/(4·r·d·t) | 2.09 | metal | 240.0 | 114.61 | 2.0 | ✔ |
| P1-DRV-08 cartucho Al | LC1 empuje en el labio (corte) | τ = T/(π·Ø21·espesor labio) | 0.48 | metal | 138.5 | 288.42 | 2.0 | ✔ |
| P1-HSG-02 | LC3 tracción en el plano (corta) | σ = R_B/(24·t) | 0.95 | short | 24.0 | 25.24 | 3.0 | ✔ |
| P1-HSG-02 | LC4 tirón de correa (corta) | σ = R_B,pin/(24·t) | 1.62 | short | 24.0 | 14.77 | 3.0 | ✔ |
| P1-HSG-04 | LC7 apoyo del tubo en la abrazadera (corta) | M = F·L = 82 N·m → F = M/s = 1500 N; p = F/(d·22) | 2.27 | short | 24.0 | 10.55 | 3.0 | ✔ |
| P1-HSG-04 | LC7 tracción de la abrazadera (2 M6, sección 2×8×22) (corta) | σ = F/(2·8·22) | 4.26 | short | 24.0 | 5.62 | 3.0 | ✔ |
| P1-HSG-07 placa Al | LC7 torsión de la placa | τ = M/(β·b·t²) | 36.95 | metal | 138.5 | 3.75 | 2.0 | ✔ |
| P1-MNT-05 | LC7 apoyo de la placa de caña sobre la cuna (corta) | p = (M/0.06 m)/(20·76) = 1375 N / 1520 mm² | 0.91 | short | 24.0 | 26.5 | 3.0 | ✔ |
| P1-STR-01 | LC5 fusible: apoyo del tubo (corta) | p = 6M/(d·L²), L = 45 mm | 2.45 | short | 24.0 | 9.77 | 3.0 | ✔ |
| P1-STR-01 | LC5 fusible: pernos del patín (corta) | p = (F/2)/(6·2·14) | 0.89 | short | 24.0 | 26.85 | 3.0 | ✔ |
| P1-PRP-02 | LC5 fusible | σ = F_fus·h/Z en la cintura (h=110 mm) | 35.25 | metal | 35.2 | 1.0 | 3.0 | ✔ (justif.) |
| P1-PRP-02 | Arrastre a 9 km/h (sostenido) | F = ½ρV²·Cd·A = 6.4 N | 0.75 | sust | 8.4 | 11.19 | 3.0 | ✔ |
| P1-PRP-02 | Fuerza lateral en giro (corta) | F = ½ρV²·C_L·A = 44 N, brazo 70 mm, eje débil | 5.96 | short | 24.0 | 4.02 | 3.0 | ✔ |
| P1-PRP-01 | Golpe radial 150 N en el anillo (corta) | M = F·L/8 (arco entre uniones) | 1.65 | short | 24.0 | 14.57 | 3.0 | ✔ |
| P1-ELE-01 | Compresión del O-ring en insertos M4 (sostenido) | F_total = 1764 N / 8 insertos vs 1 kN arranque [ESTIMADO] | 1.85 | sust | 8.4 | 4.54 | 3.0 | ✔ |
| P1-SAF-01 | Tirón del cordón 100 N (corta) | placa 7 mm en voladizo 20 mm | 6.80 | short | 24.0 | 3.52 | 3.0 | ✔ |
| P1-STR-02 tubo Al | LC5 cola trabada (fusible) | σ = F_fus·L/Z = 338 N·m / 3003 mm³ | 112.70 | metal | 240.0 | 2.13 | 2.0 | ✔ |
| P1-STR-02 tubo Al | LC5 dinámico | σ = 0.19·F·L/Z | 71.52 | metal | 240.0 | 3.36 | 2.0 | ✔ |
| P1-HSG-06 caña Al | LC7 manipulación | σ = M/Z (Ø30×3) | 52.72 | metal | 240.0 | 4.55 | 2.0 | ✔ |
| P1-MNT-08 perno 316 | LC1+LC5 corte doble | τ = (F/2)/A | 2.28 | metal | 118.3 | 51.93 | 2.0 | ✔ |
| P1-DRV-01 eje 316 | LC3/LC4 torsión+flexión (sizing) | ver 02_calculos.md §7 | — | metal | — | 2.4 | 2.0 | ✔ |
