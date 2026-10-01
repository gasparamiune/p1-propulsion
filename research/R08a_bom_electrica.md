# R08a — Sourcing BOM eléctrica con envío a Dinamarca

Proyecto P1 (cola larga eléctrica, jon boat < 2,5 m, Als Fjord). **Fecha de consulta de todos los precios: 2026-10-01.**
Etiquetas: **[VERIFICADO: url]** = página abierta en esta sesión y el dato está ahí · **[ESTIMADO: base]** · **[SUPUESTO]** · "buscar: …" = no se pudo abrir.
Complementa R06 (arquitectura eléctrica y seguridad); acá solo producto, tienda, precio y lo que el producto concreto cambia en el diseño.

---

## 0. Bases de compra (impuestos, cambio, logística)

| Dato | Valor | Fuente |
|---|---|---|
| Cambio BCE 2026-09-30 | 1 EUR = **1,1355 USD** = **7,4755 DKK** = 0,85463 GBP → 1 USD = 0,8807 EUR = 6,58 DKK | [VERIFICADO: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml] (el XML diario ya muestra 2026-10-01: 1,1298 USD / 7,4758 DKK; diferencia < 0,5 %, no cambia totales) |
| IVA DK | Reichelt DK muestra precios *"incl. 25% VAT"* | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/dc_dc_converter_r78hb_9-72_vin_single_5_vout_500_ma_sip-3-159167] |
| Compras fuera de la UE | *"If you buy goods online from outside the EU, VAT, customs and excise duty is always due."* | [VERIFICADO: https://europa.eu/youreurope/citizens/consumers/shopping/vat/index_en.htm] |
| Flipsky (CN) | *"The product price and shipping cost do not include tariffs"*; DHL 5–9 días, correo/4PX 7–25 días; despacho 3–7 días hábiles. (La página *about-tariffs* ofrece *"We can declare a low price according to your requirements"*: **no hacerlo**, es fraude aduanero.) Ni Flipsky ni este archivo incluyen el **arancel aduanero** (además del IVA) ni la tasa de despacho del courier → buscar: "TARIC 8501 32 duty rate" [ESTIMADO: ~2–3 % sobre el motor, memoria técnica, no verificado]. | [VERIFICADO: https://flipsky.net/pages/faqs] · [VERIFICADO: https://flipsky.net/pages/about-tariffs] |
| Flipsky costo de envío | No publicado (*"ship in 2-3 working days"* y nada más) → buscar: "Flipsky DHL shipping cost Denmark checkout"; uso **45 EUR** [ESTIMADO: memoria técnica, no verificado] | [VERIFICADO: https://flipsky.net/policies/shipping-policy] |
| Maytech (CN) | *"Shipping time by DHL or UPS is fast, normally 3-7 days"*; sin stock: 30–40 días | [VERIFICADO: https://maytech.cn/products/brushless-hall-sensor-motor-mto6374-170-ha-c] |
| LiTime DE | *"Kostenloser Versand für alle Bestellungen in die EU"* (excepto Chipre, Malta, Irlanda, islas pequeñas); *"Alle unsere Produkte werden aus dem deutschen Lager versandt"*; 1–2 + 2–7 días hábiles | [VERIFICADO: https://www.litime.de/policies/shipping-policy] |
| Power Queen DE | Envío *"kostenlos innerhalb der gesamten EU (außer Griechenland und Inseln)"*, 3–7 días hábiles a otros países UE | [VERIFICADO: https://www.ipowerqueen.de/products/power-queen-lifepo4-24v-50ah-smart-niedertemperatur-trolling-motor-batterie] |
| Variantes "0 % MwSt." en LiTime/Power Queen | Solo aplican a Alemania (tasa 0 % FV); para DK usar el precio normal con IVA | [VERIFICADO: páginas LiTime/PowerQueen arriba] |
| AliExpress (fallback) | Precios mostrados en EUR con región DK; IVA UE cobrado en checkout [ESTIMADO: régimen IOSS ≤ 150 EUR, no verificado en la página] | [VERIFICADO: búsquedas aliexpress.com citadas abajo] |
| No accesibles en esta sesión | hobbyking.com (403), svb24.com/svb.de (403), conrad.de (403), amazon.de (503), makerbase3d.com (captcha), flipsky.eu (sin respuesta) | — |

---

## 1. Motor BLDC outrunner (seco, sobre el agua)

| Modelo | KV | P máx | I máx | Eje | Peso | Tensión | Precio (2026-10-01) | Fuente |
|---|---|---|---|---|---|---|---|---|
| **Flipsky 6374 Battle Hardened** (hall: [NO VERIFICADO: la página de flipsky.net no menciona sensor/hall; solo revendedores de AliExpress dicen "Sensored"]) | 140/170/190 | 3500 W; 8 Nm | 85 A | 8 mm redondo o 10 mm D (108 mm / 99 mm = largo de los planos, no del eje) | **0,98 kg** | 3–12S | **87 USD** s/polea (93 con polea) = 76,6 EUR | [VERIFICADO: https://flipsky.net/products/flipsky-bldc-belt-motor-battle-hardened-6374-140kv-170kv-190kv-3500w-for-electric-skateboard] |
| Flipsky 6384 Battle Hardened | 140/170/190 | 4000 W, 9 Nm | 95 A | 8 mm (30 mm) / 10 mm / 10 mm D | 1,3 kg | 4–14S; R 0,05 Ω; 14 polos; imán N42SH | 113 USD s/polea = 99,5 EUR | [VERIFICADO: https://flipsky.net/products/flipsky-bldc-belt-motor-battle-hardened-6384-140kv-170kv-190kv-4000w-for-electric-skateboard] |
| Flipsky 7070 Battle Hardened | 110/140/170 | 2200 W nominal / 4200 W | 100 A | 10 mm redondo o D | 1,08 kg | 6–18S; **cable TEMP incluido** (blanco) | 101 USD s/polea = 89,0 EUR | [VERIFICADO: https://flipsky.net/products/flipsky-sensored-outrunner-brushless-dc-motor-battle-hardened-7070-110kv-140kv-170kv-4200w] |
| Maytech MTO6374-170-HA-C (sealed "splashproof", hall) | 170/190 (110 a pedido 94,5 USD) | 3550 W | 65 A (60 A nominal) | 8 mm × 26 mm | buscar: "MTO6374-HA-C weight" | 3–12S (12–50 V) | 82,40 USD = 72,6 EUR | [VERIFICADO: https://maytech.cn/products/brushless-hall-sensor-motor-mto6374-170-ha-c] |
| Maytech MTO6374-G (sensorless) | 90/170/200/330 | 3550 W | 65 A | 8 mm | **785 g**; R 0,0402 Ω | 2–12S | 86,80 USD (90 KV: 100,90 USD) | [VERIFICADO: https://maytech.cn/products/brushless-sensorless-motor-mto6374-190-g] |
| Fallback UE: Flipsky 6374 140KV en AliExpress | 140 | 3500 W | — | — | — | — | **94,69 EUR** (item 4000966919617, 66 vendidos) | [VERIFICADO: https://www.aliexpress.com/w/wholesale-flipsky-6374-motor.html] |
| *(agregado en verificación)* Flipsky 6374 **Waterproof** 140KV "for Surfing Boat Underwater Thruster" (AliExpress) | 140 | 3600 W (título) | — | — | — | — | 111,69 EUR (94 vendidos); otras ofertas 129,69–131,39 | [VERIFICADO: https://www.aliexpress.com/w/wholesale-flipsky-6374-motor.html] — specs no abiertas |
| *(agregado en verificación)* Flipsky Waterproof 6384 140KV 4400W (flipsky.net) | 140 | 4400 W (título) | — | — | — | — | 136 USD | [VERIFICADO listado: https://flipsky.net/search/suggest.json?q=6384&resources[type]=product&resources[limit]=10] — specs no abiertas |

Notas: (a) Flipsky vende como repuesto *"3pcs 10x19x5mm NMB Japan Steel Deep Groove Ball Bearing 6800zz/6900zz for flipsky 63 series motor"* a 4,50 USD; que sean los rodamientos **de serie** es inferencia [ESTIMADO: inferido del repuesto, no dicho en la ficha del motor] → cambiar a inox/híbrido según R06 [VERIFICADO listado/precio: https://flipsky.net/search/suggest.json?q=6384&resources[type]=product&resources[limit]=10]. (b) No hay fuente UE de motores 63xx–70xx con link abierto (HobbyKing EU 403) → buscar: "Turnigy SK8 6374 149KV EU warehouse".

---

## 2. ESC VESC 75 V / 100 A

| Modelo | V | I cont./pico | BEC | Cables | FW / advertencia | Tamaño | Precio | Fuente |
|---|---|---|---|---|---|---|---|---|
| **Flipsky 75100 V2.0** (botón o llave) | 14–84 V (4–20S) | 100 A / 250 A | **5 V @ 1 A** | 12 AWG | FW 5.02; *"Phase filter needs to be turned off for firmware 5.03 or newer"*; entradas PPM, ADC, NRF, UART | 103×58×24 mm | **88 USD** (botón) / 92 USD (llave) | [VERIFICADO: https://flipsky.net/products/flipsky-75100-v2-0-with-aluminum-pcb-with-power-key-switch-button-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller] |
| Flipsky 75100 Pro | 14–84 V | 100 A / ráfaga 120 A | 5 V @ 1,5 A | **10 AWG** | *"Phase filering is not available… turn off the phase filter"*; Bluetooth integrado | 103×58×27,7 mm | 89 USD | [VERIFICADO: https://flipsky.net/products/flipsky-75100-pro-with-aluminum-pcb-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller] |
| Flipsky 75100 Pro V2.0 | — | — | — | — | — | — | 98 USD | [VERIFICADO: https://flipsky.net/search/suggest.json?q=75100%20pro&resources[type]=product&resources[limit]=10] (listado; la URL original con q=thumb throttle no corresponde) |
| *(agregado en verificación)* **Flipsky 75100 With Aluminum PCB** | 14–84 V (4–20S) | 100 A / ráfaga 120 A | **5 V @ 1,5 A** | 12 AWG | phase filter: desactivar; PPM, ADC, NRF, UART | 103×58×18,5 mm (+5,9 USB) | **73 USD** sin caja / 77 caja alu / 106 caja refrigerada por agua | [VERIFICADO: https://flipsky.net/products/flipsky-75100-with-aluminum-pcb-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller] |
| *(agregado en verificación)* Flipsky 75100 75V 100A Single | 14–84 V | 100 A / 120 A | 5 V @ 1 A | 12 AWG | PPM, ADC, NRF, UART; limitar corriente absoluta < 200 A | 85×50,7×33,8 mm | **65 USD** | [VERIFICADO: https://flipsky.net/products/flipsky-75100-75v-100a-single-esc-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller] |
| Makerbase VESC 75100 (AliExpress) | 75 V | 100 A | — | — | — | — | 63,99–65,69 EUR; V2 alu-PCB 122,69 EUR | [VERIFICADO: https://www.aliexpress.com/w/wholesale-makerbase-vesc-75100.html] |
| Flipsky 75100 en AliExpress | — | — | — | — | — | — | ~~59,99 EUR ("Flash deal", 486 vendidos)~~ [NO VERIFICADO: no aparece en la re-consulta; el Flipsky 75100 single más barato hoy es 89,39 EUR; un clon "HOEYI 75100" 62,39 EUR/388 vendidos] / V2.0 114,39 EUR (93 vendidos) | [VERIFICADO: https://www.aliexpress.com/w/wholesale-flipsky-75100.html] |

Reino Unido (escooter-parts.co.uk: 75100 V2.0 127,99 GBP) = fuera de UE → IVA de importación otra vez; no conviene [VERIFICADO precio: https://escooter-parts.co.uk/search/suggest.json?q=75100&resources[type]=product&resources[limit]=10].

---

## 3. Corte de energía: antichispa, contactor, kill switch, desconectador

| Ítem | Producto | Dato clave | Precio | Fuente |
|---|---|---|---|---|
| Antichispa | Flipsky Antispark Switch Pro V3.0 | 3–14S (12–60 V); 100 A cont. con alu PCB/caja, 60 A con disipador; LED 16 mm; *"DO NOT power on switch without the LED button connected"* | 33 USD (disipador) / 43 (alu PCB) / **48 USD (caja alu)** | [VERIFICADO: https://flipsky.net/products/flipsky-antispark-switch-pro-with-aluminum-pcb-case-200a-for-electric-skateboard-ebike-scooter-robots] |
| Antichispa (UE fallback) | Flipsky Antispark Pro V3.0 en AliExpress | — | 33,99 EUR | [VERIFICADO: https://www.aliexpress.com/w/wholesale-flipsky-antispark-switch.html] |
| Llave manual barata | Amass **XT90-S** (par) | resistencia integrada de precarga; 45 A cont. / 90 A corto | 3,69 EUR | [VERIFICADO: https://www.rotorama.com/product/xt90s-antispark-konektor-par] |
| **Kill switch cordón (fail-safe)** | Watski "Dødmands kontakt universal" (SKU 203517) | *"M-polerne har gennemgang når sikkerhedskontakten er isat"* (cerrado con clip = fail-safe); polos C cerrados sin clip; **12 V – 15 A** | **74 DKK** | [VERIFICADO: https://www.watski.dk/Ddmands-kontakt-universal-110CP] |
| Kill switch alternativo | Osculati "Nødstopafbryder + sikkerhedsnøgle" | *"kan åbne og lukke kredsløbet afhængigt af tilsluttede terminaler"*; rating no publicado | 129 DKK (bestillingsvare) | [VERIFICADO: https://www.watski.dk/nodstopafbryder-sikkerhedsnogle-1b1Vj] |
| Kill switch con flotador | Osculati con llave y flotador | idem, flotante | 139 DKK | [VERIFICADO: https://www.watski.dk/nodstopafbryder-med-sikkerhedsnoegle-og-flyder-1b1Vp] |
| Solo cordón (sin interruptor) | Biltema Dødemandsgreb 135 cm | espiral 135 cm; *"af sluttende type til udenbordsmotorer"* | 74,90 DKK | [VERIFICADO: https://www.biltema.dk/baad/sikkerhedsudstyr/redningsliner/dodemandsgreb-135-cm-2000040861] |
| Contactor DC servicio continuo | Albright SW80 (recomendado en R06) | — | buscar: "Albright SW80 24V coil price EU"; [ESTIMADO: 60–100 EUR, memoria técnica] | — |
| Relé de bajo costo (NO es contactor) | FREI FRC3 A 24 (Reichelt) | bobina 24 V DC, **320 Ω** (→ 75 mA [ESTIMADO: 24 V/320 Ω]); AgSnO2; *"Max. switching voltage: 75 VDC – Max switching current: 70 A"* pero *"Contacts: 1 NOC, **40 A**"*; Faston 6,35/9,5 mm (no admite 16 mm² directo); tipo de carga/vida de corte DC no publicados | 3,26 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/70a_high-current_relay_frc3_24_v_1_n_o_contact-79404] |
| Descartado | Zettler AZ160-1AE-24D | relé de PCB, 60 A, 480 V **AC**; corte DC no especificado | 3,73 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/high-current_relay_1x_no_60_a_24_v_dc-415707] |
| Descartado | Lewmar kontaktor ensrettet 24 V | contactor de molinete/cabrestante (servicio intermitente [ESTIMADO: uso típico de molinete]) | 669 DKK | [VERIFICADO: https://www.watski.dk/kontakt-enkelt-1224V-116Ft] |
| **Desconectador de batería** | Biltema Hovedafbryder AFD ON/OFF (art. 25-8849) | **12–48 V DC**; 275 A cont., 455 A 5 min, 1250 A 10 s; M10; IP65; bornes de cobre estañado; llave removible | **159 DKK** | [VERIFICADO: https://www.biltema.dk/baad/eludstyr/elinstallationer-til-bade/stromafbrydere/hovedafbryder-afd-onoff-2000063980] |
| Desconectador alt. | 1852 hovedafbryder 275 A 12–48 V | Ø 52 mm de montaje | 180 DKK | [VERIFICADO: https://www.watski.dk/1852-hovedafbryder-275Amp-12-48-vdc-11ECI] |
| Desconectador alt. | Blue Sea hovedafbryder 300 A | 300 A cont., 500 A 5 min, 1500 A 10 s; **máx. 48 V** | 358 DKK | [VERIFICADO: https://www.watski.dk/blue-sea-hovedafbryder-300-ah-11Eiy] |
| Desconectador alt. | Compass24 "Hovedafbryder til batteri 275 A" | hasta 50 V; 275 A cont.; 1250 A máx. | 295 DKK | [VERIFICADO: https://www.compass24.dk/hovedafbryder-til-batteri-275-a-289021/275-5-6x5-6x7-4-1250] |

---

## 4. Batería LiFePO4 con BMS

| Producto | Config. | Energía | BMS cont. / pico | Peso | IP | Frío | Precio | €/kWh | Fuente |
|---|---|---|---|---|---|---|---|---|---|
| **LiTime 24V 50Ah TM Bluetooth** | 8S (25,6 V) | 1280 Wh | **50 A** / 250 A 1 s | 21,15 lb (9,6 kg) | IP65 | no carga < 0 °C, no descarga < −20 °C | **309,99 EUR** (envío gratis UE) | 242 | [VERIFICADO: https://www.litime.de/products/24v-50ah-bluetooth-lithium-batterie-fur-elektromotor-boote] · specs [VERIFICADO: https://www.litime.com/products/litime-24v-50ah-tm-bluetooth-lifepo4-battery] |
| Power Queen 24V 50Ah Smart | 25,6 V | 1280 Wh | 50 A; *"60A@30mins"*; carga máx. 50 A; 28,8 ± 0,4 V; R int. ≤ 40 mΩ; máx. 4P2S | buscar | IP65 | carga 0…50 °C (*"– 50°C / 32°F – 122°F"*); protección de baja T con **reanudación automática a 5 °C** (no corte a 5 °C); descarga −20…60 °C | 329,99 EUR (con cargador 29 V 20 A: 449,98) | 258 | [VERIFICADO: https://www.ipowerqueen.de/products/power-queen-lifepo4-24v-50ah-smart-niedertemperatur-trolling-motor-batterie] — 26,0×16,8×21,0 cm, bornes M8 |
| 2× LiTime 12V 50Ah TM | 2S → 25,6 V | 1280 Wh | 1,2C (60 A) 30 min c/u | 2 × ~5,1 kg (peso de envío 5110 g) | — | 0 °C / −20 °C | 2 × 189,99 = 379,98 EUR | 297 | [VERIFICADO: https://www.litime.de/products/12v-50ah-bluetooth-lithium-batterie-fur-elektromotor-boote-zuverlassige-power] (admite 4P4S) |
| 2× Power Queen 12V 50Ah | 2S | 1280 Wh | 50 A c/u | 2 × 5,29 kg | IP65 | — | pack-2 **316,78 EUR** | 247 | [VERIFICADO: https://www.ipowerqueen.de/products/power-queen-12v-50ah-lifepo4-batterie-eingebautes-50a-bms] — 19,5×16,6×17,2 cm |
| **2× Power Queen 12V 100Ah** | 2S | **2560 Wh** | **100 A** c/u | 2 × ~11 kg (peso de envío) | buscar | — | pack-2 **475,18 EUR** | **186** | [VERIFICADO: https://www.ipowerqueen.de/products/power-queen-12-v-100-ah-lifepo4-deep-cycle-batterie] (hasta 4P4S) |
| 2× LiTime 12V 100Ah TM | 2S | 2560 Wh | buscar | 2 × ~10 kg (envío 10050 g) | — | 0 °C / −20 °C | 2 × 259,99 = 519,98 EUR | 203 | [VERIFICADO: https://www.litime.de/products/12v-100ah-lifepo4-batterie-elektromotoren-tieftemperaturschutz-tm] |
| LiTime 36V 50Ah TM (12S, recomendado por R06) | 38,4 V | 1920 Wh | 50 A, 60 A 30 min | ~9,6 kg (envío) | — | — | 399,99 EUR | 208 | [VERIFICADO: https://www.litime.de/products/36v-50ah-bluetooth-lithium-batterie-group31-marine-trolling-motor] |
| Biltema | — | — | — | — | — | — | Solo LiFePO4 de arranque 2–3,5 Ah (399–549 DKK): **no sirve** | [VERIFICADO: https://find.biltema.com/v4/web/typeahead/400/da/?query=LiFePO4&take=12] |

Caja de batería: Biltema Batteriboks 340×200×245 mm interior, plástico antiácido con soporte y correa, **105 DKK** (entra la Power Queen 24 V 26,0×16,8×21,0 cm) [VERIFICADO: https://www.biltema.dk/baad/marinebatterier-og-tilbehor/batteribokse/batteriboks-340-x-200-x-245-mm-2000048673]. No declara IP → la estanqueidad la da la batería (IP65) + ubicación elevada.

---

## 5. Cargador

| Producto | Salida | Conexión | IP | Precio | Fuente |
|---|---|---|---|---|---|
| **Power Queen 29,2 V 20 A** | 29,2 V / 20 A, 100–240 VAC, ~1,3 kg | **Anderson 50 A** + terminales M8 | buscar | **102,99 EUR** | [VERIFICADO: https://www.ipowerqueen.de/products/power-queen-29-2v-20a-lifepo4-ladegerat] |
| LiTime 29,2 V 20 A | 29,2 V / 20 A | cable 145 cm con extensión Anderson 25 cm | — | 132,99 EUR | [VERIFICADO: https://www.litime.de/products/litime-29-2v-20a-lithium-batterieladegerat-fur-24v-lifepo4-lithium-batterie] |
| LiTime 36 V 15 A (para 12S) | 43,8 V / 15 A | — | IP66 | 132,99 EUR | [VERIFICADO: https://www.litime.de/products/litime-36v-15a-wasserdichtes-lithium-batterieladegerat] |
| LiTime 14,6 V 10 A (para 12 V individual) | 14,6 V / 10 A | M8 + Anderson 50 A | — | 65,99 EUR | [VERIFICADO: https://www.litime.de/products/litime-12v-10a-lithium-batterie-ladegerat-fur-12v-lifepo4-lithium-batterie] |
| AliExpress 29,2 V 10 A | 29,2 V / 10 A | — | — | 31,09 EUR (272 vendidos) | [VERIFICADO: https://www.aliexpress.com/w/wholesale-lifepo4-charger-29.2v-10a.html] |
| Biltema 12/24 V 15 A | 15,9 V máx.; 7,5 A en 24 V; "Batteritype" = *"AGM, GEL, WET, SMT, MF, LiFePO4 (12 V)"* y sin LiFePO4 en la otra línea → **no apto 24 V LFP** [VERIFICADO: tabla de propiedades de la misma página] | pinzas | IP20 | 459 DKK | [VERIFICADO: https://www.biltema.dk/bil---mc/bilbatterier/batteriladere/batterilader-1224-v-15-a-2000045787] |

---

## 6. Fusible principal y portafusibles

| Producto | Tipo | V máx. | Precio | Fuente |
|---|---|---|---|---|
| **Blue Sea MRBF (5191) 80 A** | terminal, sobre el borne | 58 V (portafusible) | **185 DKK** (60 A 195; 100 A 185) | [VERIFICADO: https://www.watski.dk/Blue-Sea-MRBF-Blok-Sikring-11cWn] |
| Portafusible Blue Sea MRBF terminal | 30–300 A, tornillo **M8** (= bornes M8 de LiTime/Power Queen) | **58 V DC** | **320 DKK** | [VERIFICADO: https://www.watski.dk/blue-sea-sikringsholder-terminal-max-300a-11wXO] |
| IMAXX midiOTO 80 A / 100 A | MIDI atornillable, M5; **poder de corte 1 kA** (80 A) | **58 V DC** | 2,52 / 2,31 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/auto_fuse_midioto_80a_58vdc_white-229133] · [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/auto_fuse_midioto_100a_58vdc_blue-229134] |
| IMAXX megaOTO HV 80/100 A | MEGA, agujeros M8 a 51 mm; *"switching capacity of 2500 A at 70 VDC"* | **70 V DC** | 3,14 EUR c/u (125 A no re-abierto) | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/automotive_fuse_megaoto_70_vdc_100_a-337908] · [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/automotive_fuse_megaoto_70_vdc_80_a-337907] |
| **Portafusible IMAXX HMD4-MG1-H** | 4× midiOTO (M5) + 1× megaOTO (M8); título "200 A, 58 V", tabla "70 Vdc / 500"; ***"Mounting on insulating base if the application voltage is between 32 and 70 V (e.g. HIB1)"*** | **58 V** (título) / 70 V (tabla) | **12,55 EUR** (+ base HIB1 si 12S: buscar "IMAXX HIB1 reichelt") | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/car_fuse_holder_hmd4-mg1-h_megaoto_midioto_200_a_58_v-407426] |
| Biltema ANL 100 A | ANL | fusible 80 V DC | 69,90 DKK | [VERIFICADO: https://www.biltema.dk/bil---mc/bilradio/bilradio-tilbehor/anl-sikring-100-a-2000058033] |
| Biltema portafusible ANL | 300 A, M10, LED | **32 V DC** | 109 DKK | [VERIFICADO: https://www.biltema.dk/bil---mc/bilradio/bilradio-tilbehor/sikringsholder-anl-2000058572] |
| Skyllermarks ANL 35–250 A | ANL M10, c-c 60 mm | no publicado | 80 DKK (casi todo sin stock) | [VERIFICADO: https://www.watski.dk/skyllermarks-sikring-anl-11Pgk] |
| TBS DCM portafusible ANL M8 300 A | ANL, M8, 600 A | **50 V** | 200 DKK | [VERIFICADO: https://www.watski.dk/dcm-anl-sikringsholder-m8-300a-11GXC] |
| Blue Sea AMI/MIDI 40–100 A + portafusible | MIDI | fusible **32 V DC**; portafusible 50 V DC, 200 A, M8 | 85 DKK + 425 DKK | [VERIFICADO: https://www.watski.dk/blue-sea-ami-midi-sikring-11cWH] · [VERIFICADO: https://www.watski.dk/sikringsholder-ami-midi-11ckP] |

---

## 7. Cable, terminales, herramientas

| Ítem | Producto | Precio | Fuente |
|---|---|---|---|
| **Cable marino estañado 16 mm²** | Skyllermarks gummikabel fortinnet, negro (se vende por dm) | **8 DKK/dm = 80 DKK/m** | [VERIFICADO: https://www.watski.dk/gummikabel-fortinnet-skyllermarks-11vPX] |
| Cable marino estañado 25 mm² | ídem | 11 DKK/dm = 110 DKK/m | ídem |
| Cable estañado rojo (dm) | Skyllermarks rojo, por dm | desde 6 DKK/dm | [VERIFICADO: https://www.watski.dk/search/?query=fortinnet%20kabel%2016] (listado) |
| Cable 16 mm² NO estañado (barato) | Biltema Batterikabel rød 16 mm², **6 m**, PVC, −40…+80 °C | 169 DKK (28 DKK/m) | [VERIFICADO: https://www.biltema.dk/bil---mc/bilbatterier/batteritilbehor/batterikabel-rod-16-mm2-2000054560] |
| Terminal estañado 16 mm² | Skyllermarks rørkabelsko 16 mm², ø6/ø8/ø10, pack 4 | 39 / **38** / 40 DKK | [VERIFICADO: https://www.watski.dk/roerkabelsko-25-95-mm-117N7] |
| Terminal estañado 25 mm² | Skyllermarks 25 mm² ø8 / ø10 (unidad) | 10 / 11 DKK | [VERIFICADO: https://www.watski.dk/roerkabelsko-25-mm-skyllermarks-11vIb] |
| Terminal cobre desnudo | Biltema rørkabelsko 16 mm² M10 / 25 mm² M10, 10 u. | 64,90 / 69,90 DKK | [VERIFICADO: https://www.biltema.dk/bil---mc/elsystem/kabelkoblinger/rorkabelsko-16-mm2-m10-10-stk-2000050964] · [VERIFICADO: https://www.biltema.dk/bil---mc/elsystem/kabelkoblinger/rorkabelsko-25-mm2-m10-10-stk-2000050965] |
| Termocontraíble con adhesivo | Biltema krympeflex 3:1, 76 u. (3,2–15 mm) | 145 DKK | [VERIFICADO: https://www.biltema.dk/bil---mc/elsystem/krympeslanger/krympeflex-sat-med-lim-76-stk-2000041559] |
| Crimpadora | Biltema kabelskotang de golpe, 8–70 mm² | 89,90 DKK | [VERIFICADO: https://www.biltema.dk/varktoj/handvarktoj/ovrigt-varktoj/kabelskotang-2000064951] |

---

## 8. Conectores y prensaestopas

| Ítem | Producto | Dato | Precio | Fuente |
|---|---|---|---|---|
| XT90 (par) | Jamara/HSTXT90 | 2 polos | 4,72 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/connector_for_li-polymer_batteries_2-pin_xt90-342799] |
| XT90-S (antichispa) | Amass | ver §3 | 3,69 EUR | [VERIFICADO: https://www.rotorama.com/product/xt90s-antispark-konektor-par] |
| AS150 | Amass AS150 macho/hembra 7 mm | solo AliExpress | 6,14 EUR (1000+ vendidos) | [VERIFICADO: https://www.aliexpress.com/w/wholesale-amass-as150.html] |
| **Anderson SB50 (gris)** [ESTIMADO: identificación como SB50 por medidas/color; la página dice "Anderson PP51S Grå" (Oceanflex) y no "SB50"] | "Anderson PP51S Grå 16 mm²" | cable hasta 16 mm²; **120 A**; 48×37×16 mm; se vende de a 1 (hacen falta 2) | **90 DKK c/u** | [VERIFICADO: https://www.watski.dk/anderson-pp51s-graa-16mm2-1st-11GKJ] |
| Anderson SB50 (fallback) | conjunto SB50 con cable | — | 7,91 EUR | [VERIFICADO: https://www.aliexpress.com/w/wholesale-anderson-sb50.html] |
| IP68 señal 4 polos | Lumberg 0332-04 macho + 0322-04 acoplador, apantallado | acelerador/hall | 7,34 + 7,51 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/plug_round_connector_ip_68_360_shielded_4-pin-116121] · [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/coupler_round_connector_ip_68_360_shielded_4-pin-116124] |
| IP68 señal 2 polos | Cliffcon 68 FM686812 | kill switch | 8,39 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/cliffcon_68_cable_connector_2_pin_ip68-230124] |
| **Prensaestopa M16 IP68** | Biltema 4–8 mm, 2 u. | −20…+80 °C | **24,90 DKK** | [VERIFICADO: https://www.biltema.dk/byggeri/elinstallationer/eldaser/kabelforskruning-m16-4-8-mm-2-stk-2000064967] |
| **Prensaestopa M20 IP68** | Biltema 6–12 mm, 2 u. | ídem | **24,90 DKK** | [VERIFICADO: https://www.biltema.dk/byggeri/elinstallationer/eldaser/kabelforskruning-m20-6-12-mm-2-stk-2000064968] |
| Prensaestopa M16 IP68 (alt.) | Delock 60615, 2 u. | — | 5,04 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/m16_cable_gland_black_ip68_2_pieces-375251] |

---

## 9. Control: acelerador, sensor hall, MCU, DC-DC

| Ítem | Producto | Dato | Precio | Fuente |
|---|---|---|---|---|
| Acelerador de pulgar (hall [NO VERIFICADO: la página no dice "hall"]) | Ebikeling thumb throttle, conector Julet 3 pines estanco, 24–52 V | salida no publicada | 24,99 USD | [VERIFICADO: https://www.ebikeling.com/products/thumb-waterproof-throttle-for-24v-36v-48v-electric-bicycle] |
| Acelerador (fallback UE) | AliExpress, pulgar 24–72 V | — | 9,49 EUR (348 vendidos); otros 4,52–6,39 EUR | [VERIFICADO: https://www.aliexpress.com/w/wholesale-thumb-throttle-ebike-hall.html] |
| Sensor hall lineal | **Allegro A1324 LUA-T** SIP-3 | −40…+150 °C | **1,68 EUR** | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/low_noise_linear_sensor_sip-3-189140] |
| Sensor hall lineal | SS49E/OH49E, 10 u. | — | 0,73 EUR (280 vendidos) | [VERIFICADO: https://www.aliexpress.com/w/wholesale-ss49e.html] |
| MCU | Arduino Nano V3 (original) | ATmega328 | 20,69 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/arduino_nano_v3_atmega_328_mini_usb-142943] |
| MCU | **ESP32-WROOM-32E DevKitC** (Espressif) | WiFi/BLE | **11,55 EUR** | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/esp32-wroom-32e_development_board-341303] |
| DC-DC (sistema 24 V) | TRACO TSR 1-2450E | **7–36 V** → 5 V 1 A, SIP-3 | 4,19 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/dc_dc_converter_tsr_1e_1_a_7-36_5_0_vdc_sip-3-288648] |
| DC-DC (sistema 36 V) | RECOM R-78HB5.0-0.5 | **9–72 V** → 5 V 0,5 A | 17,12 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/dc_dc_converter_r78hb_9-72_vin_single_5_vout_500_ma_sip-3-159167] |
| DC-DC 24→12 V (accesorios) | Biltema 24/12 V-omformer | 20–30 V in, 12–13,8 V out, 10 A | 219 DKK | [VERIFICADO: https://www.biltema.dk/bil---mc/elsystem/kontakter-og-udtag/2412-v-omformer-2000033704] |

---

## 10. Cajas para electrónica

| Producto | Medidas | IP | Precio | Fuente |
|---|---|---|---|---|
| **BOX4U 4U63181306019** | 177×126×56 mm | **IP67** | **14,65 EUR** | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/industrial_housing_177_x_126_x_56_mm_ip67_light_gray-324319] |
| BOX4U 5U320300 | 200×150×75 mm | IP65 | 18,07 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/industrial_housing_200_x_150_x_75_mm_ip65_light_gray-324383] |
| BOX4U hand-held | 185×145×39 mm | IP67 | 12,92 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/hand-held_enclosure_185_x_145_x_39_mm_ip67_black-324286] |
| Biltema standardkapsling 8 módulos (DIN) | 155×201×90 mm | IP65 | 99,90 DKK | [VERIFICADO: https://www.biltema.dk/byggeri/elinstallationer/standardcentral/standardkapsling-8-moduler-ip65-2000068548] |
| Biltema "Vandtæt og stødsikker boks" | 186×120×44 mm | sin IP declarado | 89,90 DKK | [VERIFICADO: https://www.biltema.dk/fritid/rejse/rejsetilbehor/vandtat-og-stodsikker-boks-2000032621] |

Encaje: VESC 75100 Pro 103×58×27,7 mm + antichispa caja alu 83,9×45×17 mm [VERIFICADO: páginas Flipsky §2–3] entran lado a lado en 177×126×56 mm (interior ≈ 170×119 mm [ESTIMADO: pared ~3,5 mm]). Disipación: atornillar la PCB de aluminio a una placa de aluminio en la tapa [ESTIMADO: criterio, ver R06].

---

## 11. Tabla maestra BOM (configuración recomendada 24 V / 8S, más barata con seguridad)

Fecha de consulta: **2026-10-01** para todas las filas.

| # | Componente | Especificación mínima | Producto | Tienda | Link abierto | Precio | Cant. | Subtotal EUR |
|---|---|---|---|---|---|---|---|---|
| 1 | Motor | outrunner 63xx, 140–190 KV, ≥ 2 kW, eje 8–10 mm, hall | Flipsky 6374 **190 KV** 8 mm s/polea (hall no confirmado en la ficha: preguntar al vendedor; alternativa con hall verificado: Maytech MTO6374-HA-C 82,40 USD) | flipsky.net (CN) | https://flipsky.net/products/flipsky-bldc-belt-motor-battle-hardened-6374-140kv-170kv-190kv-3500w-for-electric-skateboard | 87 USD | 1 | 76,62 |
| 2 | ESC | VESC ≥ 50 V, ≥ 50 A cont., ADC/PPM, reversa | Flipsky 75100 V2.0 (botón) (alternativa verificada más barata: 75100 With Aluminum PCB 73 USD, BEC 1,5 A, −15 USD ≈ −16,5 EUR con IVA) | flipsky.net (CN) | https://flipsky.net/products/flipsky-75100-v2-0-with-aluminum-pcb-with-power-key-switch-button-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller | 88 USD | 1 | 77,50 |
| 3 | Antichispa (precarga) | ≥ 30 V, ≥ 60 A | Flipsky Antispark Pro caja alu | flipsky.net (CN) | https://flipsky.net/products/flipsky-antispark-switch-pro-with-aluminum-pcb-case-200a-for-electric-skateboard-ebike-scooter-robots | 48 USD | 1 | 42,27 |
| 4 | Envío CN + IVA 25 % | — | DHL [ESTIMADO 45 EUR] + IVA sobre 1–3 + envío (**sin arancel ni tasa de despacho del courier**: buscar) | — | buscar: "Flipsky DHL Denmark shipping cost" | — | 1 | 105,35 [ESTIMADO] |
| 5 | Batería | LFP 24 V ≥ 1,2 kWh, BMS ≥ 50 A, IP65 | LiTime 24V 50Ah TM BT | litime.de | https://www.litime.de/products/24v-50ah-bluetooth-lithium-batterie-fur-elektromotor-boote | 309,99 EUR | 1 | 309,99 |
| 6 | Cargador | 29,2 V LFP, ≥ 10 A | Power Queen 29,2 V 20 A | ipowerqueen.de | https://www.ipowerqueen.de/products/power-queen-29-2v-20a-lifepo4-ladegerat | 102,99 EUR | 1 | 102,99 |
| 7 | Fusible principal | 80 A, ≥ 32 V (≥ 58 V si 12S) | IMAXX midiOTO 80 A 58 V | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/auto_fuse_midioto_80a_58vdc_white-229133 | 2,52 EUR | 2 (1 repuesto) | 5,04 |
| 8 | Portafusible | MIDI, ≥ 58 V | IMAXX HMD4-MG1-H | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/car_fuse_holder_hmd4-mg1-h_megaoto_midioto_200_a_58_v-407426 | 12,55 EUR | 1 | 12,55 |
| 9 | Desconectador marino | ≥ 48 V, ≥ 100 A, IP65 | Biltema Hovedafbryder AFD | Biltema DK | https://www.biltema.dk/baad/eludstyr/elinstallationer-til-bade/stromafbrydere/hovedafbryder-afd-onoff-2000063980 | 159 DKK | 1 | 21,27 |
| 10 | Kill switch cordón | contacto cerrado con clip | Dødmands kontakt universal | Watski DK | https://www.watski.dk/Ddmands-kontakt-universal-110CP | 74 DKK | 1 | 9,90 |
| 11 | Contactor (kill hardware) | bobina 24 V monoestable, ≥ 60 A DC | FREI FRC3 24 V (provisorio; **contactos 40 A según Reichelt → NO cumple ≥ 60 A ni ≥ 50 A del BMS**) → reemplazar por SW80 | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/70a_high-current_relay_frc3_24_v_1_n_o_contact-79404 | 3,26 EUR | 1 | 3,26 (SW80: buscar, [ESTIMADO 60–100]) |
| 12 | Cable potencia | 16 mm² estañado | Skyllermarks fortinnet 16 mm² | Watski DK | https://www.watski.dk/gummikabel-fortinnet-skyllermarks-11vPX | 80 DKK/m | 4 m | 42,81 |
| 13 | Terminales | 16 mm² estañados M8/M10 | Skyllermarks rørkabelsko 16 mm² ø8 + ø10 (4 u.) | Watski DK | https://www.watski.dk/roerkabelsko-25-95-mm-117N7 | 38 + 40 DKK | 2+1 | 15,52 |
| 14 | Termocontraíble c/ adhesivo | 3:1 | Biltema krympeflex 76 u. | Biltema DK | https://www.biltema.dk/bil---mc/elsystem/krympeslanger/krympeflex-sat-med-lim-76-stk-2000041559 | 145 DKK | 1 | 19,40 |
| 15 | Crimpadora | 8–70 mm² | Biltema kabelskotang | Biltema DK | https://www.biltema.dk/varktoj/handvarktoj/ovrigt-varktoj/kabelskotang-2000064951 | 89,90 DKK | 1 | 12,03 |
| 16 | Conector batería ↔ VESC | ≥ 45 A, antichispa | XT90-S (par) | Rotorama (CZ) | https://www.rotorama.com/product/xt90s-antispark-konektor-par | 3,69 EUR | 2 | 7,38 |
| 17 | Puerto de carga | Anderson 50 A (= salida de los cargadores) | Anderson PP51S gris 16 mm² | Watski DK | https://www.watski.dk/anderson-pp51s-graa-16mm2-1st-11GKJ | 90 DKK | 2 | 24,08 |
| 18 | Conector señal IP68 | 4 polos | Lumberg 0332-04 + 0322-04 | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/plug_round_connector_ip_68_360_shielded_4-pin-116121 | 7,34 + 7,51 EUR | 1 | 14,85 |
| 19 | Conector kill IP68 | 2 polos | Cliffcon 68 FM686812 | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/cliffcon_68_cable_connector_2_pin_ip68-230124 | 8,39 EUR | 1 | 8,39 |
| 20 | Prensaestopas | IP68 M16 + M20 | Biltema kabelforskruning (2 u. c/u) | Biltema DK | https://www.biltema.dk/byggeri/elinstallationer/eldaser/kabelforskruning-m16-4-8-mm-2-stk-2000064967 | 24,90 DKK | 2 | 6,66 |
| 21 | Acelerador | hall, pulgar, estanco | thumb throttle 24–72 V | AliExpress | https://www.aliexpress.com/w/wholesale-thumb-throttle-ebike-hall.html | 9,49 EUR | 1 | 9,49 |
| 22 | Sensor hall (palanca/timón) | lineal, analógico | Allegro A1324 | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/low_noise_linear_sensor_sip-3-189140 | 1,68 EUR | 2 | 3,36 |
| 23 | MCU (opcional) | 3,3 V, BLE para telemetría | ESP32-WROOM-32E DevKitC | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/esp32-wroom-32e_development_board-341303 | 11,55 EUR | 1 | 11,55 |
| 24 | DC-DC 24→5 V | ≤ 36 V in (8S) | **no comprar**: usar BEC 5 V 1 A del VESC; si hace falta: TSR 1-2450E | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/dc_dc_converter_tsr_1e_1_a_7-36_5_0_vdc_sip-3-288648 | 4,19 EUR | 0 | 0 |
| 25 | Caja electrónica | IP67, ≥ 170×120×50 | BOX4U 177×126×56 IP67 | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/industrial_housing_177_x_126_x_56_mm_ip67_light_gray-324319 | 14,65 EUR | 1 | 14,65 |
| 26 | Caja batería | interior ≥ 270×180×220 | Biltema Batteriboks 340×200×245 | Biltema DK | https://www.biltema.dk/baad/marinebatterier-og-tilbehor/batteribokse/batteriboks-340-x-200-x-245-mm-2000048673 | 105 DKK | 1 | 14,05 |
| | | | | | | | **Total** | **≈ 971 EUR ≈ 7 260 DKK** [ESTIMADO: suma; incluye envío CN estimado; excluye envíos Reichelt/Watski/AliExpress (buscar) y el contactor SW80] |

Con contactor SW80 (≈ 60–100 EUR [ESTIMADO]) y envíos UE (buscar) el total realista es **≈ 1 050–1 150 EUR** [ESTIMADO].

### Variantes de batería (reemplazan filas 5–6)

| Variante | Batería | Cargador | Δ vs base | P cont. por BMS | Comentario |
|---|---|---|---|---|---|
| Base 8S | LiTime 24V 50Ah 309,99 | PQ 29,2 V 20 A 102,99 | 0 | 25,6 × 50 = **1,28 kW** | 1,28 kWh; 80 % DoD → 1,02 kWh útiles |
| **2× PQ 12V 100Ah en serie** | 475,18 (pack-2) | mismo 29,2 V | **+165 EUR** | 25,6 × 100 = **2,56 kW** | 2,56 kWh, ~22 kg; 186 EUR/kWh; 2 BMS en serie (vigilar desbalance; cargar por separado a 14,6 V de vez en cuando) [ESTIMADO] |
| 2× PQ 12V 50Ah | 316,78 | mismo | +7 | 1,28 kW | sin ventaja salvo modularidad (2 × 5,29 kg) |
| 12S (R06) | LiTime 36V 50Ah 399,99 | LiTime 36 V 15 A 132,99 | +120 + fusible MRBF/midi 58 V; DC-DC R-78HB | 38,4 × 50 = **1,92 kW** | 1,92 kWh; obliga a descartar portafusibles de 32 V (Biltema ANL, Blue Sea AMI/MIDI) |

### Ruta alternativa todo-UE para motor/ESC/antichispa (AliExpress, IVA en checkout [ESTIMADO])
6374 140 KV 94,69 + VESC (Makerbase 75100 63,99 o Flipsky 75100 V2.0 114,39) + antichispa 33,99 = **192,67–243,07 EUR** vs **301,74 EUR** por Flipsky directo con IVA y envío estimado (filas 1–4) [VERIFICADO precios: búsquedas AliExpress §1–3 re-consultadas 2026-10-01; total: cálculo]. *(Corregido en verificación: el 75100 Flipsky a 59,99 EUR "Flash deal" no se reprodujo → límite inferior 188,67 reemplazado por 192,67 con Makerbase.)* Riesgo: vendedor/versión no verificables; precios de búsqueda AliExpress son volátiles.

---

## Hallazgos que cambian el diseño

- **El BMS manda la potencia, no el VESC**: las baterías 24 V 50 Ah verificadas tienen BMS de **50 A** (LiTime: 250 A × 1 s; Power Queen: 60 A × 30 min) → **1,28 kW continuos** (1,54 kW por 30 min). Si el tramo 8–12 km/h necesita > 1,3 kW eléctricos, la opción más barata por kWh es **2× Power Queen 12V 100Ah en serie** (475,18 EUR, 2,56 kWh, BMS 100 A → 2,56 kW, **186 EUR/kWh** vs 242 EUR/kWh de la LiTime 24V 50Ah), a costa de ~22 kg. En todo caso: VESC `l_in_current_max` ≤ 40 A con BMS de 50 A.
- **24 V vs 36 V lo deciden los accesorios marinos baratos**: Biltema portafusible ANL = **32 V**, Blue Sea AMI/MIDI = **32 V**, desconectadores Biltema/1852/Blue Sea = **≤ 48 V**. 8S (29,2 V cargada) es compatible con todo; 12S (43,8 V) obliga a MRBF (58 V, 185 + 320 DKK) o midiOTO 58 V / megaOTO 70 V + portafusible HMD4-MG1-H 58 V (2,52 + 12,55 EUR). La ruta MIDI de Reichelt es ~4,5× más barata que MRBF (15 vs 68 EUR); sirve directo en 8S, pero **en 12S el fabricante exige base aislante (HIB1) entre 32 y 70 V** (precio: buscar). *(Corregido en verificación.)*
- **KV según tensión**: con 8S (25,6 V nom.) un 190 KV da ~4 860 rpm en vacío y un 140 KV ~3 580 rpm; con 12S el 140 KV da ~5 380 rpm [ESTIMADO: KV × V]. → **190 KV para 24 V, 140 KV para 36 V**, manteniendo la misma reducción HTD. El Flipsky 6374 (0,98 kg, 87 USD, 85 A, eje 8 mm) alcanza; el 6384 (1,3 kg, +26 USD) y el 7070 (6–18S, trae cable de temperatura, 101 USD) solo si R04/R02 piden > 2 kW.
- **Motor y VESC solo se consiguen con link abierto desde China (USD)**: precio lista + envío no publicado + **25 % IVA de importación** (*"buyers are responsible for… all tax or VAT"*) → 196 EUR de lista se vuelven ≈ **302 EUR** [ESTIMADO: envío 45 EUR; sin arancel ni tasa de despacho]. Los listados de AliExpress con precio UE (193–243 EUR el trío, re-verificado) pueden ser más baratos.
- **No hace falta DC-DC 24→5 V**: el 75100 V2.0 trae **BEC 5 V @ 1 A** (Pro: 1,5 A) → alcanza para acelerador hall + ESP32/Nano. Ahorra 4–17 EUR y un componente. Ojo: VESC ADC es de 3,3 V [ESTIMADO: memoria técnica, no verificado en las fichas Flipsky abiertas]; acelerador/A1324 alimentados a 5 V necesitan divisor resistivo [ESTIMADO: rango de salida típico 0,8–4,2 V, no publicado por los vendedores].
- **Cable: 16 mm² solo en el tramo batería → fusible → desconectador → contactor; 25 mm² sobra**. El VESC sale con 12 AWG (V2.0, 3,3 mm²) o 10 AWG (Pro, 5,3 mm²) y el XT90-S es de 45 A cont.; el puerto de carga **Anderson SB50 (PP51S, hasta 16 mm², 120 A, 90 DKK c/u)** coincide con la salida Anderson 50 A de los cargadores LiTime/Power Queen.
- **Kill switch DK de 74 DKK es fail-safe pero de 12 V / 15 A**: los polos "M" conducen con el clip puesto (cordón tirado = abre). Usarlo para la bobina del contactor a 24 V queda fuera de su tensión nominal (corriente de bobina < 0,5 A [ESTIMADO]; FRC3: 24 V/320 Ω = 75 mA); alternativa: que el cordón corte la entrada de kill del VESC (3,3 V) + bobina vía relé auxiliar. Biltema: solo se encontró el cordón (Dødemandsgreb 135 cm), no un interruptor [NO VERIFICADO exhaustivamente].
- **No hay contactor DC de servicio continuo con link abierto en DK/UE**: los relés de 24 V baratos de Reichelt no sirven: FRC3 (3,26 EUR) publica *"Max switching current: 70 A"* a ≤ 75 V DC pero contactos de **40 A** (< 50 A del BMS) y Faston; AZ160 (60 A) solo tiene tensión de corte en AC (480 V AC); el Lewmar 24 V (669 DKK) es de molinete. Presupuestar un **Albright SW80 24 V** aparte (buscar; [ESTIMADO 60–100 EUR]); es el ítem de seguridad que más pesa en el costo después de la batería.
- **Carga en frío**: LiTime corta la carga bajo **0 °C**; Power Queen especifica carga en **0…50 °C** y, tras el corte por baja temperatura, **reanuda recién a 5 °C** de batería *(corregido en verificación: antes decía "corta bajo 5 °C")* → en primavera/otoño en Sønderborg cargar en interior; prever batería removible (caja Biltema 105 DKK con correa).
- **Cargador Biltema 12/24 V (459 DKK) no sirve para 24 V LFP** (LiFePO4 solo en el modo 12 V según la ficha) → cargador dedicado 29,2 V: Power Queen 20 A **102,99 EUR** (más barato que LiTime 132,99).
- **Costo total de la BOM eléctrica 24 V ≈ 971 EUR (≈ 7 260 DKK)**, ≈ 1 050–1 150 EUR con SW80 y envíos [ESTIMADO]; la batería + cargador son el 42 % (413 EUR), el tren motor/VESC/antichispa con IVA el 31 % (302 EUR).
- *(Agregados en verificación adversarial)*
- **Fusible principal: usar megaOTO HV en vez de midiOTO**. El midiOTO 80 A tiene poder de corte de solo **1 kA** a 58 V; la Power Queen 24V 50Ah declara R int. ≤ 40 mΩ → corriente de cortocircuito del orden de 29,2 V / 0,04 Ω ≈ **730 A o más** [ESTIMADO: sin resistencia de cables; con 2× 12V 100Ah probablemente > 1 kA]. El megaOTO HV 80/100 A corta *"2500 A at 70 VDC"*, cuesta 3,14 EUR (+0,62 EUR) y entra en el mismo portafusible HMD4 (posición M8).
- **Relé FRC3 descartado también como provisorio**: contactos **40 A** (< 50 A del BMS) y terminales Faston 6,35/9,5 mm → no admite el cable de 16 mm² del circuito principal; el SW80 (o equivalente) deja de ser opcional.
- **VESC más barato y con BEC mejor**: Flipsky 75100 With Aluminum PCB a **73 USD** (BEC 5 V @ 1,5 A, 100 A cont., ADC/PPM) en vez del 75100 V2.0 a 88 USD (BEC 1 A) → −16,5 EUR con IVA. Existe versión de 106 USD con carcasa refrigerada por agua (no usar agua de mar sin intercambiador [ESTIMADO: criterio]).
- **Motor**: la ficha de flipsky.net del 6374 **no confirma sensor hall** (sí lo confirma Maytech MTO6374-HA-C, 82,40 USD, sellado "splashproof"). Flipsky ofrece versiones **waterproof** del 6374 (AliExpress 111,69 EUR) y 6384 (136 USD) pensadas para thrusters; podrían evitar el cambio de rodamientos/protección anticorrosión [ESTIMADO: por el uso declarado, materiales no publicados en lo abierto], a cambio de +17–50 EUR (specs no abiertas: buscar "Flipsky waterproof 6374 140KV 3600W specs").
- **Costo importación CN subestimado**: falta arancel aduanero + tasa de despacho del courier (no publicadas en las páginas abiertas; buscar) → el tren motor/VESC/antichispa por Flipsky directo puede quedar > 302 EUR.

---

## Fuentes abiertas con éxito en esta sesión

- https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
- https://europa.eu/youreurope/citizens/consumers/shopping/vat/index_en.htm
- https://flipsky.net/pages/faqs · https://flipsky.net/pages/about-tariffs · https://flipsky.net/policies/shipping-policy
- https://flipsky.net/products/flipsky-bldc-belt-motor-battle-hardened-6374-140kv-170kv-190kv-3500w-for-electric-skateboard
- https://flipsky.net/products/flipsky-bldc-belt-motor-battle-hardened-6384-140kv-170kv-190kv-4000w-for-electric-skateboard
- https://flipsky.net/products/flipsky-sensored-outrunner-brushless-dc-motor-battle-hardened-7070-110kv-140kv-170kv-4200w
- https://flipsky.net/products/flipsky-75100-v2-0-with-aluminum-pcb-with-power-key-switch-button-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller
- https://flipsky.net/products/flipsky-75100-pro-with-aluminum-pcb-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller
- https://flipsky.net/products/flipsky-antispark-switch-pro-with-aluminum-pcb-case-200a-for-electric-skateboard-ebike-scooter-robots
- https://flipsky.net/search/suggest.json?q=6384&resources[type]=product&resources[limit]=10 · https://flipsky.net/search/suggest.json?q=thumb%20throttle&resources[type]=product&resources[limit]=10
- https://maytech.cn/products/brushless-hall-sensor-motor-mto6374-170-ha-c · https://maytech.cn/products/brushless-sensorless-motor-mto6374-190-g · https://maytech.cn/products/waterproof-6384-marine-motor-for-electric-foil-board
- https://escooter-parts.co.uk/search/suggest.json?q=75100&resources[type]=product&resources[limit]=10
- https://www.litime.de/policies/shipping-policy
- https://www.litime.de/products/24v-50ah-bluetooth-lithium-batterie-fur-elektromotor-boote
- https://www.litime.de/products/12v-50ah-bluetooth-lithium-batterie-fur-elektromotor-boote-zuverlassige-power
- https://www.litime.de/products/36v-50ah-bluetooth-lithium-batterie-group31-marine-trolling-motor
- https://www.litime.de/products/12v-100ah-lifepo4-batterie-elektromotoren-tieftemperaturschutz-tm
- https://www.litime.de/products/litime-29-2v-20a-lithium-batterieladegerat-fur-24v-lifepo4-lithium-batterie
- https://www.litime.de/products/litime-36v-15a-wasserdichtes-lithium-batterieladegerat
- https://www.litime.de/products/litime-12v-10a-lithium-batterie-ladegerat-fur-12v-lifepo4-lithium-batterie
- https://www.litime.com/products/litime-24v-50ah-tm-bluetooth-lifepo4-battery
- https://www.ipowerqueen.de/products/power-queen-lifepo4-24v-50ah-smart-niedertemperatur-trolling-motor-batterie
- https://www.ipowerqueen.de/products/power-queen-12v-50ah-lifepo4-batterie-eingebautes-50a-bms
- https://www.ipowerqueen.de/products/power-queen-12-v-100-ah-lifepo4-deep-cycle-batterie
- https://www.ipowerqueen.de/products/power-queen-29-2v-20a-lifepo4-ladegerat
- https://find.biltema.com/v4/web/typeahead/400/da/?query=LiFePO4&take=12 (API de búsqueda Biltema DK)
- Biltema DK (páginas de producto): batterikabel-rod-16-mm2-2000054560 · hovedafbryder-afd-onoff-2000063980 · sikringsholder-anl-2000058572 · anl-sikring-100-a-2000058033 · dodemandsgreb-135-cm-2000040861 · batteriboks-340-x-200-x-245-mm-2000048673 · kabelforskruning-m16-4-8-mm-2-stk-2000064967 · kabelforskruning-m20-6-12-mm-2-stk-2000064968 · standardkapsling-8-moduler-ip65-2000068548 · 2412-v-omformer-2000033704 · vandtat-og-stodsikker-boks-2000032621 · kabelskotang-2000064951 · krympeflex-sat-med-lim-76-stk-2000041559 · batterilader-1224-v-15-a-2000045787 · rorkabelsko-16-mm2-m10-10-stk-2000050964 · rorkabelsko-25-mm2-m10-10-stk-2000050965 · enkeltrela-skiftende-5080-a-2000049771 (URLs completas en las tablas)
- Watski DK: Ddmands-kontakt-universal-110CP · nodstopafbryder-sikkerhedsnogle-1b1Vj · nodstopafbryder-med-sikkerhedsnoegle-og-flyder-1b1Vp · Blue-Sea-MRBF-Blok-Sikring-11cWn · Blue-Sea-Terminal-sikring-11cor · blue-sea-sikringsholder-terminal-max-300a-11wXO · skyllermarks-sikring-anl-11Pgk · dcm-anl-sikringsholder-m8-300a-11GXC · blue-sea-ami-midi-sikring-11cWH · sikringsholder-ami-midi-11ckP · 1852-hovedafbryder-275Amp-12-48-vdc-11ECI · blue-sea-hovedafbryder-300-ah-11Eiy · gummikabel-fortinnet-skyllermarks-11vPX · roerkabelsko-25-95-mm-117N7 · roerkabelsko-25-mm-skyllermarks-11vIb · roerformede-kabelsko-af-fortinnet-kobber-11GjW · anderson-pp51s-graa-16mm2-1st-11GKJ · kontakt-enkelt-1224V-116Ft · search/?query=fortinnet%20kabel%2016
- Compass24 DK: https://www.compass24.dk/hovedafbryder-til-batteri-275-a-289021/275-5-6x5-6x7-4-1250 · https://www.compass24.dk/torqeedo-noedstopkontakt-332090/1 (175 DKK, para Torqeedo; no usado)
- Reichelt DK (todas con "incl. 25% VAT"): productos 189140, 342799, 230124, 116121, 116124, 142943, 341303, 288648, 159167, 324319, 324383, 324286, 229133, 229134, 337907, 337908, 407426, 375251, 79404, 415707 (URLs completas en las tablas)
- https://www.rotorama.com/product/xt90s-antispark-konektor-par
- https://www.ebikeling.com/products/thumb-waterproof-throttle-for-24v-36v-48v-electric-bicycle
- AliExpress (búsquedas, región DK, EUR): wholesale-flipsky-6374-motor · wholesale-flipsky-75100 · wholesale-makerbase-vesc-75100 · wholesale-flipsky-antispark-switch · wholesale-amass-as150 · wholesale-anderson-sb50 · wholesale-thumb-throttle-ebike-hall · wholesale-ss49e · wholesale-lifepo4-charger-29.2v-10a

- *(Abiertas en la verificación adversarial)*: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90d.xml · https://flipsky.net/products/flipsky-75100-with-aluminum-pcb-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller · https://flipsky.net/products/flipsky-75100-75v-100a-single-esc-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller · https://flipsky.net/search/suggest.json?q=75100%20pro&resources[type]=product&resources[limit]=10

No usados / sin acceso: hobbyking.com (403), svb24.com y svb.de (403), conrad.de (403), amazon.de (503), makerbase3d.com (captcha), let-elektronik.dk (búsqueda demasiado lenta, sin resultado en esta sesión), Jem & Fix / Elextra / RS DK (no fueron necesarios: Reichelt DK cubrió electrónica y Biltema/Watski lo marino).

---

## Verificación (adversarial)

Re-apertura 2026-10-01 por curl (endpoints `.js` de Shopify para Flipsky/Maytech/LiTime/Power Queen/Ebikeling; HTML + JSON embebido para Watski/Biltema/Reichelt/Compass24; XML BCE) y WebFetch (Flipsky cuando curl dio 429). **≈ 95 URLs re-abiertas; 0 caídas** (Ebikeling y un `suggest.json` de Flipsky dieron 429 por curl y se abrieron con WebFetch). Aritmética de la tabla maestra recalculada: 26 filas suman 970,96 EUR = 7 258 DKK (OK); conversiones USD→EUR (×0,8807) y DKK→EUR (÷7,4755) OK; 42 % / 31 % OK; KV×V OK.

| Afirmación / URL | Estado | Nota |
|---|---|---|
| Cambio BCE 1,1355 USD / 7,4755 DKK / 0,85463 GBP (2026-09-30) | corregido (link) | El XML diario ya muestra 2026-10-01 (1,1298 / 7,4758); el valor 09-30 está en eurofxref-hist-90d.xml → link cambiado |
| Flipsky FAQ: DHL 5–9 d, 4PX 7–25 d, despacho 3–7 d, *"buyers are responsible for… all tax or VAT"*, *"price and shipping cost do not include tariffs"* | OK | flipsky.net/pages/faqs |
| "La FAQ sugiere sub-declarar" | corregido | La frase está en /pages/about-tariffs (*"We can declare a low price according to your requirements"*) |
| Flipsky shipping-policy "2-3 working days" | OK | — |
| Arancel aduanero omitido | corregido (agregado) | europa.eu dice *"VAT, customs and excise duty is always due"*; el archivo solo sumaba IVA → nota + buscar TARIC |
| Flipsky 6374: 87/93 USD, 3–12S, 3500 W, 85 A, 0,98 kg, 8 mm/10 mm D | OK | flipsky.net …6374… (.js) |
| Flipsky 6374 "(sensored)" | no verificado | La ficha no menciona hall/sensor; solo títulos de revendedores AliExpress |
| 6374 "8 mm redondo (108 mm)" | corregido | 108 / 99 mm son el largo de los planos ("Shaft Drawing (108mm length)"), no longitud del eje |
| Flipsky 6384: 113 USD, 4–14S, 4000 W, 9 Nm, 95 A, 0,05 Ω, 14 polos, N42SH, 1,3 kg, eje 8 mm×30 mm | OK | — |
| Flipsky 7070: 101 USD, 6–18S, 2200/4200 W, 100 A, 1,08 kg, cable TEMP blanco | OK | — |
| Maytech MTO6374-HA-C: 82,40 USD (110 KV 94,5), 3550 W, 65/60 A, 8×26 mm, 3–12S (12–50 V), sellado, DHL 3–7 d, sin stock 30–40 d | OK | — |
| Maytech MTO6374-G: 86,80 / 100,90 USD, 785 g, 0,0402 Ω, 2–12S | OK | — |
| Rodamientos "de serie" NMB 6800ZZ/6900ZZ | corregido (etiqueta) | El listado es un repuesto "for flipsky 63 series motor" (3 pzs 4,50 USD OK); "de serie" pasa a [ESTIMADO] |
| AliExpress 6374 140KV 94,69 EUR (item 4000966919617) | OK | 66 vendidos |
| Flipsky 75100 V2.0: 88/92 USD, 14–84 V, 100/250 A, BEC 5 V@1 A, 12 AWG, FW 5.02, 103×58×24 | OK | — |
| Flipsky 75100 Pro: 89 USD, 100/120 A, BEC 1,5 A, 10 AWG, 103×58×27,7, BT | OK | — |
| Flipsky 75100 Pro V2.0 98 USD | corregido (link) | La URL citada era la búsqueda "thumb throttle"; verificado con q=75100 pro |
| AliExpress Flipsky 75100 59,99 EUR "Flash deal", 486 vendidos | no verificado | No aparece en la re-consulta; precio de oferta volátil. Ruta "todo-UE" recalculada 192,67–243,07 EUR |
| AliExpress 75100 V2.0 114,39; Makerbase 63,99–65,69 / V2 122,69 | OK | — |
| escooter-parts.co.uk 75100 V2.0 127,99 GBP | OK | — |
| Antispark Pro V3.0: 33/43/48 USD, 3–14S (12–60 V), 100 A alu / 60 A disipador, LED 16 mm, caja 83,9×45×17 | OK | — |
| AliExpress antispark 33,99 EUR | OK | 169 vendidos |
| Amass XT90-S Rotorama 3,69 EUR, 45/90 A, resistencia integrada | OK | — |
| Watski Dødmands kontakt 74 DKK, SKU 203517, 12 V–15 A, polos M cerrados con clip | OK | — |
| Osculati 129 DKK / con flotador 139 DKK | OK | stock=false (bestillingsvare) |
| Biltema Dødemandsgreb 74,90 DKK, 135 cm, "af sluttende type" | OK | — |
| FREI FRC3 "capacidad de corte DC no publicada" | corregido | Reichelt publica 70 A / 75 V DC máx. de conmutación y **contactos 40 A**, bobina 320 Ω, Faston 6,35/9,5 → no cumple ≥ 60 A (fila 11 marcada) |
| Zettler AZ160 3,73 EUR, 60 A, 480 V AC | OK | Corte DC no especificado (solo AC) |
| Lewmar kontaktor 24 V 669 DKK, molinete/capstan | OK | Una reseña de usuario dice "100 A continuo": no es especificación |
| Biltema Hovedafbryder AFD 159 DKK: 12–48 V, 275/455/1250 A, M10, IP65, Ø52, art. 25-8849 | OK | — |
| 1852 hovedafbryder 180 DKK, 275 A, 12–48 V, Ø 52 mm | OK | — |
| Blue Sea hovedafbryder 358 DKK, 300/500/1500 A, máx. 48 V | OK | La página agrega IP66 |
| Compass24 hovedafbryder 295 DKK, 50 V, 275/1250 | OK | — |
| LiTime 24V 50Ah 309,99 EUR; 50 A / 250 A 1 s; 21,15 lb; IP65; 0 °C / −20 °C | OK | litime.de + litime.com |
| Power Queen 24V 50Ah 329,99 / 449,98 EUR; 50 A, 60 A@30 min, carga 50 A, 28,8 ± 0,4 V, IP65, M8, 26,0×16,8×21,0 | OK | — |
| Power Queen "protección de carga a 5 °C" / "corta bajo 5 °C" | corregido | Ficha: carga 0…50 °C (32 °F); 5 °C es la **reanudación automática** tras protección de baja T |
| LiTime 12V 50Ah 189,99 EUR, 1,2C (60 A) 30 min, 4P4S, 5110 g | OK | — |
| PQ 12V 50Ah pack-2 316,78 EUR, 50 A, 5,29 kg, IP65, 19,5×16,6×17,2 | OK | — |
| PQ 12V 100Ah pack-2 475,18 EUR, BMS 100 A, 11 000 g envío, 4P4S | OK | — |
| LiTime 12V 100Ah TM 259,99 EUR, 10 050 g | OK | — |
| LiTime 36V 50Ah 399,99 EUR, 50 A / 60 A 30 min, 9600 g | OK | — |
| LiTime envío gratis UE desde almacén DE, 1–2 + 2–7 días | OK | La exclusión incluye también Grecia (irrelevante para DK) |
| Power Queen envío gratis UE (excepto Grecia/islas), 3–7 días | OK | — |
| Variantes "0 % MwSt. in DE" | OK | Etiqueta "in DE" en la variante; "tasa 0 % FV" es interpretación |
| Biltema LiFePO4 solo 2–3,5 Ah, 399–549 DKK | OK | API typeahead |
| Biltema Batteriboks 105 DKK, 340×200×245 interior, correa | OK | — |
| Cargadores: PQ 29,2 V 20 A 102,99 EUR (Anderson 50 A + M8, ~1,3 kg); LiTime 29,2 V 20 A 132,99; LiTime 36 V 15 A 132,99 IP66; LiTime 14,6 V 10 A 65,99 | OK | — |
| AliExpress cargador 29,2 V 10 A 31,09 EUR (272 vendidos) | OK | — |
| Biltema cargador 12/24 V "no apto 24 V LFP" [ESTIMADO] | corregido (etiqueta ↑) | Tabla de propiedades: LiFePO4 solo "(12 V)" → [VERIFICADO]; 7,5 A en 24 V |
| Blue Sea MRBF 185 DKK (60 A 195; 100 A 185); portafusible 320 DKK, 58 V, M8, 30–300 A | OK | — |
| IMAXX midiOTO 80/100 A 58 V, 2,52/2,31 EUR | OK + agregado | Poder de corte 1 kA (agregado; ver hallazgo megaOTO) |
| IMAXX megaOTO 80/100 A 70 V, 3,14 EUR | OK | 2500 A @ 70 V DC. "125 A" no tenía URL → marcado no re-abierto |
| IMAXX HMD4-MG1-H 12,55 EUR, 58 V, 200 A | corregido (incompleto) | La ficha exige **base aislante HIB1 entre 32 y 70 V** y la tabla dice 70 Vdc → "sirve para ambos voltajes" calificado |
| Biltema ANL 100 A 69,90 DKK, 80 V DC; portafusible 109 DKK, 32 V, 300 A, M10, LED | OK | — |
| Skyllermarks ANL 80 DKK, M10, c-c 60 mm, casi sin stock | OK | 10 de 11 variantes stock=false |
| TBS DCM ANL 200 DKK, V máx "—" | corregido | Ficha: 50 V, 600 A, M8 |
| Blue Sea AMI/MIDI 85 DKK, 32 V; portafusible 425 DKK | corregido (precisión) | Fusible 32 V; portafusible 50 V DC / 200 A |
| Cable Skyllermarks estañado 16 mm² 8 DKK/dm, 25 mm² 11 DKK/dm | OK | Mapeo variante→precio comprobado en el JSON de la página |
| Biltema batterikabel 16 mm² 6 m 169 DKK, PVC, −40…+80 °C | OK | — |
| Terminales Skyllermarks 16 mm² ø6/ø8/ø10 = 39/38/40 DKK (4-pack); 25 mm² ø8/ø10 = 10/11 DKK | OK | Estañados ("fortinnet") confirmado |
| Biltema rørkabelsko 16/25 mm² M10 10 u. 64,90/69,90 DKK | OK | Agujero 10,8 mm |
| Biltema krympeflex 145 DKK 3:1 76 u.; kabelskotang 89,90 DKK 8–70 mm² | OK | — |
| XT90 Jamara Reichelt 4,72 EUR | OK | 45 A continuo |
| AliExpress AS150 6,14 EUR (1000+); SB50 7,91 EUR | OK | — |
| Watski "Anderson PP51S Grå" 90 DKK, 120 A, 48×37×16, ≤ 16 mm² | OK + etiqueta | Identificarlo como "SB50" es inferencia → [ESTIMADO] |
| Lumberg 0332-04 / 0322-04 7,34 + 7,51 EUR IP68 | OK | Son códigos de Reichelt ("LUM 0332-04"); 5 A, 0,75 mm² |
| Cliffcon 68 FM686812 8,39 EUR IP68 | OK | 13 A, 2 mm² |
| Biltema prensaestopas M16 4–8 / M20 6–12, IP68, −20…+80 °C, 24,90 DKK | OK | — |
| Delock 60615 M16 IP68 5,04 EUR | OK | — |
| Ebikeling thumb throttle 24,99 USD, Julet 3 pines estanco, 24–52 V | OK + etiqueta | La página no dice "hall" → [NO VERIFICADO] |
| AliExpress acelerador 9,49 EUR (348 vendidos) | OK (aprox.) | Hoy 346 vendidos; 4,52–6,39 EUR OK |
| Allegro A1324LUA-T 1,68 EUR −40…+150 °C; SS49E 10 u. 0,73 EUR | OK | — |
| Arduino Nano 20,69 EUR; ESP32-WROOM-32E DevKitC 11,55 EUR | OK | — |
| TRACO TSR 1-2450E 7–36 V 4,19 EUR; RECOM R-78HB5.0-0.5 9–72 V 17,12 EUR | OK | — |
| Biltema 24/12 V-omformer 219 DKK, 20–30 V → 12–13,8 V, 10 A | OK | — |
| BOX4U 177×126×56 IP67 14,65; 200×150×75 IP65 18,07; 185×145×39 IP67 12,92 EUR | OK | — |
| Biltema standardkapsling 99,90 DKK 155×201×90 IP65; boks 89,90 DKK 186×120×44 | OK | — |
| Reichelt DK "incl. 25% VAT", precios en € | OK | Las 20 páginas |
| VESC ADC 3,3 V | no verificado | Sin fuente abierta → [ESTIMADO: memoria técnica] |
| "Biltema solo vende cordones, no el interruptor" | no verificado | Solo se abrió un producto; reformulado |
| Contenido de videos | — | El archivo no cita videos (OK) |
