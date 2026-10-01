# R08a — Sourcing BOM eléctrica con envío a Dinamarca

Proyecto P1 (cola larga eléctrica, jon boat < 2,5 m, Als Fjord). **Fecha de consulta de todos los precios: 2026-10-01.**
Etiquetas: **[VERIFICADO: url]** = página abierta en esta sesión y el dato está ahí · **[ESTIMADO: base]** · **[SUPUESTO]** · "buscar: …" = no se pudo abrir.
Complementa R06 (arquitectura eléctrica y seguridad); acá solo producto, tienda, precio y lo que el producto concreto cambia en el diseño.

---

## 0. Bases de compra (impuestos, cambio, logística)

| Dato | Valor | Fuente |
|---|---|---|
| Cambio BCE 2026-09-30 | 1 EUR = **1,1355 USD** = **7,4755 DKK** = 0,85463 GBP → 1 USD = 0,8807 EUR = 6,58 DKK | [VERIFICADO: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml] |
| IVA DK | Reichelt DK muestra precios *"incl. 25% VAT"* | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/dc_dc_converter_r78hb_9-72_vin_single_5_vout_500_ma_sip-3-159167] |
| Compras fuera de la UE | *"If you buy goods online from outside the EU, VAT, customs and excise duty is always due."* | [VERIFICADO: https://europa.eu/youreurope/citizens/consumers/shopping/vat/index_en.htm] |
| Flipsky (CN) | *"The product price and shipping cost do not include tariffs"*; DHL 5–9 días, correo/4PX 7–25 días; despacho 3–7 días hábiles. (La FAQ sugiere sub-declarar el valor: **no hacerlo**, es fraude aduanero.) | [VERIFICADO: https://flipsky.net/pages/faqs] · [VERIFICADO: https://flipsky.net/pages/about-tariffs] |
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
| **Flipsky 6374 Battle Hardened** (sensored) | 140/170/190 | 3500 W | 85 A | 8 mm redondo (108 mm) o 10 mm D (99 mm) | **0,98 kg** | 3–12S | **87 USD** s/polea (93 con polea) = 76,6 EUR | [VERIFICADO: https://flipsky.net/products/flipsky-bldc-belt-motor-battle-hardened-6374-140kv-170kv-190kv-3500w-for-electric-skateboard] |
| Flipsky 6384 Battle Hardened | 140/170/190 | 4000 W, 9 Nm | 95 A | 8 mm (30 mm) / 10 mm / 10 mm D | 1,3 kg | 4–14S; R 0,05 Ω; 14 polos; imán N42SH | 113 USD s/polea = 99,5 EUR | [VERIFICADO: https://flipsky.net/products/flipsky-bldc-belt-motor-battle-hardened-6384-140kv-170kv-190kv-4000w-for-electric-skateboard] |
| Flipsky 7070 Battle Hardened | 110/140/170 | 2200 W nominal / 4200 W | 100 A | 10 mm redondo o D | 1,08 kg | 6–18S; **cable TEMP incluido** (blanco) | 101 USD s/polea = 89,0 EUR | [VERIFICADO: https://flipsky.net/products/flipsky-sensored-outrunner-brushless-dc-motor-battle-hardened-7070-110kv-140kv-170kv-4200w] |
| Maytech MTO6374-170-HA-C (sealed "splashproof", hall) | 170/190 (110 a pedido 94,5 USD) | 3550 W | 65 A (60 A nominal) | 8 mm × 26 mm | buscar: "MTO6374-HA-C weight" | 3–12S (12–50 V) | 82,40 USD = 72,6 EUR | [VERIFICADO: https://maytech.cn/products/brushless-hall-sensor-motor-mto6374-170-ha-c] |
| Maytech MTO6374-G (sensorless) | 90/170/200/330 | 3550 W | 65 A | 8 mm | **785 g**; R 0,0402 Ω | 2–12S | 86,80 USD (90 KV: 100,90 USD) | [VERIFICADO: https://maytech.cn/products/brushless-sensorless-motor-mto6374-190-g] |
| Fallback UE: Flipsky 6374 140KV en AliExpress | 140 | 3500 W | — | — | — | — | **94,69 EUR** (item 4000966919617) | [VERIFICADO: https://www.aliexpress.com/w/wholesale-flipsky-6374-motor.html] |

Notas: (a) los rodamientos de serie de Flipsky son acero NMB 6800ZZ/6900ZZ (repuesto 3 pzs 4,50 USD) → cambiar a inox/híbrido según R06 [VERIFICADO: listado en https://flipsky.net/search/suggest.json?q=6384&resources[type]=product&resources[limit]=10]. (b) No hay fuente UE de motores 63xx–70xx con link abierto (HobbyKing EU 403) → buscar: "Turnigy SK8 6374 149KV EU warehouse".

---

## 2. ESC VESC 75 V / 100 A

| Modelo | V | I cont./pico | BEC | Cables | FW / advertencia | Tamaño | Precio | Fuente |
|---|---|---|---|---|---|---|---|---|
| **Flipsky 75100 V2.0** (botón o llave) | 14–84 V (4–20S) | 100 A / 250 A | **5 V @ 1 A** | 12 AWG | FW 5.02; *"Phase filter needs to be turned off for firmware 5.03 or newer"*; entradas PPM, ADC, NRF, UART | 103×58×24 mm | **88 USD** (botón) / 92 USD (llave) | [VERIFICADO: https://flipsky.net/products/flipsky-75100-v2-0-with-aluminum-pcb-with-power-key-switch-button-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller] |
| Flipsky 75100 Pro | 14–84 V | 100 A / ráfaga 120 A | 5 V @ 1,5 A | **10 AWG** | *"Phase filering is not available… turn off the phase filter"*; Bluetooth integrado | 103×58×27,7 mm | 89 USD | [VERIFICADO: https://flipsky.net/products/flipsky-75100-pro-with-aluminum-pcb-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller] |
| Flipsky 75100 Pro V2.0 | — | — | — | — | — | — | 98 USD | [VERIFICADO: https://flipsky.net/search/suggest.json?q=thumb%20throttle&resources[type]=product&resources[limit]=10] (listado) |
| Makerbase VESC 75100 (AliExpress) | 75 V | 100 A | — | — | — | — | 63,99–65,69 EUR; V2 alu-PCB 122,69 EUR | [VERIFICADO: https://www.aliexpress.com/w/wholesale-makerbase-vesc-75100.html] |
| Flipsky 75100 en AliExpress | — | — | — | — | — | — | 59,99 EUR ("Flash deal", 486 vendidos) / V2.0 114,39 EUR | [VERIFICADO: https://www.aliexpress.com/w/wholesale-flipsky-75100.html] |

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
| Relé de bajo costo (NO es contactor) | FREI FRC3 A 24 (Reichelt) | bobina 24 V DC; 1 NA AgSnO2; 70 A; 75 V DC máx.; terminales 6,35 mm; capacidad de corte DC **no publicada** | 3,26 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/70a_high-current_relay_frc3_24_v_1_n_o_contact-79404] |
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
| Power Queen 24V 50Ah Smart | 25,6 V | 1280 Wh | 50 A; *"60A@30mins"*; carga máx. 50 A; 28,8 ± 0,4 V | buscar | IP65 | protección de carga a 5 °C | 329,99 EUR (con cargador 29 V 20 A: 449,98) | 258 | [VERIFICADO: https://www.ipowerqueen.de/products/power-queen-lifepo4-24v-50ah-smart-niedertemperatur-trolling-motor-batterie] — 26,0×16,8×21,0 cm, bornes M8 |
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
| Biltema 12/24 V 15 A | 15,9 V carga; "Batteritype" lista LiFePO4 solo en una de las dos líneas (12 V) → **no apto 24 V LFP** [ESTIMADO: lectura de la ficha] | pinzas | IP20 | 459 DKK | [VERIFICADO: https://www.biltema.dk/bil---mc/bilbatterier/batteriladere/batterilader-1224-v-15-a-2000045787] |

---

## 6. Fusible principal y portafusibles

| Producto | Tipo | V máx. | Precio | Fuente |
|---|---|---|---|---|
| **Blue Sea MRBF (5191) 80 A** | terminal, sobre el borne | 58 V (portafusible) | **185 DKK** (60 A 195; 100 A 185) | [VERIFICADO: https://www.watski.dk/Blue-Sea-MRBF-Blok-Sikring-11cWn] |
| Portafusible Blue Sea MRBF terminal | 30–300 A, tornillo **M8** (= bornes M8 de LiTime/Power Queen) | **58 V DC** | **320 DKK** | [VERIFICADO: https://www.watski.dk/blue-sea-sikringsholder-terminal-max-300a-11wXO] |
| IMAXX midiOTO 80 A / 100 A | MIDI atornillable | **58 V DC** | 2,52 / 2,31 EUR | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/auto_fuse_midioto_80a_58vdc_white-229133] · [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/auto_fuse_midioto_100a_58vdc_blue-229134] |
| IMAXX megaOTO HV 80/100/125 A | MEGA | **70 V DC** | 3,14 EUR c/u | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/automotive_fuse_megaoto_70_vdc_100_a-337908] · [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/automotive_fuse_megaoto_70_vdc_80_a-337907] |
| **Portafusible IMAXX HMD4-MG1-H** | MIDI/MEGA, 200 A | **58 V** | **12,55 EUR** | [VERIFICADO: https://www.reichelt.com/dk/en/shop/product/car_fuse_holder_hmd4-mg1-h_megaoto_midioto_200_a_58_v-407426] |
| Biltema ANL 100 A | ANL | fusible 80 V DC | 69,90 DKK | [VERIFICADO: https://www.biltema.dk/bil---mc/bilradio/bilradio-tilbehor/anl-sikring-100-a-2000058033] |
| Biltema portafusible ANL | 300 A, M10, LED | **32 V DC** | 109 DKK | [VERIFICADO: https://www.biltema.dk/bil---mc/bilradio/bilradio-tilbehor/sikringsholder-anl-2000058572] |
| Skyllermarks ANL 35–250 A | ANL M10, c-c 60 mm | no publicado | 80 DKK (casi todo sin stock) | [VERIFICADO: https://www.watski.dk/skyllermarks-sikring-anl-11Pgk] |
| TBS DCM portafusible ANL M8 300 A | ANL | — | 200 DKK | [VERIFICADO: https://www.watski.dk/dcm-anl-sikringsholder-m8-300a-11GXC] |
| Blue Sea AMI/MIDI 40–100 A + portafusible | MIDI | **32 V DC** | 85 DKK + 425 DKK | [VERIFICADO: https://www.watski.dk/blue-sea-ami-midi-sikring-11cWH] · [VERIFICADO: https://www.watski.dk/sikringsholder-ami-midi-11ckP] |

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
| **Anderson SB50 (gris)** | "Anderson PP51S Grå 16 mm²" | cable hasta 16 mm²; **120 A**; 48×37×16 mm; se vende de a 1 (hacen falta 2) | **90 DKK c/u** | [VERIFICADO: https://www.watski.dk/anderson-pp51s-graa-16mm2-1st-11GKJ] |
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
| Acelerador de pulgar hall | Ebikeling thumb throttle, conector Julet 3 pines estanco, 24–52 V | salida no publicada | 24,99 USD | [VERIFICADO: https://www.ebikeling.com/products/thumb-waterproof-throttle-for-24v-36v-48v-electric-bicycle] |
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
| 1 | Motor | outrunner 63xx, 140–190 KV, ≥ 2 kW, eje 8–10 mm, hall | Flipsky 6374 **190 KV** 8 mm s/polea | flipsky.net (CN) | https://flipsky.net/products/flipsky-bldc-belt-motor-battle-hardened-6374-140kv-170kv-190kv-3500w-for-electric-skateboard | 87 USD | 1 | 76,62 |
| 2 | ESC | VESC ≥ 50 V, ≥ 50 A cont., ADC/PPM, reversa | Flipsky 75100 V2.0 (botón) | flipsky.net (CN) | https://flipsky.net/products/flipsky-75100-v2-0-with-aluminum-pcb-with-power-key-switch-button-based-on-vesc-for-electric-skateboard-electric-scooter-ebike-speed-controller | 88 USD | 1 | 77,50 |
| 3 | Antichispa (precarga) | ≥ 30 V, ≥ 60 A | Flipsky Antispark Pro caja alu | flipsky.net (CN) | https://flipsky.net/products/flipsky-antispark-switch-pro-with-aluminum-pcb-case-200a-for-electric-skateboard-ebike-scooter-robots | 48 USD | 1 | 42,27 |
| 4 | Envío CN + IVA 25 % | — | DHL [ESTIMADO 45 EUR] + IVA sobre 1–3 + envío | — | buscar: "Flipsky DHL Denmark shipping cost" | — | 1 | 105,35 [ESTIMADO] |
| 5 | Batería | LFP 24 V ≥ 1,2 kWh, BMS ≥ 50 A, IP65 | LiTime 24V 50Ah TM BT | litime.de | https://www.litime.de/products/24v-50ah-bluetooth-lithium-batterie-fur-elektromotor-boote | 309,99 EUR | 1 | 309,99 |
| 6 | Cargador | 29,2 V LFP, ≥ 10 A | Power Queen 29,2 V 20 A | ipowerqueen.de | https://www.ipowerqueen.de/products/power-queen-29-2v-20a-lifepo4-ladegerat | 102,99 EUR | 1 | 102,99 |
| 7 | Fusible principal | 80 A, ≥ 32 V (≥ 58 V si 12S) | IMAXX midiOTO 80 A 58 V | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/auto_fuse_midioto_80a_58vdc_white-229133 | 2,52 EUR | 2 (1 repuesto) | 5,04 |
| 8 | Portafusible | MIDI, ≥ 58 V | IMAXX HMD4-MG1-H | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/car_fuse_holder_hmd4-mg1-h_megaoto_midioto_200_a_58_v-407426 | 12,55 EUR | 1 | 12,55 |
| 9 | Desconectador marino | ≥ 48 V, ≥ 100 A, IP65 | Biltema Hovedafbryder AFD | Biltema DK | https://www.biltema.dk/baad/eludstyr/elinstallationer-til-bade/stromafbrydere/hovedafbryder-afd-onoff-2000063980 | 159 DKK | 1 | 21,27 |
| 10 | Kill switch cordón | contacto cerrado con clip | Dødmands kontakt universal | Watski DK | https://www.watski.dk/Ddmands-kontakt-universal-110CP | 74 DKK | 1 | 9,90 |
| 11 | Contactor (kill hardware) | bobina 24 V monoestable, ≥ 60 A DC | FREI FRC3 70 A 24 V (provisorio) → reemplazar por SW80 | Reichelt DK | https://www.reichelt.com/dk/en/shop/product/70a_high-current_relay_frc3_24_v_1_n_o_contact-79404 | 3,26 EUR | 1 | 3,26 (SW80: buscar, [ESTIMADO 60–100]) |
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
6374 140 KV 94,69 + 75100 59,99 ("Flash deal") o 114,39 (V2.0) + antichispa 33,99 = **188,67–243,07 EUR** vs **301,74 EUR** por Flipsky directo con IVA y envío estimado (filas 1–4) [VERIFICADO precios: búsquedas AliExpress §1–3; total: cálculo]. Riesgo: vendedor/versión no verificables.

---

## Hallazgos que cambian el diseño

- **El BMS manda la potencia, no el VESC**: las baterías 24 V 50 Ah verificadas tienen BMS de **50 A** (LiTime: 250 A × 1 s; Power Queen: 60 A × 30 min) → **1,28 kW continuos** (1,54 kW por 30 min). Si el tramo 8–12 km/h necesita > 1,3 kW eléctricos, la opción más barata por kWh es **2× Power Queen 12V 100Ah en serie** (475,18 EUR, 2,56 kWh, BMS 100 A → 2,56 kW, **186 EUR/kWh** vs 242 EUR/kWh de la LiTime 24V 50Ah), a costa de ~22 kg. En todo caso: VESC `l_in_current_max` ≤ 40 A con BMS de 50 A.
- **24 V vs 36 V lo deciden los accesorios marinos baratos**: Biltema portafusible ANL = **32 V**, Blue Sea AMI/MIDI = **32 V**, desconectadores Biltema/1852/Blue Sea = **≤ 48 V**. 8S (29,2 V cargada) es compatible con todo; 12S (43,8 V) obliga a MRBF (58 V, 185 + 320 DKK) o midiOTO 58 V / megaOTO 70 V + portafusible HMD4-MG1-H 58 V (2,52 + 12,55 EUR). La ruta MIDI de Reichelt es 5× más barata que MRBF (15 vs 68 EUR) y sirve para ambos voltajes.
- **KV según tensión**: con 8S (25,6 V nom.) un 190 KV da ~4 860 rpm en vacío y un 140 KV ~3 580 rpm; con 12S el 140 KV da ~5 380 rpm [ESTIMADO: KV × V]. → **190 KV para 24 V, 140 KV para 36 V**, manteniendo la misma reducción HTD. El Flipsky 6374 (0,98 kg, 87 USD, 85 A, eje 8 mm) alcanza; el 6384 (1,3 kg, +26 USD) y el 7070 (6–18S, trae cable de temperatura, 101 USD) solo si R04/R02 piden > 2 kW.
- **Motor y VESC solo se consiguen con link abierto desde China (USD)**: precio lista + envío no publicado + **25 % IVA de importación** (*"buyers are responsible for… all tax or VAT"*) → 196 EUR de lista se vuelven ≈ **302 EUR** [ESTIMADO: envío 45 EUR]. Los listados de AliExpress con precio UE (188–243 EUR el trío) pueden ser más baratos.
- **No hace falta DC-DC 24→5 V**: el 75100 V2.0 trae **BEC 5 V @ 1 A** (Pro: 1,5 A) → alcanza para acelerador hall + ESP32/Nano. Ahorra 4–17 EUR y un componente. Ojo: VESC ADC es de 3,3 V; acelerador/A1324 alimentados a 5 V necesitan divisor resistivo [ESTIMADO: rango de salida típico 0,8–4,2 V, no publicado por los vendedores].
- **Cable: 16 mm² solo en el tramo batería → fusible → desconectador → contactor; 25 mm² sobra**. El VESC sale con 12 AWG (V2.0, 3,3 mm²) o 10 AWG (Pro, 5,3 mm²) y el XT90-S es de 45 A cont.; el puerto de carga **Anderson SB50 (PP51S, hasta 16 mm², 120 A, 90 DKK c/u)** coincide con la salida Anderson 50 A de los cargadores LiTime/Power Queen.
- **Kill switch DK de 74 DKK es fail-safe pero de 12 V / 15 A**: los polos "M" conducen con el clip puesto (cordón tirado = abre). Usarlo para la bobina del contactor a 24 V queda fuera de su tensión nominal (corriente de bobina < 0,5 A [ESTIMADO]); alternativa: que el cordón corte la entrada de kill del VESC (3,3 V) + bobina vía relé auxiliar. Biltema solo vende cordones, no el interruptor.
- **No hay contactor DC de servicio continuo con link abierto en DK/UE**: los relés de 24 V baratos de Reichelt (FRC3 70 A 3,26 EUR; AZ160 60 A) no publican capacidad de corte DC; el Lewmar 24 V (669 DKK) es de molinete. Presupuestar un **Albright SW80 24 V** aparte (buscar; [ESTIMADO 60–100 EUR]); es el ítem de seguridad que más pesa en el costo después de la batería.
- **Carga en frío**: LiTime corta la carga bajo **0 °C** y Power Queen bajo **5 °C** → en primavera/otoño en Sønderborg cargar en interior; prever batería removible (caja Biltema 105 DKK con correa).
- **Cargador Biltema 12/24 V (459 DKK) no sirve para 24 V LFP** (LiFePO4 solo en el modo 12 V según la ficha) → cargador dedicado 29,2 V: Power Queen 20 A **102,99 EUR** (más barato que LiTime 132,99).
- **Costo total de la BOM eléctrica 24 V ≈ 971 EUR (≈ 7 260 DKK)**, ≈ 1 050–1 150 EUR con SW80 y envíos [ESTIMADO]; la batería + cargador son el 42 % (413 EUR), el tren motor/VESC/antichispa con IVA el 31 % (302 EUR).

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

No usados / sin acceso: hobbyking.com (403), svb24.com y svb.de (403), conrad.de (403), amazon.de (503), makerbase3d.com (captcha), let-elektronik.dk (búsqueda demasiado lenta, sin resultado en esta sesión), Jem & Fix / Elextra / RS DK (no fueron necesarios: Reichelt DK cubrió electrónica y Biltema/Watski lo marino).
