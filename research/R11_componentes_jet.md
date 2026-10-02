# R11 — Componentes comprables para el waterjet inboard de Jorge (motor, ESC, batería, bomba, tren, auxiliares)

**Fecha de consulta y de todos los precios:** 2026-10-01.
**Objeto:** el plano de Jorge (5 kW continuos / 7,2 kW máx., 72 V, 4500 rpm directo a impulsor axial Ø108 de 4 álabes + estator, tobera Ø72, eje Ø20 inox, toma enrasada con rejilla, boquilla y bucket), con la toma corregida de R10a y las correcciones de R10b.

**Etiquetas:**
- [VERIFICADO: url] = página abierta con WebFetch en esta sesión; el número está copiado de ahí.
- [ESTIMADO: base] = memoria, deducción o dato que solo aparece en el resumen del buscador (página no abierta).
- [CALCULADO] = cuenta propia con datos verificados.
- [SUPUESTO] = decisión de diseño.

**Monedas (tipos del proyecto, R08a §0):** 1 EUR = 7,4755 DKK; 1 USD = 0,8807 EUR; 1 GBP = 1,1701 EUR (0,85463 GBP/EUR). Para CAD no hay tipo del proyecto: uso el BCE del 2026-10-01, 1 EUR = 1,6095 CAD → 1 CAD = 0,6213 EUR [VERIFICADO: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml].

**IVA y envío (no repito lo de R08a §0 y R08b §1):**
- Tiendas chinas (Flipsky, Maytech, Spintend, Golden Motor, AWT): precio **sin** IVA de importación (25 %), sin arancel y sin envío. Para DK sumar ≈ +25 % de IVA + envío DHL + arancel [VERIFICADO en R08a §0].
- Tiendas DE/NL/BE: precio con el IVA del país de la tienda (19–21 %). A un particular en DK deberían facturarle con el 25 % danés [ESTIMADO: R08b, reglas OSS].
- Watski: DKK con 25 % de moms.

---

## 0. Resumen ejecutivo

1. **El dato que más cambia el diseño es el rpm/V real del motor.** Golden Motor publica el ensayo dinámico del HPM5000 [VERIFICADO: PDF de goldenmotor.com, §1.2]:
   - versión 48 V: **≈ 91 rpm/V**;
   - versión 72 V: **≈ 59 rpm/V**.

   Para que el Ø108 gire a 4500 rpm **bajo carga** hacen falta **≈ 120–127 rpm/V en 13S** o **≈ 71–75 rpm/V en 22–23S** [CALCULADO, R10b §4.8]. Con el HPM5000 de catálogo, el Ø108 se queda en ≈ 3400–3850 rpm y absorbe solo **≈ 2,2–3,1 kW** [CALCULADO §1.3]. Hay dos salidas: pedir **bobinado a medida** (Golden Motor dice "2000–6000 rpm customizable") o usar un motor de KV más alto.
2. **Motor recomendado.**

   | Clase de tensión | Motor | Masa | Precio |
   |---|---|---|---|
   | ≤ 50 V | **Maytech MTI120116 150 KV**, refrigerado por agua, eje Ø15 con chavetero | 4,4 kg | 537,50–573 USD = 473–505 € sin IVA |
   | 72 V | **Golden Motor HPM5000L (refrigerado por líquido) con bobinado de ≈ 72 rpm/V a pedido** | 11,35 kg | 545 USD = 480 € sin IVA |
   | 72 V, alternativa de catálogo | **Motenergy ME1304** (≈ 80 rpm/V [ESTIMADO]) | 16 kg | 961,20 € sin IVA, sin stock |

   El MTI120116 se alimenta de 10–16S (37–67 V), así que **no sirve para 72 V**.
3. **ESC (ambos VESC, compatibles con el firmware y los límites de rpm de P1).**
   - ≤ 50 V: **Flipsky FSESC 75350 con caja refrigerada por agua**. 350 A a 50 V, IP65 con la caja, 210 USD = 185 € [VERIFICADO].
   - 72 V: **Flipsky FSESC 110300**. 14–110 V (4–26S), 300 A, FW 6.06, filtro de fase, 1,2 kg, 219 USD = 193 € [VERIFICADO].
   - Los de 85 V (Spintend Ubox 85/250) quedan **sin margen** con 22–23S, que llegan a 80,3–84,0 V cargadas.
4. **Batería.** La regla dura es la **tasa C**, no la tensión. 7,2 kW sacados de 3 kWh son **2,4 C**, y eso no depende de la tensión [CALCULADO].
   - **≤ 50 V:**
     - No encontré ningún pack LFP **13S** comercial en la UE. Todos los "48 V" son 15S/16S (54,8/58,4 V máx.).
     - La opción comercial que cumple ≤ 50 V es **2 × LiTime 36 V 60 Ah Golf Cart en paralelo**: 12S, 43,8 V máx., 4,6 kWh, BMS 2 × 120 A, 939,98 € con IVA, ≈ 40 kg [precio VERIFICADO, masa ESTIMADA].
     - Con 12S el motor gira 8 % menos que con 13S. Elegir el KV para 38,4 V.
   - **72 V:**
     - Ninguna marca náutica (LiTime, Power Queen) vende 72 V. Sus baterías de 24 V admiten como máximo 2S [VERIFICADO].
     - La vía realista es **DIY 23S1P con celdas EVE LF50K** (3C en el ensayo de régimen, 5C de pulso, 1395 g): 3,68 kWh, ≈ 32 kg de celdas, 805 € en celdas, más un JK BMS de 200 A.
5. **Comprar vs construir.**
   - **JT132 (Wuxi AWT):** impulsor inox **Ø130**, tobera Ø70, 12 kg, 1,5–40 kW, 2000–6000 rpm, dirección y reversa mecánicas incluidas (deflector de doble ducto), entrada por cardán SWC65 o acople ISO [VERIFICADO: wuxiawt.com]. Precio ≈ 1000–1100 USD FOB [ESTIMADO: buscador], más flete, IVA y arancel.
   - Por la ley de afinidad, el Ø130 absorbe 5 kW a **≈ 3300 rpm** [CALCULADO]. **Encaja con el HPM5000 de catálogo sin rebobinar.**
   - Es la opción "comprar" más coherente: reemplaza impulsor, estator, tobera, boquilla y bucket, que son las piezas más difíciles de fabricar.
6. **Tren de la bomba (precios VERIFICADOS en tiendas DE/BE):**
   - sello mecánico tipo MG1 SiC/SiC/NBR, desde 29 €, 10 m/s, 12 bar;
   - rodamiento de doble hilera 3204‑2RS, 6,20 € (Dold); en inox AISI 420, 12,64 € + IVA;
   - par 7204 BEP SKF, 2 × 31,40 €;
   - **Rotex 24** con estrella de 92 ShA (T_KN 35 N·m; 60 N·m con 98 ShA), 67,47 €. La L‑090 de NBR (16,3 N·m) **no alcanza**;
   - eje 1.4404 Ø20 h9: 32,87 €/m.
7. **Fabricar el impulsor.**
   - Ningún servicio (Xometry, Protolabs, PCBWay, JLCCNC) da precio sin subir el CAD.
   - SLM en 316L (JLC3DP): build de 390 × 390 × 290 mm y ±0,3 mm o 0,4 % [VERIFICADO]. Con ≈ 0,4 USD/g [VERIFICADO: unionfab, ejemplo], un Ø110 de 0,8–1,3 kg costaría **≈ 300–520 €** más el torneado del diámetro exterior [ESTIMADO].
   - Referencia de producto terminado: impulsor Solas de 140 mm para Spark, 539 CAD = 335 € [VERIFICADO].

---

## 1. Motor (5 kW continuos, ≥ 7 kW pico, ~4000–5000 rpm bajo carga)

### 1.1 Requisito de rpm/V (lo que falta en el plano)

| Pack | V nominal | V máx. (cargada) | rpm/V para 4500 rpm bajo carga (85–90 % del vacío) | Etiqueta |
|---|---|---|---|---|
| LFP 12S | 38,4 | 43,8 | 130–138 | [CALCULADO] |
| LFP 13S | 41,6 | 47,45 | 120–127 | [CALCULADO] |
| LFP 22S | 70,4 | 80,3 | 71–75 | [CALCULADO]; R10b da 62,5–73,5 |
| LFP 23S | 73,6 | 84,0 | 68–72 | [CALCULADO] |

Par en el eje: 5 kW a 4500 rpm = 10,6 N·m; 7,2 kW a 4500 = 15,3 N·m; 7,2 kW a 3500 = 19,6 N·m [CALCULADO].

**Con KV "de sobra" no hay problema:** el VESC limita las rpm (`l_max_erpm`) y la corriente de batería. **Con KV corto no se llega:** solo queda debilitamiento de campo, con pérdidas y calor.

### 1.2 Candidatos

| Motor | rpm/V (fuente) | P cont. / pico | Par | I | Masa | Medidas | Eje | Refrigeración / IP | Sensores | Precio 2026‑10‑01 | Etiqueta |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Golden Motor HPM5000B 48 V** (aire, ventilador) | **91,5** (vacío 4389 rpm a 47,99 V) | 3–7,5 kW "rated"; ensayo: 5,27 kW a 3501 rpm, 83,8 % | 13 N·m nom. / 45 N·m pico (made‑in‑china); 40 N·m pico (GM) | "rated I 120 A"; 132,7 A a 5,27 kW | 11 kg | Ø206 × 126 | Chavetero "5 mm (W) × 43 mm (L) × 19 mm (D: 22,3 mm)" (Kelly); "7/8"", chaveta 5/16"" (Monster) → **medir** | "Water resistent", ventilador. Sin IP | KTY84‑130 (GM); hall no declarado en las páginas | **490 USD** (GM, = 432 €) · **994,33 €** + 28,19 € de envío, "Out of stock" (Kelly EU) · 446 USD (made‑in‑china, 1–9 u.) | [VERIFICADO: https://www.goldenmotor.com/frame-bldcmotor.htm] [VERIFICADO: https://www.goldenmotor.com/eCar/HPM48-5000.pdf] [VERIFICADO: https://www.kellycontrollers.eu/hpm5000b-5kw-48v-leghuteses] [VERIFICADO: https://goldenmotorcz.en.made-in-china.com/product/CwmnvfujhxVi/China-HPM5000B-48V-4000RPM-Brushless-DC-Motor-with-CE-Certificate.html] [VERIFICADO: https://monsterscooterparts.com/products/48v-5000w-brushless-aircooled-motor-golden] |
| **Golden Motor HPM5000B / L 72 V** (L = líquido) | **58,9** (vacío 4259 rpm a 72,25 V) | ensayo: 4,71 kW a 3730 rpm, 90,6 %; 6,19 kW a 3611 rpm, 88,1 % | 40 N·m pico (GM) | "rated I 80 A"; 98 A a 6,19 kW | 11 kg (B) / 11,35 kg (L) | Ø206 × 126 | ídem | B: aire. **L: líquido** | KTY84‑130 | **490 USD (B) / 545 USD (L)** en GM (432 / 480 €) · B: **1306,48 €** + 28,19 €, "Out of stock" (Kelly EU) · L 72 V: "Request quotation" | [VERIFICADO: https://www.goldenmotor.com/eCar/HPM72-5000.pdf] [VERIFICADO: https://www.kellycontrollers.eu/hpm5000b-5kw-72v-leghuteses] [VERIFICADO: frame-bldcmotor.htm] |
| **Maytech MTI120116** (inrunner refrigerado por agua) | KV 100 / 150 / 200 (nominal) | **máx. 18,8 kW**; continua no publicada | 20,6 N·m máx. | 380 A máx. | **4,4 kg** | Ø120 × 116 | **Ø15 × 30 mm con chavetero** | **Watercooled** | Hall opcional; máx. 120 °C; **sensor de temperatura NTC10K 3950 de fábrica** ("Yellow: Temp Sensor (NTC10K 3950k)"); construcción **12N/10P** (10 polos = 5 pares); cables 6 AWG × 300 mm | **537,50 USD** sin hall 150 KV (= 473 €) · **573 USD con hall** (= 505 €, la que se compra); "limited stock", 30–50 días si se fabrica | [VERIFICADO: https://maytech.cn/products/copy-of-maytech-fully-waterproof-mti120116-18-8kw-powerful-brushless-inrunner-motor-for-electric-surfboard-rc-boat-jetski; NTC, 12N/10P y cables releídos 2026-10-02 (la versión anterior de esta tabla decía "NTC no declarado": era falso)]. Tensión: **10–16S** |
| Maytech MTI85165‑HA‑WP | 150 / 130 KV | 10,5 kW máx. | — | 300 A | no publicada | 85 × 165 [ESTIMADO: nombre] | Chavetero (Ø no publicado) | IP68, sellado (sin camisa de agua) | Hall sí | 528,50 USD (= 465 €), "not stock item", 40–60 días | [VERIFICADO: https://maytech.cn/products/maytech-85165-150kv-brushless-sensored-motor-10kw-for-electric-car-motorcycle]. 6–16S |
| Flipsky FS65161 (eFoil) | 100 / 120 | **3 kW nom.** / 6 kW máx. | 6,3 N·m nom. / 9 N·m | 60 A nom. / 200 A | 3 kg | Ø65 × 161 | Ø12 estriado o roscado | IP68, sello cerámico; se enfría por inmersión | NTC opcional (+3 USD) | 298–301 USD (= 262–265 €) | [VERIFICADO: https://flipsky.net/products/brushless-motor-sensorless-amphibious-fully-waterproof-motor-65161-120kv-100kv-6000w-for-efoil-ejet-boards-ebike-electric-surfboard]. **Descartado**: 3 kW continuos |
| Maytech MTI65162 | 100 / 120 | 9 kW máx. | — | 300 A | — | Ø65 × 162 | Roscado | IP68 | Sin hall | 329 USD, "Sold out" | [VERIFICADO: https://maytech.cn/products/maytech-fully-waterproof-brushless-motor-65162-for-electric-surfboard-efoil]. Misma clase que el 65161 |
| **Motenergy ME1304** (PMSM, doble estator) | **≈ 80** [ESTIMADO: 9,55 / K_t con K_t = 0,12 N·m/A] | **14,5 kW** / 22 kW | 50 N·m máx. | 180 A cont. / 420 A 30 s | **16 kg** | — | **7/8"** | **Líquido** (glicol 50 %, 10 L/min, ≤ 1,5 bar), "fully enclosed" | **KTY84‑130 + encoder sin/cos** | **961,20 € sin IVA**, "out of stock", 3–6 semanas | [VERIFICADO: https://www.evea-solutions.com/en/synchronous-motors/674-me1304-pmsm-brushless-motor.html]. 24–96 V |
| QS Motor QS138 70H V3 | — | 5,5 kW cont. (72 V) | — | — | 27 lb (12,2 kg) | Ø150 × 234 | **Estriado, con reducción interna 1:2,35** | IP54 (página QS 4000 W) | — | 699,99 USD, "Sold Out" | [VERIFICADO: https://gritshift.com/products/qs138-70h-v3-motor] [VERIFICADO: https://www.qsmotor.com/product/4000w-mid-drive-motor/]. **Descartado**: con la reducción el eje sale a ~1700 rpm |

**Notas:**
- **Flux linkage del HPM48‑5000 medido con VESC:** 15,02–15,94 mWb [VERIFICADO: https://vesc-project.com/node/3376]. Con 4 pares de polos [VERIFICADO: made‑in‑china] da ≈ 87 rpm/V [ESTIMADO: fórmula 60/(2π·√3·λ·pp), de memoria]. Coincide con los 91,5 rpm/V del ensayo.
- **El VESC lee KTY84‑130** como sensor de motor [ESTIMADO: memoria del firmware; R06 solo verificó el NTC 10 k por defecto]. Confirmarlo en VESC Tool antes de comprar.

### 1.3 Punto de funcionamiento con el Ø108 del plano

**Método** [CALCULADO]:
- La curva del motor es lineal entre el vacío y el punto de 5 kW del ensayo de Golden Motor, escalada a la tensión del pack.
- La bomba sigue T = 10,6 N·m·(n/4500)², con 5 kW a 4500 rpm (R10b §4.6).

| Combinación | rpm de equilibrio | P en el eje | Lectura |
|---|---|---|---|
| HPM5000 48 V + 13S (41,6 V) + Ø108 | ≈ 3420 | **≈ 2,2 kW** | No sirve para ≥ 30 km/h (R10b pide 5–7,2 kW) |
| HPM5000 72 V + 22S (70,4 V) + Ø108 | ≈ 3850 | **≈ 3,1 kW** | Corto |
| HPM5000 72 V + 23S **cargada** (84 V) + Ø108 | ≈ 4520 | ≈ 5,1 kW | La potencia cambia ×1,6 entre lleno y vacío (R10b: ×1,59) |
| HPM5000 48 V + 13S + **JT132 Ø130** (P ∝ D⁵: ×2,53) | ≈ 3040 | **≈ 3,9 kW**, ≈ 115 A | Se acerca a 5 kW sin rebobinar; con 12–13S cargada sube |
| MTI120116 150 KV + 13S + Ø108 | 4500 (limitado por el VESC) | 5 kW, ≈ 130 A de batería | OK |

**Recomendación motor:**
- **≤ 50 V:** **Maytech MTI120116 150 KV** [SUPUESTO]. Es el único refrigerado por agua de la clase y pesa 4,4 kg.
  - Riesgo: la potencia continua no está publicada. Pedirla a Maytech (eileen@maytech.cn figura en sus páginas) junto con el caudal de refrigeración.
- **72 V:** **HPM5000L** pidiendo por escrito un bobinado de **≈ 70–75 rpm/V** (vacío ≈ 5000–5200 rpm a 70,4 V) [SUPUESTO]. Si Golden Motor no lo confirma: **ME1304** (16 kg, sin stock).

---

## 2. Controlador (ESC)

Base de configuración, seguridad y firmware: ver R06 §2. Acá van solo los modelos con la potencia del jet.

### 2.1 Clase ≤ 50 V (13S: 47,45 V máx.; hacen falta 150–200 A de batería)

| ESC | V | I continua | Pico | Refrigeración / IP | Filtro de fase | Masa / medidas | Precio | Etiqueta |
|---|---|---|---|---|---|---|---|---|
| **Flipsky FSESC 75350** | 14–84 V (3–20S) | "50V/350A, 75V/250A" | 800 A | **Caja de agua opcional; IP65 con la caja** | Sí | 2000 g con caja / 1230 g sin caja; 200 × 94,6 × 50 | **210 USD con caja** (= 185 €) / 197 USD sin caja | [VERIFICADO: https://flipsky.net/products/flipsky-fsesc-75350-84v-high-current-350a-esc-base-on-vesc-with-aluminum-case-water-cooling-enclosure-for-e-foil-fighting-robot-surfboard-agv-robot]. FW 5.02 de fábrica → el diseño exige ≥ 6.00 (LispBM): flashear en T0.0. Cables de fase y batería 8 AWG |
| Flipsky 75200 Pro V2.0 | 14–84 V (4–20S) | "50v/200A: 75V/150A" | 300 A | PCB de aluminio (aire) | Sí | 700–880 g; 130 × 68 × 41 | 150 USD (= 132 €) | [VERIFICADO: https://flipsky.net/products/flipsky-75200-pro-v2-0-with-aluminum-pcb-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller]. FW 6.02 |
| Flipsky FSESC 75200 (caja de agua) | **14–75 V (3–16S)** | 200 A | 400 A | Caja de agua, IP65 | **No** ("Phase filering is not available… 75200") | 600 g; 110 × 73 × 52 | 271 USD (= 239 €) | [VERIFICADO: https://flipsky.net/products/flipsky-fsesc-75200-75v-high-current-200a-esc-base-on-vesc-with-aluminum-case-water-cooling-enclosure-for-e-foil-fighting-robot-surfboard-agv-robot] |
| Spintend Ubox Aluminum 85/250 V2 | 85 V máx. | "250A max" de batería (según disipación) | — | Caja de aluminio + puerto de ventilador de 12 V | — | 139 × 76 × 21,7 | 279–313 USD (= 246–276 €) | [VERIFICADO: https://spintend.com/products/single-ubox-aluminum-controller-85v-250a-v2-based-on-vesc]. FW propio 6.2; "open-source firmware voids warranty" |
| Trampa VESC 100/250 (MkIII) | hasta 100 V (22S) | 250 A | 400 A | — | — | 141 × 82 × 14 [ESTIMADO: buscador] | **No se obtuvo** (página sin precio). Buscar: "Trampa VESC 100/250 MKIII price" | [VERIFICADO: https://trampa.co.uk/vesc-product-overview-page/] (solo 100 V y 250 / 400 A) |

**Recomendación ≤ 50 V:** **FSESC 75350 con caja de agua** [SUPUESTO].
- Tiene 350 A a 50 V y aguanta 7 kW sin forzarlo.
- La caja de agua usa el mismo circuito que el motor (§1).
- Tiene filtro de fase.

Alternativa más barata en seco: 75200 Pro V2.0, si el compartimento tiene ventilación forzada.

### 2.2 Clase 72 V (22–23S: 80,3–84,0 V cargada; ≥ 100 A)

| ESC | V | I continua batería / fase | Refrigeración / IP | Protocolo | Precio | Etiqueta |
|---|---|---|---|---|---|---|
| **Flipsky FSESC 110300** | **14–110 V (4–26S)** | "110V/300A" (según montaje); pico 800 A | PCB de aluminio, sin caja de agua; IP no declarado | **VESC, FW 6.06**, filtro de fase sí, BEC 5 V @ 3 A | **219 USD** (= 193 €); 1200 g; 183,8 × 80,2 × 43,8 | [VERIFICADO: https://flipsky.net/products/flipsky-fsesc-110300-high-voltage-110v-300a-with-aluminum-pcb-based-on-vesc-for-fighting-robot-surfboard-agv-robot] |
| Trampa VESC 100/250 | 100 V | 250 A / 400 A | — | VESC | Buscar | [VERIFICADO: trampa.co.uk, sin precio] |
| Spintend Ubox 100/100 Lite | "up to 22s", picos ≤ 93 V | **100 A máx.** ("less than 1 minute", según la búsqueda) | Aire, puerto de ventilador | VESC (fw UBOX_SINGLE_100) | 125 USD, **"Sold Out"** | [VERIFICADO: https://spintend.com/products/single-ubox-100v-100a-motor-controller-based-on-vesc]. **Descartado**: 100 A no son continuos |
| Spintend Ubox 85/240 | 85 V máx. ("Don't try more than 85v") | 240 A máx. | Aire | VESC | 269–312 USD | [VERIFICADO: https://spintend.com/products/single-ubox-aluminum-controller-85v-240a-controller-based-on-vesc]. **Sin margen** con 23S (84 V) y regenerando |
| Kelly KLS7230H | 18–90 V | 100 A cont. / 300 A 10 s | **IP66** | No es VESC (sinusoidal, FOC). KTY84 configurable. CAN +45,89 € | **583,63 €** + 11,95 €, "Out of stock" | [VERIFICADO: https://www.kellycontrollers.eu/kls7230h] |
| Fardriver ND72450 | 48–72 V (máx. 90 V) | 200 A batería / 450 A fase | — (179 × 120 × 55, 2,0 kg) | No es VESC (Bluetooth; reversa y "3‑Speed" de fábrica) | Sin precio en QS. 179–240 USD según el buscador [ESTIMADO] | [VERIFICADO: https://www.qsmotor.com/product/fardriver-controller-nd72450/] |
| Votol EM‑150 | 48–72 V (máx. 90 V) | 150 A pico de batería / 470 A pico de fase | — (245 × 129 × 69) | No es VESC (hall) | Sin precio. Buscar: "Votol EM150-2SP price" | [VERIFICADO: https://www.qsmotor.com/product/votol-controller-em-150/] |
| Flipsky FT110BS | 14–110 V | 100 A / 250 A | Aluminio | **No es firmware VESC oficial** ("Flipsky ESC Tool", FW V1.6) | 95 USD | [VERIFICADO: https://flipsky.net/products/flipsky-ft110bs-high-voltage-110v-with-aluminum-pcb-based-on-vesc-for-fighting-robot-surfboard-agv-robot] |

**Recomendación 72 V:** **Flipsky FSESC 110300** [SUPUESTO].
- Es el único VESC de 100 V+ con precio y stock visibles.
- Tiene 26 V de margen sobre 23S.
- Va en caja estanca con placa disipadora, o con una placa fría propia, porque no trae caja de agua.

---

## 3. Batería (~3 kWh útiles)

### 3.1 Restricciones (nuevas; las de tensión y fusibles están en R06 §4.3)

- **Tasa C:** 7,2 kW sobre 3 kWh útiles (3,75 kWh nominales con 80 % de DoD) = **1,9–2,4 C** [CALCULADO].
  - Las celdas prismáticas de 1 C, como la EVE LF105 (105 A máx. continuos [VERIFICADO: https://thebatteryshop.eu/EVE-LF105-LiFePO4-battery-cell]), obligan a ≥ 7 kWh para dar 7 kW.
- **"48 V" de catálogo es 16S** (51,2 V nominal, 58,4 V cargada) y supera los 50 V. Ejemplos verificados:
  - LiTime 51,2 V 100 Ah, BMS 100 A, 899,99 € (0 % DE 756,29 €), "No disponible" [VERIFICADO: https://www.litime.de/products/litime-51-2v-100ah-lifepo4-lithium-batterie.js];
  - "LiTime 48V 100Ah" y "48V 30Ah GC2" (no disponibles) [VERIFICADO: https://www.litime.de/search/suggest.json?q=golf&resources[type]=product&resources[limit]=10].
- **"2 × 24 V en serie" = 16S = 58,4 V cargada** → **no cumple ≤ 50 V**. Además, las de 24 V solo admiten 2S:
  - LiTime 24 V 100 Ah: "4P2S" [VERIFICADO: https://www.litime.de/products/litime-24v-100ah-lithium-lifepo4-batterie.js];
  - Power Queen 24 V 100 Ah: "bis zu 4P2S" [VERIFICADO: https://www.ipowerqueen.de/products/power-queen-lifepo4-24v-100ah-deep-cycle-solarbatterie.js].

  O sea que **tampoco se puede llegar a 72 V con ellas**.

### 3.2 Candidatos

| Opción | Config. | V nom. / máx. | Energía | BMS / C | Masa | Medidas / IP | Precio | Etiqueta |
|---|---|---|---|---|---|---|---|---|
| **2 × LiTime 36 V 60 Ah Golf Cart (paralelo)** | 12S2P | 38,4 / 43,8 | **4,6 kWh** (2 × 2304 Wh) | 2 × "Integriertes 120A BMS", "2C" → 240 A, 9,2 kW | ≈ 2 × 19,8 kg [ESTIMADO: 43,6 lb, buscador] | 8,46 × 8,15 × 20,94" [ESTIMADO: buscador]; IP no publicado | **2 × 469,99 € = 939,98 €** con IVA, envío UE gratis | [VERIFICADO: https://www.litime.de/products/36v-60ah-golfwagen-kart-lithium-batterie.js] ("bis zu 4P"). Envío: R08a §0 |
| 1 × LiTime 36 V 60 Ah | 12S | 38,4 / 43,8 | 2,3 kWh | 120 A → **4,6 kW** | ≈ 19,8 kg [ESTIMADO] | — | 469,99 € | ídem. **No da 7 kW** |
| **DIY 13S2P EVE LF50K + JK BMS** | 13S2P | 41,6 / 47,45 | 4,16 kWh | Celda: 3C en el ensayo de régimen y "5C/5C" de pulso [VERIFICADO: hoja EVE]; BMS 200 A | 36,3 kg de celdas (26 × 1395 g) + caja y BMS | Celda 135,3 × 185,3 mm; IP = la caja que se haga | Celdas 26 × 35,00 € = **910 €** (con IVA, NL) + BMS ≈ 141–172 € | [VERIFICADO: https://www.voltacell.nl/products/eve-lf50k-lifepo4-battery-cell-3-2v-50ah-a-grade-m4-thread] ("Only 6 products left": **falta stock para 26**) [VERIFICADO: https://www.battery-germany.de/wp-content/uploads/2021/02/LF50K3.2V-50Ah-Product-SpecificationVersion-D.pdf] |
| **DIY 23S1P EVE LF50K** (72 V) | 23S | 73,6 / 84,0 | **3,68 kWh** | 3C ≈ 150 A → 11 kW; BMS 200 A | 32,1 kg de celdas | ídem | 23 × 35 € = **805 €** + BMS | ídem [CALCULADO] |
| DIY 24S1P EVE LF50K (72 V) | 24S | 76,8 / 87,6 | 3,84 kWh | ídem | 33,5 kg | — | 840 € + BMS | Con 87,6 V **supera** los 85 V de Spintend; el 110300 lo admite |
| akkushop‑24 "72V LiFePO4 50Ah" | **24S16P** | 76,8 / 87,6 | "4.380Wh" (sic) | **100A** | **40,4 kg** | 460 × 350 × 190 | No visible por variante (desde 329 € la de 12 Ah); con cargador | [VERIFICADO: https://www.akkushop-24.de/72V-Lithium-Ionen-Akku-72V-LiFePO4-Lithiumeisenphosphat-Varianten-fuer-Industrie-Scooter-Boot-E-Bike-Camping-Golf]. Las demás variantes LFP tienen BMS de 20–60 A |

**JK BMS B2A24S20P** (8–24S, 200 A, balanceo activo de 2 A):
- 147,00 £ = **172 €**, con stock en el Reino Unido; impuestos de importación UE aparte [VERIFICADO: https://offgridpower.solutions/shop/jkbms-b2a24s20p-lifepo4-battery-bms].
- Almacén UE (Polonia): B2A24S15P / B2A24S20P **"Sold out"** [VERIFICADO: https://hakadibattery.com/products/eu-stock-jk-bms-active-balance-bms-4s-8s-12s-16s-20s-24s-smart-bluetooth-bms-60a-80a-100a-150a-200a-for-lifepo4-li-ion-lto-battery].
- Directo de JK: 159,98–194,96 USD [ESTIMADO: buscador].

**Cargadores:**

| Pack | Cargador | Precio | Etiqueta |
|---|---|---|---|
| 12S | LiTime 36 V 15 A, IP66 | 132,99 € | [VERIFICADO en R08a §5] |
| 13S | "LFP battery charger 47.45V 7A", XT60 | **124,31 €** (AliExpress) | [VERIFICADO: https://www.aliexpress.com/w/wholesale-47.45v-charger.html] |
| 24S | 87,6 V 10 A | 61,50 € (34 vendidos) / 80,25 € (55 vendidos) | [VERIFICADO: https://www.aliexpress.com/w/wholesale-87.6v-lifepo4-charger.html] |
| 23S | "84V‑87.6V 10A/20A/15A adjustable" | 84,00 € (8 vendidos) | ídem |

Para 23S hace falta 84,0 V (23 × 3,65). Ninguno de estos cargadores es marino ni tiene IP declarado → cargar en tierra.

**No verificados:** Victron (Lithium Smart 12,8/25,6 V, BMS externo) y Epoch (EE. UU.). No abrí sus páginas. Buscar: "Victron LiFePO4 Smart series connection max" y "Epoch 36V 100Ah EU". Ninguno vende 13S ni 72 V por lo que se sabe [ESTIMADO].

**Recomendación batería:**
- **≤ 50 V:** **2 × LiTime 36 V 60 Ah en paralelo** (939,98 €, 4,6 kWh, BMS 240 A, sin armar celdas) [SUPUESTO].
  - En 12S el ESC y el KV se dimensionan para 38,4 V.
  - Ventaja: el MRBF de 58 V y el antichispa de 60 V de R06/R08a valen en tensión. (Nota 2026-10-02: el SW80 es de 100 A y no alcanza la corriente de la selección; el diseño usa el TE KILOVAC EV200AAANA, 500 A, bobina 9–36 V alimentada a 12 V: 04_diseno/electronica §4.)
- **72 V:** **DIY 23S1P EVE LF50K + JK B2A24S20P** (≈ 977 €, 3,68 kWh, ≈ 35 kg con caja) [SUPUESTO]. Exige armar el pack, una caja estanca y un cargador de 84 V.

---

## 4. Waterjets comerciales (comprar vs construir)

| Unidad | Ø impulsor / tobera | Potencia / rpm de diseño | Masa | Materiales | Dirección / reversa | Precio | Envío a DK | Etiqueta |
|---|---|---|---|---|---|---|---|---|
| **AWT JT132** (Wuxi AWT, China) | **130 / 70 mm** | **1,5–40 kW; 2000–6000 rpm** | **12 kg** neto (20 kg bruto); 786 × 298 × 185 | Cuerpo de aluminio, **eje e impulsor inox** | **Mecánicas: dirección + reversa** con "twin duct reverse deflector" | ≈ **1000–1100 USD** por set, MOQ 1 (= 881–969 €) [ESTIMADO: buscador; la ficha no muestra precio] | Flete marítimo o aéreo + 25 % IVA + arancel: **cotizar** (wuxiawt01@163.com, +86‑13912473311) | [VERIFICADO: https://www.wuxiawt.com/JT132-pd574514898.html]. Límite: "3 m/10 ft and 0.5 ton" por unidad; entrada "ISO cardan shaft SWC 65 or ISO standard coupling" |
| AXAMARINE Jet PUMP 100 (Croacia, **UE**) | 100 mm | "5‑25 HP (4‑23 kw)", hasta 7200 rpm | — | Aluminio o inox | Tobera de dirección (con salida de agua para refrigerar); reversa no mencionada | **No publicado**; pedir cotización | Intra‑UE (sin aduana) | [VERIFICADO: https://www.jet-drive.com/] [VERIFICADO: https://www.axamarine.com/otherproducts] (Karlovac, info@aquanami.eu) |
| Maytech MTWJ12KW (motor + bomba) | **95 mm**; tobera no publicada | 13,2 kW máx. a 80 V; **130 KV**; 36–80 V | No publicada | Impulsor de aluminio o inox ("ship randomly") | No declarado | **1015,90 USD** (= 895 €); con ESC, 1376,90 USD | DHL desde China | [VERIFICADO: https://maytech.cn/products/maytech-water-jet-pump-max-87kg-thrust]. Motor con sensor de temperatura |
| Maytech MTWJ10KW | — | 10 kW nom. / 13,2 kW a 84 V; 10 920 rpm máx. | — | — | — | 833,50 USD (= 734 €), "Not in stock" | ídem | [VERIFICADO: https://maytech.cn/products/maytech-mtwj10kw-water-jet-pump-10k-powerful-motor]. Empuje máx. 81 kg a 84 V |
| Flipsky E‑Jet Pump Thruster 3000 | No publicado | **3 kW nom.** / 6 kW máx.; 6–20S | 5 kg (solo el thruster) | Aluminio; IP68 | No | 422 USD sin soporte (= 372 €) | ídem | [VERIFICADO: https://flipsky.net/products/flipsky-jet-pump-thruster-3000-6000w-underwater-thruster-for-marine-underwater-propulsion-kayaks-inflatable-boats-small-watercraft]. **Corto en continua** |
| MA‑3D JetX‑100v2 | Tobera de 100 mm; impulsor de carbono | Referencia 1 kW, 8,5 kg/kW de empuje estático | — | Impulsor de fibra de carbono, rejilla 316L | Tobera ±25° | No visible | — | [VERIFICADO: https://ma-3d.com/100mm-water-jet-thruster-jetx-100v2/]. Escala RC/kayak, chico para 5 kW |
| Sea‑Doo Spark (bomba de 140 mm, repuestos) | 140 mm | Bomba de PWC de 60–90 hp a ~7000–8000 rpm [ESTIMADO: memoria] → 5 kW a ≈ 3000–3400 rpm [CALCULADO: P ∝ n³] | — | — | El casco de la moto lleva la reversa (iBR) [ESTIMADO] | Impulsor **Solas 140 Spark 539 CAD = 335 €**; anillo de desgaste plástico 140 **100 CAD = 62 €**, inox **325 CAD = 202 €**; kit de toma Spark 2900 CAD (Minijet). Anillo OEM 267000925: **87,98 £ = 103 €** (Reino Unido). "OEM Jet Pump Fully Built" **999 USD** (EE. UU.) | Minijet (Canadá) y PWC Muscle (EE. UU.): aduana. JetSeaHub (Reino Unido): aduana post‑Brexit | [VERIFICADO: https://minijet.ca/product-category/pump/] [VERIFICADO: https://minijet.ca/shop/sea-doo-spark-plastic-wear-ring-140mm/] [VERIFICADO: https://www.jetseahub.com/product-page/seadoo-spark-wear-ring] [VERIFICADO: https://pwcmuscle.com/en/oem-jet-pump-fully-built-for-seadoo-spark.html]. Usado en DK: buscar "dba.dk sea doo spark jetpumpe" |

**Repuestos de jetboards de marca:** sin catálogo público.
- Radinn quebró en 2023 [ESTIMADO: buscador].
- topjetsurfing.com no lista piezas de bomba [VERIFICADO: https://topjetsurfing.com/accessories].
- Buscar: "Awake jet pump spare part e-surfer".

**Lectura comprar vs construir** [CALCULADO/ESTIMADO]:
- **El JT132 resuelve en una pieza lo que el plano no tiene definido** (H3, H4, H10, H15 de R10b): ducto, sello, holgura metálica, estator, boquilla externa y reversa.
- Lo que cuesta: 12 kg y su toma propia, que obliga a adaptar el fondo a su brida. El Ø130 a ≈ 3000–3300 rpm encaja con el HPM5000 de catálogo.
- Pedirle a AWT:
  - el plano de la brida de toma;
  - la altura del eje sobre el fondo, para revisar el cebado de R10a: el eje tiene que quedar ≥ 20 mm bajo la flotación estática;
  - la curva H‑Q o el empuje del impulsor estándar;
  - el paso disponible para ~5 kW.

---

## 5. Tren de la bomba (si se construye)

**Cargas de diseño** (de R10b §4.7, no las recalculo):
- par de 9,4 N·m nominal y 13,5 N·m máximo con 7,2 kW a 4500 rpm; con el HPM a 3500 rpm, 19,6 N·m [CALCULADO];
- pico del motor 40–45 N·m;
- empuje axial de 257 N (30 km/h) a 760 N (punto fijo);
- 4,7 m/s en el sello con eje Ø20.

| Partida | Producto | Especificación clave | Precio | Etiqueta |
|---|---|---|---|---|
| **Sello mecánico Ø20** | **ST "Mechanical Seal ST‑MG1" SiC/SiC/NBR, con contraaro** (tipo MG1, fuelle elastomérico) | Ejes de 8–100 mm; **12 bar; 10 m/s** (> 4,7 m/s); "Sofort lieferbar" | **"ab 29,00 €"** (19 % de IVA incluido; el precio de Ø20 aparece al elegir la medida) | [VERIFICADO: https://st-shop24.de/dichtungen/gleitringdichtungen/mechanical-seal-st-st1-sic-sic-nbr-gleitringdichtung-inkl-gegenring.html] |
| Sello (alt.) | ST‑MG1 SiC/SiC/Viton | ídem | desde 29,00 € | [VERIFICADO: https://st-shop24.de/dichtungen/gleitringdichtungen.html] |
| Sello (alt. barata) | Tipo 560 / BIA, carbón o SiC, Ø20 (bomba de agua) | — | ≈ 12 USD [ESTIMADO: buscador, Amazon US] | Buscar: "560 mechanical seal 20mm carbon SiC" |
| **Rodamiento fijo** (axial en ambos sentidos) | **3204/5204‑2RS**, doble hilera de contacto angular, 20 × 47 × 20,6 | Sellado | **6,20 €** IVA incl. (Dold, envía a Europa: R08b §1) · 9,52 € IVA incl. (Z24, "EU‑weite Lieferung ab 5,99 €") | [VERIFICADO: https://www.dold-mechatronik.de/Double-row-angular-contact-ball-bearings-3204-5204-2RS-20x47x206mm] [VERIFICADO: https://www.z24.de/a/41939-schraegkugellager-zweireihig-2rs/651077] |
| Rodamiento fijo inox | 3204 2RS "ROSTFREI", **AISI 420** | 3 en stock | **12,64 € + IVA** | [VERIFICADO: https://kugellagershop-duesseldorf.de/3204-2RS-ROSTFREI-Edelstahl]. El 420 se corroe en agua de mar (R06 §1.3): va del lado seco |
| Par de contacto angular | **SKF 7204 BEP** (40°), montar 2 en O | C = 13,3 kN, C0 = 7,65 kN (≫ 760 N) | 31,40 € IVA incl. c/u → **62,80 € el par** (Klium, BE) | [VERIFICADO: https://www.klium.com/en/skf-7204-bep-single-row-angular-contact-ball-bearing-20-x-47-x-14-mm-with-contact-angle-40-27794] |
| Soporte / caja | Dold **SS‑UCFL204** (flanco inox, eje 20) | Unidad con inserto de bolas y prisioneros: **soporte flotante, no fijo** | **38,29 €** | [VERIFICADO: https://www.dold-mechatronik.de/Stainless-steel-miniature-flanged-SS-204-UCFL-shaft-20-mm] |
| **Acople flexible** | **KTR Rotex 24** (Ø55): cubos largos + estrella **T‑PUR naranja (92 ShA)** | **T_KN 35 N·m (92 ShA) / 60 N·m (98 ShA)**; T_Kmax 70 / 120; agujero 0–35; n máx. 12 100–13 800 rpm | **67,47 €** IVA incl. (56,70 sin IVA), sin agujerear o pre‑agujereado | [VERIFICADO: https://www.z24.de/a/40157-kupplungen-rotex/660005] · torques [VERIFICADO: https://www.ach.nu/wp-content/uploads/2017/07/rotex_en.pdf] |
| Acople (comparación) | Lovejoy L‑090 / L‑095 | NBR: **16,3 / 21,9 N·m**; uretano: 24,4 / 32,9; Hytrel: 45,3 / 63,4. Agujero máx. 25 / 28 mm | — | [VERIFICADO: https://www.lovejoy-inc.com/wp-content/uploads/2017/11/JawCouplingLLineInstallGuide2012.pdf]. **L‑090 de NBR descartado** (< 19,6 N·m) |
| Acople (descartado) | Rotex 19 | 10 / 17 N·m | — | ídem (KTR) |
| **Eje** | Hörr **1.4404 (316L) Ø20**, 1 m | Tolerancia "+0,000 / −0,052" (= h9), 2,47 kg/m, corte a medida (0,5–1 m) | **32,87 €/m** IVA incl. | [VERIFICADO: https://www.hoerr-edelstahl.de/Edelstahlrohre-und-Edelstahlprofile/Rundstahl-4-bis-60-mm-V2A-Vollmaterial/Rundstahl-20-mm-Rundstab-Vollmaterial-V4A-1-4404-Edelstahl-1-m-100-cm-1000-20-mm-matt-1-4404-V4A-1-m-100-cm-1000-mm.html]. Envío gratis solo en DE (≥ 300 €) |
| Eje (alt.) | Metallstore 1.4404 Ø20 / Ø25 | — | 55,46 / 86,55 €/m **sin IVA** | [VERIFICADO: https://www.metallstore.de/edelstahl/stange-rund/1.4404-rund/] |
| Eje 17‑4PH | Evek 1.4542+AT Ø20 / Ø25,4, 1 m | **+AT = recocido de solución**: hay que envejecerlo (H1150 en uso marino [ESTIMADO: memoria]) | 190,40 / 285,84 € (bruto) | [VERIFICADO: https://evek.top/edelstahl/2598-edelstahl-stange-8mm-300mm-14542at-uns-s17400-rundstab-rundstahl-aisi-630.html]. No hace falta: el 316 da FS ≥ 5,5 (R10b) |
| Chaveta | DIN 6885 A 6 × 6 en A4 (Ø20) | — | ≈ 2–5 € [ESTIMADO] | Buscar: "Passfeder DIN 6885 A 6x6 A4" |

**Disposición recomendada** [SUPUESTO; consistente con R10a §5.2 y R10b H16]:
- sello en el techo del ducto, con la cara mojada abajo;
- cámara de drenaje con testigo;
- **3204‑2RS fijo** en una caja torneada abulonada al bloque de toma (toma el empuje en ambos sentidos);
- 6204 o UCFL204 flotante cerca del acople;
- Rotex 24 con 98 ShA y 2–3 mm de juego axial entre cubos (la distancia "s" de KTR);
- motor en soporte propio.

**Advertencia de sello:** el sello trabaja en seco si la bomba no ceba (R10a §0.2). SiC/SiC es la pareja peor en seco; carbón/SiC tolera arranques cortos en seco [ESTIMADO: memoria técnica]. Pedir **carbón/SiC** (tipo MG1 "Car/SiC") o garantizar el cebado antes de girar.

---

## 6. Impulsor y anillo de desgaste

| Vía | Dato abierto | Estimación para el Ø108–110 (1 unidad) | Etiqueta |
|---|---|---|---|
| **SLM 316L** (JLC3DP) | "Starting price $8.00"; build de **390 × 390 × 290 mm**; tolerancia **±0,3 mm o 0,4 %**; Ra 3,2–12 µm; pared mínima de 2,0 mm (1,5); 600 MPa de tracción; 72 h | Masa ≈ 0,8–1,3 kg [ESTIMADO: cubo Ø40 × 50 + 4 palas de 4–6 mm] × ≈ 0,4 USD/g → **≈ 280–460 €**, más el torneado del diámetro exterior y del agujero y el balanceo, ≈ 50–150 € en taller [ESTIMADO] | [VERIFICADO: https://jlc3dp.com/help/article/316l-stainless-steel] · precio por gramo de ejemplo [VERIFICADO: https://www.unionfab.com/blog/2025/01/metal-3d-printing-cost] ("$0.4 per gram"; 74,62 cm³ de 316L SLM cotizados a 45,49 USD) |
| **CNC 5 ejes** (Xometry, Protolabs, PCBWay, JLCCNC) | Piden el CAD para cotizar; no se obtuvo precio | Inox, 1 unidad: **≈ 600–1500 €** [ESTIMADO: memoria + "$200‑400 per piece, MOQ 10" de un fabricante, solo buscador]. Aluminio 6082/7075 anodizado: ≈ 40 % menos [ESTIMADO] | Buscar: "Xometry instant quote 5-axis impeller 316", "JLCCNC 5 axis quote" |
| **Fundición de bronce al aluminio o inox con modelo impreso** (cera o PLA perdido) | — | 400–1000 € con mecanizado posterior [ESTIMADO: memoria] | Buscar: "støberi bronze Sønderjylland" / "Feinguss Einzelteil Edelstahl Laufrad" |
| **Impulsor existente** | Solas 140 mm Spark 539 CAD = **335 €**; Solas 140 Kawasaki 489 CAD = 304 € | Exige la carcasa de 140 y el anillo de la misma moto: deja de ser el Ø108 del plano | [VERIFICADO: https://minijet.ca/product-category/pump/] |
| Impulsor de jetboard Ø95–120 | Maytech MTWJ12KW Ø95 (solo con la unidad); MA‑3D de carbono 120 mm ≈ 149 £ [ESTIMADO: buscador, eBay UK 403] | — | [VERIFICADO: maytech MTWJ12KW] |
| **Anillo de desgaste** | De Spark: plástico 100 CAD, inox 325 CAD | Para el Ø108 propio: **tornear** un tubo 316 o un buje de bronce/UHMW con el torno disponible (R10b H15), material ≈ 20–40 € [ESTIMADO] | [VERIFICADO: minijet.ca] |

**Recomendación:**
- Si se construye: **SLM 316L + torneado del diámetro exterior a medida contra un anillo de desgaste torneado** (holgura 0,5–0,8 mm medida con galgas).
- El PETG queda descartado para el impulsor (R10b H15).
- Antes de pagar: pedir a JLC3DP y a un taller CNC europeo la cotización con el mismo STEP.

---

## 7. Rejilla, placa de rodadura, dirección y bucket

| Partida | Producto | Dato | Precio | Etiqueta |
|---|---|---|---|---|
| Barras de rejilla | 1.4404 macizo Ø5–6 o pletina de 4 mm (7 barras de 4 mm, luz de 12 mm según R10a) | — | ≈ 10–20 € [ESTIMADO: ~15 €/m para Ø6 por escala de precio con el Ø20 de Hörr] | Buscar: "hoerr-edelstahl Rundstahl 6 mm 1.4404" |
| Placa de rodadura | Al **EN AW‑5083**, 8 mm, corte a medida (Dold) | 80 mm de ancho: desde 1,63 €; 160 mm: desde 3,25 €. El buscador da **31,26 €/m (80 mm) y 62,51 €/m (160 mm)** → **≈ 391 €/m²** + 1–2 € de corte | Placa de 300 × 250 ≈ 30 € [CALCULADO/ESTIMADO] | [VERIFICADO: https://www.dold-mechatronik.de/Aluminiumplatten-EN-AW-5083-Alu-Platte-unfoliert-Dicke-8mm-Breite-160mm-346kg-m-Zuschnitt-20-3000mm] (solo el "ab"); €/m [ESTIMADO: buscador]. Gemmel tiene 6 mm (16,5 kg/m²) y 8 mm (22,0 kg/m²) en 1020 × 2020 / 1520 × 3020, con el precio recién en el carrito [VERIFICADO: https://www.gemmel-metalle.de/alu-platten-und-bleche/platten/5083/1.html] |
| Cable de bucket o dirección (push‑pull) | **Ultraflex Mach5** (cable de control) | 5 ft **445 kr**; 10 ft 553 kr; 20 ft 763 kr; con stock | 59,5–102 € | [VERIFICADO: https://www.watski.dk/kontrolkabel-mach-5-ultraflex-11Jgp] |
| Caja de dirección (helm) | **Ultraflex T85** | "op til 150 HK / 40 knob" | **757 kr** = 101 € | [VERIFICADO: https://www.watski.dk/mekanisk-styring-11TiU] |
| Cable de dirección | **Ultraflex M66** | "større påhængsmotorer samt gear og rorstyring" | desde **735 kr** = 98 € | ídem |
| Volante | Osculati "Blødt rat i polyuretan", **Ø320**, eje universal Ultraflex/Morse/Teleflex | Bajo pedido | **549 kr** = 73 € | [VERIFICADO: https://www.watski.dk/search/?query=r%C3%A5t%20rat] |
| Palanca del bucket | Palanca de un cable 33C, con traba en la posición de avance (R10b H10) | — | ≈ 40–100 € [ESTIMADO] | Buscar: "Ultraflex single lever control B89 watski" |

**Recomendación:**
- Dirección: T85 + M66 + volante de 320 mm ≈ 2041 kr = **273 €**.
- Bucket: Mach5 de 8–10 ft (511–553 kr) + palanca con traba.
- Un manillar de PWC con un solo Mach5 también sirve y es más barato.
- La bisagra del bucket se dimensiona para 2 × 760 N (R10b H10).

---

## 8. Seguridad auxiliar

| Partida | Producto | Dato | Precio | Etiqueta |
|---|---|---|---|---|
| **Bomba de achique automática** | **Attwood Sahara S500 Mk2 12 V** | Automática, rodete X‑Air; 14 en stock | **649 kr** (antes 761) = 87 € | [VERIFICADO: https://www.watski.dk/attwood-sahara-mk2-automatisk-laensepumpe-11wl0] |
| Bomba (alt.) | Rule 360 12 V, sensor integrado | — | 791 kr = 106 € | [VERIFICADO: https://www.watski.dk/search/?query=niveauvagt] |
| Bomba (alt.) | Whale Supersub 650, sensor electrónico | — | 719 kr (−10 %) | ídem |
| **Alarma de nivel** | **KUS alarmboks** de nivel alto o bajo (acústica) | Tensión no publicada | **283 kr** = 38 € | [VERIFICADO: https://www.watski.dk/search/?query=h%C3%B8jvandsalarm] |
| 12 V para achique y alarma | Opción A: **batería LFP de 12 V separada**, p. ej. LiTime 12 V 50 Ah, 113,44 €. Así funciona aunque el cordón o el contactor corten el pack principal | — | 113,44 € | [VERIFICADO: https://www.litime.de/search/suggest.json?q=51.2V&resources[type]=product&resources[limit]=10] |
| | Opción B: DC‑DC Mean Well **RSD‑60H‑12** (40–160 V de entrada; sirve para 13S **y** 22–24S) | — | ≈ 32,72 £ sin IVA (Farnell UK) [ESTIMADO: buscador] | Buscar: "RSD-60H-12 reichelt" |
| **Espuma de flotación (~100 L, R10b H5)** | **TotalBoat PU 2 componentes, 2 lb/ft³**, "94% closed cell" | Kit de 2 gal → ~8 ft³ (0,227 m³). "Continuous water submersion can eventually lead to loss of buoyancy over a period of years" | 114,99 USD → **≈ 447 €/m³** (EE. UU., envío UE no publicado); 100 L ≈ 45 € | [VERIFICADO: https://www.totalboat.com/products/2-part-polyurethane-marine-flotation-foam] |
| Espuma en placa | **Divinycell H80** (PVC, 80 kg/m³), plancha de 1220 × 610 | 25 mm: 97,51 € = **131,77 €/m²** → **≈ 5271 €/m³**; 20 mm: 108,69 €/m² | 100 L ≈ 527 € | [VERIFICADO: https://www.r-g.de/en/art/5800H80] |
| Espuma barata | XPS de construcción (celda cerrada; sin combustible a bordo no hay problema de disolvente) | — | ≈ 1500–3000 DKK/m³ [ESTIMADO: no se abrió ninguna ficha con precio] | Buscar: "XPS isolering 50 mm pris jemogfix / bygma" |
| **Monitor de aislamiento (solo 72 V)** | Bender ISOMETER iso175C‑1 (IMD de vehículo eléctrico) | Mide 0–1000 V CC | **805 USD** = 709 € (EE. UU.) | [VERIFICADO: https://store.neweagle.net/shop/electric-hybrid/hv-accessories/bender-isometer-iso175c-1-insulation-monitoring-device-imd/]. IR155 ≈ 400–500 € [ESTIMADO: foro, buscador] |

Lo demás (kill switch con cordón, contactor SW80/SW80B, fusibles, cable, prensaestopas) ya está en R06 §3 y R08a §3–§8. Solo cambia esto para 72 V:
- contactor **SW80B** (96 V) [VERIFICADO en R06];
- **fusible ≥ 100 V CC**, porque MRBF, midiOTO y megaOTO (58–70 V, R08a §6) **no sirven** con 22–23S. Buscar: "Littelfuse CNN 125V" o "Class T fuse 125 VDC".

---

## 9. Tabla resumen: recomendado por partida

| # | Partida | Recomendado (≤ 50 V) | Recomendado (72 V) | Precio 2026‑10‑01 | Masa | Link | Etiqueta |
|---|---|---|---|---|---|---|---|
| 1 | Motor | **Maytech MTI120116 150 KV con hall**, refrigerado por agua, Ø15 con chavetero, NTC10K de fábrica | — | 573 USD = **505 €** sin IVA (+2,7 % arancel NC 8501 32 + 25 % IVA DK + envío) | **4,4 kg** | https://maytech.cn/products/copy-of-maytech-fully-waterproof-mti120116-18-8kw-powerful-brushless-inrunner-motor-for-electric-surfboard-rc-boat-jetski | [VERIFICADO]; continua [ESTIMADO] |
| 1 | Motor | — | **Golden Motor HPM5000L** con bobinado de ≈ 72 rpm/V a pedido | 545 USD = **480 €** sin IVA | **11,35 kg** | https://www.goldenmotor.com/frame-bldcmotor.htm | [VERIFICADO]; bobinado [SUPUESTO] |
| 1 | Motor (alt. 72 V) | — | Motenergy ME1304 | **961,20 €** sin IVA, sin stock | 16 kg | https://www.evea-solutions.com/en/synchronous-motors/674-me1304-pmsm-brushless-motor.html | [VERIFICADO] |
| 2 | ESC | **Flipsky FSESC 75350 + caja de agua** | — | 210 USD = **185 €** | 2,0 kg | https://flipsky.net/products/flipsky-fsesc-75350-84v-high-current-350a-esc-base-on-vesc-with-aluminum-case-water-cooling-enclosure-for-e-foil-fighting-robot-surfboard-agv-robot | [VERIFICADO] |
| 2 | ESC | — | **Flipsky FSESC 110300** | 219 USD = **193 €** | 1,2 kg | https://flipsky.net/products/flipsky-fsesc-110300-high-voltage-110v-300a-with-aluminum-pcb-based-on-vesc-for-fighting-robot-surfboard-agv-robot | [VERIFICADO] |
| 3 | Batería | **2 × LiTime 36 V 60 Ah** en paralelo (12S, 4,6 kWh, 240 A) | — | **939,98 €** con IVA, envío gratis | ≈ 40 kg | https://www.litime.de/products/36v-60ah-golfwagen-kart-lithium-batterie | Precio [VERIFICADO]; masa [ESTIMADO] |
| 3 | Batería | — | **DIY 23S EVE LF50K + JK B2A24S20P** (3,68 kWh) | 805 + 172 = **977 €** + caja | ≈ 35 kg | https://www.voltacell.nl/products/eve-lf50k-lifepo4-battery-cell-3-2v-50ah-a-grade-m4-thread · https://offgridpower.solutions/shop/jkbms-b2a24s20p-lifepo4-battery-bms | [VERIFICADO]; stock insuficiente |
| 3 | Cargador | LiTime 36 V 15 A IP66 (R08a) | 84 V regulable 10–20 A (AliExpress) | 132,99 € / 84,00 € | — | R08a §5 · https://www.aliexpress.com/w/wholesale-87.6v-lifepo4-charger.html | [VERIFICADO] |
| 4 | Bomba completa ("comprar") | **AWT JT132** (Ø130, dirección y reversa incluidas) | ídem | ≈ 1000–1100 USD = **881–969 €** FOB | **12 kg** | https://www.wuxiawt.com/JT132-pd574514898.html | Specs [VERIFICADO]; precio [ESTIMADO] |
| 5 | Sello | ST‑MG1 Ø20 (pedir carbón/SiC) | ídem | desde **29 €** | < 0,1 kg | https://st-shop24.de/dichtungen/gleitringdichtungen/mechanical-seal-st-st1-sic-sic-nbr-gleitringdichtung-inkl-gegenring.html | [VERIFICADO] |
| 5 | Rodamiento fijo | 3204‑2RS (Dold) | ídem | **6,20 €** | 0,15 kg [ESTIMADO] | https://www.dold-mechatronik.de/Double-row-angular-contact-ball-bearings-3204-5204-2RS-20x47x206mm | [VERIFICADO] |
| 5 | Acople | **Rotex 24** (estrella de 98 ShA para 60 N·m) | ídem | **67,47 €** + agujereado | ≈ 0,6 kg [ESTIMADO] | https://www.z24.de/a/40157-kupplungen-rotex/660005 | [VERIFICADO] |
| 5 | Eje | 1.4404 Ø20 h9, 1 m | ídem | **32,87 €** | 2,47 kg/m | https://www.hoerr-edelstahl.de/Edelstahlrohre-und-Edelstahlprofile/Rundstahl-4-bis-60-mm-V2A-Vollmaterial/Rundstahl-20-mm-Rundstab-Vollmaterial-V4A-1-4404-Edelstahl-1-m-100-cm-1000-20-mm-matt-1-4404-V4A-1-m-100-cm-1000-mm.html | [VERIFICADO] |
| 6 | Impulsor ("construir") | SLM 316L + torneado | ídem | **≈ 330–610 €** | 0,8–1,3 kg | https://jlc3dp.com/help/article/316l-stainless-steel | [ESTIMADO] |
| 7 | Dirección | Ultraflex T85 + M66 + volante Osculati Ø320 | ídem | 757 + 735 + 549 kr = **273 €** | ≈ 4 kg [ESTIMADO] | https://www.watski.dk/mekanisk-styring-11TiU | [VERIFICADO] |
| 7 | Bucket | Ultraflex Mach5 de 10 ft + palanca | ídem | 553 kr = **74 €** + palanca [ESTIMADO] | — | https://www.watski.dk/kontrolkabel-mach-5-ultraflex-11Jgp | [VERIFICADO] |
| 8 | Achique + alarma | Attwood Sahara S500 + KUS | ídem | 649 + 283 kr = **125 €** | ≈ 0,6 kg [ESTIMADO] | https://www.watski.dk/attwood-sahara-mk2-automatisk-laensepumpe-11wl0 | [VERIFICADO] |
| 8 | Flotación 100 L | PU de 2 componentes, 2 lb | ídem | **≈ 45 €** (EE. UU.) | ≈ 3,2 kg [CALCULADO: 32 kg/m³] | https://www.totalboat.com/products/2-part-polyurethane-marine-flotation-foam | [VERIFICADO] |
| 8 | IMD | No hace falta [ESTIMADO] | Bender iso175C‑1 | **709 €** | — | https://store.neweagle.net/shop/electric-hybrid/hv-accessories/bender-isometer-iso175c-1-insulation-monitoring-device-imd/ | [VERIFICADO] |

**Subtotal orientativo** (motor + ESC + batería + cargador, sin IVA de importación ni envíos CN) [CALCULADO]:
- ≤ 50 V: 473 + 185 + 940 + 133 ≈ **1730 €**; con IVA DK sobre lo chino ≈ **1900 €**.
- 72 V: 480 + 193 + 977 + 84 + 709 (IMD) ≈ **2440 €**.

**72 V suma ≈ +700 €**, sobre todo por el IMD, sin ganar nada en la batería.

---

## 10. Advertencias

1. **Tensiones de catálogo engañosas.**
   - "48 V" en LFP es 15S (54,8 V) o 16S (51,2 nominal / 58,4 V cargada). Ambas superan los 50 V de R06.
   - "2 × 24 V" = 16S, igual problema.
   - "72 V" LFP es 22S (80,3 V), 23S (84,0 V) o 24S (87,6 V): los ESC de 85 V (Spintend) no admiten 23–24S.
   - akkushop‑24 vende "72V" como 23S **y** 24S según la variante.
2. **El rpm/V de los HPM5000 de catálogo no da 4500 rpm con el Ø108.** Con 13S o 22S el conjunto entrega 2,2–3,1 kW (§1.3).
   - "2000–6000 rpm customizable" obliga a especificar el bobinado al pedir.
   - Sin eso, conviene un impulsor más grande o de más paso, como el Ø130 del JT132.
3. **Sin stock:**
   - HPM5000B 48 y 72 V y HPM5000L en Kelly EU ("Out of stock, inquire!");
   - ME1304 (EVEA, 3–6 semanas);
   - KLS7230H;
   - Spintend 100/100 ("Sold Out");
   - Maytech 65162 ("Sold out") y MTWJ10KW;
   - LiTime 51,2 V 100 Ah;
   - JK BMS en el almacén UE;
   - EVE LF50K en Voltacell ("Only 6 products left"; hacen falta 23–26);
   - Monster Scooter Parts ("backordered", solo envía dentro de EE. UU.).
4. **Motores sin NTC o con sensor no estándar.**
   - FS65161 sin sensor en la versión base (+3 USD con sensor).
   - Maytech 85165 sin sensor de temperatura declarado. (El MTI120116 **sí** trae NTC10K 3950: corregido 2026-10-02.)
   - HPM5000 y ME1304 traen **KTY84‑130**, no NTC 10 k: configurarlo en el VESC (o en Kelly) y verificar que el firmware lo lee.
   - ME1304 usa **encoder sin/cos**, no hall.
5. **El eje del HPM5000 no está bien publicado.** Kelly da 22,3 mm y chavetero de 5 mm; Monster da 7/8" (22,2 mm) y chavetero de 5/16" (7,9 mm). **Medirlo** antes de agujerear el cubo del Rotex.
6. **El Flipsky FSESC 75200 no tiene filtro de fase.** Hay que desactivarlo en FW ≥ 5.3 o el ESC se daña (R06 §2.1). El 75350 y el 110300 sí lo tienen.
7. **Firmware no VESC.**
   - Kelly, Fardriver y Votol no corren el firmware ni los límites de R06.
   - **Flipsky FT110BS** se vende "based on VESC" pero usa "Flipsky ESC Tool", FW V1.6.
   - Spintend 85/xxx anula la garantía si se carga el firmware VESC sin límites.
8. **Fusibles y contactores de R08a no sirven a 72 V:** MRBF 58 V, midiOTO 58 V, megaOTO 70 V. Hace falta un fusible ≥ 100 V CC y el SW80B.
9. **QS138 V3 tiene reducción interna de 1:2,35:** no sirve para el acople directo a 4500 rpm.
10. **JT132:**
    - precio solo del buscador;
    - el comprador paga flete, IVA y arancel;
    - "max 3 m / 0,5 t" por unidad: el casco de Jorge (2,3 m, 0,2 t) entra;
    - su toma y la altura de su eje deciden el cebado (R10a). Pedir el plano **antes** de comprar.
11. **Repuestos de Sea‑Doo, Solas y Minijet desde Canadá, EE. UU. o Reino Unido:** aduana, IVA del 25 % y tiempos de envío. No hay tienda UE verificada (BRP Shop, Riva y eBay dieron 403).
12. **Espuma PU:** "loss of buoyancy over a period of years" con inmersión continua (TotalBoat). Revisarla y no dejarla en la sentina.
13. **Rodamientos "inox" AISI 420:** se corroen en agua salada (R06 §1.3). Van del lado seco y se tratan como consumibles.

---

## 11. Fuentes abiertas en esta sesión (WebFetch, 2026‑10‑01)

**Motores:**
- goldenmotor.com/frame-bldcmotor.htm
- goldenmotor.com/eCar/HPM48-5000.pdf · HPM72-5000.pdf (ensayos dinámicos, leídos con pdftotext)
- kellycontrollers.eu: hpm5000b-5kw-72v-leghuteses · hpm5000b-5kw-48v-leghuteses · hpm5000l-5kw-48v-vizhuteses · kls7230h · kls7230s
- monsterscooterparts.com (HPM 48 V)
- goldenmotorcz.en.made-in-china.com (HPM5000B 48 V 4000 rpm)
- vesc-project.com/node/3376
- evea-solutions.com (ME1304)
- gritshift.com (QS138 V3) · qsmotor.com (4000 W, ND72450, EM‑150)

**Flipsky:**
- suggest.json para 65161, 75200, 75350, 65220 y 100V
- productos: 65161 · E‑Jet 3000 · FSESC 75200 con agua · 75200 Pro V2.0 · 75350 · 110300 · FT110BS · kit W7

**Maytech:**
- suggest.json para 65161, water cooled, 85165 y jet pump
- productos: MTI65162 · MTI120116 · MTI85165 · MTWJ10KW · MTWJ12KW

**Otros ESC:**
- Spintend: colección, 100/100, 85/250 V2, 85/240
- makerx-tech.com (G300, sin datos útiles)
- trampaboards.com (sin precio) · trampa.co.uk (overview)

**Baterías:**
- litime.de: suggest 36V, 48V, 51.2V y golf; .js de 36V 60Ah, 24V 100Ah y 51,2V 100Ah
- ipowerqueen.de: suggest 36V y 48V; .js de 24V 100Ah
- voltacell.nl (LF50K) · thebatteryshop.eu (LF105) · battery-germany.de (hoja LF50K)
- akkushop-24.de · offgridpower.solutions · hakadibattery.com
- AliExpress: 87.6v y 47.45v

**Waterjets:**
- wuxiawt.com (JT132) · wxaoweite.en.made-in-china.com (sin datos)
- minijet.ca (categoría pump y anillo de Spark) · jetseahub.com · pwcmuscle.com (2 páginas)
- ma-3d.com · jet-drive.com · axamarine.com/otherproducts · topjetsurfing.com/accessories · marinespares.com (impulsor ES 120 de EVAC, de bomba de vacío: no aplica)

**Tren de la bomba:**
- st-shop24.de (2 páginas)
- dold-mechatronik.de (3204, SS‑UCFL204, 5083 de 8 mm en 80 y 160 de ancho, categoría de acoples)
- z24.de (3204, Rotex 24)
- kugellagershop-duesseldorf.de · klium.com
- KTR Rotex (ach.nu, PDF) · Lovejoy (PDF)
- hoerr-edelstahl.de · metallstore.de · evek.top · gemmel-metalle.de · tefa24.de (datos inconsistentes, no usados)

**Impulsor:** jlc3dp.com (316L) · unionfab.com

**Auxiliares:**
- Watski: Mach5, mekanisk styring, volantes, Sahara (búsqueda y producto), højvandsalarm, niveauvagt, skum
- r-g.de (Divinycell) · totalboat.com · bauhaus.dk (XPS de 7 mm, no aplica) · jemogfix.dk (sin precio)
- store.neweagle.net (Bender)

**Tipo de cambio:** ecb.europa.eu (eurofxref-daily)

**No accesibles (403/404/503/captcha):**
- kit-elec-shop.com · goldenmotor.bike · fastride.fr · tradewheel.com · okchem.com
- sea-doo-shop.brp.com · rivaracing.com · ebay.co.uk
- nkon.nl · Biltema (API typeahead y producto) · hfmarine.dk (Anubis) · meanwell-web.com
- alibaba.com (página vacía) · jet-drive.com/shop (404)

**Solo del buscador (marcados [ESTIMADO]):**
- precio del JT132;
- masa y medidas de LiTime 36 V 60 Ah;
- precio de Fardriver y de JK directo;
- €/m de Dold 5083;
- precio del RSD‑60H‑12;
- MA‑3D 120 mm;
- quiebra de Radinn;
- precio de CNC 5 ejes.
