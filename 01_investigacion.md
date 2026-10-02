# 01 — Investigación: waterjet eléctrico inboard para el jet boat de Jorge

Resumen de lo que se aprendió, con la fuente de cada dato. El detalle y los links están en `research/`:
[R10a](research/R10a_toma_waterjet.md) (toma), [R10b](research/R10b_auditoria_plano_jorge.md) (auditoría del
plano), [R11](research/R11_componentes_jet.md) (componentes y precios), [R12](research/R12_metodos_waterjet.md)
(métodos de bomba, planeo y cargas), [R13](research/R13_legal_jet.md) (normativa), y de la etapa anterior
[R03](research/R03_proyectos_jet_ducted_efoil.md) (jets impresos), [R05](research/R05_materiales_sellado.md)
(PETG y sellado), [R06](research/R06_electrica.md) (eléctrica y seguridad) y [R07](research/R07_dinamarca.md)
(Dinamarca, agua y viento).

Etiquetas: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO]. Los números que salen del
código de este proyecto van entre marcadores `<!--V:…-->` y los actualiza `docgen.py`; los de la
investigación se citan con su informe.

## 0. Resumen ejecutivo

1. **El plano de Jorge es un croquis conceptual, no un plano fabricable.** Las vistas no comparten escala
   (dispersión del 26 %), la toma está detrás del impulsor, el corte no tiene conducto de admisión, falta el
   sello y la boquilla queda dentro de la carcasa [CALCULADO: R10b §2, §4.1]. Se rehízo el diseño entero; del
   plano quedan los requisitos (1 piloto, ≥ 30 km/h, motor directo, toma enrasada, boquilla y reversa).
2. **Jorge tenía razón con la rejilla.** El agua tiene que entrar a proa del impulsor y subir por una rampa
   hasta su cara. En el plano la rejilla estaba 22–25 cm a popa de la cara del impulsor, del lado de descarga,
   y el eje quedaba sobre la flotación: la bomba no cebaba [CALCULADO: R10a §1–§3].
3. **La estabilidad del casco es el riesgo n.º 1.** Con 0,80 m de manga y el piloto sentado alto, el GM sale
   entre −113 y +90 mm según la posición del piloto [CALCULADO: R10b H1]; con el modelo de este proyecto,
   GM = <!--V:sizing.hydrostatics.GM_m:.3f-->0.009<!--/V--> m. La propulsión no lo resuelve (D-04).
4. **La masa realista es 165–242 kg, no 150** [ESTIMADO: R10b §4.2]. Con más de ~200 kg, 5 kW continuos no alcanzan para 30 km/h
   sostenidos [CALCULADO: R10b H13–H14]. Este diseño llega a <!--V:sizing.performance.vmax_cont_kmh:.1f-->24.4<!--/V--> km/h
   sostenidos y <!--V:sizing.performance.vmax_peak_kmh:.1f-->28.3<!--/V--> km/h por ratos (02 §5).
5. **Motor y tensión.** El HPM5000 de catálogo gira muy lento para un impulsor chico (≈ 91 rpm/V a 48 V); el
   Maytech MTI120116 150 KV refrigerado por agua sí sirve en ≤ 50 V [VERIFICADO: R11 §0, §1]. No hay packs
   LFP 13S comerciales en la UE: la opción ≤ 50 V es 12S (2 × LiTime 36 V 60 Ah) [VERIFICADO: R11 §3].
6. **Comprar la bomba es una opción seria.** La AWT JT132 (Ø130, 12 kg, dirección y reversa incluidas) cuesta
   ≈ 1000–1100 USD FOB [ESTIMADO: buscador, R11 §4] y resuelve las piezas más difíciles de fabricar.
7. **Legal.** Probablemente no es "vandscooter" si el piloto va sentado *dentro* del casco; no es speedbåd
   por debajo de 19 kW; los 30 km/h solo son legales a más de 300 m de la costa, en el centro de Als Fjord, y
   nunca en Als Sund (4 kn) [VERIFICADO: R13 §0]. Confirmar por escrito (R13 §8).

## 1. El plano de Jorge y sus problemas (R10b)

Objeto: `referencias/2026-09-26_plano_preliminar_waterjet_jorge.png`, "PLANO PRELIMINAR – WATERJET PARA JET
BOAT 2.30 m", 1:10, rotulado "NO USAR COMO PLANO FINAL DE MECANIZADO". Datos del plano: casco 2,30 × 0,80 m,
puntal 0,52 m, espejo 0,42 m; 1 piloto; 5 kW nominales / 7,2 kW máx.; 72 V, 60/100 A; 4500 rpm directo a un
impulsor axial Ø108 de 4 álabes + estator; tobera Ø72; eje Ø20 inox; toma con rejilla de 120 × 90 mm; 150 kg
totales; ≥ 30 km/h [VERIFICADO: lectura del plano, R10b §2].

| N.º | Hallazgo (R10b §3) | Sev. | Cómo lo resuelve este diseño |
|---|---|---|---|
| H1 | Estabilidad inicial nula o negativa: puede volcar quieto | Crítica | **No resuelto por la propulsión.** GM = <!--V:sizing.hydrostatics.GM_m:.3f-->0.009<!--/V--> m [CALCULADO]. Bloquea la navegación hasta pasar el ensayo de escora E1 (R13 §5); casco más ancho o flotadores (03 §5, 07) |
| H2 | Eje del jet sobre la flotación: no ceba | Crítica | Eje en el impulsor a <!--V:manifest.params.h_axis:.0f-->115<!--/V--> mm de la quilla, <!--V:sizing.priming.axis_below_wl_m:.3f-->0.171<!--/V--> m bajo la flotación [CALCULADO] |
| H3 | El corte A-A no es una bomba: sin conducto, expansión brusca tras la tobera, boquilla dentro de la carcasa | Crítica | Toma enrasada → conducto de Al 5083 → impulsor → estator → tobera → boquilla **por fuera** del espejo → bucket (P1-INT, P1-PMP, P1-STE, P1-REV) |
| H4 | Falta el sello; "rodamientos fuera de la cámara húmeda" contradictorio | Crítica | Sello mecánico SiC/carbón tipo MG1 en el techo de la rampa, cámara de goteo con testigo, rodamientos en seco (P1-DRV-02, -07; D-14) |
| H5 | Baterías en la sentina, sin flotación | Alta | Caja estanca de batería, ~100 L de espuma de flotación, bomba de achique con alarma (BOM B-BOX, B-FOAM, B-BILGE, B-ALARM) |
| H6 | Capacidad menor que un adulto; 1 persona como máximo | Alta | Diseño para 1 piloto. La capacidad por 33 CFR 183.33 da <!--V:sizing.capacity.persons_gear_kg:.0f-->46<!--/V--> kg [CALCULADO]: queda como riesgo del casco (02 §2.3) |
| H7 | No es el bote de diseño del P1 anterior | Alta | Resuelto: este proyecto es para el casco de Jorge (D-01, D-02); hay que medirlo (PENDIENTES P0.1) |
| H8 | 72 V supera la tensión de seguridad de 50 V CC | Alta | 12S LFP, 43,8 V con la batería llena (D-13). 72 V solo con `allow_72v` y clase 100 V + monitor de aislamiento |
| H9 | Sin kill switch ni parada de emergencia | Alta | Cordón NC en serie con la bobina de un contactor monoestable + seta (R06 §3.5; D-18) |
| H10 | Reversa "opcional": el jet no frena ni gobierna sin chorro | Alta | Bucket obligatorio con émbolo de traba, reversa limitada al 50 %, enclavamiento de palancas (D-17) |
| H11 | Toma en el fondo contra aguas someras y arena | Alta | Rejilla de barras longitudinales, anillo de desgaste 316 reemplazable, tapa de inspección sobre la flotación, pasador de corte; regla de operación: ralentí en < 0,5 m de agua |
| H12 | ≥ 30 km/h es ilegal a < 300 m de la costa | Alta | Perfil "costa" por defecto con tope de ERPM (02 §3.1); planeo solo a > 300 m (D-18, R13 §3) |
| H13 | Masa de 150 kg irreal | Alta | Masa de diseño <!--V:sizing.masses.total_kg:.0f-->218<!--/V--> kg con la unidad de jet del CAD (02 §1; D-03) |
| H14 | Con 5 kW no llega a 30 km/h con masa realista | Alta | Motor de 6 kW continuos estimados y bomba optimizada; aun así no llega (02 §4.3). Se informa la V real y qué la mejora (07) |
| H15 | Holgura de punta de 0,5–0,8 mm no se logra en PETG | Alta | Impulsor de 316 mecanizado, anillo de desgaste de 316 torneado en sitio, holgura <!--V:sizing.pump.tip_clearance_mm:.2f-->0.40<!--/V--> mm (D-10, D-11) |
| H16 | Camino del empuje axial sin definir; motor abulonado sin acople | Media | Par 7204 BEP en un pórtico sobre la placa base toma todo el empuje; acople Rotex 24 con juego axial (D-14) |
| H17 | Motor sin tipo, refrigeración ni control definidos | Media | Maytech MTI120116 con camisa de agua + VESC Flipsky 75350 con caja de agua; refrigeración desde la bomba (D-12, D-15) |
| H18 | 60 A × 72 V ≠ 5 kW; corriente que no cierra | Baja | Potencia especificada a una tensión y limitada por corriente de batería (02 §4.2, §6) |
| H19 | LCG muy a proa (66 % del largo de fondo) | Media | Batería más a popa (x = 1,0 m); LCG = <!--V:sizing.masses.lcg_m:.2f-->1.11<!--/V--> m del espejo [CALCULADO]. Sigue a proa del 35–45 % recomendado [ESTIMADO: R10b H19] |
| H20 | Margen de cavitación chico a punto fijo y en la joroba | Media | Límite S ≤ 3,5 en el optimizador y ley de control a baja velocidad (02 §4.5–4.6) |
| H21 | Par galvánico Al–316 (≈ 670 mV) | Media | Tef-Gel, arandelas aislantes, ánodo de aluminio (R06 §6; BOM B-TEFGEL, B-ISOW, B-ANODE) |
| H22 | Riesgo de clasificación como "vandscooter" | Media | Cockpit "dentro" del casco con volante y palanca (R13 §1.4); pedir decisión escrita (D-20) |
| H23 | Cotas incoherentes, no es un plano a escala | Media | Todo rehecho en CAD paramétrico con una sola referencia (espejo y quilla), `04_diseno/` |
| H24 | Marcas de corte y cotas mal ubicadas | Baja | Ídem H23; planos de taller en `04_diseno/planos/` |
| H25 | Tabla de materiales ilegible | Baja | Materiales definidos por pieza en el manifest y la BOM; pedir a Jorge el original para comparar |

Veredicto de R10b: el plano describe otro producto que el P1 anterior (jet inboard, 1 piloto, ≥ 30 km/h,
72 V, casco propio) y no se puede fabricar tal cual. Este paquete lo toma como especificación de requisitos.

## 2. La toma: por qué la rejilla estaba mal y la regla correcta (R10a)

**Mecanismo** [VERIFICADO: R10a §3]:
- La bomba aspira por la cara de proa del impulsor. Aguas abajo (estator, tobera) el agua ya está a presión.
  Una abertura debajo de la tobera queda del lado de **descarga**: no puede aspirar.
- El plano no dibuja ningún conducto entre la rejilla y la bomba.
- **Cebado:** HamiltonJet pide la flotación "at least up to the underside of the Mainshaft (at the Impeller)"
  con el bote quieto [VERIFICADO: R10a S4 p.38]. En el plano el eje quedaba 65–85 mm sobre la flotación
  nominal [CALCULADO: R10a §3.2].
- **Tamaño:** un conducto de Ø120 que corta el fondo a 27° deja una huella de 264 mm; la abertura de 90 mm del
  plano no lo admite. En la rejilla del plano el agua pasaba a 5,2 m/s a punto fijo [CALCULADO: R10a §3.3].
- **Rejilla no enrasada:** HamiltonJet pide escalones ≤ 2 mm y nada que obstruya delante de la toma
  [VERIFICADO: R10a S6 p.43].

**Regla de diseño** [VERIFICADO / ESTIMADO: R10a §4]:
- Abertura entera **a proa** del impulsor; techo ("rampa") tangente al fondo en proa y alineado con el eje en
  la garganta; labio redondeado aguas abajo de la abertura (toma de referencia ITTC 23rd).
- Rampa de 25–30° (convencionales < ~30°; caso típico 25°); eje inclinado 5° hacia proa (bloque estándar
  de Hamilton).
- Abertura de ~2,5–2,9 D de largo × ~1,2 D de ancho; fondo liso y sin apéndices delante (≥ 5–10 D).
- Eje del impulsor ≥ 20 mm bajo la flotación en reposo.
- Rejilla de barras longitudinales, perfiladas, enrasadas, que cubre toda la abertura.
- IVR: separación en el techo con IVR < ~0,65 (alta velocidad); con IVR alto (baja velocidad, 5 kn) el
  estancamiento pasa al lado casco del labio → labio generoso.

**Aplicado en este diseño** [CALCULADO: CAD, `manifest.json`]: cara del impulsor a
<!--V:manifest.params.x_if:.0f-->268<!--/V--> mm del espejo; labio a <!--V:manifest.params.x_lip:.0f-->386<!--/V--> mm;
tangencia de la rampa a <!--V:manifest.params.x_tan:.0f-->766<!--/V--> mm; abertura
<!--V:manifest.params.L_open:.0f-->380<!--/V--> × <!--V:manifest.params.W_open:.0f-->158<!--/V--> mm; rampa de
<!--V:manifest.params.ramp:.0f-->27<!--/V-->°; rejilla de <!--V:manifest.params.grille_bars:d-->9<!--/V--> pletinas 316 con luz de
<!--V:manifest.params.toma_bar_gap:.1f-->12.2<!--/V--> mm. El conducto es de Al 5083 soldado, no de PETG (D-09).

## 3. Métodos de bomba, planeo y cargas (R12)

| Tema | Lo que se aprendió | Fuente | Dónde se usa |
|---|---|---|---|
| Tipo de bomba | Con ~5 kW a ~4000–5000 rpm el punto de diseño es un axial de Ω_s alta (≈ 5); η máx. esperable ≈ 0,76 (correlación de Bulten), 0,65–0,75 con holgura y rugosidad reales | [CALCULADO con VERIFICADO: R12 §0, T1 ec. 2.26] | `waterjet.pump.eta_design` = 0,72 |
| Relación de cubo | Con ν = 0,40 y torbellino libre el cubo se sobrecarga (D_f 0,60, w₂/w₁ 0,62); con 0,50 cierra | [CALCULADO: R12 §2.3] | D-06 |
| Álabes | 5 álabes de impulsor y 7 de estator (coprimos) | [CALCULADO: R12 §2.4, §3.1] | CAD de P1-PMP-03/06 |
| Holgura de punta | 0,3–0,4 mm con anillo de desgaste torneado en sitio | [CALCULADO / ESTIMADO: R12 §2.7] | D-10 |
| Cavitación | Límite de diseño S ≈ 3,5 (comercial ≈ 4,0); a punto fijo la potencia admisible baja; ley de control: limitar rpm o potencia a baja velocidad | [VERIFICADO: R12 §5, Bulten T1] | 02 §4.5–4.6 |
| Rejilla | Pérdida de Kirschmer chica (11–46 mm de columna); lo que importa es **dónde** va | [CALCULADO: R12 §4.3–4.4] | `waterjet.grille_k` |
| Planeo | Savitsky 1964 con `openplaning` (API verificada en el código instalado) | [VERIFICADO: R12 §6.1] | `p1calc/planing.py` |
| Joroba y 5 kn | Mercier–Savitsky 1973: R/Δ ≈ 0,12–0,17 en la joroba y 0,04–0,10 a 5 kn según el casco; coeficientes de una transcripción secundaria | [VERIFICADO rangos: R12 §6.3] | Banda de joroba de 02 §3 (no implementado como regresión, 02 §12) |
| Cargas | Empuje axial al rodamiento fijo; presión de diseño 0,2 MPa (≈ 1,3 × la de cierre); boquilla 2J·sin(δ/2); bucket J·(1 + k_r), reversa hasta 60 % del avance | [CALCULADO / VERIFICADO: R12 §7] | 02 §8 |
| Piedras | ~490 J en el rotor; trabado en 10–90° da 300–2800 N·m: el límite de corriente no protege → fusible mecánico de ~25–45 N·m | [CALCULADO: R12 §7.6] | Pasador de corte, D-11 |

## 4. Componentes y precios (R11)

Precios al 2026-10-01. Las tiendas chinas no incluyen el 25 % de IVA de importación ni el envío.

| Partida | Elegido (≤ 50 V) | Precio | Masa | Etiqueta |
|---|---|---|---|---|
| Motor | Maytech MTI120116 150 KV, refrigerado por agua, eje Ø15 con chavetero, 10–16S, 120 °C máx. | 537,50 USD = 473 € sin IVA | 4,4 kg | [VERIFICADO: R11 §1.2]; potencia continua no publicada [ESTIMADO] |
| Motor (descartado) | Golden Motor HPM5000B 48 V: ≈ 91 rpm/V de ensayo → el Ø108 se queda en ≈ 3400–3850 rpm y absorbe 2,2–3,1 kW | 490 USD | 11 kg | [VERIFICADO: R11 §1.2–1.3] |
| Controlador | Flipsky FSESC 75350 con caja de agua (VESC, filtro de fase, IP65), 350 A | 210 USD = 185 € | 2,0 kg | [VERIFICADO: R11 §2.1] |
| Batería | 2 × LiTime 36 V 60 Ah en paralelo (12S, 43,8 V máx., 4,6 kWh, BMS 2 × 120 A) | 939,98 € con IVA | ≈ 40 kg | Precio [VERIFICADO: R11 §3.2]; masa [ESTIMADO] |
| Bomba completa ("comprar") | AWT JT132 (Ø130 / tobera Ø70, dirección y reversa incluidas) | ≈ 1000–1100 USD FOB | 12 kg | Specs [VERIFICADO: R11 §4]; precio [ESTIMADO] |
| Sello | ST-MG1 Ø20 (pedir carbón/SiC), 10 m/s, 12 bar | desde 29 € | < 0,1 kg | [VERIFICADO: R11 §5] |
| Rodamientos | Par SKF 7204 BEP | 2 × 31,40 € | — | [VERIFICADO: R11 §5] |
| Acople | KTR Rotex 24 (estrella 92 ShA: 35 N·m; 98 ShA: 60 N·m) | 67,47 € | ≈ 0,6 kg | [VERIFICADO: R11 §5] |
| Eje | 1.4404 Ø20 h9 | 32,87 €/m | 2,47 kg/m | [VERIFICADO: R11 §5] |
| Impulsor ("construir") | SLM 316L + torneado, o CNC 5 ejes | ≈ 330–610 € (SLM) | 0,8–1,3 kg | [ESTIMADO: R11 §6] |
| Dirección y bucket | Ultraflex T85 + M66 + volante Ø320; Mach5 10 ft | 273 € + 74 € | ≈ 4 kg | [VERIFICADO: R11 §7] |
| Achique + alarma / flotación | Attwood Sahara S500 + KUS / PU 2 componentes 100 L | 125 € / ≈ 45 € | — | [VERIFICADO: R11 §8] |

Advertencias de R11 §10 que cambian decisiones: los "48 V" LFP de catálogo son 15–16S (54,8–58,4 V), por
encima de 50 V; el MTI120116 no declara sensor de temperatura (se agrega un NTC); los rodamientos "inox"
AISI 420 se corroen en agua salada y van del lado seco; la JT132 exige confirmar su toma y la altura de su eje
**antes** de comprarla.

Costo total del paquete actual (BOM): <!--V:bom.total_eur:.0f-->11847<!--/V--> €, de los cuales
<!--V:bom.services_eur:.0f-->4040<!--/V--> € son servicios de fabricación (CNC, torneado de taller, soldadura) [CALCULADO:
`bom.py`; ver 03 §3 y 05].

## 5. Jets comerciales y jet boats eléctricos de referencia

| Referencia | Qué es | Datos | Qué aporta | Fuente |
|---|---|---|---|---|
| **AWT JT132** | Waterjet comercial chino | Impulsor inox Ø130, tobera Ø70, 12 kg neto, 1,5–40 kW, 2000–6000 rpm, dirección + reversa (deflector de doble ducto), entrada por cardán SWC65 o acople ISO; "3 m / 0,5 t" por unidad | Es la bomba de la foto de Jorge; opción B de la matriz (03) | [VERIFICADO: R11 §4, https://www.wuxiawt.com/JT132-pd574514898.html] |
| **Lampuga Air** | Jetboard eléctrico | 2,30 × 0,75 m; motor refrigerado por agua "up to 10 kW"; 50,4 V; 3,6 kWh; hasta 50 km/h; ~55 kg de equipo | Mismo tamaño en planta que el casco de Jorge, a ~74 W/kg y con un casco mucho más liviano | [VERIFICADO: R12 §8 (T12)] |
| **Maytech MTWJ12KW** | Motor + bomba Ø95 | 13,2 kW máx. a 80 V, 130 KV, 36–80 V; 1015,90 USD | Unidad integrada de jetboard; Ø95 es chico para 200 kg | [VERIFICADO: R11 §4] |
| **Sea-Doo Spark** (bomba de 140 mm) | Repuestos de moto de agua | Impulsor Solas 140 = 335 €; anillo inox 202 €; bomba OEM armada 999 USD (EE. UU.) | Opción C: bomba usada adaptada | [VERIFICADO: R11 §4] |
| Mokai ES-Kape | Kayak con jet a nafta | 3,4 m, 75 kg, 7 hp, 32 km/h | 30 km/h con ~32 W/kg, pero con casco mucho más esbelto | [VERIFICADO: R12 §8 (T14)] |
| Jets impresos (J1–J4, PRO-JET) | Proyectos DIY de 80–85 mm | 4 kgf a 270 W; 11,5 km/h a 1,1 kW en SUP; el rotor impreso tocó el estator y hubo que llevar el gap a 3 mm | Por qué la bomba de 5–10 kW no se imprime | [VERIFICADO: R03 §1, §2.4] |

Lectura [CALCULADO / ESTIMADO: R12 §8]: este bote tiene ~25–36 W/kg y L/∇^⅓ ≈ 3,5–4. Con eso, 30 km/h es
"posible pero marginal"; Lampuga llega a 40–50 km/h con el doble de potencia por kilo.

## 6. Normativa (R13, R07)

| Tema | Conclusión | Etiqueta |
|---|---|---|
| Vandscooter (BEK 809/2019, vigente) | Definición: < 4 m, waterjet como propulsión principal, operado por personas que van "på – snarere end i – skroget". Con el piloto sentado **dentro** de un cockpit, con volante y respaldo, probablemente **no** lo es; la guía de la RCD dice que los "mini jet boats" < 4 m no son PWC. Ser eléctrico no lo excluye | [VERIFICADO: R13 §1] |
| Si se lo clasificara como vandscooter | Prohibido a < 300 m de la costa salvo tránsito perpendicular a ≤ 5 kn (Als Sund queda inutilizable), prohibido en Natura 2000; vandscooterbevis, seguro obligatorio, 0,5 ‰ | [VERIFICADO: R13 §1.3] |
| Diseño para no serlo | Asiento bajo la borda con ≥ 250 mm de costado, pies en el piso del cockpit, volante y palanca, respaldo; pedir decisión escrita a Søfartsstyrelsen y a Sønderborg Kommune | [SUPUESTO: R13 §1.4] |
| Speedbåd (BEK 749/2020) | < 4 m planeante: bevis desde 19 kW de "fremdrivningseffekt"; la norma no dice cómo se mide en eléctricos → contar el pico que deja pasar el controlador | [VERIFICADO + ESTIMADO: R13 §2] |
| Velocidad, < 300 m de la costa | 5 kn (9,26 km/h) | [VERIFICADO: R07 §1.2] |
| Velocidad, Als Sund (Sønderborg Havn) | 4 kn en todo el sund entre el sur del castillo y Alssundbroen; puente Christian X: velocidad mínima de maniobra a 250 m de cada lado; corriente de hasta 3 kn | [VERIFICADO: R13 §3, Den Danske Havnelods] |
| Velocidad, marinas | Sønderborg Lystbådehavn, Augustenborg Yachthavn, Egernsund: 3 kn; Augustenborg Havn: 4 kn | [VERIFICADO: R13 §3] |
| Dónde se puede ir a 30 km/h | Solo en la franja central de Als Fjord (> 300 m de cada orilla) y en la parte danesa ancha de Flensborg Fjord / Sønderborg Bugt; nunca en Als Sund ni en Augustenborg Fjord | [ESTIMADO: R13 §3] |
| 72 V | Sin obligación legal a bordo de un bote propio < 2,5 m; ISO 16315 (voluntaria) pide precauciones contra choque eléctrico por encima de 50 V → IP67, bus flotante con monitor de aislamiento, clase 100 V | [VERIFICADO: R13 §4] |
| Estabilidad y flotación | Sin norma obligatoria (fuera de la RCD); referencia ISO 12217-3 y 33 CFR 183.105/.225/.230; ensayos E1–E4 antes de navegar | [VERIFICADO: R13 §5] |
| Kill switch | No obligatorio para este bote; se instala igual, cortando la propulsión | [VERIFICADO: R13 §6] |

Las preguntas a las autoridades, ya redactadas en danés, están en R13 §8.

## 7. Materiales y sellado (R05)

- **PETG** absorbe poca agua (~0,3 %) pero pierde 17–28 % de tracción a 30 días en agua de mar; entre capas
  vale 38–84 % de XY; a fatiga rompe en ~10⁵ ciclos al 30 % de la UTS (extrapolado: 4–8 % a 10⁷–10⁸)
  [VERIFICADO: R05 §1, S13, S16]. HDT 68–75 °C: nada impreso cerca del motor ni del controlador.
  Consecuencia: **la bomba de un jet de 5–10 kW no se imprime** (presión cíclica, holgura de punta, paso de
  pala); el PETG queda para piezas secas o de baja carga (D-19).
- **Uniones:** tuerca A4 cautiva mejor que inserto de latón (descincificación); nada de Loctite 243 sobre
  termoplásticos [VERIFICADO: R05 §A10].
- **Sellos estáticos:** O-ring de 3,53 mm en sello de cara, con 20–30 % de compresión y 60–85 % de llenado,
  sobre cara refrentada (la superficie impresa tiene Ra 2–24 µm contra ≤ 0,8–1,6 µm pedido)
  [VERIFICADO: R05 §B2–B4].
- **Sello de eje:** el waterjet sí necesita un sello dinámico (a diferencia de la cola larga): sello
  mecánico de caras, que tolera arranques cortos en seco si es carbón/SiC [VERIFICADO: R11 §5; R05 §B6].
- **Galvánica:** 316 pasivo contra Al ≈ 670 mV (límite práctico 200 mV): aislar y ánodo de aluminio
  [VERIFICADO: R06 §0, §6].

## 8. Eléctrica y seguridad (R06)

- LFP por seguridad térmica; 12S (38,4 V nominal, 43,8 V llena) en vez de "48 V" de 16S, que supera 50 V,
  el MRBF (58 V) y el contactor SW80 estándar [VERIFICADO: R06 §0, §4.3]. El contactor elegido es el TE KILOVAC
  EV200AAANA con la bobina a 12 V desde el DC-DC (el cordón Watski de 12 V trabaja dentro de su valor nominal;
  04_diseno/electronica/README §1).
- Kill switch: cordón en serie con la bobina de un contactor monoestable; el antichispa MOSFET no es un
  elemento de seguridad [VERIFICADO: R06 §0, §3].
- VESC: los valores por defecto no sirven para un bote (corte de batería, rango ADC); configurar todo
  [VERIFICADO: R06 §2].
- Batería en lugar seco y ventilado, sobre el nivel de la sentina (ISO 13297 8.1); la LFP inmersa en agua
  salada puede entrar en runaway días después [VERIFICADO: R06 §4.2, §5.1].

## 9. Agua y viento en Als (R07)

| Tema | Dato | Etiqueta |
|---|---|---|
| Salinidad | 13,6–17,5 PSU de media mensual; densidad de cálculo 1013 kg/m³ | [VERIFICADO: R07 §2] |
| Temperatura del agua | < 15 °C en ≥ 90 % de los días de octubre a mayo; ≥ 12 °C casi siempre de junio a septiembre; máx. 23–26 °C | [VERIFICADO: R07 §3.1] |
| Agua fría | Choque por frío bajo ~15 °C; incapacitación en 2–30 min cerca de 0 °C | [VERIFICADO: R07 §3.3] |
| Viento (may–sep, día) | ≤ 6 m/s el 57–79 % de las horas; el viento fuerte es del SW/W | [VERIFICADO: R07 §4.1] |
| Ola | Als Fjord con 6 m/s: Hs 0,15–0,3 m, Tp 1,2–1,8 s → longitud de onda del orden de la eslora | [ESTIMADO: R07 §4.2] |
| Nivel | ±1,2 m por viento; bajos de arena ~0,5 m menos profundos el 1 % del tiempo | [VERIFICADO: R07 §4.3, R13 §3] |
| Criterios de salida | Temporada 15 jun – 15 sep sin traje; viento ≤ 6 m/s, ráfaga ≤ 10; Hs ≤ 0,3 m; solo de día; chaleco con cuello y cordón siempre | [SUPUESTO: R07 §3.4] |

Para un bote de 2,30 m que planea, la ola corta del fiordo con período de ~1,5 s es del largo del casco:
golpes y aire en la toma (fondo plano, R10a §7). El modelo de resistencia no la incluye (02 §12).

## 10. Qué queda abierto

| Tema | Por qué importa | Cómo se cierra |
|---|---|---|
| Medidas reales del casco y masa | Todo el cálculo usa el casco leído de un plano sin escala | PENDIENTES P0.1; actualizar `boat.*` y correr `run_all.py` |
| Estabilidad | Puede volcar quieto | Ensayo E1 de R13 §5 antes de instalar la electrónica |
| Potencia continua del MTI120116 | Es la entrada más influyente en la V máx. (02 §10) | Pedírsela a Maytech; prueba térmica |
| JT132: precio, brida de toma, altura del eje, curva | Decide entre A y B (03 §3) | Cotización a AWT (wuxiawt01@163.com, R11 §4) |
| Clasificación legal | Vandscooter o no; cómo se mide la potencia de speedbåd | Preguntas Q1–Q5 de R13 §8 |
| η real de la bomba y de la toma | El modelo usa valores de literatura | Punto fijo, V máx. con GPS, vacuómetro en la garganta (R10a §8) |
