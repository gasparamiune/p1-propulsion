# 04 — Diseño detallado (waterjet P1-J)

Todo se regenera con `python run_all.py` desde la raíz (corrido completo con FEA fino: más de una hora; `--fast` usa
mallas gruesas y no corre el FEA); cada script también corre solo.

| Archivo | Qué hace |
|---|---|
| `params.py` | Deriva la geometría de `inputs.yaml` + `resultados/sizing.json` (D impulsor, D tobera, eje, toma, alturas) y carga los módulos `params_toma/bomba/tren/direccion.py` (`extend(d)`), que agregan las interfaces de cada grupo. Define los marcos: **BOTE** (x hacia proa desde la cara exterior del espejo, z desde la quilla) y **JET** (origen en la cara de entrada del impulsor, X hacia popa por el eje); `loc_jet`, `loc_steer`, `loc_bucket`. |
| `piezas/P1-<SUB>-<NN>_<nombre>.py` | Un script por pieza: `META` (id, material, proceso impresa/torneada/comprada/referencia, cantidad, marco boat/jet/drive/steer/bucket, grupo, `allow`), `build()`, `placements()`, `checks()`. SUB: INT toma · PMP bomba · DRV tren · MOT motor · STE dirección · REV reversa · CTL mandos · ELE electrónica · BAT batería · REF casco de referencia. |
| `build_all.py` | Exporta STEP + STL (orientación de impresión), `step/P1-ASM_marcha.step.gz` y `resultados/manifest.json` (masas CAD por grupo). |
| `verify_parts.py` | Exit ≠ 0 si falla: sólido válido/manifold, envolvente de impresora, `checks()` de cada pieza, interferencias en todos los estados (boquilla −25/0/+25° × bucket arriba/abajo) contra bomba, toma, tren y casco. |
| `structural.py` + `structural_*.py` | FS por pieza y caso de carga (≥ 3 PETG, ≥ 2 metal) → 02 §9. FEA de las piezas críticas en `fea/`. |
| `planos.py` + `planos_*.py` | Planos SVG acotados de las piezas mecanizadas/soldadas → `planos/`. |
| `electronica/` | Cableado, cálculo de cables/fusibles, firmware del acelerador (perfil costa/abierto, bucket, kill). |
| `probetas/` | Probetas de PETG (holguras, roscas, O-ring) para calibrar antes de imprimir las piezas. |
| `visor/` | `build_visor.py` → visor web 3D (ensamblado, explosión, dirección, bucket, demo) para Jorge. |

## Lista de piezas

<!-- AUTO:parts_totals -->
Total impreso: **1.05 kg** de PETG, **58 h** de impresión (a 18.0 g/h); masa de la unidad de jet (CAD, sin motor): **25.94 kg**.
<!-- /AUTO:parts_totals -->

<!-- AUTO:parts_list -->
| ID | Función | Envolvente [mm] | Material | Proceso | Cant. | Caso de carga dominante | Orientación de impresión | g c/u | h c/u |
|---|---|---|---|---|---|---|---|---|---|
| P1-BAT-01_bateria | Batería LFP de la selección (modelo de referencia, una por rama) | 532×207×215 | referencia | comprada | 2 | — | — | 19800 | — |
| P1-CTL-01_placa_espejo | Placa interior del espejo para M66 + 2 prensaestopas (Al 5083 6 mm) | 6×350×90 | Al 5083 | torneada | 1 | Reacción del M66 (momento de dirección / brazo) en el espejo | — | 487 | — |
| P1-CTL-02_caja_acel | Caja PETG de palancas con sensor hall | 184×82×68 | PETG | impresa | 1 | Mano apoyada 150 N sobre la tapa [SUPUESTO: structural_direccion, FEA]; sin cargas de mando (van a P1-CTL-08) | Tapa sobre la cama (ranuras planas, sin soportes); ala arriba. 0,2 mm, 5 perímetros, 30 % giroide | 134 | 7.4 |
| P1-CTL-03_soporte_kill | Soporte PETG del kill switch con cordón y de la seta | 100×130×55 | PETG | impresa | 1 | Tirón del cordón 150 N [SUPUESTO] + golpe de mano sobre la seta 200 N [SUPUESTO] | Base sobre la cama; la cara inclinada a 45° no necesita soportes. 0,2 mm, 5 perímetros | 120 | 6.7 |
| P1-CTL-04_pasamuros_m66 | Pasamuros 316 del M66 (brida, M20, rosca 7/8" UNF) | 43×32×32 | AISI 316 | torneada | 1 | Tiro/empuje del M66 contra la placa del espejo | — | 128 | — |
| P1-CTL-05_prensaestopas | Prensaestopas M16 IP68 (comprado) | 27×24×24 | referencia | comprada | 2 | — | — | 15 | — |
| P1-CTL-06_terminal_m66 | Tubo terminal del cable M66 (comprado) | 230×22×22 | Acero | comprada | 1 | — | — | 350 | — |
| P1-CTL-07_terminal_mach5_consola | Terminal Mach5 en la consola — comprado | 22×22×140 | Acero | comprada | 1 | — | — | 120 | — |
| P1-CTL-08_placa_central | Placa central de palancas Al 5083 6 mm (eje, enclavamiento, grapas Mach5) | 120×77×182 | Al 5083 | torneada | 1 | Fuerza de mano 100 N en el pomo (150 mm) contra el enclavamiento | — | 219 | — |
| P1-CTL-09_palanca_acel | Palanca del acelerador Al 6061 8 mm | 60×8×191 | Al 6061-T6 | torneada | 1 | 100 N en el pomo (150 mm) [SUPUESTO] | — | 102 | — |
| P1-CTL-10_palanca_bucket | Palanca del bucket Al 6061 8 mm con manivela del Mach5 | 79×45×165 | Al 6061-T6 | torneada | 1 | 100 N en el pomo contra el enclavamiento / tope | — | 134 | — |
| P1-CTL-11_eje_palancas | Eje Ø12 con cabeza portaimán (316) | 18×38×18 | AISI 316 | torneada | 1 | Flexión y torsión: 100 N en el pomo del acelerador | — | 39 | — |
| P1-CTL-12_perno_enclav | Perno de enclavamiento Ø6 × 13 (316) | 6×13×6 | AISI 316 | torneada | 2 | Corte: 100 N en el pomo del bucket contra el enclavamiento | — | 3 | — |
| P1-CTL-13_varilla_consola | Varilla Ø6,4 + rótula M6 del Mach5 en la consola (comprada) | 18×8×130 | AISI 316 | comprada | 1 | — | — | 40 | — |
| P1-CTL-14_gatillo | Gatillo del desbloqueo (Al 6061 6 mm) con barra igualadora 316 de los dos Bowden | 46×10×57 | Al 6061-T6 | torneada | 1 | Apriete de la mano 100 N [SUPUESTO] en la hoja; tiro de los dos cables por la barra igualadora | — | 14 | — |
| P1-CTL-20_consola_ref | Consola (referencia, medir la real) | 250×360×532 | referencia | referencia | 1 | — | — | 0 | — |
| P1-CTL-21_volante_ref | Volante Ø320 + timonería T85 (referencia) | 242×320×320 | referencia | referencia | 1 | — | — | 0 | — |
| P1-DRV-01_shaft | Eje Ø20 AISI 316 torneado: impulsor (pasador de corte) → sello → 2×7204 → acople | 470×26×26 | AISI 316 | torneada | 1 | Par T_max del controlador y par de corte del pasador; empuje Fa a punto fijo; velocidad crítica | — | 1181 | — |
| P1-DRV-02_seal_housing | Caja del sello mecánico 316: espigón Ø42, brida 4×M6, cámara mojada, linterna de goteo | 44×70×70 | AISI 316 | torneada | 1 | Presión de diseño de la bomba 0,2 MPa + resorte del sello; bulones M6 al buje de la toma | — | 311 | — |
| P1-DRV-03_bearing_bracket | Pórtico Al 6082 sobre el conducto: alojamiento 2×7204 BECBP, 4×M8 a la placa base | 150×296×173 | Al 5052/6082 | torneada | 1 | Empuje Fa a punto fijo + reacción radial + 3 g vertical del tren; bulones M8 a la placa base de Al | — | 1642 | — |
| P1-DRV-04_bearing_7204BEP | Rodamiento SKF 7204 BECBP apareable universal (par en O), comprado | 14×47×47 | Acero | comprada | 2 | Empuje Fa + reacción radial (L10 en sizing) | — | 110 | — |
| P1-DRV-05_locknut_KM4 | Tuerca KM4 M20×1 + arandela MB4 (comprada) | 8×32×32 | Acero | comprada | 1 | Empuje en reversa (≤ Fa) y precarga | — | 25 | — |
| P1-DRV-06_bearing_cover | Tapa delantera Al de rodamientos (4×M5), toma el empuje hacia proa | 7×65×65 | Al 5052/6082 | torneada | 1 | Empuje Fa a punto fijo hacia proa: flexión de la tapa entre el aro y los M5 | — | 44 | — |
| P1-DRV-07_mech_seal_MG1_20 | Sello mecánico MG1 Ø20 carbón/SiC (comprado) | 32×35×35 | referencia | comprada | 1 | Presión del conducto, 5 m/s | — | 60 | — |
| P1-DRV-08_coupling_rotex24 | Acople Rotex 24 Ø20 / Ø motor (comprado; cubo de eje refrentado) | 72×55×55 | referencia | comprada | 1 | Par T_max del controlador; par de corte del pasador (pico) | — | 600 | — |
| P1-ELE-01_esc_stand | Base elevada PETG del controlador IP65 (4 × M6 al piso, 4 insertos M5 para la capota) | 208×138×60 | PETG | impresa | 1 | Peso del ESC + capota a 3 g vertical y 1 g lateral; tirón de cables | Base abierta sobre la cama; tablero arriba (puentes de 3,2 mm entre nervios, sin soportes). | 263 | 14.6 |
| P1-ELE-02_esc_hood | Capota antisalpicaduras PETG del controlador (4 × M5 a la base) | 208×126×55 | PETG | impresa | 1 | Apriete de la almohadilla EPDM (4 × M5) y 3 g vertical del ESC hacia arriba (golpe de ola) | Techo sobre la cama, paredes y nervios hacia arriba (sin soportes). | 207 | 11.5 |
| P1-ELE-03_cooling_outlet | Pasacasco 316 de salida del agua de refrigeración (testigo en el espejo) | 37×28×28 | AISI 316 | comprada | 1 | — | — | 45 | — |
| P1-ELE-04_esc | Controlador VESC de la selección (FSESC 75350 con caja de agua) | 200×95×50 | referencia | comprada | 1 | — | — | 2000 | — |
| P1-INT-01_conducto | Conducto de toma enrasada Al 5083 soldado: rampa C2, transición a Ø D_bore, brida bomba, buje del sello, chimenea de inspección | 447×198×350 | Al 5083 | torneada | 1 | Presión interna −p_pump_max…+p_pump_max, golpe de fondo, 3 g agua; empuje NO pasa por acá | — | 4699 | — |
| P1-INT-02_placa_base | Placa base de la toma Al 5083 10 mm: cuerpo enrasado + ala abulonada al casco, cuña de la rampa, roscas del conducto y del soporte de rodamientos | 565×350×10 | Al 5083 | torneada | 1 | Golpe de fondo, empuje del tren por el soporte de rodamientos, tracción de los bulones del conducto | — | 3042 | — |
| P1-INT-03_rejilla | Rejilla 316: pletinas perfiladas 4 × 21 longitudinales (luz ≤ 12,5) enrasadas, pletina de popa y tirante de proa, 4 × M5 A4 aislados | 368×182×21 | AISI 316 | torneada | 1 | Rejilla tapada a la presión de cierre de la bomba; golpe de objeto 200 N en el centro de una barra | — | 2014 | — |
| P1-INT-04_tapa_inspeccion | Tapa PETG Ø160 × 10 de la chimenea de inspección, O-ring de cara, 4 × M6 | 160×160×19 | PETG | impresa | 1 | Presión interna de la toma (succión de cierre / recuperación a 30 km/h) sobre Ø de la junta | Cara de la ranura del O-ring y del hexágono de la tuerca sobre la cama (fondos lisos), resalte arriba, 100 % relleno | 327 | 18.2 |
| P1-MOT-01_motor | Motor de la selección (MTI120116: Ø120 × 116, refrigerado por agua) | 146×120×120 | referencia | comprada | 1 | Par de reacción T_max sobre P1-MOT-02; 3 g vertical | — | 4400 | — |
| P1-MOT-02_motor_mount | Soporte del motor Al: placa a la cara del motor + pies al piso (4×M8) | 76×190×146 | Al 5052/6082 | torneada | 1 | Par de reacción T_max del controlador + 3 g vertical del motor; sin empuje | — | 842 | — |
| P1-PMP-01_housing | Carcasa Al 6061-T6: brida de la toma, asiento del anillo y del estator, puerto de agua | 166×193×193 | Al 6061-T6 | torneada | 1 | Presión interna 0,2 MPa; reacción del estator; momentos de boquilla/bucket en bridas | — | 1492 | — |
| P1-PMP-02_wear_ring | Anillo de desgaste 316 torneado, prensado en la carcasa; holgura de punta tip_clr | 69×143×143 | AISI 316 | torneada | 1 | Presión de la bomba (apoyado en la carcasa); roce de piedras | — | 1187 | — |
| P1-PMP-03_impeller | Impulsor axial de 5 álabes, cubo Ø66 con nariz, 2 semipasadores de corte (sin chavetero) | 69×132×132 | AISI 316 | torneada | 1 | Par máx. del controlador + empuje axial; corte del pasador (piedra) | — | 1336 | — |
| P1-PMP-04_pin_band | Anillo retén 316 que tapa los extremos del pasador de corte | 16×66×66 | AISI 316 | torneada | 1 | Centrífuga a n máx.; retención del pasador | — | 76 | — |
| P1-PMP-05_shear_pin | 2 semipasadores de corte Al 6061-T6 (fusible de par del impulsor, cambiables en el eje) | 4×30×4 | Al 6061-T6 | torneada | 2 | Par del controlador (no corta); corta a T_cut (piedra) | — | 1 | — |
| P1-PMP-06_stator | Estator Al 6061-T6 de 7 álabes con camisa, cubo con buje de agua y cono de cola | 169×143×143 | Al 6061-T6 | torneada | 1 | Reacción del par del rotor en los álabes; carga radial del buje; presión | — | 1518 | — |
| P1-PMP-07_water_bushing | Buje Ø20 lubricado por agua en el cubo del estator (2.º apoyo del eje) | 30×28×28 | POM-C | torneada | 1 | Carga radial del eje (desbalance + hidráulica) | — | 12 | — |
| P1-PMP-08_fixed_nozzle | Tobera fija Al: contracción a D_noz, rótula de la boquilla y resalte del sello de espejo | 151×161×161 | Al 6061-T6 | torneada | 1 | Presión interna 0,2 MPa; reacción de la placa de espejo por el O-ring | — | 1408 | — |
| P1-PMP-09_transom_plate | Placa de espejo Al 5083 con cuello coaxial, sello radial sobre la tobera y orejas de pivote | 44×216×199 | Al 5083 | torneada | 1 | F lateral de la boquilla y F del bucket en las orejas; sello del casco | — | 449 | — |
| P1-PMP-10_transom_gasket | Junta NBR 2 mm del espejo (bajo la placa P1-PMP-09) | 2×216×199 | NBR | comprada | 1 | Compresión de los 6 × M6 | — | 35 | — |
| P1-PMP-11_pivot_bushing | Buje POM-C de pivote de la boquilla en las orejas de la placa de espejo (×2) | 12×12×26 | POM-C | torneada | 2 | F lateral de la boquilla / F del bucket (aplastamiento) | — | 2 | — |
| P1-REF-01_casco | Casco de referencia (popa 1,4 m): fondo con astilla muerta y paño plano, pantoque, costados, espejo; recorte de la toma y agujero del espejo | 1400×798×516 | referencia | referencia | 1 | — | — | 0 | — |
| P1-REV-01_bucket | Bucket de reversa Al 5083 8 mm (cuchara + brazos + nervio), traba en cada brazo (cada una lleva todo M_h) | 203×149×170 | Al 5083 | torneada | 1 | Chorro desviado en reversa (R12: 1,4 kN) × impacto 2; presión dinámica en la chapa | — | 1233 | — |
| P1-REV-02_perno_bucket | Pivote del bucket: espaciador 316 (muñón Ø20 h7, brida Ø36, piloto Ø16 h6) + tornillo M12 A4-80 + tuerca DIN 985 | 36×68×36 | AISI 316 | torneada | 2 | Reacción del pivote = chorro/2 + traba con M_h completo (R12, una traba sola): flexión del muñón y apertura de la unión | — | 162 | — |
| P1-REV-03_buje_bucket | Buje con brida POM-C del pivote del bucket (Ø20,1/Ø24 × 18 + brida Ø30 × 1), escariado después de prensar | 30×19×30 | POM-C | torneada | 2 | Presión: reacción del pivote (chorro/2 + traba con M_h completo, R12 y reversa de sizing) | — | 4 | — |
| P1-REV-04_embolo | Émbolo de traba propio: cuerpo M24×1,5 y perno Ø16 h9 en AISI 316 + resorte inox, uno por oreja ±Y | 42×76×36 | AISI 316 | torneada | 2 | Perno Ø16: flexión + corte con M_h completo en una traba (R12) / REV_lock_r | — | 313 | — |
| P1-REV-05_soporte_mach5 | Soporte de la vaina del Mach5 (Al 5083 6 mm) | 80×100×129 | Al 5083 | torneada | 1 | Reacción del cable al mover el bucket (sin carga del chorro: la toma el émbolo) | — | 189 | — |
| P1-REV-06_perno_varilla | Tornillo con hombro Ø8 × 10 / M6 (316) | 13×26×13 | AISI 316 | torneada | 1 | Fuerza de maniobra del Mach5 (bucket sin carga del chorro) | — | 10 | — |
| P1-REV-07_terminal_mach5 | Terminal Mach5 (vaina + cabeza) en la boquilla — comprado | 22×22×140 | Acero | comprada | 1 | — | — | 120 | — |
| P1-REV-08_varilla_mach5 | Varilla Ø6,4 + rótula M6 del Mach5 (comprada) | 18×8×94 | AISI 316 | comprada | 1 | — | — | 40 | — |
| P1-REV-09_soporte_bowden | Soporte de reenvío del desbloqueo: base + montante Al 5083 soldados, 2 balancines 1:1 y 2 pestañas de reguladores M6 | 48×80×51 | Al 5083 | torneada | 1 | Tiro de diseño por cable (mano 100 N en el gatillo P1-CTL-14 repartida por el igualador) [CALCULADO] | — | 69 | — |
| P1-REV-10_bowden_embolo | Bowden inox de liberación de cada émbolo (extremo de la boquilla, comprado; ×2) | 55×10×86 | AISI 316 | comprada | 2 | — | — | 60 | — |
| P1-STE-01_boquilla | Boquilla direccional con orejas de pivote, torre del yugo y orejas del bucket | 144×104×170 | Al 6061-T6 | torneada | 1 | Desvío del chorro F_steer (R12: 364 N) + reacciones del bucket (R12: 1,4 kN, impacto ×2) | — | 1048 | — |
| P1-STE-02_perno_sup | Tornillo con hombro Ø8 / M6 del pivote superior (316 estirado) | 14×14×49 | AISI 316 | torneada | 1 | Flexión en doble apoyo + corte: reacción superior (bucket R12 + dirección) | — | 20 | — |
| P1-STE-03_arandela_pom | Arandela de empuje POM-C Ø8,4/Ø18 × 1 | 18×18×1 | POM-C | torneada | 3 | Empuje axial: peso de la boquilla + bucket y componente vertical del chorro | — | 0 | — |
| P1-STE-04_brida_yugo | Brida del yugo de dirección (Al 5083 20 mm) | 55×135×20 | Al 5083 | torneada | 1 | Par de dirección + flexión del poste (biela M66) | — | 171 | — |
| P1-STE-05_perno_inf | Espárrago con hombro Ø8 / M6 del pivote inferior (316) | 8×8×33 | AISI 316 | torneada | 1 | Flexión en voladizo + corte: F_s/2 | — | 11 | — |
| P1-STE-06_poste | Poste del yugo Ø22 con brida Ø44 y M16 (6061-T6) | 44×44×140 | Al 6061-T6 | torneada | 1 | Flexión + torsión por la fuerza de la biela del M66 | — | 151 | — |
| P1-STE-07_brazo | Brazo del yugo con rótula M8 (Al 5083 10 mm) | 61×32×10 | Al 5083 | torneada | 1 | Fuerza de la biela del M66 (momento de dirección / brazo) | — | 34 | — |
| P1-STE-08_tope_direccion | Topes de dirección ±δmax+1,5° (Al 5083 8 mm) | 156×92×32 | Al 5083 | torneada | 1 | Timón forzado contra el tope: 2 × fuerza de la biela del M66 [SUPUESTO] | — | 81 | — |
<!-- /AUTO:parts_list -->

## Verificación

<!-- AUTO:verify -->
Resultado: **FALLAS** — 65 piezas, 14160 pares×estados de interferencia; boquilla δ ∈ [-25.0, 0.0, 25.0]°, bucket {arriba, abajo}; masa de la unidad de jet (CAD) 25.94 kg.

Fallas:
- P1-REV-04: cota crítica 'contratuerca sobre el cuerpo de la boquilla [mm]' = -0.077 (ref >= 2.0)
<!-- /AUTO:verify -->

## Ajustes (los del CAD; confirmar con el taller y, en PETG, con probetas)

| Unión | Ajuste CAD | Nota |
|---|---|---|
| Eje Ø20 ↔ 2 × 7204 BECBP (en O, apareables universales) | muñón Ø20 k5 / alojamiento Ø47 H7 | Práctica de catálogo para aro interior rotante [SUPUESTO]; precarga ligera de fábrica, KM4 apretado contra el collar |
| Eje ↔ sello MG1 y tramo mojado | Ø20 h8 | Tolerancia de catálogo del sello [SUPUESTO: confirmar con la hoja del MG1] |
| Eje ↔ buje de agua POM-C del estator | muñón f7 / buje H7 | 2.º apoyo; el buje se cambia como consumible |
| Impulsor ↔ eje | deslizante; par por 2 semipasadores de corte Al 6061 en agujeros H8 escariados | Sin chaveta: los semipasadores son el fusible de par (02 §8) |
| Anillo de desgaste ↔ carcasa | prensado ligero + retenedor anaeróbico [ESTIMADO] | Holgura de punta = `tip_clr` (inputs) |
| Caja del sello ↔ buje de la toma | espigón f7 / H8 + 4 × M6 | Concentricidad del sello |
| Carcasa ↔ conducto (brida de la bomba) | espigón Ø140 h6 en rebaje H7 + 8 × M6 | Centra la bomba con el sello y el pórtico (alinear el pórtico con mandril al buje del estator) |
| Tobera ↔ carcasa | espiga de 12 mm con O-ring radial cs 3,53 + 8 × M5 | La tobera sale por el agujero del espejo para el servicio |
| Pivotes de la boquilla | pernos 316 con hombro (P1-STE-02/05) en bujes POM-C | Holgura de buje según plano |
| Pivote del bucket (P1-REV-02/03) ↔ oreja de la boquilla | espaciador 316: piloto Ø<!--V:manifest.params.REV_sp_pilot_d:g-->16<!--/V--> h6 en Ø16 H7 escariado de la oreja, brida Ø<!--V:manifest.params.REV_sp_fl_d:g-->36<!--/V--> × <!--V:manifest.params.REV_sp_fl_t:g-->3<!--/V--> contra la cara exterior, M12 A4-80 a <!--V:est.loads.structural_direccion.bolt_torque_Nm:.0f-->45<!--/V--> N·m con Tef-Gel; muñón Ø<!--V:manifest.params.REV_pin_d:g-->20<!--/V--> h7 en buje POM-C Ø<!--V:manifest.params.REV_bush_od:g-->24<!--/V--> × <!--V:manifest.params.REV_bush_L:g-->18<!--/V--> (prensado con 0,05–0,10 de interferencia en Ø24 H7 y escariado después de prensar) | La unión no desliza: la reacción del pivote pasa por el piloto, no por el tornillo (D-17c) |
| Trabas del bucket (P1-REV-04 ↔ P1-REV-01 / P1-STE-01) | perno Ø<!--V:manifest.params.REV_lock_pin_d:g-->16<!--/V--> h9 en agujero Ø<!--V:manifest.params.REV_lock_hole_d:g-->16.5<!--/V--> del brazo (con juego, a propósito); cuerpo M<!--V:manifest.params.REV_lock_thread_d:g-->24<!--/V-->×1,5 roscado en la oreja y apretado contra su collar Ø36 (cara interior anodizada de la oreja) a <!--V:manifest.params.REV_lock_T_Nm:g-->75<!--/V--> N·m con Loctite 243, sin contratuerca | Criterio de traba única: cada traba sola lleva todo M_h, así que el desfase entre las dos no importa para la resistencia; prueba funcional (los dos pernos entran solos arriba y abajo) |
| Piezas PETG (capota, base ESC, caja, tapa) | 0,25 mm diametral sobre metal | Peine de holguras de `probetas/`; roscas por tuerca A4 cautiva, nunca Loctite 243 sobre PETG |
