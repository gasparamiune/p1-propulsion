# R08b — Sourcing de la BOM mecánica con envío a Dinamarca (cola larga eléctrica P1)

Consulta: 2026-10-01. Autor: subagente de investigación P1. Alcance: piezas mecánicas compradas (no motor/ESC/batería) para la arquitectura candidata "cola larga" (motor seco arriba + HTD-5M + eje 316 inclinado en tubo + hélice de fueraborda chico con pasador de corte + kick-up), con precio y link **abierto en esta sesión**.

**Método y límites.** El cupo de WebSearch de la sesión estaba agotado, y Bing/DDG/Brave/Mojeek devolvían bloqueos o basura. Por eso fui directo a los buscadores y API de cada tienda: Watski `/search/?query=`, Biltema `find.biltema.com/v4/web/typeahead/400/da/`, AWN `search/suggest.json` y `products/<handle>.js`, Kugellager-Shop `catalogsearch`, igus `product/35?artNr=`, 3DJake `ld+json`, Dold y Tohatsu.de en HTML. No pude abrir estas tiendas (403/502/TLS/Cloudflare): kugellager-express.de, svb.de, maedler.de, misumi-ec, accu.co.uk, ebay.de/.dk, amazon.de (captcha/503), simplybearings (429), wurth.dk, 3djake.dk (certificado autofirmado vía proxy), polymaker.com, kipp/norelem (SSL), boats.net y marineengine (403), solasprop.com, baadudstyr.dk, 12voltshop.dk y varias metalerías DE/DK.

**Convenciones.** Los precios van tal cual los muestra la tienda: DKK con 25 % de moms para Watski y Biltema; EUR con 19 % de MwSt alemán para AWN, Kugellager-Shop, Dold y 3DJake.de, salvo donde se aclara. Para un comprador privado en DK, una tienda de la UE debería facturar con IVA danés (25 %), así que el precio final ≈ neto × 1,25 [ESTIMADO: reglas OSS de venta a distancia UE, memoria técnica, no verificado]. Uso 1 EUR = 7,46 DKK [ESTIMADO: paridad ERM-II 7,46038, memoria técnica, no verificado].

---

## 0. Resumen ejecutivo

| Bloque | Mejor opción encontrada (link abierto) | Precio | Etiqueta |
|---|---|---|---|
| Tubo-pata 316 | Watski "Rør AISI 316 25 mm × 1,2 mm × 2 m" | 359 kr (≈ 48 €) | [VERIFICADO] |
| Eje 316 macizo Ø12–16 | **No encontré tienda abierta con 316**; solo hay 1.4301 (V2A) en stahlshop.de a 13,80 €/kg | 1.4301 Ø16 ≈ 22 €/m | [VERIFICADO precio/kg] + [ESTIMADO €/m] |
| Bujes sumergidos | igus iglidur **H370** (igus recomienda "UW500 or H370" para uso bajo agua) | 2,71–3,34 €/u | [VERIFICADO] |
| Rodamientos "inox" | Kugellager-Shop S6201/S6202/S6203-2RS y S7202-B-2RS. **Son AISI 420, no 316**, y la tienda **no envía a DK** | 4,10–14,98 € | [VERIFICADO] |
| Rodamientos lado seco | Biltema 6001/6201/6202/6203-2RS (material no declarado; acero al cromo [ESTIMADO: memoria técnica, no verificado]) | 36,90 kr/u | [VERIFICADO precio] |
| Transmisión | Dold Mechatronik HTD-5M 15 mm: 14T b8 + 72T b14 + correa cerrada | 9,40 + 39,90 + desde 3,99 € | [VERIFICADO] |
| Hélice con pasador de corte | Tohatsu MFS2.5/3.5: **309B64107-0, alu, 188 mm / 7,4" × 6** (no 7,8"). Usa pasador de corte **309-64126-1 "SCHERSTIFT 4-24"** (kit 3GT-87500-0). Sin precio en tienda abierta | ~45–70 € | [VERIFICADO spec + pasador] + [ESTIMADO precio] |
| Ánodo | Tecnoseal/Technoseal ánodo de collar de **aluminio**: Ø19 (92 kr), Ø22 (81 kr), Ø25 (96 kr) | 81–96 kr | [VERIFICADO] |
| Antigalvánico | Tikal Tef-Gel 10 g / 60 g (AWN) | 16,99 / 41,89 € | [VERIFICADO] |
| Tornillería A4 | Watski (Comstedt A4) en blísteres de 2–10 u | 27–80 kr/blíster | [VERIFICADO] |
| PETG | eSUN PETG+ 1 kg (3DJake) / PolyLite PETG 1 kg | 15,99 / 19,99 € | [VERIFICADO] |
| **Total BOM mecánica comprada** (1 unidad, sin motor/ESC/batería, con envío) | ver §10 | **≈ 470–605 € (≈ 3 500–4 500 kr)** | [ESTIMADO: suma §10] |

Referencias comerciales (misma fecha): un Minn Kota Endura C2 30 12 V completo cuesta **1 799 kr** y es de agua dulce ("Hækmonteret ferskvand"). Un ePropulsion Spirit 1.0 Plus cuesta **8 930 kr sin batería** (pata corta o larga; pata estándar 9 299 kr) y su batería 1 276 Wh **9 390 kr** (listada como accesorio en la misma página) [VERIFICADO: https://www.watski.dk/minn-kota-endura-c2-30-12v-11Jei] [VERIFICADO: https://www.watski.dk/Epropulsion-Spirit-10-Plus-3hk-11crR].

---

## 1. Logística a Sønderborg (dato nuevo que afecta el sourcing)

| Hecho | Detalle | Fuente |
|---|---|---|
| Algunas tiendas DE dejaron de enviar a DK por la PPWR | Kugellager-Shop (CQ GmbH): "Aufgrund der neuen EU-Verpackungsverordnung (PPWR), die im August 2026 in Kraft getreten ist … nicht mehr möglich, alle EU-Mitgliedstaaten zu beliefern". La lista de países **no incluye Dänemark**. DE: 3,50 €, gratis desde 35 € | [VERIFICADO: https://www.kugellager-shop.net/kugellager-versand/] |
| Dold Mechatronik sí envía a Europa | "Wir beliefern Deutschland, Europa und die Schweiz"; el costo a cada país se calcula en el carrito. En DE: paquete ≤2 kg 6,90 € y carta ≤500 g 3,50 € | [VERIFICADO: https://www.dold-mechatronik.de/Versandinformationen] |
| 3DJake lista Dänemark entre los destinos | 3djake.de: envío gratis en DE desde 52,90 €. 3djake.dk no abrió (error TLS en el proxy) | [VERIFICADO: https://www.3djake.de/info/versand-und-lieferung] |
| Watski entrega en DK | "Hurtig levering, 1-3 hverdage", "60 dages returret" | [VERIFICADO: https://www.watski.dk/propel-78-x-8-mercury-110aj] |
| AWN cobra envío especial por largo | En el tubo de 2 m: "aufgrund der Länge extra Speditionskosten" | [VERIFICADO: https://awn.de/products/edelstahlrohr] |
| Tarifas AWN a la UE | Estándar (<31 kg, <1,20 m) a "EU-Länder": **19,99 €**; flete (Spedition) a la UE: "auf Anfrage". AWN se reserva cancelar "Insellieferungen" (Sønderborg está en parte sobre la isla de Als: riesgo, [SUPUESTO]) | [VERIFICADO: https://awn.de/policies/shipping-policy] |
| Alternativa práctica | Para las tiendas DE sin envío a DK: entregar en un paketshop/Packstation de Flensburg/Harrislee (~40 km de Sønderborg) y retirar | [SUPUESTO; distancia ESTIMADO] |

---

## 2. Eje, tubo-pata y semielaborados

| Componente | Especificación mínima | Producto | Tienda | Link abierto | Precio | Fecha | Etiqueta |
|---|---|---|---|---|---|---|---|
| Tubo-pata | 316, Ø25 × 1,2–1,5, ≥1,5 m | Rør AISI 316 25 mm × 1,2 mm × 2 m (art. 408648; `stock:false` = va por proveedor) | Watski DK | https://www.watski.dk/ror-aisi-316-25-mm-x-1-2-mm-x-2-m-1b3iu | **359 kr** | 2026-10-01 | [VERIFICADO] |
| Tubo-pata (alt. rígida) | 316, Ø30 × 1,5 | Rør AISI 316 30 mm × 1,5 mm × 3 m, "spejlpoleret" | Watski DK | https://www.watski.dk/ror-aisi-316-30-mm-x-1-5-mm-x-3-m-1b3io | **729 kr** | 2026-10-01 | [VERIFICADO] |
| Tubo-pata (alt. barata, grado sin declarar) | Ø25 × 1,5, 2 m | Osculati "Edelstahlrohr geschweißt, poliert", variantes 20/22/25 × 1,5. **No dice el grado** | AWN DE | https://awn.de/products/edelstahlrohr | 20 × 1,5: 18,29 €; **25 × 1,5: 45,99 € (agotado)** | 2026-10-01 | [VERIFICADO] |
| Eje macizo | **316/316L** Ø14–16 × 1–1,5 m, h9 o mejor | No encontré tienda abierta con 316 en barra chica | — | buscar: "Rundstab 1.4404 Ø15 h9 1000 mm", "rustfri rundstang syrefast 16 mm", "AISI 316 round bar 15mm 1m" | ≈ 30–45 € por 1,2 m | — | [ESTIMADO: 1.4301 a 13,80 €/kg × 1,40 kg/m (Ø15) × 1,2 m ≈ 23 €; ×1,3–1,5 por 316, memoria técnica] |
| Eje (sustituto **solo seco**) | 1.4301 Ø12/16 | "Edelstahl Rund 16 geschliffen", 1.4301 (V2A), corte ±3 mm; 13,80 €/kg (<5 kg) | stahlshop.de | https://stahlshop.de/edelstahl/rundstahl-geschliffen/edelstahl-rund-16-geschliffen-detail | 13,80 €/kg → Ø16 ≈ 21,9 €/m; Ø12 ≈ 12,3 €/m | 2026-10-01 | [VERIFICADO €/kg] [ESTIMADO €/m: 1,59 y 0,89 kg/m]. La propia tienda advierte: "1.4301 (V2A) ist nicht geeignet für direkten Kontakt mit Salzwasser … 1.4404 oder 1.4571 (V4A) die bessere Alternative" [VERIFICADO] |
| Eje comercial (referencia) | Ø25 con tuerca | Vetus Niro-Welle mit Hutmutter L = 1000 mm, Ø25: **dúplex 1.4462 (no 316)**, "inkl. Zinkanode", extremo según ISO 4566 | AWN DE | https://awn.de/products/vetus-niro-welle-mit-hutmutter-l-1000mm-o25mm | 347,49 € | 2026-10-01 | [VERIFICADO] (sobredimensionado y caro) |
| Bocina tipo cutlass (referencia) | Lubricada por agua | 1852 Vandsmurt propelaksel Ø25 eje / Ø42 tubo | Watski DK | https://www.watski.dk/1852-vandsmurt-propelaksel-selvludluftende-oe25mm-aksel-42mm-roer-11LV7 | 531 kr | 2026-10-01 | [VERIFICADO] (no hay Ø12–16 → bujes igus o POM torneado) |
| Tubo pultruido de fibra de vidrio | Ø25–30 × 2–3 mm | No encontrado en tiendas abiertas (Watski solo tiene túneles de bow-thruster; AWN, "Vetus GFK-Stevenrohr 30 mm, L=1500 mm" a 215,09 € [VERIFICADO: https://awn.de/products/vetus-gfk-stevenrohr-o-30-mm-l-1500-mm]) | — | buscar: "GFK Rohr pultrudiert 30x26 1000 mm", "glasfiberrør 30 mm pultruderet" | 15–35 €/m | — | [ESTIMADO: memoria técnica, no verificado] |
| Varilla para tornear bujes | POM-C o UHMW-PE Ø30–40 × 200 mm | No encontrada en tienda abierta (s-polytec y Modulor sin resultados útiles por scraping) | — | buscar: "POM-C Rundstab 40 mm Zuschnitt", "PE-UHMW Rundstab 40 mm" | 5–15 € | — | [ESTIMADO: memoria técnica, no verificado] |

---

## 3. Rodamientos y bujes

| Componente | Especificación mínima | Producto | Tienda | Link abierto | Precio | Fecha | Etiqueta |
|---|---|---|---|---|---|---|---|
| Buje sumergido Ø12 | Polímero apto bajo agua | iglidur H370 **H370SM-1214-15** / **-20** | igus.eu | https://www.igus.eu/product/35?artNr=H370SM-1214-15 | 2,71 € (1 u); 0,63 € (100 u) / -20: 2,81 € | 2026-10-01 | [VERIFICADO] (precio JSON de la página; IVA no declarado en el JSON) |
| Buje sumergido Ø14 | ídem | H370SM-1416-15 / **-20** | igus.eu | https://www.igus.eu/product/35?artNr=H370SM-1416-20 | 2,85 € / **3,34 €** | 2026-10-01 | [VERIFICADO] |
| Buje sumergido Ø15 | ídem | H370SM-1517-20 | igus.eu | https://www.igus.eu/product/35?artNr=H370SM-1517-20 | 3,08 € | 2026-10-01 | [VERIFICADO] |
| Buje sumergido Ø16 | ídem | H370SM-1618-15 / **-20** ("ready for shipping in 24 hours") | igus.eu | https://www.igus.eu/product/35?artNr=H370SM-1618-20 | 2,97 € / **3,10 €** | 2026-10-01 | [VERIFICADO] |
| Justificación del material | — | En la ficha de iglidur X6, "When not to use it?" dice "When a bearing is sought for underwater use" y deriva a **"iglidur UW500"** o **"iglidur H370"**. H370: "excellent wear resistance under water", "low moisture absorption", y también **"Electrically conductive"** (no aísla eje de tubo) | igus.eu | https://www.igus.eu/product/27?artNr=UWSM-1214-15 (ojo: /product/27 abre la ficha de **X6**, no de UW500, pese al artNr) ; https://www.igus.eu/product/35?artNr=H370SM-1618-20 | — | 2026-10-01 | [VERIFICADO] (UW500 figura "Upon request" en la ficha X6) |
| Rodamiento "inox" 12 mm | 6001-2RS | S6001 2RS (Edelstahl) | Kugellager-Shop DE (**no envía a DK**) | https://www.kugellager-shop.net/catalogsearch/result/?q=S6001-2RS | 3,25 € (neto 2,73) | 2026-10-01 | [VERIFICADO] |
| Rodamiento "inox" 12 mm | 6201-2RS | S6201 2RS, **"AISI420 / 1.4028 / X30Cr13"**, art. 22921 | Kugellager-Shop | https://www.kugellager-shop.net/ss6201-2rs-edelstahl-kugellager.html | 4,10 € (neto 3,45) | 2026-10-01 | [VERIFICADO] |
| Rodamiento "inox" 15 mm | 6202-2RS | S6202 2RS, AISI420, ≥55 HRC | Kugellager-Shop | https://www.kugellager-shop.net/ss6202-2rs-edelstahl-kugellager.html | 5,25 € (neto 4,41); 10+: 2,59 € | 2026-10-01 | [VERIFICADO] |
| Rodamiento "inox" 17 mm | 6203-2RS | S6203 2RS, AISI420 | Kugellager-Shop | https://www.kugellager-shop.net/ss6203-2rs-edelstahl-kugellager.html | 5,70 € (neto 4,79) | 2026-10-01 | [VERIFICADO] |
| Contacto angular inox (empuje) | 7202, 15 × 35 × 11 | **S7202-B-2RS TN**, 40°, AISI420, jaula PA66, sellos NBR | Kugellager-Shop | https://www.kugellager-shop.net/s7202-b-2rs-ss-7202-2rs-edelstahl-schraegkugellager-15x35x11mm.html | 14,98 € (neto 12,59) | 2026-10-01 | [VERIFICADO] |
| Rodamiento 316 real | AISI 316 | No hallado en tiendas abiertas | — | buscar: "6202-2RS AISI 316 bearing", "Rillenkugellager 1.4401" | 15–30 €/u | — | [ESTIMADO: memoria técnica, no verificado] |
| Rodamientos lado seco (DK) | 6001/6201/6202/6203-2RS (Biltema no declara material; "acero al cromo" es [ESTIMADO: memoria técnica]) | Biltema art. 41413 / 41408 / **41405** / 41404 | Biltema DK | https://www.biltema.dk/bil---mc/bilreservedele/kuglelejer/kuglelejer-6202-2rs-15x35x11-mm-2000050558 (y 6001: …-2000050563, 6201: …-2000050560, 6203: …-2000050557) | **36,90 kr** c/u | 2026-10-01 | [VERIFICADO: API https://find.biltema.com/v4/web/typeahead/400/da/?query=6202-2RS + páginas abiertas] |

---

## 4. Transmisión HTD-5M (correa 15 mm)

| Componente | Especificación mínima | Producto | Tienda | Link abierto | Precio | Fecha | Etiqueta |
|---|---|---|---|---|---|---|---|
| Polea motor | HTD-5M, 15 mm, 14–16 T, bore 8 | 14 Zähne, Bohrung 8,00 mm H7 mit Klemmschrauben | Dold Mechatronik DE | https://www.dold-mechatronik.de/Zahnriemenrad-HTD-5M-15mm-breit | **9,40 €** | 2026-10-01 | [VERIFICADO] |
| Polea motor (alt.) | 16 T b8 / 20 T b8–b14 | 16 T b8: 12,90 €; 20 T b8/b10/b12/b14: 10,00–13,90 € (hay variantes "Stahl" a 13,90–14,50 €) | Dold | ídem | 10,00–14,50 € | 2026-10-01 | [VERIFICADO] |
| Polea eje | HTD-5M 15 mm, 60–72 T, bore 12–16 | **72 Zähne**, bore 6,35 / 8 / 10 / **14,00 mm H7**, con prisioneros, 0,22 kg. **No hay 60 T** en el listado; los siguientes por debajo son 48 T y 40 T (también existen 24 T y 32 T) | Dold | ídem | **39,90 €** | 2026-10-01 | [VERIFICADO] |
| Correa | HTD-5M cerrada, 15 mm, 400–600 mm | "Zahnriemen geschlossen HTD-5M, Breite 15mm", **Neopren mit Glasfaser-Zugstrang**, 205 largos de 175 a 4 260 mm (pese a "bis-499mm" en la URL). **"Nicht vorrätig" en 400–700: 400, 450, 500 y 505 mm** (fuera de ese rango también 250, 270, 300, 375, 380, 740, 750, 790); con stock en pasos de 5–10 mm dentro de 405–440, 460–495 y 510–695 mm (faltan, p. ej., 415, 445, 455, 545) | Dold | https://www.dold-mechatronik.de/Zahnriemen-geschlossen-HTD-5M-Breite-15mm-Laenge-bis-499mm | "ab 3,99 €" (el precio de cada largo no aparece en el HTML) | 2026-10-01 | [VERIFICADO desde-precio] + [ESTIMADO 500 mm: 5–9 €] |
| Relaciones disponibles con 72 T | — | 14 T → 5,14:1 · 16 T → 4,50:1 · 20 T → 3,60:1 | — | — | — | — | [CALCULADO] |

---

## 5. Hélice, pasadores y transmisión de la hélice

| Componente | Especificación mínima | Producto | Tienda | Link abierto | Precio | Fecha | Etiqueta |
|---|---|---|---|---|---|---|---|
| Hélice OEM 2,5–3,5 hp (alu) | ~7,4–7,8", paso 5–6, pasador de corte | **Tohatsu 309B64107-0**: "Propeller Dia: 188 mm / 7.4 in", "Pitch: 6", "Material: Aluminium", para MFS 3.5, MFS 2.5, M3.5, M2.5 | tohatsu.de (catálogo, sin tienda) | https://www.tohatsu.de/zubehoer/propeller | No figura. buscar: "309B64107-0" | 2026-10-01 | [VERIFICADO spec]; precio [ESTIMADO: 45–70 €, base: hélices alu 7 1/2–7 3/4" de 4–6 hp en Watski a 399–619 kr ≈ 53–83 €; el rango 45–70 € queda por debajo de esa base] |
| Hélice OEM (plástico) | ídem | Tohatsu **309-64106-0** 7,4" × 6 (Plastik); **314B64103-0** 7,4" × 4,5 (Plastik; también M4) | tohatsu.de | ídem | No figura | 2026-10-01 | [VERIFICADO spec] |
| Pasador de corte, chaveta y arandela MFS2/2.5/3.5B | — | Kit de mantenimiento **3GT-87500-0** "Wartungsset für MFS2/2.5/3.5B" contiene **309-64126-1 "SCHERSTIFT 4-24"**, **951503-0435 "SPLINT 4-35"** y **3H6-07406-0 "UNTERLEGSCHEIBE 10.2-19-1"** | tohatsu.de | https://www.tohatsu.de/zubehoer/wartungssets | — | 2026-10-01 | [VERIFICADO códigos]. Lectura "4-24" = Ø4 × 24 mm y "10.2-19-1" = arandela Ø10,2 × 19 × 1 → eje de hélice ≈ Ø10 mm [ESTIMADO: inferencia de la nomenclatura, no verificado] |
| Bore del cubo, rosca de la tuerca | — | **No encontrados** en fuentes abiertas | — | buscar: "Tohatsu MFS3.5C propeller shaft diameter", "Tohatsu MFS2.5 propeller nut thread" | — | — | Pendiente: medir sobre la hélice comprada |
| Hélices alu 7 3/4" (contraejemplo) | — | Polastorm 7 3/4" × 8 / × 7 para Mercury 4–6 hp y Tohatsu MFS4/5/6 con **"Splines: 12 stk"** (que no lleven pasador de corte es [ESTIMADO: inferido de las estrías; la página no lo dice]) | Watski | https://www.watski.dk/propel-78-x-8-mercury-110aj ; https://www.watski.dk/propel-78-x-7-mercury-110ab | 411 / 448 kr | 2026-10-01 | [VERIFICADO] |
| Solas Amita 3 (contraejemplo) | — | Tohatsu MFS4/5/6, M5B; "12 Splines, Udstødning gennem nav" | Watski | https://www.watski.dk/-11I6X | 619 kr | 2026-10-01 | [VERIFICADO] |
| Yamaha 7 1/2" (contraejemplo) | — | 7 1/2" × 7, F4/F5/F6C y 4A/5C, **"Splines (9 stk)"**, OEM 6E0-45943-00-EL | Watski | https://www.watski.dk/propel-7-1-2-x-7-ba-yamaha-11Hrp | 399 kr | 2026-10-01 | [VERIFICADO] |
| Hélice de trolling (con pin) | Minn Kota (eje 3/8" [ESTIMADO: la página solo lista como accesorio la tuerca "MKP-9 propelmøtrik 3/8""]) | **MKP-6** Weedless Wedge: Endura 30–45, Traxxis 33–45, etc.; "Leveres med møtrik og stift" | Watski | https://www.watski.dk/MKP-6-propel-wedges-11cEV | **350 kr** | 2026-10-01 | [VERIFICADO] |
| Hélice de trolling (más empuje) | 46–70 lb | MKP-32 Weedless Wedge 2, "Leveres med møtrik og stift" | Watski | https://www.watski.dk/MKP-32-propel-wedges-2-11cE4 | 485 kr | 2026-10-01 | [VERIFICADO] |
| Pin de arrastre Minn Kota | 30–70 lb | "Omskifterpind Minn Kota 30-70 lb.", Minn Kota 2092600, unitario | Watski | https://www.watski.dk/omskifterpind-minn-kota-30-70-lb-11GmH | **13 kr** | 2026-10-01 | [VERIFICADO]; que sea el drive pin [ESTIMADO] |
| Pin de corte Minn Kota 80–112 lb | — | "Brydepind Minn Kota 80-112 lb" | Watski | https://www.watski.dk/brydepind-minn-kota-80-112-lb-11GmA | 17 kr | 2026-10-01 | [VERIFICADO] |
| Tuerca de hélice Minn Kota | — | MKP-34 propelmutt E | Watski | https://www.watski.dk/MKP-34-propelmutt-E-11Gvr | 150 kr | 2026-10-01 | [VERIFICADO] |
| Pasadores de corte de repuesto (genéricos) | Pasadores calibrados | Solo hallé los de bow-thruster Lewmar: 110TT 3,5 × 20 mm 70 kr; 140TT 4 × 20 mm 70 kr; 185TT 5 × 22 mm (alu) 85 kr | Watski | https://www.watski.dk/Brytpinnar-for-bovpropeleller-116kw | 70–110 kr | 2026-10-01 | [VERIFICADO] (sirven de stock calibrado si el bore del cubo coincide) |
| Pasador elástico inox | Spannstift | DIN 1481 en **1.4310 ("Edelstahl A2")**, variante mostrada 3 × 18 mm × 1000 u (0,02 €/u); espiral DIN 7343 1.4310, 5 × 40 mm × 500 u, 68,14 €. Otras variantes/packs no revisados | befestigungsfuchs.de | https://www.befestigungsfuchs.de/search?search=Spannstift | sin precio unitario útil para 5–10 u | 2026-10-01 | [VERIFICADO existencia]; buscar: "Spannstift ISO 8752 A4 5x30" |

---

## 6. Corrosión: ánodo, compuesto, aislación

| Componente | Especificación mínima | Producto | Tienda | Link abierto | Precio | Fecha | Etiqueta |
|---|---|---|---|---|---|---|---|
| Ánodo de collar, **aluminio** (agua salobre) | Collar para Ø chico | Tecnoseal Akselanode **Aluminium 25 mm Aksel, Smal 20 mm** (art. **204496**); 30 mm: 84 kr (**204498**); 35 mm: 91 kr (**204500**) | Watski | https://www.watski.dk/tecnoseal-akselanode-aluminium-aksel-smal-11Hml | **96 kr** | 2026-10-01 | [VERIFICADO] (números de artículo corregidos en la verificación) |
| Ánodo de collar alu 22 mm | — | Technoseal Akselanode Aluminium 55/22 mm (art. 204514; "Indvendig diameter 22 mm", ext. 54,4 mm). La misma familia ofrece 55/19, 55/25, 58/32, 64/30, 65/35… | Watski | https://www.watski.dk/Technoseal-Akselanode-Aluminium-55-22mm-11LJu | 81 kr | 2026-10-01 | [VERIFICADO] |
| Ánodo de collar alu **19 mm** (el más chico hallado) | — | Technoseal Akselanode Aluminium 55/19 mm (art. 204513; "Indvendig diameter 19 mm", ext. 54,4 mm; en stock) | Watski | https://www.watski.dk/technoseal-akselanode-aluminium-5519mm-11LJU | **92 kr** | 2026-10-01 | [VERIFICADO] |
| Ánodo de placa alu | Atornillable al soporte | Tecnoseal Alu tallerken anode sæt Ø72 mm, 11 mm de alto, 150 g, agujero 11 mm (art. 208173) | Watski | https://www.watski.dk/Tecnoseal-Alu-tallerken-anode-saet-OE72mm-150g-11Etq | 126 kr | 2026-10-01 | [VERIFICADO] |
| Ánodo alu cilíndrico chico | — | 1852 aluanoder Small 0,15 kg, 95 × 34 | Watski | https://www.watski.dk/1852-aluanoder-11wZc | 59 kr | 2026-10-01 | [VERIFICADO] |
| Ánodo de eje cónico 22–25 (alt.) | — | Plastimo Wellenanode konisch 22–25 mm (material no indicado; agotado) | AWN | https://awn.de/products/plastimo-wellenanode-konisch-welle-22-25mm | 5,46 € | 2026-10-01 | [VERIFICADO] |
| Anti-seize / antigalvánico | PTFE, apto agua de mar | **Tikal Tef-Gel 10 g** (T10); 60 g: 41,89 €. "seewasserbeständiges Schmiermittel" | AWN | https://awn.de/products/533335-tikal-tef-gel-antikorrosion-t10-lose-weiss-10g ; https://awn.de/products/tikal-tef-gel-antikorrosion-60g-weiss | **16,99 €** / 41,89 € | 2026-10-01 | [VERIFICADO] |
| Lanocote / Duralac | — | Sin resultados en Watski ni AWN | — | buscar: "Lanocote 30 g", "Duralac 115 ml" | 15–25 € | — | [ESTIMADO: memoria técnica, no verificado] |
| Arandelas aislantes | Nylon/fibra M5–M12 | Biltema "Fiber- og nylonskiver, 200 stk." (M3, M5, M6, M8, M10, M12), art. 191083 | Biltema DK | https://www.biltema.dk/bil---mc/varkstedsudstyr/befastelser/skiver/fiber--og-nylonskiver-200-stk-2000064326 | **84,90 kr** | 2026-10-01 | [VERIFICADO] |
| Arandelas G10 | — | No hallado | — | buscar: "G10 Unterlegscheibe M8", "FR4 skive M8" | — | — | — |

---

## 7. Tornillería A4, insertos, pasadores con bola

Todo lo de Watski es Comstedt A4; los precios son por blíster [VERIFICADO en las páginas indicadas, 2026-10-01].

| Componente | Variante / art. | Precio | Link abierto |
|---|---|---|---|
| Tuerca autoblocante nyloc A4 | M5 10P (118604) 27 kr · **M6 10P (118605) 34 kr** · **M8 10P (118606) 41 kr** | 27–41 kr | https://www.watski.dk/nylon-insert-lock-nut-a4-11KgL |
| Arandela A4 | M5 5,3 × 10 (118664) · M6 6,4 × 11,5 (118665) · M8 8,4 × 16 (118666), 10P | 27 kr c/u | https://www.watski.dk/washer-a4-11KgQ |
| Tornillo hexagonal A4 | M6 × 20/25/30 10P 48 kr · M6 × 40 5P 41 kr · M6 × 50 5P 32 kr · M6 × 60 5P 48 kr · **M8 × 20–50 2P 34 kr** · M8 × 60 2P 41 kr · M8 × 80/100 2P 48 kr | 32–48 kr | https://www.watski.dk/hexagon-machine-screw-a4-11KtO |
| Tornillo avellanado Torx A4 | M5 × 16 10P 34 kr … M6 × 80 2P 80 kr | 29–80 kr | https://www.watski.dk/machine-screw-torx-a4-11KFl |
| Tornillo cabeza redonda Torx A4 | M5 × 20 10P 41 kr … M6 × 50 5P 60 kr | 41–60 kr | https://www.watski.dk/pan-head-machine-screw-a4-11KFC |
| Bulón pasante grande | Watski "Bolt 8 × 130 mm A4 DIN 931 1st" 19 kr; "Bolt 10 × 80 A4" 22 kr | 19–35 kr | https://www.watski.dk/search/?query=insexskrue%20A4 |
| Inserto roscado para plástico | ruthex **M5 × 9,5 (50 u)**, **M6 × 12,7 (25 u)**, **M8 × 12,7 (20 u)**, **latón** ("Aus Messing") | 9,99 € c/pack | https://www.3djake.de/ruthex/gewindeeinsatz-m6-25-stueck (también /gewindeeinsatz-m5-50-stueck, /gewindeeinsatz-m8-20-stueck) |
| Inserto inoxidable | No hallado en tiendas abiertas | — | buscar: "Gewindeeinsatz Edelstahl Kunststoff M6 einpressen", "stainless heat-set insert M6" |
| Pasador con bola (quick-release) | "SS låsebolt 6 mm": Ø6, "Arbejdslængde mm: 20", "fjederbelastet låsemekanisme", grado no indicado (art. 408988) | 29 kr | https://www.watski.dk/ss-lasebolt-6-mm-1b3S3 |
| Pasador con bola + cable | "Plade i rustfrit stål + wire med låsebolt med fjederkugle", Ø6, cable Ø1,6 | 39 kr | https://www.watski.dk/plade-i-rustfrit-staal-wire-med-laasebolt-med-fjederkugle-1b3SM |
| Spring plunger inox M8–M10 | No encontrado en tiendas abiertas (AWN y Befestigungsfuchs sin resultado; kipp/norelem/maedler bloqueados) | 5–12 €/u | buscar: "Federndes Druckstück Edelstahl M8 GN 615", "Kugeldruckstück 1.4305 M10" [ESTIMADO: memoria técnica, no verificado] |

---

## 8. Impresión 3D (Ender-3 S1, Sprite ≤260 °C)

| Componente | Especificación mínima | Producto | Tienda | Link abierto | Precio | Fecha | Etiqueta |
|---|---|---|---|---|---|---|---|
| PETG 1 kg (económico) | 1,75 mm | eSUN PETG+ 1,75 mm / 1000 g (InStock) | 3DJake.de | https://www.3djake.de/esun/petg-yellow-12 | **15,99 €** | 2026-10-01 | [VERIFICADO] |
| PETG 1 kg | 1,75 mm | Polymaker PolyLite PETG Schwarz 1 000 g (la variante de 3 kg cuesta 59,99 € y está OutOfStock) | 3DJake.de | https://www.3djake.de/polymaker/polylite-petg-schwarz | **19,99 €** | 2026-10-01 | [VERIFICADO] |
| PETG premium | — | Prusament PETG Jet Black 1 kg; boquilla "250±10 °C", cama "80±10 °C" | prusa3d.com | https://www.prusa3d.com/product/prusament-petg-jet-black-1kg/ | 29,99 USD (geo-IP; el EUR no se mostró) | 2026-10-01 | [VERIFICADO] |
| ASA | — | Prusament ASA Jet Black 800 g; **boquilla "260±5 °C"**, **cama "110±5 °C"**, "Use an enclosure with filtration…" | prusa3d.com | https://www.prusa3d.com/product/prusament-asa-jet-black-850g/ | 25,92 USD | 2026-10-01 | [VERIFICADO] |
| Límite del hotend | — | Creality Sprite Extruder: "Standard Hotend-Kit ( ≤ 260 °C)", "Speziell für 3D Drucker: Creality Ender 3 S1"; boquillas MK8 [ESTIMADO: la página lo sugiere vía "häufig zusammen gekauft" con boquilla MK8] | 3DJake.de | https://www.3djake.de/creality-3d-drucker-ersatzteile/sprite-extruder | 74,99 € (Pro: 89,99 € [NO VERIFICADO: no aparece en la página]) | 2026-10-01 | [VERIFICADO] |
| Boquilla templada MK8 | 0,4 mm | BROZZL MK8 Düse Stahl gehärtet; menciona "Creality Ender 3 S1". Un comprador: "um ca. 10 - 15 Grad erhöhen" | 3DJake.de | https://www.3djake.de/brozzl/mk8-duese-stahl-gehaertet | **14,99 €** | 2026-10-01 | [VERIFICADO] |
| Boquilla templada (premium) | — | Micro-Swiss Düse MK8 Stahl gehärtet 0,4 mm | 3DJake.de | https://www.3djake.de/micro-swiss/duese-mk8-stahl-gehaertet | 21,99 € | 2026-10-01 | [VERIFICADO] |

---

## 9. Mando, seguridad, varios

| Componente | Especificación mínima | Producto | Tienda | Link abierto | Precio | Fecha | Etiqueta |
|---|---|---|---|---|---|---|---|
| Caña / manija telescópica | Al, con puño | Teleskophandgriff Pinnenverlängerung 75–130 cm "mit Abstellknopf" (Al anodizado, encaja en caña de hasta Ø ~46 mm); 70 cm: 21,99 €; 70 cm con botón: 17,59 € (agotadas) | AWN | https://awn.de/products/pinnenverlangerung-stufenlos-teleskopierbar-von-75-130cm-mit-abstellknopf | 39,99 € | 2026-10-01 | [VERIFICADO] |
| Manija inox | AISI 316 | Biltema "Håndgreb rustfri, silikonepakning, 300 mm", AISI 316 | Biltema DK | https://www.biltema.dk/baad/daksudstyr/soegelaender-og-baad-raekvaerk/handgreb-rustfri-silikonepakning-300-mm-2000060280 | 129 kr | 2026-10-01 | [VERIFICADO] |
| Mosquetón 316 | AISI 316 | Biltema "Karabinhage med øje, 4,6 × 55 mm" (AISI316) art. 250190 · "Karabinhage rustfri, 6 × 60 mm" (AISI316) art. 250194 | Biltema DK | https://www.biltema.dk/baad/daksudstyr/karabinhager/karabinhage-med-oje-46-x-55-mm-2000065114 ; https://www.biltema.dk/baad/daksudstyr/karabinhager/karabinhage-rustfri-6-x-60-mm-2000065104 | 39,90 / 34,90 kr | 2026-10-01 | [VERIFICADO] |
| Mosquetón 316 grande | — | Karabinhage AISI 316 med ring 120 mm (art. 401565) | Watski | https://www.watski.dk/karabinhage-aisi-316-med-ring-120-mm-11S77 | 89 kr | 2026-10-01 | [VERIFICADO] |
| Kill-cord (cordón + llave) | Espiral con clip | Sicherheitskordel für Notstopschalter mit 7 × Schlüssel (Mercury, Suzuki, Tohatsu, Honda, Yamaha…) | AWN | https://awn.de/products/sicherheitskordel-fur-notstopschalter-mit-7-x-schlussel-fur-aussenborder | **5,99 €** | 2026-10-01 | [VERIFICADO] |
| Interruptor de parada (mecánico) | — | AWN "Not-Stopp-Schalter für Außenborder", tapa roja | AWN | https://awn.de/products/not-stopp-schalter-fur-aussenborder | 11,49 € | 2026-10-01 | [VERIFICADO] (rating eléctrico no declarado → solo como señal hacia el ESC, nunca en serie con la potencia) |
| Interruptor + llave + flotador | — | Watski "Nødstopafbryder med sikkerhedsnøgle og flyder" (art. 402945, stock:false) | Watski | https://www.watski.dk/nodstopafbryder-med-sikkerhedsnoegle-og-flyder-1b1Vp | 139 kr | 2026-10-01 | [VERIFICADO] |
| Clip de repuesto | — | Clip für Notstopschalter Tohatsu | AWN | https://awn.de/products/clip-fur-notstopschalter-tohatsu | 6,59 € | 2026-10-01 | [VERIFICADO] |
| Cabo de seguridad / retenida del motor | PP 4 mm | Rulle med flettet polypropylenline 4 mm × 12 m | Watski | https://www.watski.dk/rulle-med-flettet-polypropylenline-rod-4-mm-x-12-m-11khD | 69 kr | 2026-10-01 | [VERIFICADO] |
| Lanyard inox | — | Osculati "Lanyard Assembly", 11 mm, "Edelstahl A4" (agotado) | AWN | https://awn.de/products/lanyard-assembly | 16,98 € | 2026-10-01 | [VERIFICADO] |

---

## 10. BOM consolidada recomendada (1 unidad cola larga, sin motor/ESC/batería)

| # | Ítem | Cant. | Precio unitario | Subtotal (€) | Etiqueta |
|---|---|---|---|---|---|
| 1 | Eje 316 Ø14 o Ø15 × 1,2 m (macizo, h9) | 1 | — | 30 | [ESTIMADO §2] |
| 2 | Tubo 316 Ø25 × 1,2 × 2 m (Watski) | 1 | 359 kr | 48,1 | [VERIFICADO] |
| 3 | Bujes iglidur H370 (p. ej. 1416-20) | 3 | 3,34 € | 10,0 | [VERIFICADO] |
| 4 | Rodamiento de empuje S7202-B-2RS (Kugellager-Shop **no envía a DK**: retiro en DE o buscar alternativa) | 1 | 14,98 € | 15,0 | [VERIFICADO precio] |
| 5 | Rodamientos de cabeza (Biltema 6202-2RS, lado seco) | 2 | 36,90 kr | 9,9 | [VERIFICADO] |
| 6 | Polea HTD-5M 14 T b8 + 72 T b14 | 1 + 1 | 9,40 + 39,90 € | 49,3 | [VERIFICADO] |
| 7 | Correa HTD-5M-15 (una de repuesto) | 2 | ~7 € | 14 | [ESTIMADO §4] |
| 8 | Hélice alu Tohatsu 7,4" × 6 (309B64107-0) | 1 | — | 60 | [ESTIMADO §5] |
| 9 | Pasadores de corte de repuesto | 5 | — | 10 | [ESTIMADO] |
| 10 | Ánodo alu Ø25 (Tecnoseal) | 2 | 96 kr | 25,7 | [VERIFICADO] |
| 11 | Tef-Gel 10 g | 1 | 16,99 € | 17,0 | [VERIFICADO] |
| 12 | Arandelas fibra/nylon 200 u | 1 | 84,90 kr | 11,4 | [VERIFICADO] |
| 13 | Tornillería A4 (≈10 blísteres Watski) | — | — | 47 | [ESTIMADO: 10 × 27–48 kr] |
| 14 | Pasadores de bola 6 mm | 2 | 29 kr | 7,8 | [VERIFICADO] |
| 15 | PETG 1 kg | 2 | 15,99–19,99 € | 36 | [VERIFICADO] |
| 16 | Insertos M5/M6 (solo zona seca) | 2 packs | 9,99 € | 20 | [VERIFICADO] |
| 17 | Mosquetón 316 + cabo PP 4 mm | 2 + 1 | 39,90 + 69 kr | 20,0 | [VERIFICADO] |
| 18 | Kill-cord (cordón + llave) | 1 | 5,99 € | 6,0 | [VERIFICADO] |
| 19 | Manija telescópica | 1 | 39,99 € | 40 | [VERIFICADO] |
| — | Envíos (Watski, AWN, Dold, igus, 3DJake; tubo largo con flete) | — | — | 50–130 | [ESTIMADO: AWN a la UE 19,99 € [VERIFICADO: https://awn.de/policies/shipping-policy]; Dold/3DJake/igus a DK solo se ven en el carrito; las tarifas DE de 3,50–6,90 € **no aplican** a DK; flete del tubo 2 m sin dato → el extremo bajo de 50 € es optimista] |
| | **Total** | | | **≈ 525–605 €** (≈ 3 900–4 500 kr). Sin manija ni insertos: **≈ 470–545 €** | [ESTIMADO: suma] |

---

## 11. Pendientes ("buscar:")

- buscar: "309B64107-0 Preis" / "Tohatsu propel 7,4 x 6 aluminium" (precio + **bore del cubo y rosca de la tuerca**; el pasador ya está identificado: 309-64126-1 "SCHERSTIFT 4-24", ver §5) y "309-64126-1" para precio del pasador; idem Mercury 2.5/3.5 4T (motor Tohatsu re-marcado [ESTIMADO: memoria técnica]).
- buscar: "Rundstab 1.4404 h9 15 mm 1000 mm" (a la tienda le conviene cortar a 1,2 m); en DK: "syrefast rundstål 15 mm" en un metalgrossist local, con pedido de cotización.
- buscar: "6202-2RS AISI 316" o polímero con bolas inox ("igus xiros 6202 edelstahlkugeln") para el rodamiento inferior si quedara mojado.
- buscar: "Federndes Druckstück Edelstahl M8/M10" y "Gewindeeinsatz Edelstahl Kunststoff M6".
- buscar: "GFK Rohr pultrudiert 30 x 26", "POM-C Rundstab 40 mm Zuschnitt".
- Verificar en el carrito de Dold el costo de envío a DK y el precio de la correa de 510–560 mm.

---

## Hallazgos que cambian el diseño

- **La hélice OEM de 2,5/3,5 hp es de 7,4" (188 mm), no de 7,8".** Tohatsu lista para MFS2.5/3.5 y M2.5/3.5 la **309B64107-0 de aluminio, 7,4" × 6**, y las de plástico 309-64106-0 (7,4 × 6) y 314B64103-0 (7,4 × 4,5). El cálculo de empuje y rpm debe rehacerse con D = 188 mm y P = 6" (o 4,5"). Las hélices alu de 7 1/2–7 3/4" que se consiguen en DK (399–619 kr) son de **9–12 estrías** (sin pasador de corte [ESTIMADO: inferido]). El pasador de la MFS2/2.5/3.5B es **309-64126-1 "SCHERSTIFT 4-24"** (≈ Ø4 × 24 mm) con chaveta "SPLINT 4-35" y arandela "10.2-19-1" → eje de hélice ≈ Ø10 mm [VERIFICADO códigos: https://www.tohatsu.de/zubehoer/wartungssets; medidas ESTIMADO por nomenclatura]. **Hay que comprar la hélice antes de mecanizar el extremo del eje** para medir bore y rosca.
- **Los rodamientos "inox" baratos son AISI 420 (X30Cr13), no 316**, y Kugellager-Shop ya **no envía a DK** por la PPWR (vigente desde 08/2026). Solo sirven arriba, en seco. Abajo, en el agua, van **bujes igus iglidur H370**, que igus recomienda para uso bajo agua: **2,7–3,3 €/u** en Ø12–16. Con 3 bujes se evita el cutlass de 531 kr. Ojo: igus declara H370 **"Electrically conductive"**, así que los bujes **no aíslan** el eje del tubo; la protección galvánica depende del ánodo y del Tef-Gel. El S7202 de la BOM (ítem 4) es de Kugellager-Shop, que **no envía a DK**.
- **72 T con bore máximo 14 mm H7 (Dold, 39,90 €) fija el eje en Ø14**, o en Ø15 repasando a 15 en el torno [SUPUESTO: espesor del cubo y prisioneros no verificados]. No hay 60 T. Relaciones posibles: **5,14:1 (14 T b8, 9,40 €)**, 4,5:1 (16 T) o 3,6:1 (20 T). Si el motor tiene eje de 10 mm, la polea de 14 T b8 no sirve: usar 20 T b10 (10–13,90 €), con 3,6:1.
- **Correas HTD-5M-15 de 400, 450, 500 y 505 mm sin stock** en Dold; sí hay 405–440, 460–495 y 510–695 mm, de neopreno con fibra de vidrio. La distancia entre centros debe salir de un largo disponible (p. ej. 510 o 550 mm), y conviene un tensor o ranuras de ajuste.
- **Ánodo de collar sobre el tubo-pata, no sobre el eje.** Watski tiene ánodos de collar de aluminio para **Ø19 (92 kr, art. 204513)**, **Ø22 (81 kr, art. 204514)** y **Ø25 (96 kr, art. 204496, 20 mm de ancho)** [VERIFICADO]; el más chico hallado es Ø19, así que no hay collar para un eje de Ø12–16. El único tubo 316 verificado sigue siendo **Ø25 × 1,2** (Watski, 359 kr / 2 m) → ánodo Ø25 cerca de la hélice. Un tubo Ø19–22 sería viable con ánodo, pero no hallé tubo 316 en ese Ø (el AWN 22 × 1,5 no declara grado y está agotado).
- **No hallé barra maciza 316 en Ø12–16 en ninguna tienda abierta.** El eje 1.4301 (13,80 €/kg ≈ 22 €/m en Ø16) **no sirve sumergido** en agua salobre: la propia stahlshop.de dice "1.4301 (V2A) ist nicht geeignet für direkten Kontakt mit Salzwasser" y recomienda 1.4404/1.4571 [VERIFICADO: https://stahlshop.de/edelstahl/rundstahl-geschliffen/edelstahl-rund-16-geschliffen-detail]. Opciones: pedir 1.4404 a un metalgrossist local, o diseñar el eje para que la zona mojada sea solo el tramo dentro del tubo, con bujes H370, Tef-Gel y ánodo.
- **Los insertos ruthex son de latón**. Con tornillo A4 en agua de mar se forma un par galvánico y el latón pierde el zinc [ESTIMADO: memoria técnica]. En piezas mojadas: tuerca nyloc A4 cautiva en un alojamiento hexagonal impreso (blíster de 10 por 34–41 kr) y arandela de nylon/fibra (200 por 84,90 kr). Los insertos, solo en la zona seca.
- **ASA y filamentos cargados no son viables con el Sprite de serie.** El Sprite estándar llega a ≤260 °C, Prusament ASA pide 260 ± 5 °C con cama a 110 °C y cerramiento (o buena ventilación), y la boquilla templada pide +10–15 °C (dato de **una reseña de comprador**, no del fabricante [ESTIMADO]). Que los filamentos cargados "no son viables" es un juicio de diseño [SUPUESTO], no algo que diga una fuente. Queda **PETG sin carga a 240–250 °C con boquilla de latón**: no hace falta comprar la templada de 14,99 €. Filamento: eSUN PETG+ a 15,99 €/kg.
- **Costo:** la BOM mecánica comprada ronda **470–605 € (3 500–4 500 kr)** sin motor, ESC ni batería. Eso ya es **≈ 2–2,5×** un Minn Kota Endura C2 30 completo (1 799 kr, agua dulce) y ≈ 40–50 % de un ePropulsion Spirit 1.0 Plus sin batería (8 930 kr). El rubro envíos (50–130 €) es el más incierto: AWN cobra 19,99 € a la UE y el flete del tubo de 2 m va "auf Anfrage". La ventaja de la cola larga tiene que venir de la **autonomía** (hélice grande y lenta) y de la kick-up con pasador de corte, no del precio.
- **Kill-switch fail-safe barato:** cordón espiral con 7 llaves a 5,99 € (AWN) o interruptor con llave y flotador a 139 kr (Watski). Ninguno declara corriente nominal → **solo como entrada de habilitación del ESC o de un contactor**, nunca en serie con los 48 V.
