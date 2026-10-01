# 04 — Diseño detallado

- `params.py` deriva toda la geometría de `inputs.yaml` + `resultados/sizing.json`.
- `piezas/P1-<SUB>-<NN>_<nombre>.py`: un script por pieza (`META`, `build()`, `placements()`, `checks()`).
- `build_all.py` exporta STEP + STL (orientación de impresión) y `resultados/manifest.json`.
- `verify_parts.py` (exit ≠ 0 si falla): envolvente, manifold, cotas críticas, interferencias (barrido de dirección × basculación).
- `structural.py`: FS por pieza y caso de carga (tabla en 02 §9).
- `planos.py`: planos SVG acotados de piezas torneadas/mecanizadas → `planos/`.

## Lista de piezas

<!-- AUTO:parts_totals -->
Total impreso: **6.01 kg** de PETG, **334 h** de impresión (a 18.0 g/h); masa de la unidad basculante (CAD): **8.75 kg**.
<!-- /AUTO:parts_totals -->

<!-- AUTO:parts_list -->
| ID | Función | Envolvente [mm] | Material | Proceso | Cant. | Caso de carga dominante | Orientación de impresión | g c/u | h c/u |
|---|---|---|---|---|---|---|---|---|---|
| P1-DRV-01_shaft | Eje de hélice 316 Ø16 torneado | 1357×16×16 | AISI 316 | torneada | 1 | LC3/LC4 torsión, flexión por correa, fatiga | — | 2104 | — |
| P1-DRV-02_tube_bushing | Portabuje PETG + 2 bujes igus H370 Ø16×Ø18×20 (×3) | 34×34×40 | PETG | impresa | 3 | Reacciones radiales del eje (p = F/(d·L) en el portabuje) | Eje vertical (de pie): alojamiento del buje redondo y preciso en XY. | 31 | 1.7 |
| P1-DRV-03_bridge_spacer | Separador Ø12/Ø6.5 (×2), 316 | 26×12×12 | AISI 316 | torneada | 2 | Compresión por precarga del perno M6 | — | 17 | — |
| P1-DRV-04_motor | Motor BLDC outrunner (ver BOM) | 104×63×63 | — | comprada | 1 | — | — | 980 | — |
| P1-DRV-05_pulley_motor | Polea HTD-5M motor (aluminio, bore 8) | 21×38×38 | Al | comprada | 1 | — | — | 61 | — |
| P1-DRV-06_pulley_shaft | Polea HTD-5M eje (aluminio, re-mandrinada Ø15 H7) | 21×70×70 | Al | comprada | 1 | — | — | 206 | — |
| P1-DRV-07_bearing | Rodamiento 6202-2RS 15×35×11 (×2) | 11×35×35 | AISI 52100 | comprada | 2 | — | — | 11 | — |
| P1-DRV-08_bearing_cartridge | Cartucho rodamiento A (Al 6082 torneado) | 22×56×56 | Al 5052/6082 | torneada | 1 | LC1/LC2 empuje axial, LC3/LC4 radial | — | 53 | — |
| P1-DRV-09_spacer_b | Separador de eje rodamiento B ↔ polea (316) | 4×19×19 | AISI 316 | torneada | 1 | Precarga de la pila (tuerca M12) | — | 4 | — |
| P1-DRV-10_spacer_a | Separador de eje polea ↔ rodamiento A (316) | 12×19×19 | AISI 316 | torneada | 1 | Precarga de la pila; empuje en marcha atrás | — | 10 | — |
| P1-ELE-01_esc_box | Caja estanca del ESC (O-ring + prensaestopas) | 196×174×48 | PETG | impresa | 1 | Estanqueidad (IP67 objetivo), compresión del O-ring | Fondo sobre la cama; la cara del O-ring queda arriba, lisa (última capa + lijado). | 648 | 36.0 |
| P1-ELE-02_esc_lid_heatsink | Tapa-disipador Al 4 mm (mecanizada) | 196×146×4 | Al 5052/6082 | torneada | 1 | Compresión del O-ring; disipación ESC | — | 305 | — |
| P1-ELE-03_throttle_grip | Puño giratorio del acelerador (imán) | 48×48×110 | PETG | impresa | 1 | Torsión de mano (~5 N·m), golpes | Eje vertical (Z): anillos de capa en la dirección del torque. | 102 | 5.6 |
| P1-ELE-04_hall_housing | Collar del sensor hall (fijo a la caña) | 56×56×34 | PETG | impresa | 1 | Reacción de resortes, golpes | Eje vertical (Z). | 71 | 4.0 |
| P1-HSG-01_drive_plate | Placa motriz Al 6082-T6 6 mm (motor + cartucho + tensado) | 6×74×208 | Al 5052/6082 | torneada | 1 | LC1/LC2 empuje axial, LC3 torque de motor + tiro de correa, LC4 tirón al cortar el pasador, LC6 fatiga | — | 205 | — |
| P1-HSG-02_bearing_bridge | Puente del rodamiento B (polea entre apoyos) | 154×154×12 | PETG | impresa | 1 | LC3/LC4 tiro de correa (reacción R_B) | Plana (u = Z): reacción radial en el plano de capas; alojamiento vertical. | 67 | 3.7 |
| P1-HSG-03_belt_guard | Cubrecorrea / protección de poleas | 201×85×54 | PETG | impresa | 1 | Salpicaduras, manipulación leve | Cara cerrada sobre la cama, abierto arriba (sin puentes). | 139 | 7.7 |
| P1-HSG-04_tiller_clamp | Abrazadera del tubo de caña sobre la placa Al (×2) | 22×35×46 | PETG | impresa | 2 | LC7 manipulación (par de fuerzas entre abrazaderas) | De canto: la media caña y los pernos en el plano de capas. | 24 | 1.3 |
| P1-HSG-05_motor_hood | Capó ventilado del motor | 82×72×86 | PETG | impresa | 1 | Salpicaduras; temperatura del motor (≤ 60 °C en la pieza) | Cara trasera sobre la cama (techo y laterales verticales, sin puentes largos). | 66 | 3.7 |
| P1-HSG-06_tiller_tube | Tubo de caña Al 6061-T6 Ø30×3 × 550 mm | 550×30×30 | Al 6061-T6 | comprada | 1 | LC7 | — | 378 | — |
| P1-HSG-07_tiller_plate | Placa de caña Al 6082-T6 10 mm (mecanizada) | 77×124×10 | Al 5052/6082 | torneada | 1 | LC7 manipulación (torsión en la placa) | — | 247 | — |
| P1-MNT-01_clamp_bracket | Abrazadera de popa (C) + plato de dirección | 187×189×150 | PETG | impresa | 1 | LC5 impacto (reacción en pivote) / LC1 empuje / LC7 manipulación | Perfil x-z sobre la cama (ancho y = Z de impresión): cargas en el plano XY de capas. | 1857 | 103.2 |
| P1-MNT-02_clamp_pad | Zapata giratoria del tornillo de apriete (aislante) | 40×40×12 | PETG | impresa | 2 | Apriete del tornillo (compresión) | Plana, cara de apoyo sobre la cama; compresión a través de capas (admisible). | 18 | 1.0 |
| P1-MNT-03_yoke_base | Base de horquilla / plato de dirección | 75×112×20 | PETG | impresa | 1 | LC5 impacto / LC1 empuje (momento de vuelco sobre el perno) | Plana: momentos de vuelco en el plano de capas. | 180 | 10.0 |
| P1-MNT-04_yoke_cheek | Mejilla de horquilla con perno de basculación y retén | 116×121×14 | PETG | impresa | 2 | LC5 impacto (reacción en el pivote) / LC1–LC2 empuje | Plana (espesor = Z): flexión de la mejilla en el plano de capas. | 107 | 5.9 |
| P1-MNT-05_cradle | Cuna basculante (pivote + abrazadera del tubo + base de placa motriz) | 165×115×76 | PETG | impresa | 1 | LC5 impacto (momento del tubo) / LC1 empuje / retén | De canto (w = Z): flexión del tubo y empuje en el plano u–v = plano de capas. | 1174 | 65.2 |
| P1-MNT-06_cradle_cap | Tapa inferior de la cuna (abrazadera del tubo) | 90×76×30 | PETG | impresa | 1 | LC5 impacto (flexión del tubo) / tope de marcha | Cara inferior sobre la cama, media caña hacia arriba (sin soportes). | 162 | 9.0 |
| P1-MNT-07_swivel_pin | Perno de dirección Ø16 × L (316 torneado, rosca M16 inferior) | 24×24×134 | AISI 316 | torneada | 1 | LC5/LC1 momento de vuelco | — | 226 | — |
| P1-MNT-08_tilt_pin | Perno de basculación Ø12 (316 torneado, 2 ranuras DIN 471) | 12×114×12 | AISI 316 | torneada | 1 | LC5/LC1 corte doble | — | 103 | — |
| P1-MNT-09_swivel_bushing | Buje POM Ø16×Ø24 (dirección) | 24×24×82 | POM-C | torneada | 1 | Apoyo del perno de dirección | — | 28 | — |
| P1-MNT-10_pivot_bushing | Buje POM Ø12×Ø20 (basculación) | 20×76×20 | POM-C | torneada | 1 | Apoyo del perno de basculación | — | 21 | — |
| P1-PRP-01_guard_segment | Segmento de aro protector perfilado (×6) | 117×117×76 | PETG | impresa | 6 | Golpes en el aro (LC5 secundario), arrastre | Eje del anillo = Z: impactos radiales y flexión del arco en el plano de capas. | 113 | 6.3 |
| P1-PRP-02_skeg | Patín sacrificial bajo la hélice (cintura fusible) | 126×142×27 | PETG | impresa | 1 | LC5 varada/impacto (fusible mecánico) | Plano u–v sobre la cama: flexión en el plano de capas, rotura predecible en la cintura. | 91 | 5.1 |
| P1-PRP-03_propeller | Hélice comprada (ver BOM) — volumen barrido | 70×254×254 | Al / compuesto | comprada | 1 | — | — | 250 | — |
| P1-PRP-05_antivent_plate | Placa antiventilación sobre la hélice | 100×120×5 | PETG | impresa | 1 | Presión hidrodinámica baja; golpes leves | Plana: flexión en el plano de capas. | 76 | 4.2 |
| P1-SAF-01_killswitch_mount | Soporte de kill switch con cordón (en la caña) | 75×75×30 | PETG | impresa | 1 | Tirón del cordón (~100 N) al caer al agua | Eje del collar = Z; tirón del cordón en el plano de capas de la placa. | 39 | 2.1 |
| P1-STR-01_lower_housing | Carcasa inferior + aleta/brazo/montura del protector | 194×199×56 | PETG | impresa | 1 | LC5 impacto en patín/protector, LC6 vibración | De canto (w = Z): fuerzas del patín y del protector en el plano de capas. | 271 | 15.1 |
| P1-STR-02_tail_tube | Tubo de cola Al 6061-T6 Ø40×3 | 1171×40×40 | Al 6061-T6 | comprada | 1 | LC5 impacto (flexión), LC6 | — | 1102 | — |
<!-- /AUTO:parts_list -->

## Verificación

<!-- AUTO:verify -->
Resultado: **OK** — 38 piezas, 7846 pares×estados de interferencia; dirección ψ ∈ [-35.0, 0.0, 35.0]°, basculación φ ∈ [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]°; masa unidad CAD 8.75 kg vs estimación 9.0 kg.
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
