# 06 — Ensamblaje y pruebas del waterjet

**Estado:** procedimiento de compras por etapa, cambios en el casco, montaje, aislamiento galvánico, pruebas T0–T4, FMEA, mantenimiento y bloqueos. **[NO EJECUTADO]**: no hay ninguna pieza fabricada; nada se montó ni se probó. Mandan el código y `resultados/*.json`; los números de diseño van entre marcadores `<!--V:…-->` y los regenera `docgen.py`.

Etiquetas: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO]. IDs de pieza: `04_diseno/README.md` y `resultados/manifest.json`. Ítems de compra: columna `ID` de [`bom.csv`](bom.csv). Ensayos eléctricos T0.1–T0.20: [`04_diseno/electronica/README.md`](04_diseno/electronica/README.md) §10. Bloqueos H-n: §8 (no confundir con los hallazgos H1–H25 de R10b).

**Reglas que valen para todo el documento**
- R1. **La estabilidad va primero.** El ensayo de escora T1.1 (R13 §5, E1) se hace con el casco SIN cortar y lastre equivalente, antes de comprar servicios o cortar el fondo. Si no pasa, no se sigue (D-04).
- R2. **El sello mecánico nunca gira en seco.** Con el bote fuera del agua el eje se gira solo a mano y despacio. El motor gira solo con la estrella del acople sacada (T0) [ESTIMADO: R10a §0.2, §8.3].
- R3. **Tef-Gel en todo A4/316 que toque aluminio**, más arandela aislante de nylon (B-TEFGEL, B-ISOW) (§4).
- R4. **Marca de pintura** cruzando cabeza y pieza en toda unión apretada: si la marca está corrida, la unión está floja.
- R5. **Sistema eléctrico flotante:** BAT− no toca el casco; aislación > 1 MΩ (T0.1) [VERIFICADO: R06 §5.1, ISO 13297 4.1].
- R6. **Nunca trabajar en la rejilla, la chimenea o la popa con el sistema armado:** cordón afuera y S1 en OFF [VERIFICADO: R10a §0.1].
- R7. **Pares de apriete.** El único calculado en el repositorio es el de las tuercas M8 del pórtico: <!--V:manifest.params.drv_nut_torque_Nm:.0f-->15<!--/V--> N·m con Tef-Gel (P1-DRV-03, estructural.json). Para el resto (M3–M8 A4-70, KM4, prisioneros) usar la tabla del proveedor de la tornillería y la del fabricante del rodamiento; **no están calculados** (bloqueo H-6).

---

## 1. Compras y fabricación por etapa

La lista completa, con proveedor, precio, etiqueta y especificación mínima, está en [`bom.csv`](bom.csv). Total del sistema <!--V:bom.total_eur:.0f-->10865<!--/V--> € ≈ <!--V:bom.total_dkk:.0f-->81219<!--/V--> DKK; con los cambios de casco y el equipo de operación, <!--V:bom.total_with_hull_and_gear_eur:.0f-->11583<!--/V--> € [CALCULADO: `bom.py`]. Regla: **no se compra nada caro antes de cerrar P0** (PENDIENTES_GASPAR).

| Etapa | Condición para empezar | IDs de `bom.csv` | Monto | Nota |
|---|---|---|---|---|
| E0 — Medir y decidir | Ninguna | Nada (cinta, nivel, balanza, lastre) | — | PENDIENTES P0: medidas, estabilidad, cotizaciones, consulta legal |
| E1 — Casco y seguridad del bote (Jorge) | T1.1 (E1) aprobado con el casco tal cual o ya modificado; casco medido | H-CUT-BOT, H-CUT-TR, H-HOLES, H-FLOORS, H-WELD, H-SIKA, H-PRIMER, H-BATT, H-FOAMBAY; B-FOAM, B-BILGE, B-ALARM, B-BILGE-HOSE, B-12V | Casco: <!--V:bom.hull_changes_eur:.0f-->504<!--/V--> € | Los cortes se replantean sobre el casco medido (§2) |
| E2 — Equipo de operación | Antes de la primera prueba en el agua (T1) | B-PFD, B-CORD, B-PADDLE, B-ANCHOR, B-LIGHT, B-BAILER | <!--V:bom.operation_gear_eur:.0f-->215<!--/V--> € | Va también con la JT132 (opción B) |
| E3 — Núcleo eléctrico | Respuesta de Maytech (potencia continua, pares de polos) y `run_all.py` en verde | B-MOT, B-ESC, B-BAT, B-CHG | Núcleo: <!--V:bom.core_eur:.0f-->1952<!--/V--> € | Sirve para A y para B (D-05). Medir las baterías recibidas antes de comprar B-BOX |
| E4 — Potencia, seguridad eléctrica y mando | E3 recibido | B-BOX, B-FUSE, B-FUSEH, B-SW, B-BUS, B-CAB-*, B-TERM*, B-SHRINK*, B-ANDERSON, B-GLAND32, B-RPRE, B-CONT, B-KILL, B-ESTOP, B-CFUSE, B-KCONN, B-MCU, B-DCDC, B-PCB, B-HALL, B-MAG, B-SIGNAL, B-ENCL, B-WIRE, B-CRIMP | — | B-CONT: tensión de bobina y de cierre confirmadas por escrito (README de electrónica §7; bloqueo H-9) |
| E5 — Servicios de fabricación (solo opción A) | AWT no confirma las 4 condiciones de 03 §3, o la JT132 no entra en el casco | S-CNC-IMP, S-CNC-STAT, S-TURN-HSG, S-TURN-NOZ, S-TURN-TP, S-MILL-STE, S-LASER, S-WELD-INT, S-WELD-AL, S-WELD-316, S-ANOD; materia prima MP-* | Servicios <!--V:bom.services_eur:.0f-->3910<!--/V--> € + materia prima <!--V:bom.raw_material_eur:.0f-->1243<!--/V--> € | Con la JT132 queda solo la placa de adaptación de la toma, el pórtico y el soporte del motor (03 §4) |
| E6 — Tren, sellado y corrosión | E5 encargado (o JT132 comprada) | B-SEAL, B-BRG, B-KM4, B-CPL, B-KEY, B-CIRC, B-NUT16, B-LOCTITE, B-HW, B-STUD, B-INS, B-ORING, B-GREASE, B-GASKET, B-GLAND16, B-GLAND20, B-TEFGEL, B-ISOW, B-ANODE, B-TAP | — | Comprar con el eje: el sello y los rodamientos se prueban en el eje terminado |
| E7 — Refrigeración y mandos | Consola de Jorge medida | B-HOSE, B-BARB, B-HCLAMP, B-STRAIN, B-COOL-THRU; B-HELM, B-M66, B-WHEEL, B-MACH5, B-ROD5, B-ROT8, B-INDEX, B-BOWDEN, B-KNOB | — | Largo del M66, del Mach5 y del Bowden medidos en el bote |
| E8 — Impresión en PETG | Perfiles y probetas de 05 aprobados | B-PETG → P1-CTL-02, P1-CTL-03, P1-ELE-01, P1-ELE-02, P1-INT-04 | <!--V:manifest.totals.printed_mass_g:.0f-->1020<!--/V--> g, <!--V:manifest.totals.printed_hours:.0f-->57<!--/V--> h | Piezas secas o de baja carga (D-19) |
| E9 — Repuestos | Con E6 | R-SEAL, R-ORING, R-SPIDER, R-FUSE, R-PIN, R-BUSH | — | R-PIN: 5 pasadores de corte (ver bloqueo H-12 sobre la cantidad) |

---

## 2. Cambios en el casco que hace Jorge

Todas las cotas salen del CAD (`resultados/manifest.json → params`) con el casco **leído del plano** (D-02, [ESTIMADO]). Antes de cortar: casco medido (PENDIENTES P0.1), `inputs.yaml → boat.*` actualizado, `python run_all.py` en verde y **replanteo sobre el casco real** con plantilla de cartón o MDF. Origen: cara exterior del espejo, crujía, quilla (x hacia proa, z hacia arriba).

| # | Cambio | Cotas (CAD) | Verificar antes de seguir |
|---|---|---|---|
| C1 | **Recorte del fondo para la placa base P1-INT-02** (H-CUT-BOT) | La placa va de x = <!--V:manifest.params.toma_plate_x0:.0f-->286<!--/V--> a <!--V:manifest.params.toma_plate_x1:.0f-->801<!--/V--> mm, semiancho <!--V:manifest.params.toma_plate_y:.0f-->150<!--/V--> mm, en crujía; el recorte es la placa menos el ala de <!--V:manifest.params.toma_rim_w:.0f-->25<!--/V--> mm por lado, con <!--V:manifest.params.toma_seal_gap:.1f-->0.5<!--/V--> mm de luz para el Sikaflex. Abertura hidráulica <!--V:manifest.params.L_open:.0f-->380<!--/V--> × <!--V:manifest.params.W_open:.0f-->158<!--/V--> mm entre el labio (x = <!--V:manifest.params.x_lip:.0f-->386<!--/V-->) y la tangencia de la rampa (x = <!--V:manifest.params.x_tan:.0f-->766<!--/V-->). Fondo de <!--V:manifest.params.bottom_t:.0f-->4<!--/V--> mm [SUPUESTO: medir] | Zona plana, sin quilla, tracas ni remaches en la abertura y ≥ 0,5 m limpio a proa de la tangencia [VERIFICADO: R10a §7, §8.2]. Escalón placa ↔ fondo ≤ 1 mm (P1-INT-02). **Espesor real del fondo** (con cualquier sobreplaca): con el supuesto la tobera fija y la carcasa quedan a pocos milímetros del fondo interior; si supera 6 mm, subir `waterjet.axis_height_m` lo mismo, correr `run_all.py` (`verify_parts.py` falla si no) y revisar que el eje siga bajo la flotación (`sizing.priming.axis_below_wl_m`) [auditoria.md W-16] |
| C2 | **Agujeros del ala** (H-HOLES) | M<!--V:manifest.params.toma_hull_bolt:.0f-->6<!--/V--> ISO 10642 A4-70 avellanados desde afuera, paso <!--V:manifest.params.toma_hull_pitch:.0f-->70<!--/V--> mm, tuerca autofrenante A4 adentro. Taladrar con la placa presentada como plantilla | Avellanado: cabeza enrasada con el fondo |
| C3 | **Agujero del espejo** (H-CUT-TR) | Ø<!--V:manifest.params.transom_hole_d:.1f-->160.8<!--/V--> mm, centro en crujía a z = <!--V:manifest.params.z_noz:.0f-->92<!--/V--> mm sobre la quilla (eje de la tobera). Espejo de <!--V:manifest.params.transom_t:.0f-->6<!--/V--> mm [SUPUESTO: medir]. Más los 6 × M6 de la placa de espejo P1-PMP-09 (taladrar con la placa como plantilla) | El agujero queda concéntrico con el eje del conducto: verificar con el conducto presentado y un hilo tenso por el eje antes de cortar |
| C4 | **Pasos del espejo, sobre la flotación** (H-HOLES) | Pasacasco del testigo de refrigeración P1-ELE-03 (Ø17); salida de achique (B-BILGE-HOSE); pasamuros M66 P1-CTL-04 (M20 × 1,5) y 2 prensaestopas M16 (Mach5 y Bowden) en la placa interior P1-CTL-01 (6 × M6); 2 × M6 del tope de dirección P1-STE-08 | Todo por encima de la flotación medida (T1.2): la flotación de cálculo está a <!--V:sizing.hydrostatics.draft_m:.3f-->0.285<!--/V--> m de la quilla [CALCULADO] |
| C5 | **Varengas y refuerzos** (H-FLOORS, H-WELD) | Al 5083 6 mm a ambos lados del recorte y bajo el pórtico (x ≈ <!--V:manifest.params.brg_bracket_x0:.0f-->532<!--/V-->–<!--V:manifest.params.brg_bracket_x1:.0f-->682<!--/V-->) y el soporte del motor (x ≈ <!--V:manifest.params.mot_x0:.0f-->682<!--/V-->–<!--V:manifest.params.mot_x1:.0f-->797<!--/V-->); refuerzo del borde del recorte. Los pies del motor P1-MOT-02 van con 4 × M<!--V:manifest.params.mot_foot_bolt:.0f-->8<!--/V--> a las varengas a través del piso | El empuje a punto fijo, hasta <!--V:sizing.mech.Fa_max_N:.0f-->665<!--/V--> N [CALCULADO], va del pórtico a la placa base y de los bulones del ala al casco: las varengas le dan rigidez al borde del recorte. Soldadura con cordones intermitentes, sin recalentar el fondo (H-WELD). Dimensionarlas con el casco medido |
| C6 | **Piso en la zona del motor** | Piso a z = <!--V:manifest.params.floor_z:.0f-->75<!--/V--> mm sobre la quilla en el CAD; luz motor ↔ piso <!--V:manifest.params.mot_clear_floor:.0f-->16<!--/V--> mm [CALCULADO] | Si el piso real está más alto, cambia el soporte del motor: medir antes de pedir P1-MOT-02 |
| C7 | **Flotación fija ~100 L** (B-FOAM, H-FOAMBAY) | Espuma de celda cerrada en compartimentos bajo el asiento y en proa, repartida a ambas bandas, **fuera de la sentina** [ESTIMADO: R10b H5, 1,5 × peso neto sumergido] | E2/E3 (T1.4–T1.5): flota inundado con escora ≤ 10° [VERIFICADO: 33 CFR 183.225]. La espuma PU pierde flotación con inmersión continua: revisable [VERIFICADO: R11 §10.12] |
| C8 | **Achique** (B-BILGE, B-ALARM, B-12V, B-BILGE-HOSE) | Bomba automática en el punto más bajo de la sentina (a proa de la toma), alarma de nivel alto, 12 V desde un DC-DC aislado **aguas arriba de S1/K1** con fusible F4 | Funciona con el kill tirado y S1 en OFF (T0.M8) |
| C9 | **Bancada de baterías** (H-BATT) | Caja estanca B-BOX con las 2 baterías (≈ 40 kg) sobre calzos, por encima del nivel de sentina, 2 correas ≥ 4 × peso | ISO 13297 8.1: batería en lugar seco sobre el agua de sentina [VERIFICADO: R06 §5.1] |
| C10 | **Cockpit** (si E1 lo exige y para la clasificación legal) | Asiento bajo la borda, brazola ≥ 250 mm, volante, palancas y respaldo; nada de montura ni manillar [ESTIMADO: R13 §1.4, §9] | Es lo que sostiene que no es "vandscooter" (D-20). Si E1 falla: manga en la flotación ≥ 0,9 m o flotadores laterales (D-04) |

La chimenea de inspección termina a z = <!--V:manifest.params.toma_chim_top:.0f-->350<!--/V--> mm: su tapa tiene que quedar ≥ 60 mm sobre la flotación medida [visor REVISAR P1-INT-04; R10a §0.3]. Si con el casco medido no queda, alargar la chimenea antes de soldar.

---

## 3. Secuencia de montaje

Prerrequisitos: T1.1 aprobado (R1); cambios de casco C1–C10 hechos; piezas recibidas e inspeccionadas contra sus planos (`04_diseno/planos/`); ensayos de taller de 05 §7 aprobados, en particular la **prueba de estanqueidad del conducto soldado** (aire 0,3 bar + jabón, S-WELD-INT) y la **prueba hidrostática de la toma y la bomba a 0,3 MPa** [ESTIMADO: R12 §7.2; presión de diseño <!--V:est.loads.structural_bomba.loads_used.p_design_Pa:.0f-->200000<!--/V--> Pa]. Las piezas tienen el orden de montaje verificado en el CAD (checks de P1-DRV-01: cada pieza pasa por los Ø de lo ya montado; `params_tren.py`).

**Importante:** la bomba **no pasa por el agujero del espejo**: la brida de la toma (Ø<!--V:manifest.params.pump_flange_od:.0f-->193<!--/V-->) y la de la tobera (Ø<!--V:manifest.params.pmp_f2_od:.0f-->186<!--/V-->) son mayores que el agujero (Ø<!--V:manifest.params.transom_hole_d:.1f-->160.8<!--/V-->). Carcasa, estator y tobera se montan desde adentro del casco; por el espejo asoma solo el resalte de la tobera, y la placa de espejo se pone desde afuera.

| Paso | Qué | Cómo (uniones y pares) | Verificar antes del paso siguiente |
|---|---|---|---|
| M1 | **Toma: placa base + conducto** (P1-INT-01/02, subconjunto soldado por el taller) | Presentar en seco desde adentro: el ala apoya sobre el casco y el cuerpo llena el recorte. Limpiar, Sika Aktivator + Primer (H-PRIMER), cama de Sikaflex-291i de 0,5–1 mm en el ala y en la luz (H-SIKA). Bulones M6 del ala (C2) con Tef-Gel. En el mismo paso, los 4 tornillos ISO 10642 M8 × 35 A4-70 del pórtico (B-STUD) desde afuera, cabeza en Sikaflex, tuerca provisoria. Curado según la ficha de Sika (R05 S36) antes de cargar | Escalón ≤ 1 mm en todo el perímetro; cordón de Sikaflex continuo afuera y adentro; los 4 espárragos perpendiculares a la placa (escuadra) |
| M2 | **Rejilla y tapa de inspección** (P1-INT-03, P1-INT-04) | Rejilla desde afuera, 4 × M5 A4 con Tef-Gel. Tapa con O-ring y grasa de silicona (B-GREASE), 4 × M6 con arandela ancha; tornillo de purga con arandela de estanqueidad | Barras enrasadas, escalón ≤ 2 mm y sin rebabas [VERIFICADO: R10a §8.6]; luz entre barras <!--V:manifest.params.toma_bar_gap:.1f-->16.3<!--/V--> mm (ver H-11 sobre dedos) |
| M3 | **Bomba hacia el espejo: carcasa con impulsor** (P1-PMP-01 con P1-PMP-02 prensado y torneado por el taller; P1-PMP-03) | Impulsor adentro del anillo de desgaste (queda suelto hasta que llegue el eje). O-ring de cara en la carcasa (grasa de silicona). Carcasa contra la brida del conducto con <!--V:manifest.params.pump_flange_n:.0f-->8<!--/V--> × M<!--V:manifest.params.pump_flange_bolt:.0f-->6<!--/V--> A4, Tef-Gel, tuercas A4 del lado del conducto, apriete en cruz | Puerto de refrigeración <!--V:manifest.params.pmp_cool_thread:-->G1/8<!--/V--> arriba; la carcasa no toca el espejo; la tobera (paso M8) va a quedar centrada en el agujero del espejo |
| M4 | **Eje con sello, en banco** (P1-DRV-01, P1-DRV-02, P1-DRV-07) | Asiento fijo del sello prensado en la caja (copa de NBR mojada con agua, sin grasa en las caras). Desde la **punta de popa** del eje: caja del sello hasta el collar y cabeza rotante hasta su anillo DIN 471 de respaldo. Después, anillo DIN 471 de empuje + arandela 316 en la ranura delantera del impulsor (B-CIRC) | Nada pasa por el collar Ø26; caras del sello limpias (alcohol isopropílico, sin tocarlas con los dedos); fuelle sin torcer |
| M5 | **Eje con sello, desde proa** | El subconjunto entra por proa, punta de popa primero, por el buje del sello de la toma (Ø<!--V:manifest.params.seal_spigot_d:.0f-->42<!--/V--> H8), el tubo del conducto y el agujero del impulsor. Espigón de la caja en el buje con Tef-Gel; 4 × M6 A4 de la caja con Tef-Gel y arandela aislante | El impulsor apoya contra la arandela y el DIN 471 de empuje; la linterna del sello queda con las ventanas a la vista y la salida G1/8 abajo |
| M6 | **Pórtico sobre los espárragos** (P1-DRV-03) | Sacar las tuercas provisorias. El pórtico baja vertical sobre los 4 espárragos M<!--V:manifest.params.brg_bracket_bolt:.0f-->8<!--/V-->, pasando el alojamiento Ø47 por la punta de proa del eje. Arandela ISO 7089 + tuerca ISO 4032 A4 **a mano** | Zapatas apoyadas planas sobre la placa base (galga 0,05 mm no entra) |
| M7 | **Rodamientos, KM4 y tapa** (P1-DRV-04/05/06) | Par 7204 BEP **en O**, prensados a la vez en el alojamiento y en el muñón **desde proa** contra el collar (tubo de montaje sobre los dos aros). MB4 + KM4 con llave de gancho y doblar un diente de la MB4 en la ranura. Tapa P1-DRV-06 con 4 × M<!--V:manifest.params.drv_cover_bolt:.0f-->5<!--/V--> A4 y Tef-Gel; grasa + anillo V del lado del acople. Con el casquillo de centrado en la caja del sello, apretar las tuercas M8 a <!--V:manifest.params.drv_nut_torque_Nm:.0f-->15<!--/V--> N·m con Tef-Gel. Escariar 2 pasadores Ø6 por zapata | **T0.M1** giro libre a mano y **T0.M3** juego axial. Marca de pintura en las 4 tuercas |
| M8 | **Pasador de corte, retén, estator y tobera** (P1-PMP-04 a 08), desde adentro, por popa de la carcasa | Pasador Al 6061 Ø<!--V:sizing.mech.shear_pin.d_mm:.1f-->3.5<!--/V--> por el cubo y el eje; anillo retén P1-PMP-04 deslizado (Loctite 641) y 2 × M3 avellanados; DIN 471 de retención de popa (opcional). Estator con el buje de agua ya prensado (H7/s6, desde proa, en banco) deslizado en la carcasa sobre el muñón; 2 × M5 radiales anti-giro; agujero de refrigeración alineado con el puerto. Tobera fija con <!--V:manifest.params.pump_flange_n:.0f-->8<!--/V--> × M6 A4 y Tef-Gel: su espiga aprieta la camisa del estator | **T0.M2** holgura de punta con galgas (el eje ya está en sus dos apoyos) y **T0.M1** otra vez |
| M9 | **Placa de espejo desde popa** (P1-PMP-09, P1-PMP-10, P1-PMP-11) | Junta NBR + Sikaflex en el espejo. O-ring radial con grasa de silicona en el resalte de la tobera; la placa desliza el cuello sobre el resalte. 6 × M6 A4 a través del espejo con Tef-Gel, arandelas aislantes y arandelas grandes o contraplaca adentro. Bujes POM de pivote prensados | La bomba sigue apoyada solo en la brida de la toma: aflojar y volver a apretar la placa no mueve el eje (comparador en el cubo del acople, sin cambio) |
| M10 | **Acople** (P1-DRV-08) | Cubo del lado del eje refrentado a su largo de montaje, chaveta 6 × 6 A4 (B-KEY) y prisionero con Loctite 243 (lejos de todo PETG). Cubo del lado del motor en el eje Ø15 del motor con su chaveta. Estrella T-PUR 92 ShA | Chavetas sin juego lateral; prisioneros con marca |
| M11 | **Motor** (P1-MOT-01 sobre P1-MOT-02) | Soporte a la cara del motor con <!--V:manifest.params.mot.mount_n:.0f-->4<!--/V--> × M<!--V:manifest.params.mot.mount_bolt:.0f-->6<!--/V--> (medir el motor recibido). Pies a las varengas con 4 × M8 a través del piso, con Tef-Gel. Separación entre cubos = <!--V:manifest.params.drv_coupling.s:.1f-->2.0<!--/V--> mm (juego axial: el motor no recibe empuje) | **T0.M4** alineación del acople; T0.M1 con el motor acoplado |
| M12 | **Refrigeración** (B-BARB, B-STRAIN, B-HOSE, B-HCLAMP, P1-ELE-03) | Espiga 316 en el puerto de la carcasa → filtro en línea → manguera Ø6 × 8 → caja de agua del controlador → camisa del motor → pasacasco testigo del espejo (sobre la flotación, a la vista). Abrazaderas A4 en cada espiga. Manguera de la linterna del sello (G1/8 abajo) a la sentina, visible | **T0.M7** con agua de red: sin fugas y sale por el testigo |
| M13 | **Boquilla, bucket y cables** (P1-STE-*, P1-REV-*, P1-CTL-01/04/05) | Boquilla entre las orejas de la placa de espejo con 3 arandelas POM; perno superior P1-STE-02 y espárrago inferior P1-STE-05 roscados M6 con Loctite 243. Brida del yugo 4 × M8 A4 con Tef-Gel, poste, brazo, biela M8 con contratuercas. Tope de dirección P1-STE-08 al espejo (2 × M6). Bucket con bujes POM, pernos P1-REV-02 y tuerca autoblocante A4; émbolo P1-REV-04 con contratuerca; soporte Mach5 P1-REV-05, varilla y perno P1-REV-06 (Loctite 243); soporte del Bowden P1-REV-09. Pasamuros M66 y prensaestopas en la placa P1-CTL-01 (Sikaflex afuera). Mach5 y Bowden con un bucle libre hasta la boquilla | **T0.M6**: la dirección para en el tope (±<!--V:manifest.params.STE_stop_deg:.1f-->26.5<!--/V-->°) antes de que la boquilla toque la tobera; el bucket arriba no toca el chorro; la traba entra arriba y abajo [CALCULADO: `verify.json` sin interferencias en δ ±<!--V:manifest.params.steer_max:.0f-->25<!--/V-->° y bucket arriba/abajo] |
| M14 | **Electrónica** (B-BOX y lista de E4; README de electrónica §1–§9) | Caja de baterías en su bancada; las 2 baterías en paralelo con **un fusible por rama** de <!--V:sizing.electrical.fuse_branch_a:.0f-->125<!--/V--> A a barras; F1 de <!--V:sizing.electrical.fuse_a:.0f-->250<!--/V--> A a ≤ 175 mm del borne + [VERIFICADO: R06 §5.1]; S1, K1 con R_pre, controlador sobre P1-ELE-01 con la capota P1-ELE-02; cable DC <!--V:sizing.electrical.cable_dc.section_mm2:.0f-->70<!--/V--> mm² y fases <!--V:sizing.electrical.cable_phase.section_mm2:.0f-->95<!--/V--> mm², terminales crimpados con termocontraíble con adhesivo; NTC pegado al estator del motor; caja IP67 de mando. **BAT− no va al casco** | **T0.1** aislación y **T0.2** tensiones antes de unir las baterías en paralelo |
| M15 | **Mandos** (consola de Jorge, P1-CTL-02/03/08–14) | Caja T85 + volante, cable M66 a la biela del yugo; unidad de palancas sobre la placa central P1-CTL-08 (2 × M6 por debajo de la tapa de la consola); Mach5 de la consola; gatillo y Bowden; hall con imán (entrehierro del plano); soporte del kill switch y seta | T0.5 calibración, T0.M6 enclavamiento, T0.10–T0.11 bucket con el firmware |

---

## 4. Aislamiento galvánico

Casco, placa base, conducto, placa de espejo y bucket son Al 5083: el mismo metal, sin par entre ellos (D-09). El riesgo está en el 316 en contacto con aluminio bajo el agua: ~670 mV de diferencia contra un límite práctico de 200 mV [VERIFICADO: R06 §6, Gerr].

| Par | Dónde | Medida | Control |
|---|---|---|---|
| Tornillería A4 ↔ Al | Ala de la placa base, bridas de la bomba, placa de espejo, brida del yugo, tope, pórtico | Tef-Gel en roscas y asientos + arandela de nylon bajo cabeza y tuerca (B-TEFGEL, B-ISOW) [VERIFICADO: R06 §6] | Visual al desarmar: sin polvo blanco alrededor de las cabezas |
| Anillo de desgaste 316 ↔ carcasa 6061 | Asiento prensado (sin anodizado: S-ANOD enmascara los asientos H7) | Loctite 648 en el prensado; ánodo | Inspección por la tobera al cambiar el pasador |
| Caja del sello 316 ↔ buje del conducto 5083 | Espigón y brida de 4 × M6 | Tef-Gel en el espigón y la cara; arandelas aislantes | Al desmontar el sello |
| Rejilla 316 ↔ bloque del labio y placa base 5083 | Ranuras y bolsillos, bajo el agua | Tef-Gel en ranuras y tornillos M5; ánodo. Ver bloqueo H-11 | Inspección mensual desde afuera |
| Pasador Al 6061 ↔ eje e impulsor 316 | Cubo del impulsor | Pasador consumible (§7); el Al es el ánodo: se corroe él, no el eje | Se cambia por mantenimiento |
| Pernos 316 ↔ boquilla 6061 y bucket 5083 | Pivotes | Bujes y arandelas de POM (P1-PMP-11, P1-STE-03, P1-REV-03): sin contacto metal-metal | Juego de los bujes (§7) |
| Émbolo A4 ↔ oreja de la boquilla | Rosca M20 | Tef-Gel en la rosca | Al lubricar el émbolo |
| Pasamuros M66 316 ↔ espejo 5083 | Sobre la flotación | Sikaflex + Tef-Gel + arandela aislante | — |
| Sistema eléctrico ↔ casco | BAT− y todo el circuito de potencia | Flotante: nada del circuito toca el casco [VERIFICADO: R06 §5.1, ISO 13297 4.1] | **T0.1** > 1 MΩ BAT− ↔ casco, BAT− ↔ eje, B+ ↔ casco, antes de cada temporada |
| Protección catódica | Carcasa / conducto | Ánodo de **aluminio** (no zinc en agua salobre) con continuidad eléctrica a la carcasa y al conducto (B-ANODE) [VERIFICADO: R06 §6, Fisheries Supply] | Continuidad ánodo ↔ conducto ↔ carcasa < 1 Ω con multímetro [SUPUESTO]; cambiar al 50 % consumido o una vez por año [VERIFICADO: R06 §6] |

Nada de latón ni de fibra de carbono bajo el agua [VERIFICADO: R06 §0, §6]. Los insertos de latón (B-INS) van solo en la base y la capota del controlador, que son piezas secas.

---

## 5. Pruebas por etapas

No se pasa de etapa si una prueba no pasa. Cada prueba deja un registro: fecha, quién, valores medidos, fotos o video, log del VESC exportado. Criterios numéricos desde `sizing.json → success.*` (factores en `inputs.yaml → operation.success` [SUPUESTO]) y 02 §11.

### T0 — Banco en seco (bote en tierra o en el trailer)

**Condición:** acople desconectado (estrella sacada; correr el motor hacia proa sobre sus pies): el sello no gira en seco (R2). Extintor ABC a mano.

| # | Prueba | Cómo | Pasa si | Si no pasa |
|---|---|---|---|---|
| T0.1–T0.20 | Electrónica, kill switch y firmware | README de electrónica §10 (aislación, tensiones, precarga, contactor, calibración, configuración del VESC, arranque con acelerador abierto, rampa, bucket, kill por cordón y seta 10/10, barreras independientes, falla de sensor, pérdida de PPM, watchdog, vida del interruptor, perfil COSTA/ABIERTO) | Los criterios de esa tabla; en particular corte < 1 s en 10/10 (T0.12–T0.13) | Corregir y repetir la prueba entera. Sin T0.12–T0.15 aprobadas no hay T2 |
| T0.M1 | Giro libre | A mano en el cubo del acople, 3 vueltas lentas, después de M7, M8 y M11 | Sin roce, sin punto duro, sin ruido de contacto del impulsor con el anillo | Desarmar: buscar el contacto (marca brillante en el anillo o en las puntas) |
| T0.M2 | Holgura de punta | Galgas en 4 posiciones del anillo × 4 posiciones angulares del impulsor (girando a mano) | 0,3–0,4 mm radial en las 16 lecturas [ESTIMADO: R12 §2.7]; diseño <!--V:manifest.params.tip_clr:.2f-->0.40<!--/V--> mm, concentricidad del anillo ≤ <!--V:manifest.params.pmp_ring_TIR:.2f-->0.05<!--/V--> mm | Diferencia > 0,1 mm entre lecturas: excentricidad del eje (revisar el centrado del pórtico, paso M7). Holgura < 0,3: el taller repasa el anillo; > 0,4: anillo nuevo |
| T0.M3 | Juego axial y vibración | Comparador 0,01 mm en la cara del cubo del acople, empujar y tirar a mano del eje; golpe de martillo de goma en el eje montado con el celular apoyado (app de espectro) | Juego axial no perceptible (< 0,01 mm) [SUPUESTO: par 7204 apareado y precargado]; primera frecuencia propia > rpm máx. (<!--V:sizing.mech.n_max_rpm:.0f-->4723<!--/V--> rpm) / 60 con margen; el cálculo da <!--V:sizing.mech.crit_ratio:.1f-->3.4<!--/V--> × [CALCULADO; método de 02 §12] | Juego: KM4 floja o rodamientos no apareados. Frecuencia baja: revisar el buje de agua (2.º apoyo) |
| T0.M4 | Alineación del acople | Comparador sobre el cubo del lado del motor, girando a mano; galgas entre cubos en 4 posiciones | Separación entre cubos <!--V:manifest.params.drv_coupling.s:.1f-->2.0<!--/V--> mm en las 4 posiciones; desalineación radial y angular dentro de la tabla de KTR para Rotex 24 (pedirla con el acople: no está en el repositorio) | Calzar los pies del motor; repetir |
| T0.M5 | Motor solo | VESC Tool: detección del motor (FOC), sentido de giro, pares de polos, lectura del NTC | Gira en el sentido de la bomba: <!--V:manifest.params.pmp_rot_sense:-->antihorario visto desde popa (+X, regla de la mano derecha)<!--/V-->; pares de polos anotados en `inputs.yaml` y `run_all.py` corrido (cambia el tope de ERPM de COSTA, hoy <!--V:sizing.legal_speed.erpm_cap:.0f-->10462<!--/V--> ERPM [CALCULADO con los pares de polos de `inputs.yaml`]); NTC a temperatura ambiente ±3 °C [SUPUESTO] | Sentido: invertir dos fases o el parámetro del VESC. Pares de polos distintos: volver a cargar `l_max_erpm` (T0.6, T0.20) |
| T0.M6 | Mandos mecánicos | Volante tope a tope; palanca del bucket con el acelerador en 0 y fuera de 0; gatillo | Boquilla ±<!--V:manifest.params.steer_max:.0f-->25<!--/V-->° y para en el tope mecánico; el bucket baja y sube completo y la traba entra sola en las dos posiciones; con el acelerador fuera de 0 la palanca del bucket no se mueve (enclavamiento) | Ajustar terminales del M66/Mach5 y el Bowden; nunca sacar el tope |
| T0.M7 | Circuito de refrigeración | Agua de red a baja presión en la espiga de la carcasa, 5 min | Sale chorro continuo por el testigo del espejo; ninguna gota en espigas, filtro, caja de agua ni camisa | Rehacer la unión; abrazaderas nuevas |
| T0.M8 | Achique y alarma | Agua en la sentina hasta el flotante, con S1 en OFF y el cordón afuera | Bomba arranca sola y desagota por el pasacasco; alarma suena con el nivel alto | Revisar el DC-DC de 12 V y F4: tienen que estar aguas arriba de S1/K1 |

### T1 — Estanqueidad, flotación y escora

**T1.1 bloquea todo lo demás** (R13 §5; D-04). Se hace primero con el casco sin cortar y lastre equivalente (antes de comprar), y se repite con el equipo instalado.

| # | Prueba | Cómo | Pasa si | Si no pasa |
|---|---|---|---|---|
| T1.1 | **E1 — escora con carga desplazada** | En el muelle, agua calma. Masa de diseño <!--V:sizing.masses.total_kg:.0f-->217<!--/V--> kg con lastre; piloto de 100 kg o lastre equivalente con su CG ≥ 100 mm sobre el asiento, desplazado 0,1 m, 0,2 m y hasta la borda. Inclinómetro del celular, francobordo con regla | Sin entrada de agua; francobordo residual ≥ 100 mm; escora ≤ 15° con el piloto a 0,2 m de crujía [SUPUESTO: umbrales de R13 §5; método: ISO 12217-3 ESTIMADO y 33 CFR 183.230 VERIFICADO] | El cálculo da GM = <!--V:sizing.hydrostatics.GM_m:.3f-->0.008<!--/V--> m y <!--V:sizing.heel_pilot_0p1m_deg:.0f-->79<!--/V-->° con 0,1 m [CALCULADO, casco ESTIMADO]: lo esperable es que falle. Cambio de casco (manga en la flotación ≥ 0,9 m, flotadores laterales, asiento más bajo) y repetir. **No se sigue** |
| T1.2 | Calado y cebado geométrico | Todo instalado, piloto a bordo, agua del fiordo: medir el calado en el espejo, en crujía, y la altura de la tapa de la chimenea sobre el agua | Eje del impulsor (a <!--V:sizing.priming.axis_height_m:.3f-->0.115<!--/V--> m de la quilla) ≥ 20 mm bajo la flotación [VERIFICADO: R10a §3.2, §8.1]; cálculo: <!--V:sizing.priming.axis_below_wl_m:.3f-->0.170<!--/V--> m bajo; tapa ≥ 60 mm sobre el agua; todos los pasos del espejo sobre el agua | Eje alto: no ceba → bajar el eje (`h_axis`) y rehacer la toma. Tapa baja: alargar la chimenea |
| T1.3 | Estanqueidad a flote | 24 h amarrado, sistema sin girar, sentina seca y fotografiada al empezar | Sentina seca a las 24 h; testigo del sello seco; sin agua alrededor de la placa base, la placa de espejo ni los pasacascos [VERIFICADO: R10a §8.5] | Localizar con papel tisú; sacar el bote antes de que la batería toque agua. Rehacer el Sikaflex o el sello |
| T1.4 | E2 — inundado | **Sin baterías, motor ni controlador**: lastre inerte de igual peso sumergido; llenar de agua; más 2/15 del peso del piloto sumergido; 18 h | Flota; idealmente nivelado, escora ≤ 10° [VERIFICADO: 33 CFR 183.105 / 183.225] | Más flotación (C7) y repartirla mejor; repetir |
| T1.5 | E3 — inundado con carga desplazada | Como T1.4 con medio peso de persona en una banda | Escora ≤ 30° [VERIFICADO: 33 CFR 183.230] | Ídem |
| T1.6 | E4 — reabordaje | Persona con chaleco, desde el agua, sin ayuda ni escalera auxiliar | Sube sin volcar el bote [VERIFICADO: RCD 2.3, vía R13 §5] | Escalón o asa de reabordaje en el espejo, lejos de la boquilla; repetir |

### T2 — Muelle, amarrado

Bote amarrado de proa a un punto fijo con el dinamómetro en el cabo, en ≥ 1 m de agua libre bajo la toma, sin bañistas. Piloto a bordo con chaleco y cordón. VESC Tool registrando (corriente, rpm, temperaturas, fallas).

| # | Prueba | Cómo | Pasa si | Si no pasa |
|---|---|---|---|---|
| T2.1 | Purga y cebado | Purgar la chimenea (sale agua por el tornillo, cerrar); arrancar a rpm bajas | Chorro continuo por la tobera en ≤ 3 s [SUPUESTO: R10a §8.4] | Cortar; volver a purgar; revisar el O-ring de la tapa (si entra aire la bomba se desceba) |
| T2.2 | Refrigeración | Testigo del espejo al arrancar; caudal con jarra graduada y cronómetro a <!--V:sizing.legal_speed.n_legal_rpm:.0f-->2840<!--/V--> rpm (las de 5 kn) | Sale agua por el testigo en el primer minuto; caudal ≥ <!--V:sizing.cooling.Q_l_min_legal:.1f-->3.3<!--/V--> L/min [CALCULADO a 5 kn; a punto fijo la altura de la bomba es mayor con las mismas rpm] | Parar. Filtro tapado, manguera aplastada u orificio obstruido |
| T2.3 | Testigo del sello | Ventanas de la linterna y manguera testigo durante T2.1–T2.6 | Seco: ≤ 1 gota por minuto [SUPUESTO] | Parar; cambiar el sello (R-SEAL); revisar que no haya girado en seco |
| T2.4 | Dirección y bucket con chorro | Ralentí; volante tope a tope; bucket abajo **con el acelerador en 0**, reversa al límite del firmware, dinamómetro en el cabo de popa | Boquilla sin vibración ni golpe en los topes; reversa ≥ 0,8 × <!--V:sizing.performance.reverse_N:.0f-->188<!--/V--> N del modelo [SUPUESTO: mismo factor que el punto fijo]; la traba sostiene el bucket abajo | Reversa débil: revisar el recorrido del bucket (<!--V:manifest.params.bucket_down_deg:.0f-->70<!--/V-->° en el CAD) |
| T2.5 | **Rampa de punto fijo** | Escalones de 25 % de acelerador hasta fondo, 10 s cada uno; dinamómetro, rpm y corriente de batería | Empuje a fondo ≥ <!--V:sizing.success.bollard_min_N:.0f-->532<!--/V--> N (modelo <!--V:sizing.performance.bollard_N:.0f-->665<!--/V--> N) [CALCULADO]; corriente de batería ≤ <!--V:sizing.electrical.I_bat_limit_A:.0f-->192<!--/V--> A; rpm a fondo cerca del tope de punto fijo (<!--V:sizing.performance.peak_curve.0.n_rpm:.0f-->4329<!--/V--> rpm) | **No pasa** si las rpm suben con el empuje plano o hay ruido de grava (cavitación o aire) [VERIFICADO como síntoma: R10a §8.7]: rejilla, purga, tope de ERPM del perfil abierto (02 §4.6). Empuje bajo sin cavitación: holgura de punta, η de la bomba (bloqueo H-3) |
| T2.6 | Temperaturas | 3 min a fondo amarrado, después 5 min a ralentí; NTC del motor, temperatura del controlador (VESC) y del agua del testigo | Motor ≤ <!--V:sizing.thermal.T_motor_steady_C:.0f-->46<!--/V--> °C + 20 K [CALCULADO estacionario a V máx. + margen SUPUESTO] y siempre < <!--V:sizing.thermal.t_winding_max_C:.0f-->120<!--/V--> °C; sin recorte térmico en el log; agua del testigo tibia, ΔT ≤ 15 K [SUPUESTO: `inputs.yaml` cooling.dT_max_k; cálculo <!--V:sizing.cooling.dT_water_K:.1f-->1.7<!--/V--> K] | Revisar caudal (T2.2); pedir a Maytech el caudal de la camisa |
| T2.7 | Kill en el agua | Motor al 30 %: tirar del cordón; 5 veces; luego la seta | Sin empuje en < 1 s (video); al reponer el cordón con el acelerador abierto no arranca; 5/5 | Volver a T0.12–T0.15 |
| T2.8 | Limpieza de rejilla | Acelerador en 0, pulsador sostenido | Reversa lenta que dura ≤ 3 s y suelta lo atrapado (T0.11 b) | Revisar el firmware (README §5.2) |

### T3 — Agua calma, a menos de 300 m de la costa, a 5 kn

Als Fjord en calma (viento ≤ 6 m/s, Hs ≤ 0,3 m [SUPUESTO: R07 §3.4]), de día, con acompañante en otro bote, agua de ≥ 1 m bajo la toma. Perfil COSTA.

| # | Prueba | Cómo | Pasa si | Si no pasa |
|---|---|---|---|---|
| T3.1 | Límite legal (perfil COSTA) | Piloto liviano, batería llena, a fondo; GPS, 2 pasadas en sentidos opuestos | Media ≤ 9,0 km/h [SUPUESTO: 02 §3.1; límite 9,26 km/h = 5 kn] | `l_max_erpm` nuevo = actual × 9,0 / v medida (02 §3.1); repetir |
| T3.2 | Potencia a 5 kn | 5 kn estables por GPS, 2 min por sentido; P de batería del VESC | P_bat ≤ <!--V:sizing.success.p_legal_max_W:.0f-->2241<!--/V--> W (modelo <!--V:sizing.performance.legal.P_bat:.0f-->1724<!--/V--> W) [CALCULADO] | Resistencia mayor que el modelo: cargar el punto en `inputs.yaml`, `run_all.py`; revisar rejilla y holgura |
| T3.3 | Dirección | A 5 kn, volante a tope a cada banda hasta completar 360° | Gira en ambos sentidos sin pérdida de chorro ni golpes; diámetro de giro (GPS) ≤ 4 esloras [SUPUESTO] | Topes, recorrido del M66, boquilla |
| T3.4 | Reversa y freno | Desde 5 kn: acelerador a 0, bucket abajo, reversa al límite | Se detiene en ≤ 3 esloras [SUPUESTO]; marcha atrás controlable con la dirección; la traba sostiene el bucket | Recorrido y traba del bucket; límite de reversa |
| T3.5 | Hombre al agua | A 5 kn, tirar del cordón | Sin empuje en < 1 s; el bote se detiene y deriva | No navegar hasta resolver |
| T3.6 | Crucero de 30 min a 5 kn | Registro continuo | Testigo de refrigeración y del sello correctos todo el tiempo; sentina seca; energía consumida coherente con <!--V:sizing.legal_speed.autonomy_legal_h:.1f-->2.4<!--/V--> h de autonomía ±30 % [SUPUESTO: tolerancia] | Cargar el consumo medido en `inputs.yaml`; revisar fugas |

### T4 — Fuera de los 300 m: planeo y velocidad máxima

Solo en la franja central de Als Fjord a > 300 m de cualquier costa; **nunca en Als Sund (4 kn) ni en Augustenborg Fjord** [VERIFICADO: R13 §3]. Mismas condiciones de tiempo que T3, acompañante, perfil ABIERTO solo ahí.

| # | Prueba | Cómo | Pasa si | Si no pasa |
|---|---|---|---|---|
| T4.1 | Tiempo de 0 a planeo | A fondo desde parado; video + GPS; 3 veces | t ≤ <!--V:sizing.success.t_plane_max_s:.0f-->15<!--/V--> s (modelo <!--V:sizing.performance.t_to_plane_s:.1f-->inf<!--/V--> s; margen en la joroba <!--V:sizing.performance.hump_margin_min:.0%-->-6%<!--/V-->) [CALCULADO] | No planea: corriente de batería al límite (log), BMS cortando (FMEA F13), LCG (mover lastre a popa), masa real |
| T4.2 | V máx. sostenida | GPS, ida y vuelta, 1 min estable por sentido, batería > 50 % | Media ≥ <!--V:sizing.success.vmax_min_kmh:.1f-->21.3<!--/V--> km/h (modelo <!--V:sizing.performance.vmax_cont_kmh:.1f-->25.1<!--/V--> km/h; **el diseño no llega a los 30 km/h** del plano: D-12, 03 §3) [CALCULADO] | Cargar el punto; potencia continua real del motor (bloqueo H-3) |
| T4.3 | Térmico de crucero | 30 min de crucero rápido (perfil ABIERTO, sin llegar a fondo continuo: la autonomía a fondo es <!--V:sizing.energy.t_top_min:.0f-->37<!--/V--> min) | Motor ≤ <!--V:sizing.thermal.t_winding_max_C:.0f-->120<!--/V--> °C de bobinado (NTC) sin recorte en 30 min [VERIFICADO: R11 §1.2; criterio 02 §11] | Bajar la potencia continua del VESC; caudal de refrigeración |
| T4.4 | Aire con ola corta | Recorrido con ola corta de través y de proa, registrando rpm | Sin picos de rpm > 10 % sin mover el acelerador [SUPUESTO: R10a §8.10] | Bajar el tope de ERPM; limitar la ola de salida |

### Después de cada salida

Enjuagar con agua dulce casco, rejilla, boquilla, bucket, émbolo y conectores; mirar la rejilla y el impulsor por la chimenea (sistema desarmado); testigo del sello; sentina; anotar horas de motor, Wh, fallas del VESC y golpes en el registro. Cargar en tierra.

---

## 6. FMEA

Escalas 1–10 [SUPUESTO: juicio de este documento, no salen de ningún JSON]: **S** severidad (10 = muerte o pérdida del bote), **O** ocurrencia (10 = casi segura), **D** detección (10 = no se detecta antes de que pase). RPN = S × O × D. Prioridad: S ≥ 9 o RPN ≥ 120.

| # | Modo de falla | Efecto | S | O | D | RPN | Mitigación | Prueba que lo cubre |
|---|---|---|---|---|---|---|---|---|
| F1 | Piedra u objeto traba el impulsor | Corta el pasador: sin chorro no hay dirección ni freno. Sin pasador, ~490 J del rotor dañan eje, álabes o acople [CALCULADO: R12 §7.6] | 7 | 5 | 3 | 105 | Pasador Ø<!--V:sizing.mech.shear_pin.d_mm:.1f-->3.5<!--/V--> que corta a <!--V:sizing.mech.shear_pin.T_cut_Nm:.1f-->33.5<!--/V--> N·m; rejilla; ralentí en aguas bajas; pagaya y ancla a bordo; repuestos | Probeta del pasador (05 §7); T0.M1; checklist |
| F2 | El pasador corta solo, por arranque brusco o fatiga | Pérdida de propulsión sin aviso | 6 | 3 | 5 | 90 | Corta a ~1,8 × el par máximo del controlador (<!--V:sizing.mech.T_max_Nm:.1f-->18.6<!--/V--> N·m) [CALCULADO]; rampa ≥ 1 s del firmware; cambio por mantenimiento (§7) | T0.8; T2.5; §7 |
| F3 | Aire en la toma al arrancar (chimenea sin purgar) | La bomba no ceba o se desceba: sin chorro ni gobierno | 5 | 6 | 3 | 90 | Tornillo de purga; tapa con O-ring que sella en ambos sentidos; eje <!--V:sizing.priming.axis_below_wl_m:.3f-->0.170<!--/V--> m bajo la flotación [CALCULADO] | T2.1; checklist |
| F4 | Aire en marcha (ola corta, cabeceo, fondo plano) | Las rpm se disparan, pérdida de control momentánea [VERIFICADO: R10a §0.4] | 6 | 5 | 4 | 120 | Toma en crujía y a proa del impulsor, nada delante; tope de ERPM; soltar el acelerador; Hs ≤ 0,3 m | T4.4 |
| F5 | Algas o una bolsa tapan la rejilla | Pierde empuje, cavita, calienta | 5 | 6 | 4 | 120 | Rejilla de barras longitudinales perfiladas; pulsador de limpieza (reversa ≤ 3 s); chimenea de inspección; parar el motor suelta lo atrapado [VERIFICADO: R10a §7] | T0.11; T2.8; checklist |
| F6 | Cavitación sostenida | Erosión del impulsor y del anillo, ruido, menos empuje | 5 | 4 | 6 | 120 | S a V máx. <!--V:sizing.performance.top.S:.2f-->3.45<!--/V--> < 3,5; tope de ERPM del perfil abierto = rpm de punto fijo (02 §4.6); rampa | T2.5; inspección del impulsor (§7) |
| F7 | El sello gira en seco (bote en tierra, prueba con el acople puesto) | Caras dañadas → fuga | 7 | 4 | 5 | 140 | R2; T0 con la estrella sacada; caras carbón/SiC (toleran arranques cortos en seco) [VERIFICADO: R11 §5] | Procedimiento de T0; T2.3 |
| F8 | Fuga del sello mecánico en marcha | Agua a la sentina y, si pasa la linterna, a los rodamientos | 8 | 4 | 3 | 96 | Linterna con ventanas y manguera testigo; rodamientos del lado seco; achique + alarma; repuesto R-SEAL | T1.3; T2.3; checklist |
| F9 | Refrigeración cortada (filtro tapado, manguera aplastada, orificio obstruido) | Sobretemperatura de controlador y motor | 6 | 5 | 3 | 90 | Testigo visible desde el puesto; filtro en línea; NTC y límites térmicos del VESC | T0.M7; T2.2; checklist |
| F10 | Fuga del circuito de refrigeración adentro (manguera suelta: agua a presión de la bomba) | Agua sobre el controlador y en la sentina | 7 | 3 | 4 | 84 | Abrazaderas A4 en cada espiga; manguera ≥ 2 bar; recorrido lejos de la electrónica; capota P1-ELE-02; achique | T0.M7; T2.2 |
| F11 | Sobretemperatura del motor (potencia continua real < la estimada) | Recorte de potencia o bobinado dañado | 6 | 4 | 3 | 72 | NTC10K 3950 del motor (variante con hall, B-MOT) al VESC con recorte por temperatura; caudal de <!--V:sizing.cooling.Q_l_min_top:.1f-->5.2<!--/V--> L/min a V máx. [CALCULADO]; dato de Maytech (H-3) | T2.6; T4.3 |
| F12 | Sobretemperatura del controlador | Recorte de potencia en mal momento (joroba, giro) | 5 | 3 | 3 | 45 | Caja de agua del controlador en el mismo circuito; base elevada | T2.6; T4.3 |
| F13 | Corte por BMS de una batería en la joroba (rama desbalanceada > 120 A) | La otra rama toma todo y también corta: pérdida total de potencia de golpe | 6 | 4 | 5 | 120 | Límite de corriente de batería del VESC <!--V:sizing.electrical.I_bat_limit_A:.0f-->192<!--/V--> A < BMS 2 × 120 A [VERIFICADO: R11 §3.2]; cables de paralelo de igual largo y sección (B-CAB-PAR); baterías a ≤ 0,2 V entre sí antes de unirlas | T0.2; T2.5 y T4.1 (log de corriente) |
| F14 | Fusible de rama abierto (queda una batería sola) | La que queda se sobrecarga y su BMS corta en la primera aceleración | 5 | 3 | 6 | 90 | Fusible por rama de <!--V:sizing.electrical.fuse_branch_a:.0f-->125<!--/V--> A; medir la tensión de cada batería antes de salir | T0.2; checklist |
| F15 | Cable de fase cortado, flojo o en corto | Falla del controlador, arco, pérdida de propulsión | 7 | 3 | 4 | 84 | <!--V:sizing.electrical.cable_phase.section_mm2:.0f-->95<!--/V--> mm² con terminales crimpados y termocontraíble con adhesivo; prensaestopas; sujeción sin roce con bordes; protección por sobrecorriente del VESC | Inspección de tirón en M14; log de fallas del VESC en T2 |
| F16 | Pérdida de aislación (BAT− o B+ toca el casco) | Corrientes parásitas, corrosión rápida; corto si fallan los dos polos | 8 | 2 | 4 | 64 | Sistema flotante; F1 a ≤ 175 mm del borne; cubrebornes | T0.1 cada temporada |
| F17 | El kill switch no corta (K1 soldado, cableado) | El motor sigue con el piloto en el agua | 10 | 2 | 3 | 60 | 4 barreras independientes (README de electrónica §2); prueba del clic antes de cada salida | T0.12–T0.15; T2.7; checklist |
| F18 | El piloto cae con el cordón sin enganchar | Bote sin piloto en marcha | 10 | 3 | 7 | 210 | Cordón espiral al chaleco como primer ítem del checklist; sin cordón no arma (contacto cerrado con clip) | Checklist (no hay prueba técnica que lo detecte) |
| F19 | El bucket baja a velocidad (traba suelta, gatillo apretado) | Frenada violenta, piloto proyectado, daño en orejas y bulones | 8 | 2 | 4 | 64 | Émbolo indexador que traba arriba; enclavamiento mecánico de palancas; el firmware corta el avance al bajar el bucket (BKT_HOLD); bucket calculado para <!--V:est.loads.structural_direccion.F_bucket_N:.0f-->1408<!--/V--> N | T0.M6; T0.10–T0.11; T3.4 |
| F20 | El bucket no baja o no sube (Mach5 o émbolo agarrotados por sal) | Sin freno ni reversa, o reversa permanente limitada | 6 | 3 | 3 | 54 | Enjuague con agua dulce y lubricación; prueba en el checklist | Checklist; T3.4 |
| F21 | Falla del cable de dirección M66 o se suelta la biela | Boquilla libre: sin gobierno | 8 | 2 | 4 | 64 | Topes mecánicos a ±<!--V:manifest.params.STE_stop_deg:.1f-->26.5<!--/V-->°; rótula con contratuerca y marca; kill + bucket para frenar; pagaya | T0.M6; checklist |
| F22 | Vuelco por falta de estabilidad (al subir, reabordar o moverse) | Piloto al agua fría, bote volcado | 10 | 7 | 2 | 140 | Cambio de casco si E1 falla; asiento bajo; batería en el fondo; flotación | T1.1; T1.4–T1.6 |
| F23 | Inundación por la toma o la placa base (Sikaflex despegado, fisura en la soldadura, bulones flojos) | El bote se llena por un agujero de <!--V:manifest.params.L_open:.0f-->380<!--/V--> mm en el fondo | 9 | 3 | 4 | 108 | 5083 soldado y probado a presión; Sikaflex + bulones; flotación ~100 L; achique con alarma | Prueba de estanqueidad de taller (05 §7); T1.3; T1.4 |
| F24 | Agua por la chimenea (tapa mal cerrada, purga abierta) | Entra agua en marcha; la bomba aspira aire | 7 | 3 | 3 | 63 | Tapa ≥ 60 mm sobre la flotación; perillas; purga cerrada en el checklist | T1.2; checklist |
| F25 | Corrosión galvánica (pasador, rejilla 316 en 5083, tornillería A4) | Pasador debilitado, rejilla o bulones flojos, picaduras en el casco | 6 | 5 | 5 | 150 | §4: Tef-Gel, aislantes, ánodo de aluminio, sistema flotante | T0.1; §7 (ánodo, pasador) |
| F26 | Agua en la caja de baterías | LFP en agua salada: fuga térmica posible días después [VERIFICADO: R06 §4.2] | 9 | 2 | 4 | 72 | Caja estanca elevada sobre la sentina, prensaestopas un cable por paso; si se mojó: aislar al aire libre y descartar | T1.3; checklist |
| F27 | Holgura de punta crece (arena) | Menos empuje, más cavitación | 4 | 5 | 4 | 80 | Anillo de desgaste reemplazable; ralentí en arena | T0.M2 periódico (§7); T2.5 comparado |
| F28 | Desalineación del acople o estrella fatigada | Vibración, carga en rodamientos y motor | 5 | 3 | 4 | 60 | Alineación con comparador; estrella de repuesto R-SPIDER | T0.M4; §7 |
| F29 | Exceso de velocidad dentro de 300 m (perfil ABIERTO olvidado) | Multa; riesgo para bañistas | 7 | 4 | 5 | 140 | COSTA por defecto al encender; ABIERTO solo pasando por COSTA con el acelerador en 0; tope de <!--V:sizing.legal_speed.erpm_cap:.0f-->10462<!--/V--> ERPM en COSTA [CALCULADO] | T0.11 c; T0.20; T3.1 |
| F30 | Atrapamiento en la toma (persona en el agua junto a la popa, pelo, correas) | Lesión grave o ahogamiento [VERIFICADO: R10a §0.1] | 10 | 2 | 6 | 120 | Sistema desarmado con gente cerca de la popa; kill; luz de rejilla (H-11) | Checklist |
| F31 | Sensor del acelerador o PPM fallan | Avance inesperado o parada | 8 | 2 | 2 | 32 | Firmware: neutro ante falla de sensor, timeout de PPM, watchdog | T0.16–T0.18 |

---

## 7. Mantenimiento

| Ítem | Cada | Criterio | Acción |
|---|---|---|---|
| Pasador de corte (P1-PMP-05) | Cada temporada o 50 h de motor, y **siempre después de un golpe** [ESTIMADO: justificación de la fila de fatiga de P1-PMP-05 en `resultados/estructural.json`] | — | Cambiar (R-PIN). Hay que sacar tobera y estator desde adentro (§3, M8) |
| Ánodo de aluminio (B-ANODE) | Mirar cada mes; continuidad cada temporada | Cambiar al 50 % consumido o una vez por año [VERIFICADO: R06 §6] | Reemplazar; Tef-Gel en sus espárragos |
| Holgura de punta | Cada temporada y después de navegar sobre arena | 0,3–0,4 mm; anillo nuevo si pasa de 0,8 mm [ESTIMADO: R12 §2.7] | T0.M2 |
| Sello mecánico | Testigo en cada salida | > 1 gota por minuto en marcha [SUPUESTO] | Cambiar (R-SEAL); revisar el eje bajo el fuelle |
| Rodamientos 7204 BEP | Cada temporada | Sin juego axial (T0.M3), sin ruido al girar a mano, grasa limpia; vida L10 calculada muy por encima del uso [CALCULADO: 02 §7] | Regrasar el lado del acople; cambiar si hay óxido (agua pasó la linterna) |
| Buje de agua del estator (P1-PMP-07) | Cada temporada | Juego radial del eje en el buje: anotar el valor nuevo y cambiar al doble [SUPUESTO] | Cambiar (R-BUSH) |
| Estrella del Rotex | Cada temporada | Sin grietas ni deformación permanente | R-SPIDER |
| Bujes y arandelas de POM (pivotes) | Cada temporada | Juego visible en la boquilla o el bucket | Tornear nuevos |
| O-rings | Cada vez que se abre una brida o la tapa | Siempre | Juego nuevo (R-ORING), grasa de silicona |
| Filtro de refrigeración y rejilla | Cada salida | Limpios | Limpiar |
| Aislación del sistema eléctrico | Cada temporada | > 1 MΩ (T0.1) | Buscar el contacto |
| Tornillería | Cada salida (marcas de pintura); reapretar el pórtico a <!--V:manifest.params.drv_nut_torque_Nm:.0f-->15<!--/V--> N·m después de las primeras 2 h [SUPUESTO] | Marca corrida = floja | Reapretar al par y volver a marcar |
| Flotación y achique | Cada temporada (espuma); cada salida (achique y alarma) | Espuma seca y entera | Reemplazar la espuma mojada |
| Baterías | Invierno | Guardar secas, cargadas a nivel de almacenamiento según LiTime; cargar solo sobre 5 °C (B-CHG) | — |

---

## 8. Bloqueos abiertos (al 2026-10-02)

| H | Problema | Bloquea | Fuente |
|---|---|---|---|
| H-1 | **Estabilidad:** GM = <!--V:sizing.hydrostatics.GM_m:.3f-->0.008<!--/V--> m con el casco leído del plano; E1 probablemente falla | Todo: compras de E1 en adelante, cortes en el casco, T2–T4 | D-04; R13 §5; 02 §2.2 |
| H-2 | Casco sin medir: fondo, espejo, calado, piso y consola son [ESTIMADO] o [SUPUESTO]. Con un fondo > 6 mm la bomba no entra con el eje a la altura actual (auditoría W-16) | Cortes C1–C6, pedido de placa base, conducto, soporte del motor y cables | D-02; PENDIENTES P0.1 |
| H-3 | Potencia continua del MTI120116 no publicada ([ESTIMADO] en `inputs.yaml`); η y curva de la bomba sin ensayo | Interpretar T2.5, T4.2 y T4.3; la V máx. sostenida no llega a 30 km/h (estado del optimizador: <!--V:sizing.status:-->sin_solucion_dura<!--/V-->) | D-12; 02 §12 |
| H-4 | Pares de polos del motor: el tope de ERPM de COSTA y del perfil abierto es rpm × pares de polos. El dato de `inputs.yaml` se está corrigiendo (el MTI120116 es 12N10P); confirmarlo con la detección del VESC y regenerar | T3 (perfil COSTA) | 02 §3.1; T0.M5 |
| H-5 | Clasificación legal sin respuesta escrita (vandscooter / speedbåd / playas) | Construir el cockpit definitivo; T3 en Als Sund; T4 | D-20; R13 §8 |
| H-6 | Pares de apriete no calculados salvo las M8 del pórtico (bridas M6, placa de espejo, M5, M3, KM4, prisioneros) | Cierre de los pasos M3–M13 | Este documento (R7) |
| H-7 | Ley anti-cavitación y detección de descarga no implementadas en el firmware (solo el tope de ERPM) | T2.5 a fondo, T4 | 02 §4.6 |
| H-8 | Decisión A (bomba propia) o B (JT132) sin cerrar | Encargos de E5 (servicios) y E6 | D-05; 03 §3 |
| H-9 | Contactor K1 de ≥ 250 A: modelo, tensión de bobina y tensión de cierre sin confirmar por escrito (la alimentación de la bobina se está redefiniendo en el README de electrónica) | T0.4 | README de electrónica §7, §11; BOM B-CONT |
| H-10 | Corriente de hasta 3 kn en Als Sund, contra 0,5 m/s de `inputs.yaml` | Operación en Als Sund (a 4 kn de límite, con 3 kn en contra casi no se avanza) | R13 §3 |
| H-11 | Luz de rejilla <!--V:manifest.params.toma_bar_gap:.1f-->16.3<!--/V--> mm: R10a §8.6 pedía que una varilla de Ø13 no pase (dedos), y la rejilla de 316 queda en contacto con el 5083 bajo el agua | T2 con gente cerca; aprobación de P1-INT-03 | R10a §0.1, §8.6; §4 |
| H-12 | Repuestos de pasadores: 3 según el plano P1-PMP-05 y estructural.json; 5 según el plano P1-DRV-01, el visor y R-PIN | Checklist (se llevan 5) | Planos, `bom.csv` |
| H-13 | Placa de espejo: 6 × M6 según P1-PMP-09 y el CAD; 7 agujeros según P1-PMP-10 y B-HW | Corte de la junta y taladrado del espejo (C3) | Docstrings P1-PMP-09/10; `bom.csv` |
| H-14 | Cambiar el pasador obliga a sacar tobera y estator desde adentro del casco (las bridas no pasan por el agujero del espejo): no se puede hacer en el agua | Operación lejos de la rampa: llevar pagaya y ancla | §3 |
| H-15 | La calibración real del corte del pasador sale de la probeta (05 §7) | T2.5 a fondo | D-11 |
