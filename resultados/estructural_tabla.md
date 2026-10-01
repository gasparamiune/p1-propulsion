<!-- generado por 04_diseno/structural.py -->
| Pieza | Caso de carga | Modelo | σ [MPa] | Admisible | S [MPa] | FS | Obj. | OK |
|---|---|---|---|---|---|---|---|---|
| P1-MNT-01 | Apriete (sostenido) | M = F_apriete·brazo = 2083 N·41 mm; Z = b·t²/6 (esquina de la C) | 3.80 | sust | 13.0 | 3.43 | 3.0 | ✔ |
| P1-MNT-01 | LC5 impacto + apriete (corta) | (M_apriete + H_imp·h) / Z; H_imp = 0.5·F_pico = 580 N | 7.43 | short | 26.0 | 3.5 | 3.0 | ✔ |
| P1-MNT-01 | LC1 empuje avante (corta) | (M_apriete + T·h)/Z | 5.62 | short | 26.0 | 4.63 | 3.0 | ✔ |
| P1-MNT-01 | Apriete: apoyo de la placa de reparto (sostenido) | p = F_tornillo / (40×40 mm) | 0.65 | sust | 13.0 | 19.98 | 3.0 | ✔ |
| P1-MNT-02 | Apriete (sostenido, compresión) | p = F / (π·D²/4) | 0.83 | sust | 13.0 | 15.69 | 3.0 | ✔ |
| P1-MNT-03 | LC5 vuelco (corta) | M_vuelco=58.9 N·m → F_perno=701 N; flexión local brazo 20 mm, b=40, t=20.0 | 5.26 | short | 26.0 | 4.94 | 3.0 | ✔ |
| P1-MNT-04 | Tuerca cautiva M6 en mejilla: arranque por corte (corta) | τ = F_perno/(2·t·h), h = 18 mm; admisible 0.5·S | 1.39 | metal | 13.0 | 9.35 | 3.0 | ✔ |
| P1-MNT-04 | LC5 en el plano (corta) | M = (H/2)·h; Z = t·L²/6 (L=64) | 3.08 | short | 26.0 | 8.44 | 3.0 | ✔ |
| P1-MNT-04 | Golpe lateral 200 N (corta) | M=(F/2)·h; Z = L·t²/6 (fuera del plano) | 4.86 | short | 26.0 | 5.36 | 3.0 | ✔ |
| P1-MNT-04 | Apoyo del perno Ø12 (corta) | p = (H/2)/(d·t) | 1.73 | short | 26.0 | 15.06 | 3.0 | ✔ |
| P1-MNT-05 | LC5 dinámico (corta) | p = 6M/(d·L²), M = 0.19·F·L = 249 N·m | 4.61 | short | 26.0 | 5.64 | 3.0 | ✔ |
| P1-MNT-05 | LC5 cola trabada (corta) | p = 6M/(d·L²), M = F_fus·L = 338 N·m | 6.27 | short | 26.0 | 4.15 | 3.0 | ✔ |
| P1-MNT-05/06 | Tope de marcha (sostenido) | F = (T·e + M_grav)/r = 431 N sobre tapón Ø16 | 2.14 | sust | 13.0 | 6.07 | 3.0 | ✔ |
| P1-MNT-05/06 | LC6 golpe de ola 3 g en el tope (corta) | F = 1089 N | 5.42 | short | 26.0 | 4.8 | 3.0 | ✔ |
| P1-MNT-05/06 | LC6 ola ±1 g (fatiga) | F_a = 363 N | 1.81 | fat | 7.8 | 4.32 | 3.0 | ✔ |
| P1-MNT-05 | LC1 apoyo del buje del pivote (corta) | p = F/(d·w), POM Ø20 × ancho | 0.35 | short | 26.0 | 73.66 | 3.0 | ✔ |
| P1-MNT-05 | LC6 1P lateral ±15 % T (fatiga) | p_a = 6M/(d·L²) | 0.56 | fat | 7.8 | 13.87 | 3.0 | ✔ |
| P1-MNT-06 | LC5 cola trabada: apoyo extremo (corta) | p = F_ext/(d·25), F_ext = 4701 N | 4.70 | short | 26.0 | 5.53 | 3.0 | ✔ |
| P1-MNT-06 | LC5: arandela Ø24 de perno pasante (corta) | p = (F_ext/2)/(π(24²−6.4²)/4) | 5.59 | short | 26.0 | 4.65 | 3.0 | ✔ |
| P1-HSG-01 | LC1 empuje bollard (corta) | franja buje→pernos: M = (T/2)·11 mm, Z = 30·t²/6 (t=7) | 7.20 | short | 26.0 | 3.61 | 3.0 | ✔ |
| P1-HSG-01 | Crucero (sostenido) | franja buje→pernos: M = (T/2)·11 mm, Z = 30·t²/6 (t=7) | 4.03 | sust | 13.0 | 3.23 | 3.0 | ✔ |
| P1-HSG-01 | LC6 ±15 % empuje (fatiga) | franja buje→pernos: M = (T/2)·11 mm, Z = 30·t²/6 (t=7) | 0.60 | fat | 7.8 | 12.9 | 3.0 | ✔ |
| P1-HSG-01 | LC3 tiro de correa en el alojamiento (corta) | p = R_A/(D·B) | 1.20 | short | 26.0 | 21.64 | 3.0 | ✔ |
| P1-HSG-01 | LC4 golpe de hélice: tirón de correa (corta) | p = R_A,pin/(D·B) | 1.89 | short | 26.0 | 13.73 | 3.0 | ✔ |
| P1-HSG-01 | LC3 torque de rotor trabado en colisos M4 (corta) | p = Q/(4·r·d·t) | 2.09 | short | 26.0 | 12.42 | 3.0 | ✔ |
| P1-HSG-02 | LC3 tracción en el plano (corta) | σ = R_B/(24·t) | 1.36 | short | 26.0 | 19.18 | 3.0 | ✔ |
| P1-HSG-02 | LC4 tirón de correa (corta) | σ = R_B,pin/(24·t) | 2.14 | short | 26.0 | 12.17 | 3.0 | ✔ |
| P1-HSG-04 | LC7 apoyo del tubo en la abrazadera (corta) | M = F·L = 82 N·m → F = M/s = 1500 N; p = F/(d·22) | 2.27 | short | 26.0 | 11.44 | 3.0 | ✔ |
| P1-HSG-04 | LC7 tracción de la abrazadera (2 M6, sección 2×8×22) (corta) | σ = F/(2·8·22) | 4.26 | short | 26.0 | 6.1 | 3.0 | ✔ |
| P1-HSG-07 placa Al | LC7 torsión de la placa | τ = M/(β·b·t²) | 36.95 | metal | 138.5 | 3.75 | 2.0 | ✔ |
| P1-MNT-05 | LC7 apoyo de la placa de caña sobre la cuna (corta) | p = (M/0.06 m)/(20·76) = 1375 N / 1520 mm² | 0.91 | short | 26.0 | 28.75 | 3.0 | ✔ |
| P1-STR-01 | LC5 fusible: apoyo del tubo (corta) | p = 6M/(d·L²), L = 45 mm | 2.44 | short | 26.0 | 10.64 | 3.0 | ✔ |
| P1-STR-01 | LC5 fusible: pernos del patín (corta) | p = (F/2)/(6·2·14) | 0.89 | short | 26.0 | 29.13 | 3.0 | ✔ |
| P1-PRP-02 | LC5 fusible | σ = F_fus·h/Z en la cintura (h=110 mm) | 38.25 | metal | 38.2 | 1.0 | 3.0 | ✔ (justif.) |
| P1-PRP-02 | Arrastre a 9 km/h (sostenido) | F = ½ρV²·Cd·A = 6.4 N | 0.81 | sust | 13.0 | 15.98 | 3.0 | ✔ |
| P1-PRP-02 | Fuerza lateral en giro (corta) | F = ½ρV²·C_L·A = 44 N, brazo 70 mm, eje débil | 6.22 | short | 26.0 | 4.18 | 3.0 | ✔ |
| P1-PRP-01 | Golpe radial 150 N en el anillo (corta) | M = F·L/8 (arco entre uniones) | 6.61 | short | 26.0 | 3.93 | 3.0 | ✔ |
| P1-ELE-01 | Compresión del O-ring en insertos M4 (sostenido) | F_total = 1404 N / 8 insertos vs 1 kN arranque [ESTIMADO] | 2.28 | sust | 13.0 | 5.7 | 3.0 | ✔ |
| P1-SAF-01 | Tirón del cordón 100 N (corta) | placa 7 mm en voladizo 20 mm | 6.80 | short | 26.0 | 3.82 | 3.0 | ✔ |
| P1-STR-02 tubo Al | LC5 cola trabada (fusible) | σ = F_fus·L/Z = 338 N·m / 3003 mm³ | 112.70 | metal | 240.0 | 2.13 | 2.0 | ✔ |
| P1-STR-02 tubo Al | LC5 dinámico | σ = 0.19·F·L/Z | 82.85 | metal | 240.0 | 2.9 | 2.0 | ✔ |
| P1-HSG-06 caña Al | LC7 manipulación | σ = M/Z (Ø30×3) | 52.72 | metal | 240.0 | 4.55 | 2.0 | ✔ |
| P1-MNT-08 perno 316 | LC1+LC5 corte doble | τ = (F/2)/A | 2.57 | metal | 118.3 | 46.1 | 2.0 | ✔ |
| P1-DRV-01 eje 316 | LC3/LC4 torsión+flexión (sizing) | ver 02_calculos.md §7 | — | metal | — | 3.66 | 2.0 | ✔ |
