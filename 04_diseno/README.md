# 04 — Diseño detallado

- `params.py` deriva toda la geometría de `inputs.yaml` + `resultados/sizing.json`.
- `piezas/P1-<SUB>-<NN>_<nombre>.py`: un script por pieza (`META`, `build()`, `placements()`, `checks()`).
- `build_all.py` exporta STEP + STL (orientación de impresión) y `resultados/manifest.json`.
- `verify_parts.py` (exit ≠ 0 si falla): envolvente, manifold, cotas críticas, interferencias (barrido de dirección × basculación).
- `structural.py`: FS por pieza y caso de carga (tabla en 02 §9).
- `planos.py`: planos SVG acotados de piezas torneadas/mecanizadas → `planos/`.

## Lista de piezas

<!-- AUTO:parts_totals -->
Total impreso: **1.02 kg** de PETG, **57 h** de impresión (a 18.0 g/h); masa de la unidad de jet (CAD, sin motor): **24.08 kg**.
<!-- /AUTO:parts_totals -->

<!-- AUTO:parts_list -->
| ID | Función | Envolvente [mm] | Material | Proceso | Cant. | Caso de carga dominante | Orientación de impresión | g c/u | h c/u |
|---|---|---|---|---|---|---|---|---|---|
| P1-CTL-01_placa_espejo | Placa interior del espejo para M66 + 2 prensaestopas (Al 5083 6 mm) | 6×342×90 | Al 5083 | torneada | 1 | Reacción del M66 (momento de dirección / brazo) en el espejo | — | 476 | — |
| P1-CTL-02_caja_acel | Caja PETG de palancas con sensor hall | 181×78×68 | PETG | impresa | 1 | Pisada/golpe 300 N sobre la tapa [SUPUESTO]; sin cargas de mando (van a P1-CTL-08) | Tapa sobre la cama (ranuras planas, sin soportes); ala arriba. 0,2 mm, 5 perímetros, 30 % giroide | 103 | 5.7 |
| P1-CTL-03_soporte_kill | Soporte PETG del kill switch con cordón y de la seta | 100×130×55 | PETG | impresa | 1 | Tirón del cordón 150 N [SUPUESTO] + golpe de mano sobre la seta 200 N [SUPUESTO] | Base sobre la cama; la cara inclinada a 45° no necesita soportes. 0,2 mm, 5 perímetros | 120 | 6.7 |
| P1-CTL-04_pasamuros_m66 | Pasamuros 316 del M66 (brida, M20, rosca 7/8" UNF) | 43×32×32 | AISI 316 | torneada | 1 | Tiro/empuje del M66 contra la placa del espejo | — | 128 | — |
| P1-CTL-05_prensaestopas | Prensaestopas M16 IP68 (comprado) | 27×24×24 | referencia | comprada | 2 | — | — | 15 | — |
| P1-CTL-06_terminal_m66 | Tubo terminal del cable M66 (comprado) | 230×22×22 | Acero | comprada | 1 | — | — | 350 | — |
| P1-CTL-07_terminal_mach5_consola | Terminal Mach5 en la consola — comprado | 22×22×140 | Acero | comprada | 1 | — | — | 120 | — |
| P1-CTL-08_placa_central | Placa central de palancas Al 5083 6 mm (eje, enclavamiento, grapas Mach5) | 120×77×182 | Al 5083 | torneada | 1 | Fuerza de mano 100 N en el pomo (150 mm) contra el enclavamiento | — | 219 | — |
| P1-CTL-09_palanca_acel | Palanca del acelerador Al 6061 8 mm | 60×8×191 | Al 6061-T6 | torneada | 1 | 100 N en el pomo (150 mm) [SUPUESTO] | — | 102 | — |
| P1-CTL-10_palanca_bucket | Palanca del bucket Al 6061 8 mm con manivela del Mach5 | 79×28×165 | Al 6061-T6 | torneada | 1 | 100 N en el pomo contra el enclavamiento / tope | — | 116 | — |
| P1-CTL-11_eje_palancas | Eje Ø12 con cabeza portaimán (316) | 18×38×18 | AISI 316 | torneada | 1 | Flexión y torsión: 100 N en el pomo del acelerador | — | 39 | — |
| P1-CTL-12_perno_enclav | Perno de enclavamiento Ø6 × 13 (316) | 6×13×6 | AISI 316 | torneada | 2 | Corte: 100 N en el pomo del bucket contra el enclavamiento | — | 3 | — |
| P1-CTL-13_varilla_consola | Varilla Ø6,4 + rótula M6 del Mach5 en la consola (comprada) | 18×8×130 | AISI 316 | comprada | 1 | — | — | 40 | — |
| P1-CTL-20_consola_ref | Consola (referencia, medir la real) | 250×360×532 | referencia | referencia | 1 | — | — | 0 | — |
| P1-CTL-21_volante_ref | Volante Ø320 + timonería T85 (referencia) | 242×320×320 | referencia | referencia | 1 | — | — | 0 | — |
| P1-DRV-01_shaft | Eje Ø20 AISI 316 torneado: impulsor (pasador de corte) → sello → 2×7204 → acople | 470×25×25 | AISI 316 | torneada | 1 | Par T_max del controlador y par de corte del pasador; empuje Fa a punto fijo; velocidad crítica | — | 1180 | — |
| P1-DRV-02_seal_housing | Caja del sello mecánico 316: espigón Ø42, brida 4×M6, cámara mojada, linterna de goteo | 44×70×70 | AISI 316 | torneada | 1 | Presión de diseño de la bomba 0,2 MPa + resorte del sello; bulones M6 al buje de la toma | — | 311 | — |
| P1-DRV-03_bearing_bracket | Pórtico Al 6082 sobre el conducto: alojamiento 2×7204 BEP, 4×M8 a la placa base | 150×296×173 | Al 5052/6082 | torneada | 1 | Empuje Fa a punto fijo + reacción radial + 3 g vertical del tren; bulones M8 a la placa base de Al | — | 1715 | — |
| P1-DRV-04_bearing_7204BEP | Rodamiento SKF 7204 BEP (par en O), comprado | 14×47×47 | Acero | comprada | 2 | Empuje Fa + reacción radial (L10 en sizing) | — | 110 | — |
| P1-DRV-05_locknut_KM4 | Tuerca KM4 M20×1 + arandela MB4 (comprada) | 8×32×32 | Acero | comprada | 1 | Empuje en reversa (≤ Fa) y precarga | — | 25 | — |
| P1-DRV-06_bearing_cover | Tapa delantera Al de rodamientos (4×M5), toma el empuje hacia proa | 7×65×65 | Al 5052/6082 | torneada | 1 | Empuje Fa a punto fijo hacia proa: flexión de la tapa entre el aro y los M5 | — | 44 | — |
| P1-DRV-07_mech_seal_MG1_20 | Sello mecánico MG1 Ø20 carbón/SiC (comprado) | 32×35×35 | referencia | comprada | 1 | Presión del conducto, 5 m/s | — | 60 | — |
| P1-DRV-08_coupling_rotex24 | Acople Rotex 24 Ø20 / Ø motor (comprado; cubo de eje refrentado) | 72×55×55 | referencia | comprada | 1 | Par T_max del controlador; par de corte del pasador (pico) | — | 600 | — |
| P1-ELE-01_esc_stand | Base elevada PETG del controlador IP65 (4 × M6 al piso, 4 insertos M5 para la capota) | 208×138×60 | PETG | impresa | 1 | Peso del ESC + capota a 3 g vertical y 1 g lateral; tirón de cables | Base abierta sobre la cama; tablero arriba (puentes de 3,2 mm entre nervios, sin soportes). | 263 | 14.6 |
| P1-ELE-02_esc_hood | Capota antisalpicaduras PETG del controlador (4 × M5 a la base) | 208×126×55 | PETG | impresa | 1 | Apriete de la almohadilla EPDM (4 × M5) y 3 g vertical del ESC hacia arriba (golpe de ola) | Techo sobre la cama, paredes y nervios hacia arriba (sin soportes). | 207 | 11.5 |
| P1-ELE-03_cooling_outlet | Pasacasco 316 de salida del agua de refrigeración (testigo en el espejo) | 37×28×28 | AISI 316 | comprada | 1 | — | — | 45 | — |
| P1-ELE-04_esc | Controlador VESC de la selección (FSESC 75350 con caja de agua) | 200×95×50 | referencia | comprada | 1 | — | — | 2000 | — |
| P1-INT-01_conducto | Conducto de toma enrasada Al 5083 soldado: rampa C2, transición a Ø D_bore, brida bomba, buje del sello, chimenea de inspección | 447×198×345 | Al 5083 | torneada | 1 | Presión interna −p_pump_max…+p_pump_max, golpe de fondo, 3 g agua; empuje NO pasa por acá | — | 4709 | — |
| P1-INT-02_placa_base | Placa base de la toma Al 5083 10 mm: cuerpo enrasado + ala abulonada al casco, cuña de la rampa, roscas del conducto y del soporte de rodamientos | 565×350×10 | Al 5083 | torneada | 1 | Golpe de fondo, empuje del tren por el soporte de rodamientos, tracción de los bulones del conducto | — | 3044 | — |
| P1-INT-03_rejilla | Rejilla 316: 7 pletinas perfiladas 4 × 20 longitudinales enrasadas, pletina de popa y tirante de proa, 4 × M5 A4 | 368×182×21 | AISI 316 | torneada | 1 | Rejilla tapada a la presión de cierre de la bomba; golpe de objeto 200 N en el centro de una barra | — | 1599 | — |
| P1-INT-04_tapa_inspeccion | Tapa PETG Ø160 × 10 de la chimenea de inspección, O-ring de cara, 4 × M6 | 160×160×19 | PETG | impresa | 1 | Presión interna de la toma (succión de cierre / recuperación a 30 km/h) sobre Ø de la junta | Cara de la ranura del O-ring y del hexágono de la tuerca sobre la cama (fondos lisos), resalte arriba, 100 % relleno | 327 | 18.2 |
| P1-MOT-01_motor | Motor de la selección (MTI120116: Ø120 × 116, refrigerado por agua) | 146×120×120 | referencia | comprada | 1 | Par de reacción T_max sobre P1-MOT-02; 3 g vertical | — | 4400 | — |
| P1-MOT-02_motor_mount | Soporte del motor Al: placa a la cara del motor + pies al piso (4×M8) | 76×190×146 | Al 5052/6082 | torneada | 1 | Par de reacción T_max del controlador + 3 g vertical del motor; sin empuje | — | 842 | — |
| P1-PMP-01_housing | Carcasa Al 6061-T6: brida de la toma, asiento del anillo y del estator, puerto de agua | 163×193×193 | Al 6061-T6 | torneada | 1 | Presión interna 0,2 MPa; reacción del estator; momentos de boquilla/bucket en bridas | — | 1690 | — |
| P1-PMP-02_wear_ring | Anillo de desgaste 316 torneado, prensado en la carcasa; holgura de punta tip_clr | 69×143×143 | AISI 316 | torneada | 1 | Presión de la bomba (apoyado en la carcasa); roce de piedras | — | 1187 | — |
| P1-PMP-03_impeller | Impulsor axial de 5 álabes, cubo Ø66 con nariz, pasador de corte (sin chavetero) | 69×132×132 | AISI 316 | torneada | 1 | Par máx. del controlador + empuje axial; corte del pasador (piedra) | — | 1333 | — |
| P1-PMP-04_pin_band | Anillo retén 316 que tapa los extremos del pasador de corte | 16×66×66 | AISI 316 | torneada | 1 | Centrífuga a n máx.; retención del pasador | — | 76 | — |
| P1-PMP-05_shear_pin | Pasador de corte Al 6061-T6 (fusible de par del impulsor) | 4×59×4 | Al 6061-T6 | torneada | 1 | Par del controlador (no corta); corta a T_cut (piedra) | — | 2 | — |
| P1-PMP-06_stator | Estator Al 6061-T6 de 7 álabes con camisa, cubo con buje de agua y cono de cola | 169×143×143 | Al 6061-T6 | torneada | 1 | Reacción del par del rotor en los álabes; carga radial del buje; presión | — | 1570 | — |
| P1-PMP-07_water_bushing | Buje Ø20 lubricado por agua en el cubo del estator (2.º apoyo del eje) | 30×28×28 | POM-C | torneada | 1 | Carga radial del eje (desbalance + hidráulica) | — | 12 | — |
| P1-PMP-08_fixed_nozzle | Tobera fija Al: contracción a D_noz, rótula de la boquilla y resalte del sello de espejo | 143×186×186 | Al 6061-T6 | torneada | 1 | Presión interna 0,2 MPa; reacción de la placa de espejo por el O-ring | — | 1594 | — |
| P1-PMP-09_transom_plate | Placa de espejo Al 5083 con cuello coaxial, sello radial sobre la tobera y orejas de pivote | 44×211×196 | Al 5083 | torneada | 1 | F lateral de la boquilla y F del bucket en las orejas; sello del casco | — | 419 | — |
| P1-PMP-10_transom_gasket | Junta NBR 2 mm del espejo (bajo la placa P1-PMP-09) | 2×211×196 | NBR | comprada | 1 | Compresión de los 7 × M6 | — | 35 | — |
| P1-PMP-11_pivot_bushing | Buje POM-C de pivote de la boquilla en las orejas de la placa de espejo (×2) | 12×12×26 | POM-C | torneada | 2 | F lateral de la boquilla / F del bucket (aplastamiento) | — | 2 | — |
| P1-REF-01_casco | Casco de referencia (popa 1,4 m): fondo con astilla muerta y paño plano, pantoque, costados, espejo; recorte de la toma y agujero del espejo | 1400×798×516 | referencia | referencia | 1 | — | — | 0 | — |
| P1-REV-01_bucket | Bucket de reversa Al 5083 4 mm (cuchara + brazos + nervio) | 195×123×143 | Al 5083 | torneada | 1 | Chorro desviado en reversa (R12: 1,4 kN) × impacto 2; presión dinámica en la chapa | — | 539 | — |
| P1-REV-02_perno_bucket | Perno con hombro Ø10 × 9,8 / M8 del bucket (316) | 16×34×16 | AISI 316 | torneada | 2 | Corte simple + flexión: reacción del bucket (R12 1,4 kN × impacto 2) / 2 | — | 23 | — |
| P1-REV-03_buje_bucket | Buje con brida POM-C Ø10,1/Ø14 × 8 + brida Ø20 × 1 | 20×9×20 | POM-C | torneada | 2 | Aplastamiento: reacción del bucket / 2 | — | 1 | — |
| P1-REV-04_embolo | Émbolo indexador A4 M20 / perno Ø12 (comprado) | 30×38×30 | AISI 316 | comprada | 1 | Corte del perno Ø10: momento del bucket en reversa / REV_lock_r | — | 160 | — |
| P1-REV-05_soporte_mach5 | Soporte de la vaina del Mach5 (Al 5083 6 mm) | 80×93×129 | Al 5083 | torneada | 1 | Reacción del cable al mover el bucket (sin carga del chorro: la toma el émbolo) | — | 187 | — |
| P1-REV-06_perno_varilla | Tornillo con hombro Ø8 × 10 / M6 (316) | 13×22×13 | AISI 316 | torneada | 1 | Fuerza de maniobra del Mach5 (bucket sin carga del chorro) | — | 9 | — |
| P1-REV-07_terminal_mach5 | Terminal Mach5 (vaina + cabeza) en la boquilla — comprado | 22×22×140 | Acero | comprada | 1 | — | — | 120 | — |
| P1-REV-08_varilla_mach5 | Varilla Ø6,4 + rótula M6 del Mach5 (comprada) | 18×8×94 | AISI 316 | comprada | 1 | — | — | 40 | — |
| P1-STE-01_boquilla | Boquilla direccional con orejas de pivote, torre del yugo y orejas del bucket | 144×104×165 | Al 6061-T6 | torneada | 1 | Desvío del chorro F_steer (R12: 364 N) + reacciones del bucket (R12: 1,4 kN, impacto ×2) | — | 845 | — |
| P1-STE-02_perno_sup | Tornillo con hombro Ø8 / M6 del pivote superior (316 estirado) | 14×14×49 | AISI 316 | torneada | 1 | Flexión en doble apoyo + corte: reacción superior (bucket R12 + dirección) | — | 20 | — |
| P1-STE-03_arandela_pom | Arandela de empuje POM-C Ø8,4/Ø18 × 1 | 18×18×1 | POM-C | torneada | 3 | Empuje axial: peso de la boquilla + bucket y componente vertical del chorro | — | 0 | — |
| P1-STE-04_brida_yugo | Brida del yugo de dirección (Al 5083 20 mm) | 51×126×20 | Al 5083 | torneada | 1 | Par de dirección + flexión del poste (biela M66) | — | 159 | — |
| P1-STE-05_perno_inf | Espárrago con hombro Ø8 / M6 del pivote inferior (316) | 8×8×33 | AISI 316 | torneada | 1 | Flexión en voladizo + corte: F_s/2 | — | 11 | — |
| P1-STE-06_poste | Poste del yugo Ø22 con brida Ø44 y M16 (6061-T6) | 44×44×140 | Al 6061-T6 | torneada | 1 | Flexión + torsión por la fuerza de la biela del M66 | — | 151 | — |
| P1-STE-07_brazo | Brazo del yugo con rótula M8 (Al 5083 10 mm) | 61×32×10 | Al 5083 | torneada | 1 | Fuerza de la biela del M66 (momento de dirección / brazo) | — | 34 | — |
<!-- /AUTO:parts_list -->

## Verificación

<!-- AUTO:verify -->
Resultado: **FALLAS** — 60 piezas, 8718 pares×estados de interferencia; boquilla δ ∈ [-25.0, 0.0, 25.0]°, bucket {arriba, abajo}; masa de la unidad de jet (CAD) 24.08 kg.

Fallas:
- P1-CTL-14: falta en manifest (no construida)
- P1-REV-01: cota crítica 'abajo: punto más bajo sobre la quilla (z_bote, ±δmax) [mm]' = 3.746 (ref >= 5.0)
- P1-REV-09: falta en manifest (no construida)
- P1-REV-10: falta en manifest (no construida)
- P1-STE-08: falta en manifest (no construida)
<!-- /AUTO:verify -->

## Ajustes (iniciales, a confirmar con probetas P1.1–P1.2)

| Ajuste | Valor CAD | Nota |
|---|---|---|
| Holgura general pieza impresa / pieza metálica | 0,25 mm diametral | Peine de holguras P1.1 |
| Rodamiento A 6202 en cartucho de Al / rodamiento B en puente impreso | Ø35 M7 (prensado) / Ø35 + 0,10 (flotante) | A localiza; B flota con 1 mm de juego axial |
| Buje igus H370 en portabuje impreso | Ø18 − 0,05 | P1.2 |
| Perno Ø12 en mejillas / buje POM del pivote | +0,10 / +0,25 | Perno fijo en mejillas, gira en el buje |
| Tubo Ø40 en cuna / carcasa inferior | +0,30 | Apriete por tapa / perno pasante |
| Eje Ø16 en bujes igus H370 | ajuste de igus (Ø16 h9 en buje prensado) | Apto bajo agua (igus) |
| Ranura de O-ring (caja ESC) | ver ELE-01 | Pasada 2: cordón 3,53 mm (research/R05) |
| Roscas | tuerca A4 cautiva (estándar); insertos de latón solo M4 de la tapa de la caja ESC (zona seca) | Nunca Loctite 243 sobre PETG |
