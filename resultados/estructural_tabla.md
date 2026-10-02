<!-- generado por 04_diseno/structural.py -->
| Pieza | Caso de carga | Modelo | σ [MPa] | Admisible | S [MPa] | FS | Obj. | OK |
|---|---|---|---|---|---|---|---|---|
| P1-PMP-03 | Álabe en la raíz: par de diseño 15.3 N·m + empuje | voladizo: F_t=T/(Z·r_m)=62 N a span/2 + F_a=153 N/álabe en r̄; M=2.98 N·m; W_mín perfil cubo=79 mm³ (c=53.9, t=4.31) | 37.94 | metal | 205.0 | 5.4 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz, fatiga: par de diseño 15.3 N·m + empuje | σ_a = 0.30·σ_m (paso por 7 álabes del estator, toma); K_f 1.5; S_e 316 | 11.38 | metal | 120.0 | 10.54 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz: par máx. del controlador 18.6 N·m + empuje | voladizo: F_t=T/(Z·r_m)=75 N a span/2 + F_a=153 N/álabe en r̄; M=3.06 N·m; W_mín perfil cubo=79 mm³ (c=53.9, t=4.31) | 38.97 | metal | 205.0 | 5.26 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz, fatiga: par máx. del controlador 18.6 N·m + empuje | σ_a = 0.30·σ_m (paso por 7 álabes del estator, toma); K_f 1.5; S_e 316 | 11.69 | metal | 120.0 | 10.26 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz: par de corte del pasador 33.5 N·m (traba repartida) | voladizo: F_t=T/(Z·r_m)=135 N a span/2 + F_a=153 N/álabe en r̄; M=3.58 N·m; W_mín perfil cubo=79 mm³ (c=53.9, t=4.31) | 45.57 | metal | 205.0 | 4.5 | 2.0 | ✔ |
| P1-PMP-03 | Cubo: aplastamiento del semipasador al par de corte | F = T_corte/(2·r_eje) = 1674 N por lado sobre el tramo interior 3.5×5.0 mm (la ranura aligerante deja 5.0 + 4.0 mm de contacto; conservador: solo el interior) | 95.66 | metal | 307.5 | 3.21 | 2.0 | ✔ |
| P1-PMP-05 | Par máx. del controlador (margen contra corte intempestivo) | 2 semipasadores, 2 secciones de corte a r_eje: τ=T/(d_eje·A)=96.5 MPa; τ_u=0,6·S_u=174 MPa; T_corte/T_máx=1.80 (criterio R12 ≥ 1,5) | 96.50 | metal | 174.0 | 1.8 | 2.0 | ✔ (justif.) |
| P1-PMP-05 | Fatiga a par de crucero (Goodman en corte) | τ_m=73.7, τ_a=11.1 MPa (T_top 14.2 N·m, ±15%); S_e,τ=0,577·S_e; índice Goodman 0.62 | 0.62 | metal | 1.0 | 1.6 | 2.0 | ✔ (justif.) |
| P1-PMP-06 | Álabe del estator en la raíz: par de diseño 15.3 N·m | voladizo (conservador, en realidad empotrado en camisa y cubo): F_t=44 N, F_a=36 N, F_r buje=26 N; W_mín=70 mm³ (c=44.4, t=4.44) | 25.83 | metal | 240.0 | 9.29 | 2.0 | ✔ |
| P1-PMP-06 | Álabe del estator, fatiga: par de diseño | σ_a=0.30·σ_m (estelas de 5 álabes); S_e Al anodizado = 0.6·S_e; K_f 1.5 | 7.75 | metal | 38.4 | 4.96 | 2.0 | ✔ |
| P1-PMP-06 | Álabe del estator en la raíz: par máx. del controlador 18.6 N·m | voladizo (conservador, en realidad empotrado en camisa y cubo): F_t=54 N, F_a=36 N, F_r buje=26 N; W_mín=70 mm³ (c=44.4, t=4.44) | 27.64 | metal | 240.0 | 8.68 | 2.0 | ✔ |
| P1-PMP-06 | Álabe del estator, fatiga: par máx. del controlador | σ_a=0.30·σ_m (estelas de 5 álabes); S_e Al anodizado = 0.6·S_e; K_f 1.5 | 8.29 | metal | 38.4 | 4.63 | 2.0 | ✔ |
| P1-PMP-01 | Presión interna 0.20 MPa (R12 §7.2) | aro delgado σ=p·r/t, r=73.9, t=5.0 | 2.96 | metal | 240.0 | 81.2 | 2.0 | ✔ |
| P1-PMP-08 | Presión interna 0.20 MPa (R12 §7.2) | aro delgado σ=p·r/t, r=68.9, t=5.0 | 2.76 | metal | 240.0 | 87.09 | 2.0 | ✔ |
| P1-PMP-01 | Bulones brida toma (8×M6): presión + bucket + momentos | F_ax=3857 N (p hasta el sello Ø152.3), M=242.2 N·m (boquilla 364 N, bucket 1408 N, peso) → F_bulón=1217 N sobre A_s=20.1 mm² (sin precarga) | 60.54 | metal | 450.0 | 7.43 | 2.0 | ✔ |
| P1-PMP-08 | Bulones brida carcasa–tobera (8×M5 roscados): presión + bucket + momentos | F_ax=3419 N (p hasta el sello Ø142.8), M=182.8 N·m (boquilla 364 N, bucket 1408 N, peso) → F_bulón=1029 N sobre A_s=14.2 mm² (sin precarga) | 72.49 | metal | 450.0 | 6.21 | 2.0 | ✔ |
| P1-PMP-01 | Rosca M5 de la brida trasera en Al 6061-T6: precarga + servicio | barrido τ = F/(π·d·L·0,6), L engranada = 7.75 mm (M5 × 20), F_v = 3000 N [ESTIMADO] + 1029 N | 55.17 | metal | 138.5 | 2.51 | 2.0 | ✔ |
| P1-PMP-01 | Tornillos anti-rotación del estator (2×M5) al corte | F=130 N por tornillo (T_max 18.6 N·m, r=71.4), corte en A_s | 9.16 | metal | 259.6 | 28.35 | 2.0 | ✔ |
| P1-PMP-06 | Camisa: aplastamiento de la punta del M5 anti-giro al par máx. | σ_b = F/(d·h), h = 3.5 mm (agujero liso Ø5.5) | 7.43 | metal | 360.0 | 48.45 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: aplastamiento del alojamiento del buje — F lateral de la boquilla 364 N | σ_b=F/(d·t), d=12.0, t=25.5 | 1.19 | metal | 187.5 | 157.87 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: sección neta y desgarro — F lateral de la boquilla 364 N | máx(F/((w−d)·t), F/(2·(e−d/2)·t)·√3), w=24.0, e=12.0 | 2.06 | metal | 125.0 | 60.76 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: flexión en el arranque — F lateral de la boquilla 364 N | M=F·15.0 mm, W=w·t²/6 (eje débil) | 2.09 | metal | 125.0 | 59.73 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: fatiga — F lateral de la boquilla 364 N | σ_a = σ flexión (maniobras, ~1e5–1e6 ciclos); S_e 5083; K_f 1.5 | 2.09 | metal | 73.3 | 35.04 | 2.0 | ✔ |
| P1-PMP-11 | Buje de pivote POM: presión — F lateral de la boquilla 364 N | p=F/(d·L), d=8.0, L=25.5 (un solo buje) | 1.78 | metal | 25.0 | 14.03 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: aplastamiento del alojamiento del buje — F del bucket 1408 N | σ_b=F/(d·t), d=12.0, t=25.5 | 4.59 | metal | 187.5 | 40.81 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: sección neta y desgarro — F del bucket 1408 N | máx(F/((w−d)·t), F/(2·(e−d/2)·t)·√3), w=24.0, e=12.0 | 7.96 | metal | 125.0 | 15.71 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: flexión en el arranque — F del bucket 1408 N | M=F·15.0 mm, W=w·t²/6 (eje débil) | 8.10 | metal | 125.0 | 15.44 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: fatiga — F del bucket 1408 N | σ_a = σ flexión (maniobras, ~1e5–1e6 ciclos); S_e 5083; K_f 1.5 | 8.10 | metal | 73.3 | 9.06 | 2.0 | ✔ |
| P1-PMP-11 | Buje de pivote POM: presión — F del bucket 1408 N | p=F/(d·L), d=8.0, L=25.5 (un solo buje) | 6.89 | metal | 25.0 | 3.63 | 2.0 | ✔ |
| P1-PMP-09 | Bulones placa–espejo (6×M6): F del bucket 1408 N + momento | brazo 36 mm al espejo; F_bulón=413 N sobre A_s=20.1 mm² | 20.53 | metal | 450.0 | 21.92 | 2.0 | ✔ |
| P1-PMP-09 | Cuello: F lateral de la boquilla con el O-ring a tope | voladizo del cuello M=F·L=6.0 N·m, W anillo=116736 mm³ | 0.05 | metal | 125.0 | 2444.39 | 2.0 | ✔ |
| P1-STE-01 | Flexión del tubo por el desvío del chorro (fatiga, sizing) | M = F_s·e = 323 N × 66 mm; Z tubo Ø101.1/Ø91.1 | 0.62 | metal | 90.0 | 145.97 | 2.0 | ✔ |
| P1-STE-01 | Oreja del bucket: flexión en su plano (bucket R12, corta) | F/2 = 704 N a 52 mm de la raíz; sección 8 × 36 | 21.12 | metal | 240.0 | 11.36 | 2.0 | ✔ |
| P1-STE-01 | Oreja del bucket: flexión (reversa sizing, fatiga) | F/2 = 349 N a 52 mm; 8 × 36 | 10.47 | metal | 90.0 | 8.59 | 2.0 | ✔ |
| P1-STE-01 | Oreja de pivote (dentro de la de la bomba): flexión de la raíz | F = √((F_b/2)²+(F_s/2)²) = 727 N a 12 mm; 25 × 30 | 2.33 | metal | 240.0 | 103.14 | 2.0 | ✔ |
| P1-STE-02 | Hombro Ø8 biempotrado: flexión + corte (bucket R12 + dirección, corta) | reacción superior 1490 N en luz 28.5 mm (M = F·L/8); 316 estirado | 111.17 | metal | 310.0 | 2.79 | 2.0 | ✔ |
| P1-STE-02 | Hombro Ø8: flexión por maniobras (fatiga) | F_s/2 = 162 N, M = F·L/8 | 11.46 | metal | 180.0 | 15.7 | 2.0 | ✔ |
| P1-STE-05 | Hombro Ø8 en voladizo: flexión + corte (corta) | reacción inferior 195 N a 14.3 mm | 56.20 | metal | 310.0 | 5.52 | 2.0 | ✔ |
| P1-STE-05 | Hombro Ø8 en voladizo: flexión por maniobras (fatiga) | F_s/2 = 162 N a 14.3 mm | 45.86 | metal | 180.0 | 3.93 | 2.0 | ✔ |
| P1-STE-02 | Presión en el buje POM de la oreja de la bomba (P1-PMP-11) | 1490 N / (Ø8 × 25.5) | 7.29 | metal | 20.0 | 2.74 | 2.0 | ✔ |
| P1-STE-03 | Arandela POM: empuje axial (peso boquilla + bucket + componente vertical) | 60 N [ESTIMADO] / 199 mm² | 0.30 | metal | 10.0 | 33.18 | 2.0 | ✔ |
| P1-STE-06 | Poste Ø22: flexión + torsión (biela M66, M_s con F_s R12) | F_biela = M_s/79 mm = 304 N a 138 mm de la brida | 41.03 | metal | 240.0 | 5.85 | 2.0 | ✔ |
| P1-STE-06 | Poste Ø22: flexión (fatiga, sizing) | F_biela = 269 N | 35.66 | metal | 90.0 | 2.52 | 2.0 | ✔ |
| P1-STE-06 | Brida del poste: 4 × M8 A4-70 en Ø32 (tracción) | F = 4M/(n·BC) = 1313 N; As 36,6 mm² | 35.87 | metal | 450.0 | 12.55 | 2.0 | ✔ |
| P1-STE-04 | Banda de la brida: torsión (momento del poste) + flexión | T = 42.0 N·m en 24 × 20 (α = 0.217); F_biela × 76 mm | 36.92 | metal | 125.0 | 3.39 | 2.0 | ✔ |
| P1-STE-04 | 4 × M8 A4-70 a la torre: tracción por el momento del poste | F = M/(19 mm)/2 = 1105 N por bulón | 30.20 | metal | 450.0 | 14.9 | 2.0 | ✔ |
| P1-STE-08 | Placa de topes 8 mm: flexión en su plano (timón forzado) | F = 2·F_biela = 607 N a 90 mm del ala; sección 32 × 8 | 40.02 | metal | 125.0 | 3.12 | 2.0 | ✔ |
| P1-STE-06 | Poste contra el tope: flexión (timón forzado) | F = 607 N a 111 mm de la brida | 64.69 | metal | 240.0 | 3.71 | 2.0 | ✔ |
| P1-STE-08 | 2 × M6 A4-70 del ala al espejo (tracción por el momento) | M = F × 40 mm / 30 mm entre bulón y borde | 40.27 | metal | 450.0 | 11.18 | 2.0 | ✔ |
| P1-STE-07 | Brazo 10 mm: flexión por la altura de la rótula + tracción | F_biela 304 N; M = F × 12 mm en 24 × 10 | 10.37 | metal | 125.0 | 12.05 | 2.0 | ✔ |
| P1-REV-01 | Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta) | p = 98 kPa, luz 53.5 mm (nervio central), t = 6 | 3.89 | metal | 125.0 | 32.15 | 2.0 | ✔ |
| P1-REV-01 | Chapa de la cuchara: franja (fatiga de soldadura, 1e5) | ídem | 3.89 | metal | 68.0 | 17.49 | 2.0 | ✔ |
| P1-REV-01 | Cuchara como viga entre brazos (bucket R12, corta) | M = F·L/8, L = 107; I_arco = 388e3 mm⁴ | 2.30 | metal | 125.0 | 54.33 | 2.0 | ✔ |
| P1-REV-01 | Brazo lateral: flexión (bucket R12, corta) | M = M_h/n = 127/2 N·m por brazo trabado; sección 6 × 60 | 17.61 | metal | 125.0 | 7.1 | 2.0 | ✔ |
| P1-REV-01 | Brazo lateral: flexión (reversa sizing, fatiga de soldadura) | M = M_h,sizing/n = 63/2 N·m | 8.73 | metal | 68.0 | 7.79 | 2.0 | ✔ |
| P1-REV-01 | Agujero de traba: aplastamiento del brazo (émbolo Ø12) | F = M_h/(n·r) = 127 N·m / (2 × 45 mm) = 1408 N | 19.56 | metal | 125.0 | 6.39 | 2.0 | ✔ |
| P1-REV-01 | Pivote: aplastamiento del brazo + refuerzo (buje Ø14 × 12) | F/2 = 704 N | 4.19 | metal | 125.0 | 29.83 | 2.0 | ✔ |
| P1-REV-02 | Perno con hombro Ø10: flexión + corte (bucket R12, corta) | F/2 = 704 N a 7.5 mm | 57.63 | metal | 205.0 | 3.56 | 2.0 | ✔ |
| P1-REV-02 | Perno con hombro Ø10: flexión (fatiga) | F/2 = 349 N | 26.67 | metal | 180.0 | 6.75 | 2.0 | ✔ |
| P1-REV-03 | Buje POM Ø10/Ø14 × 8: presión (bucket R12, corta) | 704 N / (10 × 12) | 5.87 | metal | 20.0 | 3.41 | 2.0 | ✔ |
| P1-REV-03 | Buje POM: presión (reversa sizing, oscilación) | 349 N / (10 × 12) | 2.91 | metal | 10.0 | 3.44 | 2.0 | ✔ |
| P1-REV-04 | Perno del émbolo Ø12: flexión + corte (M_h con bucket R12) | F = 1408 N a 4.5 mm; 316 | 47.15 | metal | 205.0 | 4.35 | 2.0 | ✔ |
| P1-REV-04 | Perno del émbolo: flexión (reversa sizing, fatiga) | F = 698 N | 18.53 | metal | 180.0 | 9.72 | 2.0 | ✔ |
| P1-REV-06 | Tornillo con hombro Ø8 de la varilla: flexión (palanca forzada) | F = 100 N × 125/46 = 272 N a 6 mm | 32.44 | metal | 205.0 | 6.32 | 2.0 | ✔ |
| P1-REV-09 | Soporte del Bowden 4 mm: placa de tope en voladizo | tiro 60 N [ESTIMADO] a 34 mm; sección 16 × 4 | 47.81 | metal | 125.0 | 2.61 | 2.0 | ✔ |
| P1-CTL-14 | Gatillo 6 mm: flexión por el apriete (100 N a 20 mm del pivote) | sección 10 × 6 | 20.00 | metal | 240.0 | 12.0 | 2.0 | ✔ |
| P1-REV-05 | Soporte del Mach5: placa lateral en voladizo (palanca forzada) | 272 N a 48 mm; 6 × 124 | 0.85 | metal | 125.0 | 147.35 | 2.0 | ✔ |
| P1-CTL-09 | Palanca del acelerador: flexión en el cubo (100 N en el pomo) | M = 100 N × 120 mm; barra 16 × 8 | 35.16 | metal | 240.0 | 6.83 | 2.0 | ✔ |
| P1-CTL-10 | Palanca del bucket: flexión en el escalón (100 N en el pomo) | M = 100 N × 125 mm; 16 × 8 | 36.62 | metal | 240.0 | 6.55 | 2.0 | ✔ |
| P1-CTL-11 | Eje Ø12: torsión (100 N en el pomo del acelerador) | T = 15 N·m | 76.57 | metal | 205.0 | 2.68 | 2.0 | ✔ |
| P1-CTL-11 | Pasador Ø4 A4 palanca–eje: doble corte | F = T/d = 1250 N | 86.14 | metal | 450.0 | 5.22 | 2.0 | ✔ |
| P1-CTL-12 | Perno de enclavamiento Ø6: corte (palanca forzada contra el enclavamiento) | F = 100 N × 125 / 22 = 568 N | 46.41 | metal | 205.0 | 4.42 | 2.0 | ✔ |
| P1-CTL-08 | Placa central: aplastamiento del perno de enclavamiento (6 mm) | 568 N / (6 × 6) | 15.78 | metal | 125.0 | 7.92 | 2.0 | ✔ |
| P1-CTL-08 | Placa central: flexión bajo el eje (100 N en el pomo) | M = 100 N × 190 mm; sección 6 × 56 | 6.06 | metal | 125.0 | 20.63 | 2.0 | ✔ |
| P1-CTL-02 | Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta) | franja 50 × 6 apoyada, luz 50: M = F·L/4 | 6.25 | short | 24.0 | 3.84 | 3.0 | ✔ |
| P1-CTL-03 | Cara PETG 10 mm: tirón del cordón 150 N [SUPUESTO] (corta, cruza capas) | franja 50 × 10 empotrada, luz 76: M = F·L/8; ÷ f_Z (cara inclinada 32°) | 4.28 | short | 24.0 | 5.61 | 3.0 | ✔ |
| P1-CTL-03 | Cara PETG 10 mm: golpe sobre la seta 200 N [SUPUESTO] (corta, cruza capas) | ídem | 5.70 | short | 24.0 | 4.21 | 3.0 | ✔ |
| P1-CTL-01 | Placa de refuerzo 6 mm: carga del pasamuros del M66 | placa circular empotrada R 60, carga 304 N en r 10 | 13.40 | metal | 125.0 | 9.33 | 2.0 | ✔ |
| P1-CTL-04 | Pasamuros M66: cuerpo Ø20/Ø9,6 a tracción + flexión | 304 N; momento por 20 mm de voladizo | 9.42 | metal | 205.0 | 21.77 | 2.0 | ✔ |
| P1-INT-01 | Techo plano entre costados, p = máx(p_cierre, p_golpe) | placa larga empotrada: σ = p·b²/(2t²), b = W_open = 158, t = 5.0 | 33.73 | metal | 125.0 | 3.71 | 2.0 | ✔ |
| P1-INT-01 | Costado plano más alto (en el labio), p = máx(p_cierre, p_golpe) | placa empotrada brida–techo: σ = p·h²/(2t²), h = 156 | 32.68 | metal | 125.0 | 3.83 | 2.0 | ✔ |
| P1-INT-01 | Fatiga de la soldadura del costado: Δp = p_ram + p_succión = 42 kPa, 1e+05 ciclos | Δσ = Δp·h²/(2t²) vs FAT 25 (IIW, m = 3) → 68 MPa | 20.43 | metal | 67.9 | 3.32 | 2.0 | ✔ |
| P1-INT-01 | Bulones M6 A4 brida ↔ placa (14): precarga + p·A_abertura + 3 g | σ = (F_v + Φ·F/n)/A_s, F_v = 2200 N (2.4 N·m), F = 4455 N, Φ = 0,25 | 113.41 | metal | 450.0 | 3.97 | 2.0 | ✔ |
| P1-INT-02 | Rosca ciega M6 × 8 de la brida del conducto en 5083: barrido del filete | τ = (F_v + Φ·F/n)/(π·d·L·0,6), L útil = 6.5 mm, F_v = 2200 N vs τ_y = R_p0,2/√3 | 31.01 | metal | 72.2 | 2.33 | 2.0 | ✔ |
| P1-INT-02 | Junta brida del conducto ↔ placa: precarga M6 vs cordón NBR (1137 mm) + apertura | FS = F_v/((q_cordón·L + (1−Φ)·F)/n), q = 4 N/mm [ESTIMADO]; σ y S en N | 563.56 | metal | 2200.0 | 3.9 | 2.0 | ✔ |
| P1-INT-01 | Tubo junto a la brida de la bomba: momento del bucket (sin placa de espejo) | σ = M/(π r² t), M = F_bucket·358 | 3.13 | metal | 125.0 | 39.98 | 2.0 | ✔ |
| P1-INT-01 | Bulones M6 de la brida de la bomba: precarga + momento del bucket | σ = (F_v + Φ·4M/(n·r_bc))/A_s, Φ = 0,25 (VDI 2230) | 217.90 | metal | 450.0 | 2.07 | 2.0 | ✔ |
| P1-INT-01 | Tubo del eje en voladizo (sin contar el alma): caja del sello | σ = F·L/W, L = 74 | 2.34 | metal | 125.0 | 53.35 | 2.0 | ✔ |
| P1-INT-01 | Chimenea de inspección: presión de cierre (aro) | σ = p·r/t | 0.74 | metal | 125.0 | 169.06 | 2.0 | ✔ |
| P1-INT-02 | Paño lateral entre bulones del conducto y del ala: golpe de fondo | σ = p·b²/(2t²), b = 68 | 1.17 | metal | 125.0 | 106.56 | 2.0 | ✔ |
| P1-INT-02 | Tornillos M8 A4-70 del soporte (ISO 10642 desde abajo + tuerca): precarga + vuelco del empuje | σ = (F_v + Φ·F_t)/A_s, F_v = 6944 N (10 N·m, K 0.18), F_t = 458 N, Φ = 0,25 | 192.87 | metal | 450.0 | 2.33 | 2.0 | ✔ |
| P1-INT-02 | Asiento cónico de la cabeza M8 en el 5083 (aplastamiento) | σ_b = F/(π/4·(dk² − d²)), área PROYECTADA, dk = 16, F = F_v + F_t (auditoría Pass 3 H5) | 50.82 | metal | 125.0 | 2.46 | 2.0 | ✔ |
| P1-INT-02 | Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono) | τ = F/(π·dk·(t − h_cono)), t − h = 6.0 | 24.54 | metal | 72.2 | 2.94 | 2.0 | ✔ |
| P1-INT-02 | Bulones M6 del ala al casco (26): precarga + golpe de fondo + presión en la abertura | σ = (F_v + Φ·F/n)/A_s, F = 8757 N, Φ = 0,25 | 203.19 | metal | 450.0 | 2.21 | 2.0 | ✔ |
| P1-INT-02 | Aplastamiento del casco (Al 4 mm) por el empuje en los bulones del ala | σ_b = (T/n)/(d·t) | 1.23 | metal | 125.0 | 102.04 | 2.0 | ✔ |
| P1-INT-02 | Arranque de la cabeza avellanada M6 en el casco de 4 mm (corte del labio de 1,2 mm) | τ = (F/n)/(π·d_m·t_labio), d_m = 9 | 9.93 | metal | 72.2 | 7.27 | 2.0 | ✔ |
| P1-INT-03 | Barra con la rejilla tapada (bolsa) a la presión de cierre | viga simplemente apoyada L = 330, w = p·paso, W = 212 mm³ (sección perfilada) | 70.14 | metal | 205.0 | 2.92 | 2.0 | ✔ |
| P1-INT-03 | Barra: golpe de objeto 200 N en el centro | M = P·L/4 | 77.88 | metal | 205.0 | 2.63 | 2.0 | ✔ |
| P1-INT-03 | Apoyo de la barra contra la cuña de la placa (aplastamiento del Al) | σ_b = R/(b·9 mm) | 5.00 | metal | 125.0 | 24.98 | 2.0 | ✔ |
| P1-INT-04 | Tapa: succión/contrapresión de cierre (corta) | σ = 3(3+ν)p a²/(8t²), a = 58, t = 13.0 | 1.72 | short | 24.0 | 13.94 | 3.0 | ✔ |
| P1-INT-04 | Tapa: recuperación de presión a 30 km/h (sostenida) | ídem con p_ram | 0.63 | sust | 8.4 | 13.32 | 3.0 | ✔ |
| P1-INT-04 | Tapa: ciclo marcha ↔ punto fijo Δp = 42 kPa (olas/maniobras) | ídem con Δp | 1.07 | lcf | 3.6 | 3.34 | 3.0 | ✔ |
| P1-INT-04 | Tapa en la purga (r = 32, espesor neto 13.6): ciclo Δp (olas/maniobras) | σ_r = 3(3+ν)p(a² − r²)/(8t²) | 0.69 | lcf | 3.6 | 5.23 | 3.0 | ✔ |
| P1-INT-04 | Tapa: aplastamiento bajo arandela M6 Ø18 (sostenido) | σ = F/(π/4(18² − 6,4²)) | 0.30 | sust | 8.4 | 28.28 | 3.0 | ✔ |
| P1-DRV-01 | Agujero del pasador: par de corte del pasador (traba con piedra) | τ = T_corte/(πd³/16 − d_h·d²/6), T_corte 33.5 N·m, sección neta, K_t = 1 (dúctil, estático) | 25.07 | metal | 118.3 | 4.72 | 2.0 | ✔ |
| P1-DRV-01 | Agujero del pasador: fatiga en V máx. (T_top ± 15%) | Goodman τ_a/τ_e + τ_m/τ_u, K_ts 2.0 (Peterson), S_e corrosión 180 MPa; σ_eq = τ_a·τ_u/τ_e + τ_m | 30.35 | metal | 297.1 | 9.79 | 2.0 | ✔ |
| P1-DRV-01 | Ranura DIN 471 de empuje: par de corte del pasador + Fa | von Mises √(σ² + 3τ²), τ = T_corte/(π·19³/16), σ = Fa/A_fondo, K_t = 1 (dúctil, estático) | 43.14 | metal | 205.0 | 4.75 | 2.0 | ✔ |
| P1-DRV-01 | Ranura DIN 471 de empuje: fatiga en V máx. | Goodman von Mises σ_a/S_e + σ_m/S_u; K_ts 3.0, K_t ax 4.0; empuje en V máx. ∝ T_top | 78.46 | metal | 515.0 | 6.56 | 2.0 | ✔ |
| P1-DRV-01 | Chaveta 6×6 del acople: aplastamiento a T_max | p = 2T/(d·(h − t1)·(l − b)), l = 22 mm, cubo de acero | 46.42 | metal | 100.0 | 2.15 | 2.0 | ✔ |
| P1-DRV-08 | Chaveta 5×5 del eje del motor Ø15 en el cubo del acople: aplastamiento a T_max | p = 2T/(d·(h − t1)·(l − b)), encastre l = 26.5 mm, T_max 18.6 N·m (sizing), cubo de acero | 57.58 | metal | 100.0 | 1.74 | 2.0 | ✔ (justif.) |
| P1-DRV-08 | Eje del motor Ø15 con chavetero: torsión a T_max | τ = 16T/(π·(d − t1)³) (sección neta conservadora), acero del motor [SUPUESTO: S_y ≥ 300 MPa, no publicado] | 94.79 | metal | 300.0 | 3.16 | 2.0 | ✔ |
| P1-DRV-01 | Rosca M20×1 (KM4): Fa en reversa + par T_max | von Mises en el núcleo (d − 1,083·P), σ = Fa/A, τ = 16T/(π d3³) | 24.35 | metal | 205.0 | 8.42 | 2.0 | ✔ |
| P1-DRV-02 | Presión de diseño 0.20 MPa en la cámara mojada (espigón) | anillo de pared delgada σ = p·r/t (espigón, la sección más delgada) | 1.20 | metal | 205.0 | 170.83 | 2.0 | ✔ |
| P1-DRV-02 | Bulones 4 × M6 A4-70 al buje de la toma: presión + resorte del sello | σ = F/(4·A_s), F = p·π/4·Ø42² + 150 N (sin precarga) | 5.31 | metal | 450.0 | 84.71 | 2.0 | ✔ |
| P1-DRV-02 | Brida de 8 mm: flexión entre espigón y bulones | placa anular como viga por unidad de perímetro: σ = 6·F·e/(π·BC·t²) | 1.42 | metal | 205.0 | 144.76 | 2.0 | ✔ |
| P1-DRV-03 | Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa) | flexión en su plano σ = M/(t·L²/6), M = Fa/2 · 121 mm, L = 150 mm, ZAT soldada | 1.02 | metal | 115.0 | 112.35 | 2.0 | ✔ |
| P1-DRV-03 | Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico | σ = P·L/4/(b t²/6) + Fa·e/(t·b²/6)/2, L = 200, b = 31, e = 35 mm, ZAT | 16.59 | metal | 115.0 | 6.93 | 2.0 | ✔ |
| P1-DRV-03 | Espárragos 4 × ISO 10642 M8 A4-70: vuelco por Fa + corte (servicio) | F_t = Fa·h/Δx/2 + 3g/4, F_s = Fa/4; von Mises sobre A_s (carga de servicio; Δx = 120) | 15.45 | metal | 450.0 | 29.13 | 2.0 | ✔ |
| P1-DRV-03 | Espárrago M8 A4-70: precarga (10 N·m, F_v 6944 N) + F_t | σ = (F_v + F_t)/A_s (conservador: Φ = 1) vs R_p0,2 A4-70 | 202.25 | metal | 450.0 | 2.23 | 2.0 | ✔ |
| P1-DRV-03 | Tuerca ISO 4032 A4 sobre espárrago A4: precarga (10 N·m) + F_t | barrido de filetes τ = F/(π·d·m·0,6), m = 6.8, F = T/(K·d) + F_t (K 0.18) vs 0,58·R_p0,2 A4-70 | 72.19 | metal | 261.0 | 3.62 | 2.0 | ✔ |
| P1-DRV-03 | Zapata ranurada: aplastamiento bajo la arandela ISO 7093 (precarga + F_t) | σ = F/A, A = anillo Ø24/Ø8,4 fuera de la ranura de 9 mm = 241 mm², ZAT | 30.66 | metal | 115.0 | 3.75 | 2.0 | ✔ |
| P1-DRV-03 | Pasadores ISO 8735 Ø6 A4 (2 por zapata): corte por Fa (sin contar fricción) | τ = Fa/(4·A), σ_eq = √3·τ vs R_p0,2 A4-70 | 11.71 | metal | 450.0 | 38.44 | 2.0 | ✔ |
| P1-INT-02 | Agujero ciego de los pasadores Ø6 (6 mm) en el 5083: aplastamiento por Fa | σ_b = (Fa/4)/(d·h) vs R_p0,2 5083-H111 125 MPa [ESTIMADO] | 5.31 | metal | 125.0 | 23.55 | 2.0 | ✔ |
| P1-DRV-03 | Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo | corte del resalte τ = Fa/(π·D·t_resalte), σ_eq = √3·τ | 2.99 | metal | 240.0 | 80.3 | 2.0 | ✔ |
| P1-DRV-06 | Tapa: empuje Fa hacia proa entre el aro exterior y los M5 | placa anular por unidad de perímetro σ = 6·Fa·e/(2π r_m t²) | 3.51 | metal | 240.0 | 68.4 | 2.0 | ✔ |
| P1-DRV-06 | Bulones 4 × M5 A4-70 de la tapa: Fa | σ = Fa/(4·A_s) (sin precarga) | 13.46 | metal | 450.0 | 33.44 | 2.0 | ✔ |
| P1-MOT-02 | Placa: 3 g vertical del motor en voladizo (sin cartelas) | σ = W·e/(b t²/6), W = 3 g × 4.4 kg, e = 63 mm, b = 2·95 − Ø64 | 3.88 | metal | 115.0 | 29.6 | 2.0 | ✔ |
| P1-MOT-02 | Placa: par de reacción T_max (en su plano) + 3 g | corte en la sección por el agujero τ = (T/ (2·y_pie) + W/2)/(b·t) , σ_eq = √3·τ | 0.27 | metal | 115.0 | 423.85 | 2.0 | ✔ |
| P1-MOT-02 | Bulones 4 × M6 a la cara del motor: T_max + 3 g (corte) | τ = (T/(n·r) + W/n)/A_s, σ_eq = √3·τ (sin fricción por precarga) | 12.79 | metal | 450.0 | 35.18 | 2.0 | ✔ |
| P1-MOT-02 | Bulones 4 × M8 de los pies al casco: vuelco 3 g + par | F_t = W·e/Δx/2 + T/(2·y_pie) sobre A_s | 7.00 | metal | 450.0 | 64.28 | 2.0 | ✔ |
| P1-ELE-01 | Insertos M5 de la capota: apriete de las tiras de EPDM (sostenido) | arranque τ = F/(π·Ø·L) del inserto, F = máx(EPDM 160 N, 3 g arriba 66 N)/4; cruza capas (×f_Z) | 0.52 | sust | 8.4 | 16.02 | 3.0 | ✔ |
| P1-ELE-01 | Paredes del pedestal: 3 g vertical de ESC + capota (compresión sostenida) | σ = 3 g·m/A_paredes (pandeo despreciable: h/t = 19) | 0.03 | sust | 8.4 | 245.74 | 3.0 | ✔ |
| P1-ELE-01 | Orejas M6 al piso: 2 g lateral (golpe) del conjunto a la altura del CG | vuelco: F_t = m·2g·h_CG/(ancho)/2 sobre el anillo de la oreja (7 mm, cruza capas) | 0.16 | short | 24.0 | 153.03 | 3.0 | ✔ |
| P1-ELE-02 | Techo de la capota: reacción de las tiras de EPDM (sostenida) | voladizo desde la pared por unidad de largo σ = 6·q·b·(b/2 + c)/t² | 1.31 | sust | 8.4 | 6.39 | 3.0 | ✔ |
| P1-DRV eje 316 | Torsión máx. del controlador + fatiga (sizing) | 02_calculos.md §7 | — | metal | — | 4.0 | 2.0 | ✔ |
