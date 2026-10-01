# 06 — Ensamblaje y pruebas

**Estado:** procedimiento de montaje, uniones, sellado, aislamiento galvánico, ensayos T0–T4, FMEA y mantenimiento. **[NO EJECUTADO]**: ninguna pieza existe todavía; nada se montó ni se probó. Prevalecen el código y `resultados/*.json`; los números de diseño van con marcadores que regenera `docgen.py`.
Etiquetas: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO]. IDs de pieza: `04_diseno/README.md`. Ítems de compra: columna ID de `bom.csv` (p. ej. B-IGUS). Ensayos eléctricos T0.1–T0.19: `04_diseno/electronica/README.md` §10. Uniones U-nn: §4. Bloqueos abiertos H-nn: §10.

**Puertas de entrada (no empezar sin esto):**
1. PENDIENTES P0 completo: bote medido, placa de capacidad leída (P0.2), hélice MKP-32 comprada y **medida** (P0.7) y `run_all.py` en verde con esos datos (re-dimensiona eje, pasador, protector y patín).
2. Probetas P1.1–P1.9 aprobadas, en especial P1.2 (bujes), P1.3 (tuerca cautiva), P1.6 (caja con O-ring), P1.8 (patín) y P1.9 (pasador).
3. Bloqueos de §10 marcados "antes de tornear" o "antes de montar" resueltos por el dueño del diseño.

**Reglas que valen para todo el documento**
- R1. Nunca Loctite 243 ni otro anaeróbico sobre PETG o donde pueda chorrear sobre PETG (D-18). Rosca A4 en tuerca cautiva de PETG: tuerca nyloc o cianoacrilato de baja resistencia tipo Loctite 425 [VERIFICADO: research/R05 §A10.3].
- R2. Tef-Gel en todo tornillo, separador o arandela A4/316 que toque aluminio, más arandela o vaina de nylon (D-36; B-ISO, B-ISOW).
- R3. PETG se limpia solo con IPA:agua 50:50; nunca acetona ni MEK [VERIFICADO: research/R05 §A11].
- R4. Tuerca A4 cautiva como unión estándar en PETG; insertos de latón solo en la caja ESC (D-18, research/R05 §A10.3).
- R5. Toda unión apretada lleva una marca de pintura que cruza cabeza y pieza: marca corrida = unión floja.
- R6. Sistema eléctrico flotante: nada del circuito toca el casco (README electrónica §1, ítem 5).
- R7. Hasta aprobar T0 el motor gira **sin correa** (o sin hélice) y con el cordón en la mano.

## 1. Herramientas y consumibles

| Herramienta / consumible | Uso | Origen |
|---|---|---|
| Torno | DRV-01, -03, -08, -09, -10; MNT-07…-10; re-mandrinado de DRV-06; pasadores PRP-04 | Gaspar |
| Taladro + machos M3–M8 | Placas Al (HSG-01, HSG-07, ELE-02), tubo STR-02, M3 ciegos de ELE-02, rosca M6 del puente en HSG-01 (H-5) | Gaspar |
| Soldador + multímetro | Insertos M4 de ELE-01 (≈ 245 °C para PETG [VERIFICADO: research/R05 §A10.1]); conectores bala y placa de optos; aislación, continuidad, tensiones, mV en uniones | Gaspar |
| Dinamómetro | Torques con palanca, bollard pull, retén, correa, probetas P1 | Gaspar |
| Palanca de torque | Llave fija o de tubo + brazo de 0,20 m tirado a 90° con el dinamómetro: T = F · 0,20 m (2,5 N·m = 12,5 N) [CALCULADO] | armar |
| Crimpadora 8–70 mm², termocontraíble con adhesivo | Terminales 16 mm² y toda punta de cable | B-CRIMP, B-SHRINK |
| Tef-Gel; arandelas y vainas de nylon | A4 sobre Al | B-ISO, B-ISOW |
| Cordón O-ring 3,53 + cianoacrilato + grasa de silicona; epoxi 2K | Caja ESC, sensor hall, buje MNT-09 | B-ORING, B-EPOXY |
| Calibre 0,02 mm, calibre de profundidad, micrómetro 0–25 mm | k5/H7/M7, pila del eje | buscar: micrómetro exterior 0-25 mm |
| Termómetro IR; PC con VESC Tool + USB; celular con GPS y cámara ≥ 120 fps; extintor ABC | T0–T4 | buscar: termómetro infrarrojo |
| Grasa dieléctrica de silicona; grasa de PTFE | J1/J2; perno MNT-08 (plano) | buscar: dielectric silicone grease / PTFE grease |
| Loctite 425; fijador de retención cilíndrico; Loctite 243 (solo metal-metal) | R1; agujero de DRV-06; prisioneros | buscar: Loctite 425 / retaining compound cylindrical |
| Arandelas A4 DIN 9021 M6 (Ø18) y DIN 125 M4/M6; 2 anillos DIN 471 Ø12 inox; tuerca M12×1,25 A4 autoblocante; tuerca M16×1,5 A4 autoblocante + arandela elástica | §4 | buscar: skive A4 M6 DIN 9021 / DIN 471 12 A4 |
| IPA, lijas al agua 400–1200, papel tisú, gel de sílice | Limpieza, cara de sello, T1 | — |

## 2. Preparación

### 2.1 Piezas torneadas y mecanizadas (planos en `04_diseno/planos/`)

| Pieza | Material (BOM) | Plano | Operaciones | Control |
|---|---|---|---|---|
| P1-DRV-01 eje | 316/316L Ø16 h9 (B-BAR16); **nunca 1.4301** (D-07) | `P1-DRV-01_shaft.svg` | Largo <!--V:sizing.layout.shaft_length_mm:.0f-->1357<!--/V--> mm. Arriba: tramo Ø15 k5 + rosca M12×1,25; 2 planos de 1 mm a 90° para los prisioneros. Abajo: asiento = bore **medido** de la hélice (Ø12,7 [ESTIMADO]) + agujero Ø2,1 pasante + retención según la hélice. r 1 mm en escalones; Ra 0,8 en la zona del buje inferior. Barra larga: pasar por el husillo con luneta y tornear un extremo por vez [SUPUESTO] | **Antes de tornear: H-4** (largo del tramo Ø15 = pila real medida − 0,5 mm). k5 = 15,001–15,009 mm [ESTIMADO: ISO 286, confirmar en tabla]; salto en el tramo Ø15 ≤ 0,05 mm y rectitud ≤ 0,3 mm rodando sobre mesa plana [SUPUESTO] |
| DRV-09 / DRV-10 | 316 Ø20 (B-BAR-PIN) | `P1-DRV-09_spacer_b.svg`, `P1-DRV-10_spacer_a.svg` | Ø19 × Ø15,1 × 4,5 / 12,0 mm | Caras paralelas ±0,02 (plano); apoyan solo en el aro interior |
| DRV-03 ×2 | 316 (sobrante de Ø16 o Ø20) | `P1-DRV-03_bridge_spacer.svg` | Ø12 × Ø6,5 × 26 | Caras paralelas ±0,05; ambos iguales |
| DRV-06 polea del eje | Dold 40 T (B-PUL-S) | `P1-DRV-06_pulley_shaft_rebore.svg` | Re-mandrinar a Ø15 H7 centrando sobre los dientes con mordazas blandas; 2 prisioneros M5 A4 a 90° | H7 = 15,000–15,018 [ESTIMADO: ISO 286]; salto ≤ 0,05 (plano) |
| DRV-08 cartucho | Al 6082-T6 (B-CARTBAR; **Ø55 no alcanza la brida Ø56**, H-14) | sin SVG: STEP `04_diseno/step/P1-DRV-08_bearing_cartridge.step` | Cuerpo Ø42, brida Ø56 × 4, asiento Ø35 M7 × 12, labio con paso Ø21, 3 × Ø4,4 en Ø49 a 120° | M7 = 34,975–35,000 [ESTIMADO: ISO 286]: el rodamiento no entra a mano en frío |
| MNT-07 perno de dirección | 316 (cabeza Ø24: **no sale de Ø20**, H-14) | `P1-MNT-07_swivel_pin.svg` | Cabeza Ø24 × 5, cuerpo Ø16 f7, rosca M16×1,5 | Gira en MNT-09 sin juego perceptible |
| MNT-08 perno de basculación | 316 Ø20 | `P1-MNT-08_tilt_pin.svg` | Ø12 h8 × 114, 2 ranuras DIN 471 | Los anillos entran y retienen |
| MNT-09 / MNT-10 | POM-C Ø25 (B-POM) | `P1-MNT-09_swivel_bushing.svg`, `P1-MNT-10_pivot_bushing.svg` | Ø24 × Ø16,2 H8 × 82 / Ø20 × Ø12,25 × 76 | Los pernos entran a mano |
| PRP-04 pasador ×6 | 316 Ø<!--V:sizing.mech.shear_pin.d_std_mm:.1f-->2.0<!--/V--> (B-PIN) | `P1-PRP-04_shear_pin.svg` | Cortar a 18,7 mm, aristas matadas | P1.9 con 3 del lote: corte entre 0,8 y 1,2 × <!--V:sizing.mech.shear_pin.Q_shear_Nm:.1f-->12.4<!--/V--> N·m, idealmente en el cubo real de la MKP-32 |
| HSG-01 placa motriz | Al 6082-T6 6 mm (B-PLATE6) | sin SVG: plantilla 1:1 desde el STEP | 208 × 74 mm: Ø42,2 del cartucho, 3 × Ø4,4, coliso central r 12,5 y 4 colisos M4 (±8 mm), 4 × Ø6,5 a la cuna, 2 × M6 **roscados** para el puente (H-5) | Plantilla presentada sobre la cuna y el motor reales antes de taladrar |
| HSG-07 placa de caña | Al 6082-T6 10 mm (B-PLATE10) | `P1-HSG-07_tiller_plate.svg` | 77 × 124 mm, 9 agujeros (4 tapa, 1 cáncamo, 4 abrazaderas), r 3; anodizar o pintar | Coordenadas ±0,2 mm |
| ELE-02 tapa-disipador | Al 4 mm (B-ALPLATE) | `P1-ELE-02_esc_lid_heatsink.svg` | 196 × 146 mm, 8 × Ø4,4; M3 **ciegos** para ESC y antichispa; 4 × M4 del disipador con arandela Dowty | Cara interior plana ≤ 0,1 mm (regla + galga) [SUPUESTO]; ningún M3 pasante |
| STR-02 tubo de cola | Al 6061-T6 Ø40×3 (B-TUBE) | docstring de STR-02 | Cortar a <!--V:sizing.layout.tube_length_mm:.0f-->1171<!--/V--> mm; 2 × Ø6,4 del perno de la carcasa inferior; 2 × Ø6 de drenaje; radiales de los M5 de los portabujes (H-12) | Sin rebabas (lima y avellanador) |
| HSG-06 caña | Al 6061-T6 Ø30×3 (B-TILLER) | — | Cortar a 550 mm | — |

### 2.2 Piezas impresas

Perfiles, orientación (`resultados/manifest.json`), secado, probetas y post-proceso: **`05_fabricacion.md`**. PETG con HDT ≥ 70 °C (D-29). Recepción de cada pieza antes de montar:
- masa dentro de ±10 % de "g c/u" de `04_diseno/README.md` [SUPUESTO]; sin delaminación, costuras abiertas ni hilos en los agujeros; holguras con la pieza metálica real (peine P1.1);
- ELE-01: insertos M4 a ≈ 245 °C quedando **0,3 mm por debajo** de la cara del reborde, para que el latón no toque la tapa de Al [SUPUESTO]; ranura del O-ring 2,57–2,72 × 4,50–4,75 mm [VERIFICADO: research/R05 §B3]; cara de sello lijada al agua o con epoxi + lijado (research/R05 §B4);
- DRV-02 ×3: 2 bujes H370 prensados por portabuje con el ajuste aprobado en P1.2;
- tuercas A4 cautivas colocadas en sus bolsillos antes de cerrar cada unión (MNT-01, -03, -04, -05; STR-01).

## 3. Secuencia de montaje

Orden: M1 cardán → M2 cola → M3 cuna y cabezal → M4 eje y pila → M5 correa y cubiertas → M6 hélice y protector → M7 unión cola–cardán → M8 caña y mandos → M9 eléctrica → M10 instalación en el bote. Banco: tablón de 40 mm atornillado al banco como espejo de prueba [SUPUESTO]. Masa de la unidad basculante: <!--V:verify.unit_mass.cad_kg:.2f-->8.75<!--/V--> kg (CAD): montar y levantar entre dos.

| Paso | Piezas | Acción | Control | Unión |
|---|---|---|---|---|
| M1.1 | MNT-01, MNT-09 | Buje POM en el buje vertical, con gota de epoxi o pasador (plano MNT-09) | MNT-07 entra y gira a mano sin juego radial perceptible | — |
| M1.2 | MNT-01, 2 tuercas M12 + placas de reparto A4 40×40×4, B-CLAMP, MNT-02 ×2 | Tuercas y placas en sus bolsillos; tornillos en T; zapatas en la punta | Cada tornillo recorre a mano toda la luz (espejo <!--V:manifest.params.tr_t_min:d-->20<!--/V-->–<!--V:manifest.params.tr_t_max:d-->65<!--/V--> mm); la zapata gira libre | U-01 |
| M1.3 | MNT-03, MNT-04 ×2, 4 tuercas M6 + 2 tuercas M12 cautivas | Tuercas en las mejillas; mejillas a la base con 4 × M6 desde abajo | Luz entre mejillas 78 ± 0,3 mm [CALCULADO: 2·(46 − 7)]; mejillas a escuadra ±0,5 mm en 100 mm [SUPUESTO] | U-03 (H-3) |
| M1.4 | MNT-01, B-WASH, MNT-03, MNT-07, tuerca M16 | Arandela UHMW sobre el plato, base encima, perno desde arriba, tuerca abajo | Dirección ±35° libre; juego vertical ≤ 0,5 mm [SUPUESTO] | U-02 |
| M1.5 | MNT-03, M8 A4 + B-STOP + contratuerca | Tornillo de trimado/tope desde abajo, altura inicial del CAD | — | U-18 (H-2, H-3) |
| M1.6 | MNT-04 ×2, B-SPRING ×2 | Émbolos de bola hasta enrasar la bola con la cara interior; se calibran en M7.2 | — | U-19 |
| M2.1 | STR-02 | Preparado según §2.1 | Largo ±1 mm | — |
| M2.2 | STR-02, DRV-02 ×3, M5 ×3 | Deslizar los portabujes con una varilla marcada: centros a 22 / 585 / 1149 mm de la boca superior [CALCULADO: layout.u_bush − layout.u_tube_top]; M5 radial con vaina + Tef-Gel | Una varilla Ø16 h9 de 1,4 m (o el eje) pasa por los tres sin forzar | U-13 (H-12) |
| M2.3 | STR-01, STR-02 | Encastrar la carcasa inferior 45 mm; perno transversal M6 (traba también el portabuje inferior) | Aleta en el plano de simetría de la cola ±1° | U-14 |
| M3.1 | MNT-05, MNT-10, 4 tuercas M6 | Buje POM del pivote en la cuna; tuercas cautivas de la placa motriz | MNT-08 entra a mano y gira sin juego visible | — |
| M3.2 | DRV-07 (A), DRV-08 | Calentar el cartucho a ≈ 100 °C (horno) y dejar caer el rodamiento hasta el labio [SUPUESTO]; nunca empujar por el aro interior | Rodamiento a tope contra el labio; gira suave | — |
| M3.3 | DRV-08, HSG-01 | Cartucho desde la cara de popa (brida contra la placa), 3 × M4 | Brida apoyada: galga 0,05 no entra | U-07 |
| M3.4 | HSG-01, DRV-04 (Flipsky 6374 190 KV) | Motor en los colisos, a media carrera; largo de tornillo = placa + arandela + rosca útil del motor − 1 mm (MEDIR el motor) | La punta no toca el bobinado; la campana gira libre; cabezas vs polea: H-6 | U-08 |
| M3.5 | HSG-01, MNT-05 | Placa a la cara delantera de la cuna; el cartucho entra en su rebaje | Cartucho asentado en el fondo del rebaje, sin luz | U-04 |
| M4.1 | DRV-01, conjunto M2 | Eje desde abajo (el extremo Ø12 primero) por STR-01 y los 3 portabujes hasta que asome ≈ 78 mm por la boca, como en la posición final [CALCULADO: layout.u_tube_top − layout.u_shaft_top]; V-ring entre el hombro y la boca si cabe (H-11) | Gira a mano en los bujes con ≤ 0,3 N·m (≤ 10 N con el dinamómetro a 30 mm) [SUPUESTO] | — |
| M4.2 | Cola + cuna, MNT-06, HSG-07 | Cuna boca abajo; apoyar el tubo en la media caña desplazado ≥ 80 mm hacia la hélice (el paso Ø22 de la cuna es cerrado) y deslizar todo hacia la cuna: el eje entra por el paso Ø22 en el rodamiento A (k5: empuje a mano; si pide más de ≈ 200 N, retirar y pulir al lado bajo de k5 [SUPUESTO], nunca a golpes por las bolas); tubo a tope contra el escalón; tapa y placa de caña con los 4 pernos pasantes | Tubo a tope; aleta de STR-01 en el plano de simetría de la cuna ±1° | U-05 (H-2) |
| M4.3 | DRV-10, DRV-06, DRV-09, DRV-07 (B), tuerca M12×1,25 | Desde arriba: separador A, polea (fijador de retención en el agujero; prisioneros sobre los planos), separador B, rodamiento B empujado por su aro interior, tuerca | **Antes de apretar:** el aro interior de B sobresale ≥ 0,3 mm del escalón Ø12/Ø15 (calibre de profundidad); con la geometría actual queda 2 mm por debajo (H-4). Después: juego axial del eje no perceptible (≤ 0,05 mm) [SUPUESTO] | U-10, U-11 |
| M4.4 | HSG-02, DRV-03 ×2, 2 × M6 | Puente deslizado sobre el rodamiento B (flotante); separadores entre puente y placa | Rodamiento B entra sin forzar; el eje sigue girando con ≤ 0,3 N·m; ninguna punta de M6 asoma por la cara de popa (H-5) | U-09 |
| M5.1 | B-BELT, DRV-05, DRV-06 | Polea del motor alineada con la del eje (regla sobre las caras); correa de <!--V:sizing.mech.belt.length_std_mm:.0f-->405<!--/V--> mm; tensar corriendo el motor en los colisos | Flecha ≈ 3 mm con 10 N en el centro del ramal (P5.3); desalineación ≤ 0,5 mm [SUPUESTO]; centros ≈ <!--V:sizing.mech.belt.center_actual_mm:.1f-->126.5<!--/V--> mm | U-08, U-12 |
| M5.2 | HSG-05, HSG-03 | Capó a la cara de popa de la placa; cubrecorrea (fijación: H-13) | Girar a mano: sin roce; capó y cubrecorrea abiertos abajo (drenan) | — |
| M6.1 | PRP-03, PRP-04 | Hélice en el asiento, pasador del lote ensayado (P1.9), tuerca de la hélice | Pasador sobresale igual a ambos lados; sin juego angular hélice–eje perceptible | — |
| M6.2 | PRP-01 ×6, PRP-02, STR-01 | Segmentos unidos por las orejas (M4 tangenciales); montura superior al brazo de STR-01; patín con su lengüeta en la ranura | Holgura punta de pala–aro ≥ 5 mm a 0/90/180/270° (checks de PRP-01); patín ≥ 15 mm bajo la punta de pala (checks de PRP-02) | U-15, U-16 |
| M6.3 | PRP-05 | Placa antiventilación al brazo de STR-01 | — | U-17 |
| M7.1 | Cuna + cardán, MNT-08, 2 × DIN 471 | Cuna entre mejillas, perno con grasa de PTFE, anillos | Juego axial ≤ 0,5 mm [SUPUESTO]; basculación 0→25° libre; el retén enclava en marcha y basculada | U-20 |
| M7.2 | Émbolos | Calibrar la precarga (P5.1) y bloquear | 60–130 N horizontales en el patín para bascular (modelo <!--V:sizing.mech.kickup.F_release_at_skeg_fwd_N:.0f-->89<!--/V--> N) | U-19 |
| M7.3 | Tope/trimado | Ajustar con nivel digital sobre el tubo | Eje a 25 ± 1° respecto de la vertical del espejo real medido en P0.1 (D-04) [SUPUESTO: tolerancia] | U-18 |
| M8.1 | HSG-06, HSG-04 ×2, HSG-07 | Tubo de caña en las abrazaderas (0,6 mm de apriete) | 200 N en el puño (LC7): la caña no gira ni desliza | U-06 |
| M8.2 | ELE-04, ELE-03, imán, resortes | Collar del hall fijo (M5 de apriete); imán pegado con epoxi en el cubo del puño; resortes | Retorno al centro desde ±30° 10/10 | — |
| M8.3 | SAF-01, B-KILL | Soporte junto al puño; interruptor Watski en el Ø22 | El clip entra y sale sin esfuerzo con el cordón a la muñeca | — |
| M8.4 | Cables del hall y del cordón | Por dentro del tubo de caña, alivio de tensión en ambas puntas, J1/J2 IP68 con grasa dieléctrica | Ningún cable apoyado en aristas; bucle de servicio (M9.5) | — |
| M9.1 | B-BAT (2 × Power Queen 12 V 100 Ah, D-19), B-BOX ×2 | Baterías en sus cajas, amarradas, sobre la sentina y centradas (trimado, 02 §6); puente serie de 16 mm² | Diferencia de tensión entre baterías ≤ 0,2 V (T0.2) | U-26 |
| M9.2 | F1 (MIDI 58 V, <!--V:sizing.fuse.rating_a:d-->80<!--/V--> A), S1, K1 (contactor monoestable), R_pre, antichispa Flipsky, ESC | Según diagrama y §4 de `04_diseno/electronica/README.md`; F1 a ≤ 178 mm del borne + (medir el cable); bobina de K1 en serie con seta y cordón Watski (D-22) | Polaridad; tracción de 200 N por terminal sin deslizar [SUPUESTO] | U-26, U-27 |
| M9.3 | ELE-01 (interior 160×110×45, D-20), ELE-02 | ESC y antichispa con pad térmico a la tapa; disipador con pasta; un cable redondo por prensaestopas (H-10); O-ring con grasa de silicona; tapa en cruz en 2 pasadas | T1 antes de navegar | U-21…U-24 |
| M9.4 | Fases 3 × 10 mm² | Conectores bala soldados dentro del capó; fijar los cables a la cuna junto al pivote | — | U-28 |
| M9.5 | Todos los cables a la unidad | Bucle de servicio ≥ 150 mm [ESTIMADO: arco de ±35° a ≈ 110 mm del eje de dirección + 25° a ≈ 80 mm del pivote] | Barrido T0.M4 sin tensar cables | — |
| M9.6 | ESC Flipsky 75100 V2.0 | Configuración de README electrónica §6 (FW ≥ 5.03, filtro de fase apagado), con `l_max_erpm` = <!--V:sizing.legal_speed.erpm_cap:.0f-->25137<!--/V--> (D-30; H-8) | T0.6 | — |
| M10.1 | Cardán + unidad | Sobre el espejo (2 personas); apretar U-01 | C apoyada en el borde y en la cara exterior, sin luz | U-01 (H-1) |
| M10.2 | B-LANYARD | Cabo de seguridad: cáncamo de la unidad → punto fuerte del bote con lazo textil; el mosquetón no apoya en el aluminio [SUPUESTO] | Largo libre ≤ 1 m [SUPUESTO]: si la abrazadera se suelta, la unidad queda colgando junto al espejo y no se va al fondo | U-29 (H-9) |
| M10.3 | ELE-01 | Caja alta y a la sombra, sobre tabla de HDPE o madera amarrada al banco (sin agujeros en el casco) [SUPUESTO] | — | U-25 |

## 4. Torques y uniones

**Reglas:** R1–R2 de la cabecera. Torque → precarga con F = T / (K·d), K = 0,2 [SUPUESTO: el mismo de `inputs.yaml` mount.clamp_screw_torque_nm].
- **Sobre PETG** (cabeza, arandela o tuerca cautiva apoyando en plástico): T ≤ K·d·A_apoyo·S_corta/3, con S_corta = <!--V:est.allowables_MPa.short:.1f-->24.0<!--/V--> MPa [CALCULADO]. Esa precarga supera la admisible sostenida (S_sost = <!--V:est.allowables_MPa.sust:.1f-->8.4<!--/V--> MPa): **se relaja por fluencia** y ningún cálculo de 02 §9 la usa. Por eso: bloqueo por nyloc o Loctite 425 (nunca por precarga), marca de pintura y re-apriete al mismo valor a las 24 h y al inicio de temporada. No hay limitadores de compresión metálicos (research/R05 §A5): H-3.
- **Metal–metal A4-70 con Tef-Gel:** T = 0,8 · 0,2 · d · (0,6 · R_p0,2 · A_s), R_p0,2 = 450 MPa [ESTIMADO: ISO 3506-1 clase 70, de memoria técnica; el 0,8 descuenta la lubricación del Tef-Gel].

| U | Unión | Elementos | Torque [N·m] | Base | Bloqueo / aislamiento |
|---|---|---|---|---|---|
| U-01 | Abrazadera de popa | 2 × M12 A4 en T, tuerca cautiva + placa de reparto, zapata MNT-02 | **≤ 2,5** (12,5 N a 0,20 m) | [CALCULADO: inputs.yaml mount.clamp_screw_torque_nm]. El FEA da FS 0,32 en el puente de la C con ese apriete: **H-1** | Re-apretar antes de cada salida (D-13); Tef-Gel en la rosca (anti-agarrotamiento A4/A4); la zapata aísla del casco |
| U-02 | Perno de dirección MNT-07 | Tuerca M16×1,5 autoblocante + arandela elástica | Por fricción: 10–30 N en el puño para girar la caña | [SUPUESTO: ergonomía; ajustar en T3] | Nyloc |
| U-03 | Mejillas → base | 4 × M6 cabeza cilíndrica en contrapunzonado Ø11,2 + tuerca cautiva en la mejilla | 0,4 | [CALCULADO: cabeza Ø10 sobre PETG] | Loctite 425; H-3 |
| U-04 | Placa motriz → cuna | 4 × M6, cabeza sobre Al; tuerca cautiva AF 10 en la cuna | 0,5 | [CALCULADO: cara de la tuerca 54 mm²] | Loctite 425; Tef-Gel + arandela de nylon bajo la cabeza |
| U-05 | Tapa + cuna + placa de caña | 4 × M6 pasantes ≈ 130 mm [CALCULADO: 109 mm de PETG desde el contrapunzonado + 10 de Al + arandela + nyloc], cabeza abajo en contrapunzonado Ø11,2; arandela Ø24 + nyloc sobre el Al | 0,4 | [CALCULADO: cabeza Ø10 sobre PETG]. Bajo LC5 la cabeza no cumple: **H-2** | Tef-Gel + arandela de nylon sobre el Al |
| U-06 | Abrazaderas de caña | 2 × M6 c/u, cabeza con DIN 9021 sobre PETG, nyloc bajo la placa Al | 1,5 | [CALCULADO: ≤ 2,1 por apoyo; sección 2 × 8 × 22 a S_corta/3] | Tef-Gel + arandela de nylon en el Al |
| U-07 | Cartucho → placa | 3 × M4 + nyloc (Al/Al) | 1,5 | [CALCULADO: A4-70] | Tef-Gel + arandelas de nylon |
| U-08 | Motor → placa | 4 × M4 en la rosca del motor | 1,5 | [CALCULADO: A4-70] | Tef-Gel; altura de cabeza: H-6 |
| U-09 | Puente → separadores → placa | 2 × M6, cabeza con DIN 9021 sobre el puente; **rosca M6 en la placa** | 2,0 | [CALCULADO: ≤ 2,1 por apoyo bajo DIN 9021] | Tef-Gel en rosca y caras del separador; H-5 |
| U-10 | Pila del eje | Tuerca M12×1,25 A4 autoblocante | 15 | [ESTIMADO: precarga ≈ 6 kN ≫ empuje <!--V:est.loads.T_bollard_N:.0f-->309<!--/V--> N; limitado por la rosca corta y el agarrotamiento A4/A4] | Tef-Gel en la rosca; **H-4** |
| U-11 | Polea del eje | 2 prisioneros M5 A4 sobre los planos + fijador de retención en el agujero | 2,0 | [ESTIMADO: prisionero inox en cubo de Al; sin ficha] | Loctite 243 en los prisioneros (metal-metal, R1) |
| U-12 | Polea del motor | Prisioneros de fábrica sobre el plano del eje Ø8 | Según Dold; si no figura, 2,0 | [ESTIMADO] buscar: Dold Zahnriemenrad Gewindestift Anzugsmoment | Loctite 243 |
| U-13 | Portabujes DRV-02 | M5 A4 radial: vaina en el tubo, rosca formada en el PETG | 0,25 | [CALCULADO: equivalente a tuerca M5 sobre PETG] | Tef-Gel; H-12 |
| U-14 | Carcasa inferior ↔ tubo | M6 transversal + nyloc, DIN 9021 a ambos lados | 1,5 | [CALCULADO: ≤ 2,1] | Tef-Gel en el tramo que cruza el tubo; H-12 |
| U-15 | Patín → carcasa inferior | 2 × M6 + nyloc + DIN 9021 | 1,5 | [CALCULADO: ≤ 2,1] | El patín debe romper en la cintura (<!--V:est.loads.F_skeg_fuse_N:.0f-->300<!--/V--> N), no en los pernos |
| U-16 | Aro protector | 6 uniones tangenciales M4 + nyloc, DIN 125 | 0,3 | [CALCULADO: arandela Ø9 sobre PETG] | Nyloc |
| U-17 | Placa antiventilación | 2 × M4 a tuerca cautiva | 0,2 | [CALCULADO: cara de tuerca M4] | Loctite 425 |
| U-18 | Tope / trimado | M8 en tuerca cautiva de MNT-03 + contratuerca | 1,0 | [CALCULADO: cara de tuerca M8 91 mm² ≤ 1,2] | Contratuerca; H-3 |
| U-19 | Retén | 2 émbolos M12 en tuerca cautiva de la mejilla + contratuerca | 2,0 la contratuerca | [CALCULADO: tuerca M12 ≤ 3,1] | Precarga por P5.1 |
| U-20 | Perno de basculación | MNT-08 + 2 × DIN 471 | — | — | Grasa de PTFE |
| U-21 | Tapa ELE-02 → caja ELE-01 | 8 × M4 en insertos de latón | 0,25 (en cruz, 2 pasadas) | [CALCULADO: 8 × 312 N = 2,5 kN ≥ 1764 N de compresión del O-ring (02 §9, fila ELE-01); 312 N por inserto = 1/3 del arranque de 1 kN ESTIMADO] | Arandela de nylon bajo la cabeza; insertos hundidos 0,3 mm |
| U-22 | Disipador → tapa | 4 × M4 desde adentro, arandela Dowty, rosca ciega ≥ 5 mm en el disipador | 1,5 | [CALCULADO: A4-70] | Pasta térmica; Tef-Gel en la rosca |
| U-23 | ESC y antichispa → tapa | M3 ciegos, pad térmico | 0,6 | [CALCULADO: A4-70 M3]; usar el valor del fabricante si es menor | — |
| U-24 | Prensaestopas M20/M16 | Contratuerca por dentro; cúpula | A mano + ¼ de vuelta hasta que el cable no gire | [ESTIMADO: sin ficha de torque] | Junta sobre cara plana (research/R05 §B8) |
| U-25 | Caja ESC → tabla | 4 orejas M5 | 1,0 | [CALCULADO: DIN 9021 Ø15 sobre PETG ≤ 1,2] | Si va al aluminio: Tef-Gel + arandelas de nylon |
| U-26 | Bornes: batería, portafusible HMD4 (M8), desconectador AFD (M10), contactor | Terminales tubulares estañados | Valor del fabricante; si falta: M8 8, M10 12 | [ESTIMADO: rango habitual de bornes de cobre; buscar: Power Queen 12V 100Ah terminal torque] | Contacto limpio metal-metal; protector solo por fuera después de apretar; cubrebornes |
| U-27 | Terminales 16 mm² | Crimpado B-CRIMP + termocontraíble con adhesivo | — | — | Tracción 200 N sin deslizar [SUPUESTO] |
| U-28 | Fases ↔ motor | Conectores bala 5,5 mm soldados + funda | — | — | Dentro del capó (motor seco, research/R05 §B8) |
| U-29 | Cáncamo del cabo | M8 A4 por HSG-07 | Pendiente de H-9 | — | Tef-Gel + arandela de nylon |

## 5. Mapa de sellado

Principio: cero sellos dinámicos sumergidos; la cola drena y solo la caja ESC es estanca (D-03, research/R05 §B1).

| # | Penetración / junta | Método | Prueba y criterio |
|---|---|---|---|
| S1 | Tapa ELE-02 ↔ caja ELE-01 | O-ring NBR70 Ø3,53 en ranura axial (25 % de aplastamiento, 78 % de llenado, D-23), empalme con cianoacrilato, grasa de silicona; cara lijada o con epoxi; U-21 | P1.6 y T1.1–T1.3: 0 g de agua |
| S2 | 5 × prensaestopas M20 (2 DC + 3 fases) | Un cable redondo por prensaestopas, OD medido dentro de 6–12 mm; contratuerca por dentro sobre la pared rebajada de 5 mm (D-20); lazo de goteo | T1.1 |
| S3 | Prensaestopas M16 (hall) y demás cables de señal y mando | Igual que S2. El CAD tiene 1 × M16 y hacen falta al menos 2 (hall + cordón/seta) más la alimentación del DC-DC: **H-10** | T1.1 |
| S4 | Respiradero ePTFE M12 (B-VENT) | Pared lateral +y, a 22 mm del fondo (CAD); evita el bombeo térmico | T1.2 (ciclo térmico) |
| S5 | 4 × M4 del disipador a través de la tapa | Arandela Dowty bajo la cabeza, por dentro; U-22 | T1.1 |
| S6 | M3 de ESC y antichispa en la tapa | **Ciegos** (≤ 3 mm en 4 mm): no son penetración si no se pasan | Inspección antes de T1 |
| S7 | Insertos M4 del reborde | Fuera de la ranura: no son camino de fuga | — |
| S8 | Conectores J1 (Lumberg 4 polos) y J2 (Cliffcon 2 polos), IP68 | Grasa dieléctrica de silicona en junta y contactos; tapas puestas al desconectar; enjuague | T1.4: > 20 MΩ entre pines y a masa de agua [SUPUESTO] |
| S9 | Sensor hall en ELE-04 | Encapsulado en epoxi; salida por prensaestopas M12 (no está en la BOM: H-14) | T1.5 |
| S10 | Puntas de cable y terminales | Termocontraíble con adhesivo (el agua viaja dentro del multifilar, research/R05 §B8) | Inspección |
| S11 | Boca superior del eje | V-ring excluidor (B-VRING) + drenaje Ø6 de la cuna hacia abajo; alojamiento sin definir: **H-11** | T1.6 |
| S12 | Drenajes de la cola | Tubo 2 × Ø6, labio de STR-01, cuna Ø6; capó y cubrecorrea abiertos abajo; ranuras de lavado de DRV-02 | T1.6: escurre en < 5 min con la cola basculada [SUPUESTO] |
| S13 | Motor y fases | **No se sellan**: motor seco bajo capó con drenaje; conectores bala dentro del capó (research/R05 §B8) | Enjuague post-uso |
| S14 | Baterías | Cajas Biltema sobre la sentina; cubrebornes; Anderson SB50 en zona seca. Batería que estuvo en agua salada: no cargar, aislar al aire libre y descartar (README electrónica §9) | Inspección |
| S15 | Interruptor de cordón y seta | Comerciales (seta IP65); entradas de cable con termocontraíble con adhesivo | T3.1 |

## 6. Mapa galvánico

Serie en agua de mar respecto de Ag/AgCl: Al marino −820 mV; 316 pasivo −150 mV; 316 activo (rendija, sin O₂) −550 mV; latón −450 mV; más de 200 mV de diferencia exige medidas [VERIFICADO: research/R06 §6.1]. **Decisión D-36: sin ánodo en P1**; todo par metálico mojado se separa. Sistema eléctrico flotante: BAT− sin conexión al casco (ISO 13297 4.1, README electrónica §1); se verifica con T0.1 y T0.M8 (> 1 MΩ).

| # | Par | Zona | ΔV aprox. | Aislamiento aplicado | Decisión |
|---|---|---|---|---|---|
| G1 | Eje 316 ↔ pasador 316 ↔ tuerca A4 | Sumergido | ≈ 0 (mismo metal); hasta 400 mV entre 316 pasivo y activo en rendija | Ranuras de lavado en DRV-02; enjuague; cola guardada basculada y seca (research/R05 §A12) | Sin ánodo; picaduras = inspección por temporada |
| G2 | Eje 316 ↔ hélice MKP-32 | Sumergido | 0 si es de compuesto [ESTIMADO: D-36, confirmar al recibirla]; ≈ 670 mV si fuera de Al | — | Si es de Al: ánodo obligatorio (buje Ø16→Ø25 + ánodo de Al Ø25, D-36) |
| G3 | Eje 316 ↔ tubo Al 6061 | Sumergido | ≈ 670 mV | Sin contacto: bujes igus H370 en portabujes de PETG | T0.M8: eje ↔ tubo > 1 MΩ |
| G4 | M5 A4 de portabujes y M6 A4 de la carcasa inferior ↔ tubo Al | Sumergido | ≈ 670 mV (cátodo chico, ánodo grande: el caso menos grave, research/R06 §6.2) | Tef-Gel + vaina de nylon (la del M6 no cabe en Ø6,4: H-12) | Inspección por temporada |
| G5 | Tornillería A4 ↔ placas Al 6082 (HSG-01, HSG-07, DRV-08, ELE-02) | Salpicadura | ≈ 670 mV | Tef-Gel + arandelas de nylon bajo cabeza y tuerca | — |
| G6 | Separadores 316 DRV-03 ↔ placa HSG-01 | Salpicadura | ≈ 670 mV | Tef-Gel en las caras | — |
| G7 | Polea Al (DRV-06) ↔ eje y separadores 316 | Salpicadura (bajo cubrecorrea) | ≈ 670 mV | Fijador de retención llena el agujero; Tef-Gel en las caras de los separadores; enjuague | — |
| G8 | Rodamientos 52100 ↔ cartucho Al / eje 316 | Seca con salpicadura | Acero entre 316 y Al [ESTIMADO: no tabulado en R06] | Sello 2RS; grasa repelente al agua en los asientos [SUPUESTO]; cambio por temporada (D-37) | — |
| G9 | Motor (Al y acero) ↔ placa Al; M4 A4 en el motor | Salpicadura | Al/Al ≈ 0; A4/Al ≈ 670 mV | Tef-Gel en los M4 | — |
| G10 | Pernos 316 MNT-07/08 ↔ bujes POM ↔ PETG | Salpicadura | — | No hay par metálico | — |
| G11 | M12 A4 de la abrazadera ↔ casco Al | Salpicadura | ≈ 670 mV | Zapata MNT-02 de PETG entre tornillo y espejo; placa de reparto dentro de la C | T0.M8: tornillo ↔ casco > 1 MΩ |
| G12 | Cáncamo M8 A4 ↔ placa de caña Al (+ inserto de latón previsto en la cuna) | Salpicadura | A4/Al ≈ 670 mV; latón/Al ≈ 370 mV | Tef-Gel + arandela de nylon; el latón no debe tocar el Al: **H-9** | — |
| G13 | Mosquetón inox del cabo ↔ casco Al | Salpicadura | ≈ 670 mV | Lazo textil al punto fuerte; el inox no apoya en el casco [SUPUESTO] | — |
| G14 | Insertos de latón ↔ M4 A4 ↔ tapa Al (caja ESC) | Seca/salpicadura (fuera del O-ring) | latón/Al ≈ 370 mV | Insertos hundidos 0,3 mm; arandela de nylon bajo la cabeza; Tef-Gel | Latón solo aquí (R4) |
| G15 | Caja ESC ↔ banco Al del bote | Salpicadura | — | Tabla de HDPE o madera; si se atornilla al Al: Tef-Gel + nylon | — |
| G16 | Terminales de cobre estañado ↔ bornes (batería, fusible, desconectador, contactor) | Seca (cajas) | Cobre/latón/estaño: misma familia [ESTIMADO] | Cubrebornes; enjuague nunca dentro de las cajas | — |
| G17 | Tubos Al 6061 ↔ placas Al 6082 | Salpicadura | Aleaciones de Al: diferencia chica [ESTIMADO] | — | Sin acción |
| G18 | Imán NdFeB niquelado en el puño | Salpicadura | — | Pegado y cubierto con epoxi | — |

## 7. Pruebas escalonadas

No se pasa a la etapa siguiente si una prueba no pasa. Cada etapa se registra (fecha, temperatura del aire y del agua, carga a bordo, firmware y XML del VESC, resultados).

### T0 — banco en seco
Condiciones: unidad completa sobre el tablón de 40 mm (o en el bote en tierra); motor sin correa en T0.1–T0.19, T0.M1 y T0.M2; con correa y **sin hélice** en T0.M3 y T0.M9; extintor a mano. Primero las pruebas eléctricas **T0.1–T0.19** (README electrónica §10: aislación, precarga, contactor, calibración, configuración, arranque con acelerador abierto, rampas, inversión, cordón y seta 10/10 en < <!--V:sizing.success.kill_time_max_s:.1f-->1.0<!--/V--> s, barreras por separado, falla de sensor, PPM, watchdog, 200 aperturas del cordón). Luego:

| # | Procedimiento | Pasa si | Si no pasa |
|---|---|---|---|
| T0.M1 | Girar el eje a mano sin correa, 10 vueltas | ≤ 0,3 N·m (≤ 10 N tangente a la polea, r 32 mm), sin puntos duros [SUPUESTO] | Alinear portabujes; revisar rectitud del eje y el prensado de los H370 |
| T0.M2 | Juego axial del eje con la pila apretada | No perceptible (≤ 0,05 mm) [SUPUESTO] | H-4 |
| T0.M3 | Correa: tensión y marcha 10 min al 30 % sin hélice | Flecha ≈ 3 mm con 10 N; la correa no migra > 2 mm sobre la polea [SUPUESTO] | Re-alinear poleas (U-11/U-12) |
| T0.M4 | Barrido de dirección −35/0/+35° × basculación 0–25° (estados de `verify_parts.py`) | Sin roces de piezas, sin cables tensos ni pellizcados | Rehacer el bucle de servicio (M9.5) |
| T0.M5 | Fuerza horizontal en el patín para bascular, motor parado | 60–130 N (P5.1; modelo <!--V:sizing.mech.kickup.F_release_at_skeg_fwd_N:.0f-->89<!--/V--> N); vuelve a enclavar en marcha | Regular los émbolos (U-19) |
| T0.M6 | Abrazadera en el tablón con U-01: medir la apertura de la C al pie de la pata a 0 y 24 h; luego 200 N verticales en el puño | Δ apertura ≤ 0,5 mm en 24 h; con 200 N la unidad no se mueve > 2 mm y vuelve [SUPUESTO] | **H-1** (el FEA anticipa que no pasa) |
| T0.M7 | Hélice montada: salto de la punta de pala y holgura al aro en un giro | Salto ≤ 2 mm; holgura ≥ 5 mm en todo el giro [SUPUESTO] | Revisar asiento y aro |
| T0.M8 | Aislación con multímetro (S1 OFF): eje ↔ tubo; tornillos M12 ↔ casco; tubo ↔ casco; tapa ELE-02 ↔ BAT− | > 1 MΩ [ESTIMADO: criterio de research/R06 §6.4] | Buscar el contacto antes de mojar nada |
| T0.M9 | Con correa y **sin hélice**, a fondo 10 s | rpm de motor ≤ <!--V:sizing.legal_speed.rpm_cap_motor:.0f-->3591<!--/V--> (tope `l_max_erpm` <!--V:sizing.legal_speed.erpm_cap:.0f-->25137<!--/V--> ERPM con 7 pares de polos; contar los imanes); sin vibración ni ruido de rodamiento | Corregir `si_motor_poles` / `l_max_erpm` (H-8) |

### T1 — estanqueidad
Condiciones: tanque o balde de ≥ 0,6 m, agua dulce; papel tisú y gel de sílice dentro de la caja; cables reales cortos con las puntas selladas.

| # | Procedimiento | Pasa si | Si no pasa |
|---|---|---|---|
| T1.1 | Caja ELE-01 completa (prensaestopas, respiradero, tapa con U-21), 30 min a 0,5 m | Papel seco: <!--V:sizing.success.watertight_after_immersion-->0 g de agua en caja ESC tras 30 min a 0,5 m (T1)<!--/V--> | Ubicar la fuga con aire a +0,2 bar y agua jabonosa por el puerto del respiradero (research/R05 §B9); re-lijar o epoxi en la cara, O-ring nuevo, prensaestopas; plan B: caja comercial IP67 BOX4U (D-20) |
| T1.2 | Ciclo térmico: caja a ≈ 45 °C (sol o agua tibia) y 15 min sumergida en agua fría | Seca | Respiradero (S4), O-ring |
| T1.3 | Repetir T1.1 tras 20 aperturas y cierres | Seca | Cambiar O-ring; revisar creep del reborde |
| T1.4 | J1 y J2 acoplados, 30 min a 0,3 m | > 20 MΩ entre pines y pin-agua [SUPUESTO: tope del multímetro]; sin agua al desacoplar | Grasa dieléctrica; cambiar conector |
| T1.5 | ELE-04 sumergido 30 min con el Nano leyendo | Lectura estable ±5 cuentas (ruido de README electrónica §5.3), sin `FAULT` | Re-encapsular |
| T1.6 | Manguera 1 min sobre el cabezal (en marcha y basculado) y cola sumergida hasta la flotación 10 min | Rebaje del cartucho y rodamiento A secos (papel); escurre en < 5 min [SUPUESTO] | H-11; destapar drenajes |

### T2 — muelle o tanque: bollard pull y térmico
Condiciones: bote amarrado de proa con el dinamómetro en el cabo horizontal; ≥ 1,5 m de agua bajo la hélice (como P0.3); viento ≤ 4 m/s [SUPUESTO]; chaleco, cordón a la muñeca, extintor; cabo de seguridad de la unidad puesto; temperatura del aire registrada. Con H-1 abierto, T2 solo con la unidad atada y nadie en el agua.

| # | Procedimiento | Pasa si | Si no pasa |
|---|---|---|---|
| T2.1 | Escalones de 25/50/75/100 % × 30 s | Empuje crece en cada escalón; sin ruidos ni salto de correa | Tensión de correa (P5.3) |
| T2.2 | Bollard: 100 % durante 3 min (el modelo llega al límite térmico en <!--V:sizing.thermal.bollard.t_to_limit_min:.1f-->6.3<!--/V--> min) | Empuje ≥ <!--V:sizing.success.bollard_pull_min_N:.0f-->238<!--/V--> N (predicho <!--V:sizing.success.bollard_pull_pred_N:.0f-->280<!--/V--> N); I_bat ≤ 75 A (PENDIENTES P3; modelo <!--V:sizing.bollard_fwd.I_bat:.0f-->48<!--/V--> A); sin salto de dientes | Ventilación (burbujas), inmersión, paso real de la hélice; ajustar `propeller.efficiency_factor` (D-40) y correr `run_all.py` |
| T2.3 | Temperaturas al terminar T2.2 (IR) | Carcasa del motor ≤ <!--V:sizing.success.T_motor_case_max_C:.0f-->80<!--/V--> °C; piezas impresas ≤ <!--V:sizing.success.T_printed_parts_max_C:.0f-->50<!--/V--> °C (cuna junto a la placa, capó, puente) | H-7: más ventilación, menos corriente |
| T2.4 | Marcha atrás al 50 % durante 30 s | La cola no se levanta (FS de retención del modelo <!--V:sizing.mech.kickup.fs_reverse_hold:.1f-->7.6<!--/V-->); registrar el empuje (modelo <!--V:sizing.bollard_rev.T_horiz:.0f-->89<!--/V--> N) | Subir la precarga del retén (P5.1) |
| T2.5 | Crucero térmico: 30 min a corriente de motor ≈ <!--V:sizing.cruise.design.I_m:.0f-->49<!--/V--> A (crucero de diseño) | NTC del motor ≤ 85 °C sin recorte del VESC; tapa ELE-02 ≤ 50 °C (P2.3); R_th = (T_NTC,∞ − T_aire) / <!--V:sizing.thermal.cruise_design.P_loss_motor_W:.0f-->141<!--/V--> W ≤ 0,45 K/W [ESTIMADO: inputs.yaml motor rth_k_w], con T_NTC,∞ extrapolada de la curva (τ ≈ 10 min [ESTIMADO: inputs.yaml]) | **H-7** (el modelo da <!--V:sizing.thermal.cruise_design.T_motor_steady_C:.0f-->93<!--/V--> °C estacionario con aire a 30 °C) |
| T2.6 | Uniones de potencia al terminar T2.2 | Cada borne ≤ temperatura del cable + 10 K (IR); ≤ 10 mV por unión a ≈ 50 A [SUPUESTO] | Limpiar y re-apretar (U-26) |
| T2.7 | Inspección | Marcas de pintura intactas; apertura de la C como en T0.M6; caja ESC seca | Re-apretar; repetir T2 |

### T3 — agua calma y poco profunda
Condiciones: 0,6–1,2 m de agua (se hace pie), fondo de arena, sin olas, viento ≤ 4 m/s [SUPUESTO], agua ≥ 12 °C [VERIFICADO: research/R07 §3.4, inputs.yaml water.temp_operating_min_c], acompañante con cabo desde la orilla, remos, chaleco puesto, cordón atado. Primero 1 persona. **Requiere H-1, H-2, H-3 y H-8 resueltos.**

| # | Procedimiento | Pasa si | Si no pasa |
|---|---|---|---|
| T3.1 | Avance, atrás, giros ±35°; a 50 % tirar del cordón, luego la seta | Para en < 1 s; con el puño abierto no rearranca; 5/5 | Volver a T0.12–T0.15 |
| T3.2 | Varada controlada en arena a ≈ 2 km/h | Bascula; el patín toca primero y no rompe; vuelve a marcha | Si rompe: revisar P1.8; si no bascula: bajar la precarga (P5.1) |
| T3.3 | Límite legal: 1 persona, batería llena, a fondo, 2 pasadas opuestas ≥ 200 m con GPS | Media ≤ 9,0 km/h (PENDIENTES P4; límite <!--V:sizing.legal_speed.limit_kmh:.2f-->9.26<!--/V--> km/h, D-30) | `l_max_erpm` nuevo = actual × 9,0 / v medida; repetir |
| T3.4 | Crucero con la carga real (2 personas solo si pasó P0.2): 6,0 km/h media de ida y vuelta | P_bat (VESC Tool) ≤ <!--V:sizing.success.cruise_P_bat_max_W:.0f-->910<!--/V--> W | Re-calibrar R(v) (P0.3–P0.4); crucero a 5,5 km/h |
| T3.5 | V máx con 2 personas, tope puesto | ≥ <!--V:sizing.success.vmax_min_kmh:.1f-->6.3<!--/V--> km/h | Ídem T3.4; revisar ventilación |
| T3.6 | Giros cerrados y aceleraciones a fondo | Sin ventilación sostenida (rpm sube > 20 % sin ganar velocidad) [SUPUESTO] | Trimado (M7.3), placa PRP-05 |

### T4 — Als Fjord en calma, a < 300 m de la costa
Condiciones: viento ≤ 6 m/s [VERIFICADO: research/R07 §4.1], sin ola, de día, < 300 m de la costa y ≤ 5 kn (tope puesto), agua ≥ 12 °C registrada; chaleco puesto, cordón, remos, ancla, teléfono en bolsa estanca; acompañante informado (en tierra o en otro bote); P0.2 aprobado (francobordo de popa ≥ 150 mm); batería al 100 %; `checklist_salida.md`.

| # | Procedimiento | Pasa si | Si no pasa |
|---|---|---|---|
| T4.1 | 2 h a 6 km/h en circuito paralelo a la costa; registrar Wh (VESC Tool) y GPS | Consumo ≤ 960 Wh por hora [CALCULADO: <!--V:sizing.battery.E_usable_wh:.0f-->2304<!--/V--> Wh usables / (2 h × 1,2)] → ≥ <!--V:sizing.success.endurance_min_h:.0f-->2<!--/V--> h con 20 % de reserva | Re-calibrar (P0.3–P0.4); crucero 5,5 km/h; batería mayor (D-19) |
| T4.2 | Registro del VESC durante T4.1 | Sin recorte térmico; caja ESC ≤ 50 °C | H-7 |
| T4.3 | Simulacro: cordón a 6 km/h y remar 50 m | Motor parado < 1 s; remos en uso en < 30 s [SUPUESTO] | Reorganizar a bordo |
| T4.4 | Al volver: caja ESC, aislación T0.1, marcas | Seca; > 1 MΩ; marcas intactas | No volver a salir hasta corregir |

### Post-uso (cada salida)

| # | Control | Pasa si | Si no pasa |
|---|---|---|---|
| PU.1 | Enjuague con agua dulce de toda la unidad, girando el eje a mano | Sin arena en bujes ni en el aro | Repetir |
| PU.2 | Cola basculada fuera del agua, escurrida | Drenajes sin agua a los 5 min | Destapar |
| PU.3 | PETG: cuna, tapa, abrazadera, mejillas, patín, aro | Sin fisuras, blanqueamiento ni deformación | Reemplazar antes de salir |
| PU.4 | Pasador: con la polea sujeta, girar la hélice a mano | Sin juego angular | Cambiar el pasador |
| PU.5 | Batería y mando | S1 OFF, cordón guardado, carga en interior a ≥ 5 °C (BMS) | — |
| PU.6 | Registro | Horas de motor, Wh, eventos, golpes | — |

## 8. FMEA

Escalas 1–10 [ESTIMADO: criterio del autor]: S severidad, O ocurrencia, D detección (10 = no se detecta). RPN = S·O·D. Orden por RPN; **en negrita los modos con S ≥ 9**.

| # | Función | Modo de falla | Efecto | S | Causa | O | Control actual | D | RPN | Acción | Responsable / prueba |
|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 | **Sostener la unidad** | **Fluencia o fatiga de PETG en cuna, tapa o abrazadera** | Caída o pérdida de la unidad con la hélice girando | **9** | FEA: FS 0,32 (MNT-01), 0,74 (MNT-06), 0,86 (MNT-04) | 4 | Cabo de seguridad, inspección PU.3 | 4 | 144 | Resolver H-1…H-3 antes de T3 | Dueño del diseño / FEA, T0.M6 |
| F2 | **Flotar con margen** | **Sobrecarga del bote / inundación** | Embarque de agua, vuelco, hipotermia | **10** | Carga útil <!--V:sizing.masses.payload_kg:.0f-->248<!--/V--> kg vs capacidad estimada <!--V:sizing.masses.capacity_kg:.0f-->160<!--/V--> kg (D-16) | 4 | P0.2, francobordo ≥ 150 mm, solo en calma, chalecos | 3 | 120 | 1 adulto o batería chica si P0.2 no pasa | Gaspar / P0.2, checklist |
| F3 | **Fijar al espejo** | **La abrazadera se suelta** | Unidad colgando del cabo; golpe a personas o casco | **9** | Apriete ≤ 2,5 N·m que se relaja; C flexible (H-1) | 3 | Re-apriete antes de cada salida, cabo | 4 | 108 | H-1; T0.M6 a 24 h | Gaspar / checklist |
| F4 | Durabilidad | Corrosión: 316 en rendija bajo bujes; A4 en Al | Pérdida de sección del eje, tornillos flojos | 6 | Agua estancada, falta de enjuague (G1, G4, G5) | 4 | Tef-Gel, nylon, enjuague | 4 | 96 | Inspección por temporada (§9) | Gaspar / §9 |
| F5 | Potencia continua | Sobrecalentamiento del motor | Recorte del VESC; PETG cercano > 50 °C | 5 | <!--V:sizing.thermal.cruise_design.T_motor_steady_C:.0f-->93<!--/V--> °C estacionario en crucero de diseño (H-7) | 6 | NTC + límite 85 °C del VESC | 3 | 90 | T2.5; ventilación o menos corriente | Gaspar / T2.5 |
| F6 | Proteger electrónica | Agua en la caja ESC | VESC en falla, pérdida de propulsión (K1 sigue cortando) | 7 | Porosidad del PETG, prensaestopas, bombeo térmico | 4 | O-ring + IP68 + respiradero | 3 | 84 | T1.1–T1.3; H-10 | Gaspar / T1 |
| F7 | **Parada de emergencia** | **El cordón no corta: corto entre sus 2 conductores o agua en J2** | Motor sigue con una persona en el agua | **10** | Cable aplastado en la caña, J2 sin grasa (README electrónica §8) | 2 | Seta; prueba previa a cada salida | 4 | 80 | Prueba de cordón en el muelle siempre; P2: interruptor de 2 canales | Gaspar / prueba previa |
| F8 | Fusible mecánico | Pasador corta prematuro | Pérdida de propulsión: remos | 5 | Fatiga: FS Goodman <!--V:sizing.mech.shear_pin.fatigue_cruise.fs_goodman:.2f-->1.46<!--/V--> en crucero | 5 | Cambio cada 10 h; 5 repuestos | 3 | 75 | §9 | Gaspar / PU.4 |
| F9 | **Conducir potencia** | **Unión de potencia floja → calentamiento / incendio** | Fuego en la caja de batería o la consola | **9** | Torque bajo, terminal mal crimpado | 2 | F1 a ≤ 178 mm; U-26/U-27 | 4 | 72 | T2.6 por temporada | Gaspar / T2.6 |
| F10 | Fusible mecánico | Pasador no corta | Golpe pasa a correa, eje y placa; tirón a la abrazadera | 8 | Pasador más grueso o de otro acero; τ real mayor | 2 | P1.9; plano PRP-04 | 4 | 64 | Solo pasadores del lote ensayado | Gaspar / P1.9 |
| F11 | Parada de emergencia | Contactor K1 soldado | Se pierde la barrera de hardware; quedan 2–3 | 7 | Cierre sin precarga | 3 | R_pre; clic en la prueba previa; T0.15 | 3 | 63 | Encender siempre con el cordón afuera (README electrónica §7) | Gaspar / prueba previa |
| F12 | Llevar energía a la unidad | Roce o corte de cables al bascular o girar | Corto de fases (F1), `FAULT`, o parada por cordón | 7 | Bucle de servicio corto | 3 | Bucle ≥ 150 mm | 3 | 63 | T0.M4; inspección | Gaspar / T0.M4 |
| F13 | Volver a puerto | Pérdida de propulsión con viento de tierra | Deriva mar adentro (W/SW dominante, research/R07) | 7 | Batería, pasador, falla eléctrica | 3 | < 300 m, remos, ancla | 3 | 63 | Simulacro T4.3 | Gaspar / T4.3 |
| F14 | Aguas someras | Golpe de hélice en arena o piedra | Patín roto, pasador cortado, aro dañado | 6 | Fondo < calado de la punta de pala | 5 | Patín fusible <!--V:est.loads.F_skeg_fuse_N:.0f-->300<!--/V--> N, kick-up, pasador | 2 | 60 | Patín y segmentos de repuesto | Gaspar / T3.2 |
| F15 | **Almacenar energía** | **Cortocircuito de batería** | Arco, quemaduras, fuego | **9** | Herramienta sobre bornes, agua salada en la caja | 2 | Cubrebornes, F1, caja | 3 | 54 | S1 OFF y Anderson desconectado para trabajar | Gaspar / M9 |
| F16 | Transmisión | Salto o rotura de correa | Pérdida de propulsión | 5 | Tensión baja, desalineación | 3 | P5.3; FS de correa <!--V:sizing.mech.belt.fs_belt:.2f-->1.81<!--/V--> | 3 | 45 | Correa de repuesto | Gaspar / T2.2 |
| F17 | Control | Sobrecalentamiento del ESC | Recorte, pérdida de potencia | 5 | Disipador peor que <!--V:sizing.thermal_esc.heatsink.R_hs_required_K_W:.2f-->0.58<!--/V--> K/W o caja al sol | 3 | Tapa Al + disipador | 3 | 45 | T2.5; caja a la sombra | Gaspar / T2.5 |
| F18 | Cumplir la norma | Velocidad > 5 kn a < 300 m | Infracción; riesgo para bañistas | 5 | `l_max_erpm` mal cargado (H-8) | 3 | Tope de ERPM | 3 | 45 | T3.3 | Gaspar / T3.3 |
| F19 | Retener en reversa | La cola bascula en marcha atrás | Ventilación, sin frenada | 6 | Retén flojo | 2 | FS <!--V:sizing.mech.kickup.fs_reverse_hold:.1f-->7.6<!--/V-->; reversa 50 % | 3 | 36 | T2.4 | Gaspar / T2.4 |
| F20 | **Mando** | **Falla del sensor del acelerador / arranque inesperado** | Hélice arranca con alguien cerca | **9** | Hall o imán suelto, ruido | 2 | `FAULT` en el mismo tick; armado solo con 1 s en cero | 2 | 36 | T0.7, T0.16 | Gaspar / T0 |
| F21 | Almacenar energía | Descarga profunda o carga en frío | Batería dañada, sin propulsión | 4 | Corte del VESC mal puesto; carga < 5 °C | 3 | `l_battery_cut`; BMS | 3 | 36 | Cargar en interior | Gaspar / PU.5 |
| F22 | Proteger personas | Atrapamiento en correa o hélice en el muelle | Lesión en la mano | 8 | Manipular con S1 ON | 2 | Cubrecorrea, aro, cordón afuera | 2 | 32 | Regla R7; S1 OFF para tocar la cola | Gaspar |
| F23 | Retener la unidad | Pérdida de la unidad por la borda | Pérdida económica; tirón de cables | 6 | Abrazadera suelta sin cabo | 2 | Cabo de seguridad | 2 | 24 | M10.2 (H-9) | Gaspar / checklist |

## 9. Mantenimiento e inspección

| Cuándo | Tarea | Criterio |
|---|---|---|
| Antes de cada salida | `checklist_salida.md`; re-apretar U-01; cabo de seguridad; prueba de cordón y seta (README electrónica §10, prueba previa); batería ≥ 80 % | Todo pasa o no se sale |
| Después de cada salida | PU.1–PU.6 | §7 |
| Cada 10 h de motor | Cambiar el pasador (02 §7: FS Goodman <!--V:sizing.mech.shear_pin.fatigue_cruise.fs_goodman:.2f-->1.46<!--/V-->); flecha de correa; juego radial del eje en la hélice | Pasador nuevo del lote ensayado; flecha ≈ 3 mm con 10 N |
| Mensual o cada 20 h | Abrir la caja ESC: O-ring, grasa de silicona, gel de sílice; aislación T0.1; repaso de U-01…U-29 por las marcas | Sin humedad; > 1 MΩ; marcas sin correr |
| Inicio de temporada | Rodamientos 6202 nuevos (D-37); O-ring nuevo; bujes H370 (juego radial ≤ 0,5 mm en la hélice [SUPUESTO]); V-ring; desmontar el eje e inspeccionar picaduras bajo los bujes; sacar un A4 de cada placa Al y mirar la rosca; T0 y T1 completos; balancear cada batería a 14,6 V por separado (D-19) | Sin picaduras ni polvo blanco de corrosión en el Al; T0/T1 pasan |
| PETG (cada salida y por temporada) | Lupa en cuna, tapa, abrazadera, mejillas, base, patín y aro; medir la luz de la C y la apertura de la cuna | Reemplazar ante fisura, blanqueamiento o deformación permanente > 1 mm [SUPUESTO] |
| Fin de temporada | Unidad desmontada, lavada con agua dulce y seca; Tef-Gel renovado; impresas a la sombra; batería en interior > 5 °C | — |
| Kit a bordo | 5 pasadores, botador Ø2, llave en T M12, llaves 8/10/13, allen, correa, patín, 1 segmento de aro, cinta autovulcanizante | Completo |

## 10. Bloqueos abiertos (detectados al 2026-10-01)

| H | Problema | Bloquea | Fuente |
|---|---|---|---|
| H-1 | MNT-01: con 2,5 N·m el puente de la C queda en FS 0,32 a fluencia (la C se abre) | T3, T4 (T2 solo atada) | `04_diseno/fea/README.md` |
| H-2 | MNT-06: el tope de marcha comprime la tapa (FS 0,74 con la cola trabada) y los pernos pasantes apoyan solo con la cabeza Ø10 en el contrapunzonado Ø11,2 (structural.py supone arandela Ø24, que no cabe) | T3, T4 | FEA + este documento |
| H-3 | MNT-03/04: ranuras de tuercas M6 (FS 0,86; 2,20 con p99); cabezas M6 sin arandela y tuerca M8 del tope sin verificar al aplastamiento; sin limitadores de compresión (research/R05 §A5) | T3, T4 | FEA + este documento |
| H-4 | Pila del eje 2 mm más corta que el tramo Ø15: la tuerca asienta en el escalón; rosca de 7,5 mm, corta para una autoblocante | Tornear DRV-01 | Este documento |
| H-5 | Pernos del puente HSG-02 a 28,9 mm del eje del motor: tuerca o punta en la cara de popa contra la campana (r 31,5 mm) | M4.4 | Este documento |
| H-6 | Cabezas M4 del motor en 2 mm de luz contra la polea del motor | M3.4 | Este documento |
| H-7 | Motor a <!--V:sizing.thermal.cruise_design.T_motor_steady_C:.0f-->93<!--/V--> °C estacionario en crucero de diseño (> 85 °C, ≈ <!--V:sizing.thermal.cruise_design.t_to_limit_min:.0f-->20<!--/V--> min); no está entre las restricciones duras | T4.1 si T2.5 no pasa | Este documento |
| H-8 | README electrónica §6 pone `l_max_erpm` 30000 > tope legal <!--V:sizing.legal_speed.erpm_cap:.0f-->25137<!--/V--> | T3 | Este documento |
| H-9 | Cáncamo M8 del cabo sobre inserto de latón en zona de salpicadura, tocando la placa Al | M10.2 | Este documento |
| H-10 | Caja ESC: faltan pasos (2.º M16, mando, DC-DC) para "un cable por prensaestopas" | M9.3, T1 | README electrónica §11 + este documento |
| H-11 | V-ring sin alojamiento ni secuencia de montaje en el CAD | T1.6 | Este documento |
| H-12 | Perno M6 de STR-01 "con vaina" en agujero Ø6,4; M5 de portabujes con rosca formada en PETG; agujeros radiales no listados en STR-02 | M2 | Este documento |
| H-13 | Agujeros M4 del cubrecorrea HSG-03 sin pieza donde roscar | M5.2 | Este documento |
| H-14 | BOM: barra Ø55 < brida Ø56 (DRV-08); Ø20 no da la cabeza Ø24 (MNT-07); faltan inserto M8, prensaestopas M12, DIN 9021, DIN 471, tuercas M12×1,25 y M16×1,5, fijadores y grasas de §1 | Compras | Este documento |
| H-15 | Textos desactualizados: PENDIENTES P3 dice 247 N (sizing: <!--V:sizing.success.bollard_pull_min_N:.0f-->238<!--/V--> N); D-21 dice fusible de 100 A (sizing: <!--V:sizing.fuse.rating_a:d-->80<!--/V--> A); docstring de MNT-06 dice "a insertos"; D-34 vs DC-DC del README electrónica | Documentación | Este documento |
