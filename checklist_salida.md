# Checklist de salida — P1 cola larga eléctrica (Als Fjord / Sønderborg)

Fecha ______ · Patrón ______ · Acompañante ______ · Zona ______ · Ocaso ____ · Regreso ≤ ____ h · T agua ____ °C · Viento ____ m/s (ráfaga ____)

Una casilla sin marcar = **no se sale**. Fuentes: R07 = research/R07_dinamarca.md (los umbrales de §3.4 son criterios propuestos [SUPUESTO] sobre datos [VERIFICADO]); D-nn = decisiones.md; P0–P5 = PENDIENTES_GASPAR.md; elec = 04_diseno/electronica/README.md; 06 = 06_ensamblaje_y_pruebas.md; 07 = 07_roadmap_P2.md. Pronóstico: buscar: "DMI vejr Sønderborg".

**Una sola vez, antes de la primera salida:** T0, T1 y T2 aprobados [06]; H-1…H-3 de 06 resueltos. Con el diseño actual el FEA da FS 0,32 en la abrazadera MNT-01, 0,74 en la tapa MNT-06 y 0,86 en la mejilla MNT-04 (2,20 con p99), contra 3 → rediseño impreso o Al antes de T3 [04_diseno/fea; 07 §2.1].

## 1. Antes de salir (pronóstico y plan)
- [ ] Viento medio ≤ 6 m/s y ráfaga ≤ 10 m/s [R07 §3.4]
- [ ] Viento de tierra (W/SW en la costa E de Als y en Sønderborg Bugt): ≤ 5 m/s [R07 §3.4, §4.1]
- [ ] Ola Hs ≤ 0,3 m en la zona elegida [R07 §3.4]
- [ ] Solo de día; regreso ≥ 1 h antes del ocaso [R07 §1.3, §3.4]
- [ ] 15 jun–15 sep y agua ≥ 12 °C: sin traje térmico. Fuera de eso: traje seco/neopreno. Agua < 10 °C: no se sale [R07 §3.4; D-31]
- [ ] Alguien en tierra conoce zona, hora de regreso y teléfono; si no hay aviso 30 min después de esa hora, llama al 112 [R07 §1.4, §3.4; 30 min: SUPUESTO]
- [ ] Alcohol: 0,0 ‰ [R07 §1.2, política del proyecto]

## 2. Bote y carga
- [ ] Carga útil (personas + equipo + batería <!--V:sizing.battery.mass_kg:.0f-->22<!--/V--> kg + unidad <!--V:manifest.totals.unit_mass_kg_cad:.1f-->8.9<!--/V--> kg) ≤ placa de capacidad (____ kg); sin placa vale la estimada de <!--V:sizing.masses.capacity_kg:.0f-->160<!--/V--> kg → 1 adulto [P0.2; D-16]
- [ ] Francobordo en popa ≥ 150 mm con todos a bordo, medido en el muelle [P0.2]
- [ ] Batería fija en su caja estanca, tapa puesta, por encima del agua de sentina; bultos al centro/proa, bote nivelado [elec §9; R09 §1.4]
- [ ] Chalecos con cuello (CE/ratmærke, talla y peso correctos) **puestos y cerrados**, todos [R07 §1.2, §3.3]
- [ ] Remos o pagaya · ancla 3–5 kg + cabo ≥ 20 m (≥ 3 × profundidad) · achicador [R07 §1.4; D-35; bom B-ANCHOR]
- [ ] Luz blanca todo horizonte · silbato · teléfono cargado en bolsa estanca · manta térmica [R07 §1.4]

## 3. Unidad mecánica
- [ ] Abrazadera re-apretada a ≤ 2,5 N·m con llave dinamométrica sobre cabeza hexagonal (con mango en T el par no se mide; la llave no está en la BOM) [inputs `mount.clamp_screw_torque_nm`; D-13]
- [ ] La C no se abrió: apertura al pie de la pata = valor anotado en T0.M6 ± 0,5 mm; marcas de pintura de los tornillos alineadas [06 T0.M6, T2.7]
- [ ] Cabo de seguridad unidad → bote: cáncamo firme, mosquetón cerrado [D-13]
- [ ] Pasador de corte 316 Ø<!--V:sizing.mech.shear_pin.d_std_mm:.1f-->2.0<!--/V-->: con la polea sujeta, la hélice no tiene juego angular. Cambiarlo tras cualquier golpe o cada 10 h de motor; 2 de repuesto + herramienta a bordo [D-11; R09 §5.3; 06 PU.4; 10 h: SUPUESTO]
- [ ] Retén de basculación encastra con clic; la cola bascula a mano con 60–130 N en el patín [P5.1; D-10]
- [ ] PETG (abrazadera, cuna, tapa, mejillas, carcasa inferior, patín, 6 segmentos del protector, placa antiventilación) sin fisuras, blanqueo ni deformación; la hélice gira a mano sin rozar el aro [06 PU.3; D-12]
- [ ] Correa con dientes sanos, flecha ≈ 3 mm con 10 N en el centro del ramal; cubrecorrea puesto [P5.3]
- [ ] Tuerca de hélice apretada y trabada; palas sin mellas [D-06]

## 4. Eléctrico
- [ ] Conectores (Anderson, J1, J2) secos y con grasa dieléctrica; caja ESC cerrada con todos sus tornillos [elec §9]
- [ ] Batería ≥ 80 %: carga completa (cargador de 29,2 V terminado) en las últimas 48 h [SUPUESTO: P1 no tiene medidor de SoC]
- [ ] Encendido: desconectador ON con el cordón **afuera** (LED destella cada 2 s) → esperar ≥ 2 s → poner el cordón: se oye el clic de K1. Sin clic: no salir (K1 soldado o sin bobina) [elec §5.7, §7, §8]
- [ ] Cordón atado al chaleco del timonel (nunca al bote) [R07 §1.4; D-22]
- [ ] Arranque solo con acelerador en cero: con el puño abierto no arranca (LED a 4 Hz); 1 s en cero → arma (LED fijo) [elec §5.7, T0.7]
- [ ] Prueba de corte en el muelle con el motor al mínimo: tirar del cordón → para y se oye K1 en < 1 s; repetir con la seta [elec §10; 02 §11]
- [ ] Modo costa: `l_max_erpm` = <!--V:sizing.legal_speed.erpm_cap:.0f-->3700<!--/V--> ERPM en VESC Tool; si muestra otro valor (p. ej. el de elec §6), cargar este [02 §3.1; D-30]

## 5. En el agua
- [ ] Siempre a < 300 m de la costa danesa [R07 §1.2]
- [ ] Velocidad ≤ 5 kn = <!--V:sizing.legal_speed.limit_kmh:.2f-->9.26<!--/V--> km/h por GPS; lejos de bañistas [R07 §1.2]
- [ ] En aguas de < 1 m: ≤ 6 km/h (efecto de fondo y riesgo de varada) [R09 §1.8]
- [ ] Media vuelta a los 60 min de crucero; a los 45 min si la vuelta es contra el viento [SUPUESTO: misión 2 h + reserva 20–30 %, R07 hallazgos]
- [ ] Golpe o vibración nueva: acelerador a cero, cordón afuera, revisar pasador y correa antes de seguir [D-11]
- [ ] Viento > 6 m/s (borregos en casi toda la superficie) u ola que rompe: a la costa más cercana, sin cruzar [R07 §3.4; borregos: ESTIMADO, escala Beaufort]

## 6. Al volver
- [ ] Cordón afuera, desconectador OFF, llave retirada [06 PU.5]
- [ ] Enjuague con agua dulce girando el eje a mano: cola, hélice, protector, abrazadera y conectores con sus tapas puestas; sin arena en bujes ni en el aro [06 PU.1; R03 §5; elec §9]
- [ ] Caja ESC seca por fuera; cada 5 salidas o tras ola/lluvia fuerte, abrirla: 0 gotas adentro; si entró agua: secar y repetir T1 antes de volver a salir [06 T4.4; 5 salidas: SUPUESTO]
- [ ] Cargar la batería en interior: el BMS no carga por debajo de 5 °C [bom.csv B-CHG; 06 PU.5]
- [ ] Registro: horas de motor (sumarlas al pasador), Wh recargados (medidor de enchufe: buscar: "energimåler stikkontakt"), T agua, viento, incidentes [06 PU.6; medidor: SUPUESTO]
- [ ] Mensual y tras cualquier inmersión del motor: con el desconectador OFF, BAT−, B+ y fases contra casco y tubo de cola > 1 MΩ (multímetro); picaduras en tubo y herrajes [elec T0.1; R03 hallazgos; D-36]
