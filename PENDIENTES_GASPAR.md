# PENDIENTES_GASPAR — lo que hay que hacer en el mundo físico, en orden

Cada ítem tiene un **criterio de cierre**. No se pasa al bloque siguiente con uno abierto, salvo que se diga lo contrario. Después de cada medición: cargar el valor en `inputs.yaml` con la etiqueta `[VERIFICADO: medido AAAA-MM-DD]`, correr `python run_all.py` (incluye `verify_parts.py` y `docgen.py`) y mirar qué cambió en `resultados/sizing.json`. Bloqueos que esto destraba: 06 §8.

Valores de referencia del diseño actual [CALCULADO con el casco leído del plano]: masa total <!--V:sizing.masses.total_kg:.0f-->218<!--/V--> kg, calado <!--V:sizing.hydrostatics.draft_m:.3f-->0.286<!--/V--> m, GM <!--V:sizing.hydrostatics.GM_m:.3f-->0.009<!--/V--> m, V máx. sostenida <!--V:sizing.performance.vmax_cont_kmh:.1f-->24.4<!--/V--> km/h, costo total <!--V:bom.total_eur:.0f-->11847<!--/V--> €.

---

## P0 — Antes de comprar o cortar nada

### P0.1 Medir el casco y lo que lo rodea (con Jorge)

| # | Qué | Cómo | Se carga en | Criterio de cierre |
|---|---|---|---|---|
| P0.1.1 | **Casco**: eslora total, manga en la borda, manga y altura del pantoque, ancho del fondo, largo del fondo, puntal, astilla muerta en 3 estaciones (espejo, 0,5 m y 1,0 m), material y espesor de chapa, peso del casco | Cinta, nivel, escuadra, transportador o inclinómetro del celular; peso con 2 balanzas de baño (proa y popa); fotos con cinta en cuadro | `boat.loa_m`, `beam_m`, `lwl_m`, `bottom_beam_m`, `chine_beam_m`, `chine_height_m`, `gunwale_height_m`, `deadrise_deg`, `hull_mass_kg` | Todos los campos con etiqueta VERIFICADO y `run_all.py` en verde |
| P0.1.2 | **Fondo en la zona de la toma**, de 0 a 1,0 m del espejo: planitud, quilla, tracas, refuerzos o varengas existentes, remaches; **espesor real del fondo, con cualquier sobreplaca** | Regla de 1 m y galgas; calibre en un borde o medidor de espesor por ultrasonido | `boat.bottom_thickness_mm` | Zona plana y libre desde x = <!--V:manifest.params.toma_plate_x0:.0f-->286<!--/V--> hasta 0,5 m a proa de la tangencia (x = <!--V:manifest.params.x_tan:.0f-->766<!--/V--> mm) [VERIFICADO: R10a §8.2]. **Si el fondo mide más de 6 mm:** con el supuesto actual de <!--V:manifest.params.bottom_t:.0f-->4<!--/V--> mm la tobera fija y la carcasa quedan a pocos milímetros del fondo interior; subir `waterjet.axis_height_m` lo mismo que el exceso, correr `run_all.py` (`verify_parts.py` falla si no se sube) y confirmar que el eje siga bajo la flotación (`sizing.priming.axis_below_wl_m`, hoy <!--V:sizing.priming.axis_below_wl_m:.3f-->0.171<!--/V--> m) [auditoria.md W-16] |
| P0.1.3 | **Espejo**: alto, espesor, material, ángulo con la vertical; qué hay por dentro alrededor del centro del agujero | Cinta, calibre, inclinómetro; marcar en el espejo el centro previsto (crujía, z = <!--V:manifest.params.z_noz:.0f-->92<!--/V--> mm sobre la quilla) | `boat.transom_height_m`, `transom_thickness_mm` | Agujero de Ø<!--V:manifest.params.transom_hole_d:.1f-->166.0<!--/V--> mm y placa de espejo de radio <!--V:manifest.params.pmp_tp_R:.0f-->108<!--/V--> mm sin refuerzos ni soldaduras en el medio; `run_all.py` en verde |
| P0.1.4 | **Calado en popa con la masa de diseño** | En el muelle, agua calma; piloto + lastre hasta la masa total de diseño; calado en el espejo (crujía) y en proa; marcar la flotación con cinta | Comparar con `sizing.hydrostatics.draft_m`; ajustar `boat.block_coeff` hasta que coincida | Calado medido cargado. El eje del impulsor (a <!--V:sizing.priming.axis_height_m:.3f-->0.115<!--/V--> m de la quilla) queda ≥ 20 mm bajo la flotación medida [VERIFICADO: R10a §3.2, §8.1] |
| P0.1.5 | **Piso, consola y asiento** | Altura del piso sobre la quilla entre x = <!--V:manifest.params.mot_x0:.0f-->682<!--/V--> y <!--V:manifest.params.mot_x1:.0f-->797<!--/V--> mm (motor); posición, ancho y alto de la consola; altura del asiento y del CG del piloto sentado | `boat.floor_height_m`; `masses.items.pilot` (x, z); cotas de consola de `params_direccion.py` (CTL_*) | El motor no toca el piso (`verify_parts.py` en verde); la unidad de palancas y el T85 entran en la consola real |
| P0.1.6 | **Motor recibido** (después de P0.3) | Ø y largo del eje, chavetero, brida (diámetro de agujeros, cantidad y rosca), largo total; pares de polos con la detección de VESC Tool (motor solo, sin bomba) | `motor.options.MTI120116_150.shaft_d_mm`, `pole_pairs` y la tabla de motores de `params_tren.py` | `run_all.py` en verde: agujero del cubo del Rotex, soporte P1-MOT-02 y tope de ERPM de COSTA recalculados |
| P0.1.7 | **Baterías recibidas** | Medidas y peso de cada una | `masses.items.battery`; BOM B-BOX | La caja estanca elegida las contiene con sus cables; `run_all.py` en verde |

### P0.2 Estabilidad — bloquea todo lo demás

| # | Acción | Criterio de cierre |
|---|---|---|
| P0.2.1 | **Ensayo E1 de escora con carga desplazada** con el casco tal cual (sin cortar) y lastre hasta la masa de diseño (R13 §5; procedimiento en 06 T1.1): piloto de 100 kg o lastre equivalente con el CG ≥ 100 mm sobre el asiento, corrido 0,1 m, 0,2 m y hasta la borda | Sin entrada de agua, francobordo residual ≥ 100 mm y escora ≤ 15° con el piloto a 0,2 m de crujía [SUPUESTO: umbrales de R13 §5]. Video y fotos del inclinómetro archivados |
| P0.2.2 | Si E1 no pasa (lo esperable: el cálculo da <!--V:sizing.heel_pilot_0p1m_deg:.0f-->78<!--/V-->° con 0,1 m): decidir con Jorge el cambio de casco: manga en la flotación ≥ 0,9 m, flotadores laterales o asiento más bajo (D-04; R10b H1) | Cambio hecho o diseñado, cargado en `inputs.yaml`, GM recalculado positivo con margen y E1 repetido y aprobado |

### P0.3 Cotizaciones por escrito

| # | A quién | Qué preguntar | Criterio de cierre |
|---|---|---|---|
| P0.3.1 | **AWT, JT132** (wuxiawt01@163.com, R11 §4) | (1) Plano de la brida de toma y si entra en un fondo plano de las medidas de P0.1.2; (2) altura del eje sobre el fondo, para que quede ≥ 20 mm bajo la flotación en reposo; (3) curva H-Q o empuje del impulsor estándar a ~4000 rpm y 6 kW, y pasos de impulsor disponibles; (4) entrada del eje (cardán SWC 65 o acople ISO) y largo; (5) precio, flete a DK, arancel, plazo y repuestos (anillo de desgaste, impulsor) | Respuesta escrita con (1)–(4) y costo puesto en DK. Decisión A/B tomada y anotada en D-05: B si se cumplen las 4 condiciones de 03 §3 y el costo puesto no supera ~1500 € [SUPUESTO: D-05]; la estimación actual es <!--V:cmp.B_jt132_landed_eur_min:.0f-->1437<!--/V-->–<!--V:cmp.B_jt132_landed_eur_max:.0f-->1549<!--/V--> € [ESTIMADO] |
| P0.3.2 | **Maytech, MTI120116 150 KV** | Potencia continua con camisa de agua y el caudal de agua que necesita; curva de eficiencia o resistencia de fase; KV real; pares de polos; Ø y chavetero del eje y patrón de la brida; sensor de temperatura disponible; plazo | Potencia continua por escrito, cargada en `inputs.yaml → motor.options.MTI120116_150.p_cont_w` (hoy [ESTIMADO], D-12) y `run_all.py` corrido. Si da menos que lo estimado, revisar la V máx. (02 §10) antes de comprar |
| P0.3.3 | **Taller CNC** (solo si sale A) | Impulsor 316L en 5 ejes (`04_diseno/step/P1-PMP-03_impeller.step` + plano de ángulos `P1-PMP-03_tabla_angulos_alabes.svg`) y estator de Al 6061-T6 (`P1-PMP-06_stator.step`): material certificado (1.4404 para el impulsor), Ø exterior con sobremedida para tornear contra el anillo, balanceo G6.3, plazo; alternativa SLM 316L + torneado. Torneados de carcasa, tobera y placa de espejo (S-TURN-*) y anodizado duro (S-ANOD) | 2 cotizaciones por escrito por ítem, comparadas con `bom.csv` (S-CNC-IMP, S-CNC-STAT, S-TURN-*, S-ANOD) |
| P0.3.4 | **Soldadura de aluminio** | Conducto de la toma en 5083 sobre la placa base, con prueba de estanqueidad (aire 0,3 bar + jabón) (S-WELD-INT); pórtico, soporte del motor y bucket (S-WELD-AL); rejilla 316 (S-WELD-316); varengas al fondo del casco (H-WELD) | Cotización escrita que incluya la prueba de estanqueidad del conducto |
| P0.3.5 | **Contactor K1** (B-CONT) | TE KILOVAC **EV200AAANA** (500 A, 12–900 V CC, bobina 9–36 V con economizador; hoja EV200 VERIFICADA en el README de electrónica §4/§7), 149 € sin IVA en EV Europe (2026-10-02): confirmar stock y pedir | Pedido hecho; hoja de datos archivada en `referencias/` |

### P0.4 Consulta legal por escrito (antes de construir el cockpit)

| # | Acción | Criterio de cierre |
|---|---|---|
| P0.4.1 | Mandar las preguntas en danés de **R13 §8** (Q1–Q2 a Søfartsstyrelsen, Q4 a Sønderborg Kommune, Q5 a la policía, Q6 a Sønderborg Havn, Q7 a la aseguradora) con planos y fotos del cockpit. Q1 ya dice "katalog 18,8 kW maks., begrænset i controlleren til ca. 8,4 kW batterieffekt" (R13 §8, actualizado 2026-10-02); el diseño actual da <!--V:sizing.performance.P_shaft_peak_kW:.1f-->6.5<!--/V--> kW al eje como máximo [CALCULADO]. Q3 pregunta por 72 V: el pack es 12S, <!--V:sizing.performance.vmax_by_battery.v_max.V_bat:.1f-->43.8<!--/V--> V a carga plena (D-13), así que Q3 se reformula o se omite | Respuestas escritas archivadas en `referencias/`; D-20 actualizado. Si la respuesta es "vandscooter": se pierde Als Sund (R13 §1.3) y se replantea el proyecto antes de comprar |

---

## P1 — Probetas y ensayos de taller (05 §7)

Los procedimientos completos están en 05 §7; si algo de acá difiere, manda 05. Mínimo que tiene que estar aprobado antes del montaje (06 §3):

| # | Ensayo | Criterio de cierre |
|---|---|---|
| P1.1 | **Pasador de corte**: 3 pasadores del lote en un eje y un cubo de prueba de Ø20, palanca + dinamómetro hasta el corte | Corta entre 0,8 y 1,2 × <!--V:sizing.mech.shear_pin.T_cut_Nm:.1f-->33.5<!--/V--> N·m [SUPUESTO: tolerancia] y nunca por debajo de 1,5 × el par máximo del controlador (<!--V:sizing.mech.T_max_Nm:.1f-->18.6<!--/V--> N·m) [VERIFICADO como criterio: R12 §7.6]. Si no, cambiar el Ø en `inputs.yaml` (`shear_pin.d_options_mm`) |
| P1.2 | **Estanqueidad del conducto soldado** (taller, S-WELD-INT) | Aire 0,3 bar + agua jabonosa en todos los cordones: ninguna burbuja |
| P1.3 | **Prueba hidrostática de toma y bomba** armadas, con tapas ciegas | 0,3 MPa sin pérdidas ni deformación [ESTIMADO: R12 §7.2; presión de diseño <!--V:est.loads.structural_bomba.loads_used.p_design_Pa:.0f-->200000<!--/V--> Pa] |
| P1.4 | **Anillo de desgaste** prensado y torneado en la carcasa (taller) | Concentricidad ≤ <!--V:manifest.params.pmp_ring_TIR:.2f-->0.05<!--/V--> mm; con el impulsor, holgura de punta 0,3–0,4 mm con galgas [ESTIMADO: R12 §2.7] |
| P1.5 | **Impulsor** recibido | Balanceo G6.3 certificado por el taller; Ø de punta medido, coherente con P1.4 |
| P1.6 | **Piezas de PETG** (tapa de inspección, base y capota del controlador, caja de palancas, soporte del kill switch): probetas de 05 §7 | Criterios de 05 §7 |
| P1.7 | **Bujes POM-C en agua 48 h** (05 §7, ensayo P1.10): bujes del estator P1-PMP-07, de la placa de espejo P1-PMP-11 **y del bucket P1-REV-03 (×2)**, prensados en su alojamiento definitivo (los del bucket ya escariados a Ø20,1 después de prensar, 05 §4) | Criterios de 05 §7 para P1-PMP-07/11; P1-REV-03: Ø int a las 48 h ≥ Ø del muñón del espaciador P1-REV-02 medido + 0,05 mm [SUPUESTO: mismo criterio que P1-PMP-11] y el bucket gira a mano sin puntos duros. La tabla generada de 05 todavía no incluye P1-REV-03 (05 §10, hallazgo 9) |
| P1.8 | **Recepción de los resortes de los émbolos** (B-SPRING, ×2) | Largo libre, Ø ext y largo compacto con calibre: Ø ext ≤ 15 (entra libre en el Ø16 H8 del cuerpo) y compacto ≤ 17 mm. Fuerza con una balanza de cocina y un tope a 30 mm (instalado) y a 18 mm (perno afuera): ≈ 20 N y ≈ 45 N ± 20 % [SUPUESTO: tolerancia; valores ESTIMADOS de P1-REV-04]. Anotar los dos valores: con más de 45 N al final sube la fuerza del gatillo (≈ 82 N estimados, 06 T0.M6b) → avisar a DIRECCIÓN (`04_diseno/piezas/_release.py SPRING_F_MAX`) |
| P1.9 | **Recepción de émbolos, espaciadores y tornillería de la traba** (torneado propio o de taller) | Perno del émbolo Ø16 **h9** = 15,957–16,000 mm con micrómetro en 3 puntos [CALCULADO: ISO 286]; interior del cuerpo Ø16 H8 = 16,000–16,027 (el perno desliza sin juego visible y sin trabarse); la rosca **M24×1,5 del cuerpo entra a mano en la oreja** de la boquilla (antes y después del anodizado; repasar con B-TAP24 si no) y la contratuerca B-NUT24 entra en el cuerpo; espaciador P1-REV-02: muñón Ø20 h7 = 19,979–20,000 y piloto Ø16 h6 = 15,989–16,000 [CALCULADO: ISO 286], el piloto entra en el Ø16 H7 de la oreja; tornillos M12 × 60 marcados «A4-80» (B-PIVM12) |
| P1.10 | **Paso de las vainas del Bowden por el espejo** (B-GLINS en el prensaestopas M16 de Biltema, B-GLAND16) | El precio de B-GLINS está verificado, el **ajuste no**: el inserto es de 2 × 4,5 mm y la vaina del Bowden es Ø5 [ESTIMADO: B-BOWDEN]. Medir el Ø real de la vaina recibida y probar el inserto dentro del cuerpo del prensaestopas M16 de Biltema: las dos vainas entran y, con la tuerca apretada, no pasa agua con un vaso de agua apoyado afuera 10 min [SUPUESTO: prueba]. Si no entran o no sellan: inserto del Ø real (2 × 5) o un prensaestopas por vaina, y corregir B-GLINS en `inputs.yaml` |

---

## P2 — Banco y pruebas (06 §5)

| # | Etapa | Criterio de cierre |
|---|---|---|
| P2.1 | **T1.1 (E1)** con todo instalado (se repite P0.2.1) | Mismo criterio que P0.2.1 |
| P2.2 | **T0** banco en seco, acople desconectado: electrónica T0.0–T0.20 (T0.0: FW ≥ 6.00 en el VESC, sin él no hay LispBM ni perfil COSTA/ABIERTO) + mecánica T0.M1–T0.M8 | Todas pasan; kill por cordón y por seta < 1 s en 10/10 |
| P2.3 | **T1** estanqueidad, calado e inundado (T1.2–T1.6) | 24 h sin agua en la sentina; eje ≥ 20 mm bajo la flotación; E2–E4 aprobados |
| P2.4 | **T2** muelle, amarrado | Chorro en ≤ 3 s; testigo de refrigeración y sello correctos; empuje a punto fijo ≥ <!--V:sizing.success.bollard_min_N:.0f-->612<!--/V--> N; sin cavitación en la rampa |
| P2.5 | **T3** agua calma, < 300 m, 5 kn | Perfil COSTA ≤ 9,0 km/h de media; P de batería a 5 kn ≤ <!--V:sizing.success.p_legal_max_W:.0f-->2213<!--/V--> W; reversa y kill en marcha |
| P2.6 | **T4** fuera de 300 m (centro de Als Fjord) | Planeo en ≤ <!--V:sizing.success.t_plane_max_s:.0f-->15<!--/V--> s; V máx. GPS ≥ <!--V:sizing.success.vmax_min_kmh:.1f-->20.8<!--/V--> km/h; 30 min de crucero sin recorte térmico |
