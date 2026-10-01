# R04 — Jon boats de aluminio < 2,5 m y referencias comerciales (trolling motors / fueraborda eléctricos)

Fecha de consulta de todas las fuentes: 2026-10-01. Alcance: (A) geometría, peso, capacidad y espejo de botes de aluminio de fondo plano chicos; (B) motores comerciales aptos para agua salada como referencia de empuje, consumo, peso y costo; (C) datos medidos de velocidad contra potencia en botes chicos, para calibrar R(v).

## 0. Método y convenciones

- **Etiquetas:** [VERIFICADO: Sx] = leído en la fuente Sx (lista en §D) abierta en esta sesión; [CALCULADO] = cuenta hecha aquí con datos verificados (fórmula indicada); [ESTIMADO: base]; [SUPUESTO]. "buscar: …" = no se pudo abrir ninguna fuente que lo respalde.
- **Unidades:** 1 lbf = 4,448 N; 1 lb = 0,4536 kg; 1 in = 25,4 mm; 1 kn = 1,852 km/h; 1 mph = 1,609 km/h. Para pasar EUR a DKK uso 7,4755 DKK/EUR, el valor que `inputs.yaml` marca hoy como [VERIFICADO: BCE 2026-09-30]. La versión anterior usaba 7,46. Los precios en SEK, GBP, USD y AUD quedan en su moneda; no los convierto porque no verifiqué el tipo de cambio.
- **Control de calidad:** WebFetch resume las páginas con un modelo y **se equivocó al menos una vez**: en La Maltière 285 dio una manga de 1,35 m, pero el texto crudo dice 4,0026 ft = 1,22 m. Los números de las tres fuentes con más peso en las conclusiones (Boote, MBY y La Maltière 285) los revisé contra el HTML crudo con curl. Los PDF de Torqeedo, ePropulsion y BoatBuilderCentral los leí con pdftotext. El resto viene del resumen de WebFetch.
- **Bloqueados (403, Cloudflare o tollbit):** lundboats.com, minnkota.johnsonoutdoors.com, tinboats.net, forum.crappie.com, bassresource, thehulltruth, microskiff, svb24, la página de Lowe, seajayboats y proalimarinepunts. Ningún dato sale de ellas.
- **Verificación adversarial (2026-10-01):** se reabrieron las 61 URLs de §D con curl (texto crudo y pdftotext). S2, S5, S6, S15 y S35 bloquean curl (403/503/CAPTCHA) y se leyeron con WebFetch. Las correcciones están en el texto y se resumen en "Verificación (adversarial)", antes de los hallazgos. Los valores del proyecto (`resultados/sizing_tablas.md`, `inputs.yaml`) se actualizaron a los vigentes ese día.

---

## Parte A — Botes de aluminio de fondo plano chicos

### A.1 Hallazgo de mercado

- **Casi no existen jon boats de aluminio < 2,5 m en catálogos actuales.** Los modelos más chicos de Tracker, Lowe, Alumacraft, Princecraft y Marine (CZ) miden 3,0–3,1 m [VERIFICADO: S1, S2, S10, S13, S7]. En Dinamarca, los aluminio de fondo plano a la venta arrancan en 3,0–3,08 m (Aquarib 3000, SeaExplorer 310 ALU) [VERIFICADO: S8, S18, S19]. Lo único < 2,5 m que encontré es el SeaCraft Mini Tinny 210 (AU, 2,10 m), el **Horizon 240 Pathfinder (AU, 2,40 m, punta en V, 50 kg)** [VERIFICADO: S72; agregado en la verificación, aparecía listado en S11 y S12] y dos plegables, Seahopper Scamp (2,03 m) y Lighter (2,40 m) [VERIFICADO: S11, S20; el material de los Seahopper no figura en S20]. *Nota de verificación:* S7 menciona que Marine fabrica un "10 JON", más chico que el 12 JON, pero la página no da su eslora.
- **Consecuencia:** el bote del usuario es probablemente un 8 ft estadounidense viejo, un *car-topper* australiano o chino, o algo casero. No hay ficha de fábrica confiable, así que **hay que medirlo**: eslora, manga, ancho de fondo, puntal, alto y espesor de espejo, y placa de capacidad si la tiene.
- **Marco legal:** la Directiva 2013/53/UE de embarcaciones de recreo cubre "a hull length from 2.5 to 24 metres" [VERIFICADO: S26]. Un bote con casco < 2,5 m queda **fuera del marcado CE**, así que puede no traer categoría de diseño ni placa de carga máxima [ESTIMADO: inferencia del alcance; buscar: Søfartsstyrelsen fritidsfartøjer under 2,5 m krav].

### A.2 Tabla de cascos (de menor a mayor eslora)

| Modelo (origen) | LOA m | Manga m | Puntal m | Peso vacío kg | Personas | Carga máx kg | hp máx | Espejo | Chapa mm | Precio (fuente) |
|---|---|---|---|---|---|---|---|---|---|---|
| Seahopper Scamp (UK, **plegable**; material no figura en S20; ref. geométrica) | 2,03 | 1,27 | — | 32 con 3 asientos y remos (el "22 casco" de la versión anterior **no figura en S20: eliminado**) | 3 (remo/motor) | 250 | — | — | — | — [VERIFICADO: S20] |
| SeaCraft Mini Tinny 210 (AU) | 2,10 | 1,16 | — | 22 | 2 | — | 5 (3,5 recom.) | short shaft; **peso máx en espejo 35 kg** | 1,2 fondo/costados | AUD 1.999 (de lista AUD 2.149) [VERIFICADO: S11] |
| **Horizon 240 Pathfinder (AU, "V punt", aluminio)** | 2,40 | **1,45** | — | **50** | 2 | — | 5, **long shaft** | — | — | AUD 3.319, solo casco [VERIFICADO: S72] |
| Seahopper Lighter (UK, plegable) | 2,40 | 1,27 | — | 34 con asientos y remos | 4 (remo/motor) | 325 | — | — | — | — [VERIFICADO: S20] |
| La Maltière Tender 2700 (FR; S6 menciona "high-resistance silicone joints", así que lo de soldado no está verificado) | 2,70 (8,86 ft) | ilegible¹ | ilegible¹ | 31 | 2 | ilegible¹ | 1–3 cv, short shaft | — | 2,0 fondo / 1,5 costados nervados | 1.709 € [VERIFICADO: S6] |
| La Maltière Tender 285 (FR, fondo plano, proa aguda) | 2,85 | 1,22 | 0,41 (alto) | 42 | 2–3 | 220 | 3–5, short shaft | — | — | desde 2.139 €; **calado 10 cm** [VERIFICADO: S5, texto crudo] |
| SeaCraft Mini Tinny 295 (AU) | 2,95 | 1,19 | — | ~30 | 2 | — | 5 | short shaft; peso máx en espejo 35 kg | 1,2/1,2 | AUD 2.199 [VERIFICADO: S12] |
| Bantam 10 (UK; S15 no dice "fondo plano") | 3,0 | 1,1 (44") | 0,38 (proa 15") | 38 | 2 | 168 | 5 | — | 1,2 | £1.199 [VERIFICADO: S15 vía WebFetch; curl recibe CAPTCHA] |
| Aquarib 3000 (DK) | 3,00 | 1,28 | 0,50 | ~50 | 2 | 200 | 6 (recom. ≤ 2,5) | short shaft | 2,0 (5052-H32), cat. C | 12.995 kr [VERIFICADO: S8] |
| Tracker Grizzly 10 Jon (US) | 3,0 (9'10") | 1,32 | — | — | — | — | 3,5 | — | — | USD 1.495 [VERIFICADO: S2] |
| Princecraft PR 1032 (CA) | 3,04 | — | — | 36 (80 lb) | 2 | — | 3,5 | — | — | — [VERIFICADO: S10] |
| Lowe L1032 Jon 2026 (US, remachado) | 3,05 (10'0") | 1,22 (4'0") | — | 36 (80 lb) | 2 | **125 (275 lb)** | no figura² | **381 mm (1'3")** | — | — [VERIFICADO: S13] |
| Stacer 3m Skimmer (AU) | 3,07 (casco 2,97) | 1,30 | 0,45 | 44 | 2 | — | 6 ("Main Motor Weight: 28kg"; leído como máximo [ESTIMADO]) | S/S | **1,2 fondo/costados/espejo** | AUD 950 (aviso) [VERIFICADO: S4] |
| SeaExplorer 310 ALU (DK, B.O. Marine) | 3,08 | 1,34 | 0,55 | 41 | 2 | 218 | 4 (**motor ≤ 18,2 kg**) | S | 1,2/1,2 (H36), cat. D | 14.500 kr sin motor; 18.900 kr con Honda 2,3 hp [VERIFICADO: S18, S19] |
| Alumacraft 1032 Jon (US) | 3,10 (10'2") | 1,19 (47") | — | 45 (99 lb) | 2 | 170 (375 lb) | 3 | **15" (381 mm)** | 0,059" (1,5) | — [VERIFICADO: S1] |
| Stessco 309 Car Topper (AU) | 3,10 | 1,44 | 0,50 | 65 | 2 | — | 6 | **short 15"**; peso máx en espejo 35 kg | 1,6 | POA [VERIFICADO: S14] |
| Kimple 330 Angler (SE) | 3,30 | 1,16 | — | 45 | 2 | 220 | 6 | **38 cm** | 1,4 | 18.900 SEK [VERIFICADO: S9] |
| Marine 12 Jon (CZ/DE) | 3,70 | 1,20 | — | 37 | 3 | 278 | 3,5 PS | Kurzschaft | ~1,2, cat. D | 2.035 € [VERIFICADO: S7] |
| Appleby 10 ft jon (US, foro) | 3,05 | — | — | — | — | 111 (245 lb) | — | — | — | [VERIFICADO: S21] |

¹ La página publica "Width 1.148294 / Height 1.148294 / Load (livre) 97.6241". Los valores son incoherentes (mismo número para manga y alto; carga de 44 kg para 2 personas), así que no los uso.
² Un resultado de búsqueda decía 3,5 hp, 32" (813 mm) de ancho de fondo y 16" (406 mm) de puntal, pero la página que abrí no lo muestra. Queda como [ESTIMADO: resumen de búsqueda no verificado].

### A.3 Relaciones derivadas (para escalar a 2,44 × 1,20 m)

| Relación | Rango observado | Base |
|---|---|---|
| Peso vacío / (LOA × manga) | 8,3–14,6 kg/m²; mediana ≈ 11 | [CALCULADO: 12 cascos de aluminio de A.2, recalculado en la verificación: Marine 8,3 … Stessco 14,6]. El Horizon 240 que se agregó da 14,4 y queda dentro del rango |
| Carga máx / (LOA × manga), aluminio con norma CE o USCG | 34–63 kg/m²; mediana ≈ 52 | [CALCULADO: Lowe 33,6 · Alumacraft 46 · Bantam 51 · Aquarib 52 · SeaExplorer 53 · Kimple 57 · Marine 63 · La Maltière 63] |
| Carga máx / área, plegables Seahopper (sin norma) | 97–107 kg/m² | [CALCULADO: S20]: las placas varían ×2 según quien las fije |
| Regla USCG 33 CFR 183.35 | carga máx ≤ (desplazamiento máximo − peso del bote) / 5 | [VERIFICADO: S25] |
| Regla USCG 183.37 (botes de remo o con placa ≤ 2 hp) | carga máx ≤ **3/10** × (desplazamiento máximo − peso del bote) | [VERIFICADO: S25]. Con la caja de A.4 da (845 − 45) × 0,3 ≈ 240 kg. Solo vale si el **fabricante** clasificó el casco para ≤ 2 hp; no sirve para re-placar uno clasificado para 3–5 hp |
| Regla USCG 183.41 (personas) | (carga + 32 lb) / 141 lb por persona | [VERIFICADO: S25]: supone **64 kg por persona** |
| Regla USCG 183.53 (hp) | factor L × ancho de espejo (ft) ≤ 35 → 3 hp; fondo plano de pantoque duro: "reduce one capacity limit" | [VERIFICADO: S24]. 8 ft × 3 ft = 24 → **≤ 3 hp** |

### A.4 Rangos de diseño para el jon boat del proyecto (LOA ≤ 2,5 m)

| Parámetro | Mín | Típico | Máx | Base |
|---|---|---|---|---|
| LOA | 2,03 | 2,44 | 2,50 | [VERIFICADO: S20, S11] + límite del proyecto |
| Eslora en flotación (LWL) | 1,7 | 2,0 | 2,3 | [ESTIMADO: LOA − 0,2…0,5 m de proa lanzada tipo pram/jon] |
| Manga máxima | 1,10 | 1,20 | 1,45 | [VERIFICADO: 1,16 (S11), 1,27 (S20), 1,45 Horizon 240 (S72); clase 3 m 1,10–1,44] |
| Ancho de fondo (pantoque) | 0,75 | 0,90 | 1,05 | [ESTIMADO: manga − 2 × abocinado de 0,10–0,20 m; no encontré ningún dato verificado] |
| Puntal (costado) | 0,33 | 0,38 | 0,45 | [ESTIMADO: alto de espejo 0,38 (S1, S9, S13); clase 3 m 0,45–0,55 (S4, S8, S18) es mayor] |
| Peso vacío | 22 | 32 | 50 | [VERIFICADO: 22 kg Mini Tinny 210 (S11), 50 kg Horizon 240 (S72)] + [CALCULADO: 8,3–14,6 kg/m² × 2,93 m² = 24–43] |
| Carga máx de placa (personas + motor + equipo) | ~100 | ~150 | ~185 (250+ en plegables) | [CALCULADO: 34–63 kg/m² × 2,93 m²; caja 2,44 × 1,2 × 0,38 con Cb 0,75 → desplazamiento máx ≈ 845 kg → (845 − 45)/5 = **160 kg** por regla USCG] |
| Altura de espejo | 330 | **381** (15") | 430 (508 si es "long shaft") | [VERIFICADO: 381 mm Alumacraft/Lowe (S1, S13), 38 cm Kimple (S9), "short 15"" (S14), estándar 15/20/25" (S23); el Horizon 240 de 2,40 m pide "long shaft" (S72), o sea 20" = 508 mm]; mín y 430 [SUPUESTO] |
| Espesor de espejo | ~1,2 (chapa desnuda) | 30–45 (chapa + taco) | 63 | [VERIFICADO: espejo de 1,2 mm en Stacer (S4); abrazadera ePropulsion 28–63 mm (S31)]; típico [ESTIMADO: memoria técnica, no verificado] |
| Calado cargado (Δ 250–330 kg) | 0,10 (vacío + 1 p.) | 0,17 | 0,22 | [VERIFICADO: 10 cm La Maltière 285 (S5)] + [CALCULADO: Δ / (ρ × A_flot) con A_flot 1,5–1,9 m²] |
| Francobordo cargado | 0,12 | 0,18 | 0,25 | [CALCULADO: puntal − calado] |
| Espesor de chapa | 1,2 | 1,5 | 2,0 | [VERIFICADO: S1, S4, S6, S8, S11, S14, S18] |
| **Peso máx colgado del espejo** | 18 | 28 | 35 | [VERIFICADO: "Max motor vægt 18,2 kg" (S18, S19); "Main Motor Weight: 28kg" (S4, leído como máximo); "max transom weight 35 kg" (S11, S12, S14)] |
| Potencia máx de placa | 3 hp | 3,5–5 hp | 6 hp | [VERIFICADO: S1, S2, S4, S11, S13, S18; USCG ≤ 3 hp (S24)] |

### A.5 Montaje en el espejo

- **Altura de la hélice:** en cascos lentos o de desplazamiento, la placa anticavitación de un fueraborda chico de bote auxiliar suele ir "2 or 3" below the bottom" (51–76 mm), para no airear la hélice cuando el bote cabecea [VERIFICADO: S23]. El largo de pata se mide desde el interior de la abrazadera hasta la placa anticavitación; los estándares son 15/20/25" (381/508/635 mm) [VERIFICADO: S23].
- **ePropulsion Spirit 1.0 Evo:** abrazadera para espejos de **28–63 mm** de espesor; la pata S (625 mm) se recomienda para espejos de **400–500 mm** de alto y la L para > 500 mm [VERIFICADO: S31]. En un jon boat de 381 mm, la S queda unos 20 mm más honda que lo recomendado, lo que es aceptable a baja velocidad según S23 [CALCULADO]. El manual también **recomienda** ("A cable is recommended") **un cable de seguridad del motor al bote** [VERIFICADO: S31].
- **Torqeedo Travel:** pata S de 62,5 cm o L de 75 cm, con trim manual 0/7/14/21° [VERIFICADO: S34, S35].

---

## Parte B — Referencias comerciales

### B.1 Tabla de motores (bollard N/W = empuje declarado o medido / potencia eléctrica máxima)

| Motor | Tipo · agua salada | Tensión | I máx A | P eléc. máx W | Empuje lb / N | **N/W** [CALCULADO] | Peso motor kg | Pata | Hélice | Precio (fuente, 2026-10-01) |
|---|---|---|---|---|---|---|---|---|---|---|
| Minn Kota Riptide Endura C2 55 | trolling · sí | 12 | 50 | 620 | 55 / 245 (24,9 kgf) | 0,40 | — | 107 cm | "Power Prop" | **5.499 kr** [VERIFICADO: S42] |
| Minn Kota Riptide Transom 55 SC | trolling · sí (ánodo de zinc, inoxidable) | 12 | — | 600 | 55 / 245 | 0,41 | 9,6 | 107 cm | plástico | 659 € (≈ 4.926 kr [CALCULADO con 7,4755]) [VERIFICADO: S40, S41] |
| Minn Kota Riptide RT80/T | trolling · sí | 24 | 56 | 1.344 [CALCULADO: 24 V × 56 A] | 80 / 356 | 0,26 | [NO VERIFICADO: los "40 lb" de S39 son el peso con caja de 9×22×59", no el del motor] | 42" | Weedless Wedge 2 | USD 999,99–1.105,59 [VERIFICADO: S38, S39] |
| Watersnake Venom SXW 54/42 | trolling · sí | 12 | 13–54 | 648 [CALCULADO: 12 V × 54 A] | 54 / 240 | 0,37 | 8,5 | 42" (106 cm) | 3 palas | 3.199 SEK [VERIFICADO: S43, S44]; AUD 359 [S43] |
| Watersnake Venom SXW 65/42 | trolling · sí | 12 | 13–50 | 600 [CALCULADO: 12 V × 50 A] | 65 / 289 | 0,48 ⚠ | 10,0 | 42" | 3 palas | AUD 440 [VERIFICADO: S43] |
| Watersnake ASP T24 | trolling kayak · sí | 12 | 9–20 | 240 [CALCULADO: 12 V × 20 A] | 24 / 107 | 0,45 | — | 61 cm | 2 palas | AUD 189 [VERIFICADO: S45] |
| Newport NV 55 | trolling con escobillas · sí | 12 | 52 | 624 [CALCULADO: 12 V × 52 A] | 55 / 245 | 0,39 | 10,4 (23 lb) | 30" | 3 palas | **USD 239,99** [VERIFICADO: S46, precio de la variante 55 lb; los USD 169,99 de antes son de la de 36 lb: **corregido**] |
| Newport NV 86 | trolling con escobillas · sí | 24 | 48 | 1.152 [CALCULADO: 24 V × 48 A] | 86 / 383 | 0,33 | 11,3 (25 lb) | 36" | 3 palas | USD 359,99 [VERIFICADO: S46] |
| Rhino VX65 V2 | trolling · "saltwater compatible" | 12 | 47 | 560 | 65 / 289 | **0,52 ⚠** | 10,0 | 79 cm | — | 439,99 € [VERIFICADO: S51]; 489,99 € [S52] |
| Haswing Protruar 1.0 | sin escobillas · sí según fabricante | 12 | 50 | 600 | 65 / 289 | **0,48 ⚠** | 5,9–6,6 | 900 mm (S: más corta) | 3 palas 9,3", 1.250 rpm | 429 € [VERIFICADO: S48]; USD 319,99 [S49] |
| Haswing Protruar 3.0 | sin escobillas | 24 | 60 [CALCULADO: 1.440 W / 24 V] | 1.440 | 110 / 489 | 0,34 | [NO VERIFICADO³] | [NO VERIFICADO³] | — | 699,01 € [VERIFICADO: S48, nombre y precio en la lista de la tienda] |
| Haswing Protruar 5.0 | sin escobillas | 24 | — | 2.520 | 160 / 712 | 0,28 | 14 | 1.000 mm | 3 palas 10,7", 1.450 rpm | 999 € [S48]; 7.995 SEK [VERIFICADO: S50] |
| Newport NT300 | fueraborda sin escobillas · sí | 36 | 37 | 1.300 | 110 / 489 | 0,38 ⚠ | 10,8 (23,8 lb) | 24,6" / 29" | 2 palas 9,8" | USD 1.299,99 [VERIFICADO: S47] |
| **ePropulsion Spirit 1.0 Evo** | fueraborda integrado · sí | 48 nom. (39–60) | **20,8 nominal** | 1.000 | 71 / 316 declarado [S33]; **290 medido⁴** | 0,32 declarado / **0,29 medido** | 10,2 (S) / 10,6 (L) sin batería según el manual (S31); 11,3 según Watski (S32); batería 8,7–8,8 | 625 / 750 mm | **280 mm × 5,8" (147 mm), 2 palas, 1.200 rpm máx** | **Watski DK: 9.199 kr el motor S, que "leveres uden batteri og betjening" (sin batería ni mando), + 9.390 kr la batería de 1.276 Wh + 2.578 kr la caña (tiller) + 719 kr el cargador = 21.886 kr** [VERIFICADO: S32; **corregido**, antes decía 18.589 kr sin caña ni cargador]; 2.549 € en DE con batería, caña y cargador [VERIFICADO: S33] |
| **Torqeedo Travel 1103 C** (descontinuado) | fueraborda integrado · sí | 29,6 | — | 1.100 (propulsiva 540) | 70 / 311 declarado; **310 medido⁴** | 0,28 / **0,28** | 11,3 (S) + batería 6,0 = 17,3 | 62,5 / 75 cm | v10/p1100, 1.450 rpm | "on request" [VERIFICADO: S34, S36]; 2.249 € en el test [S60] |
| Torqeedo Travel (2024) | fueraborda · sí | 36 | — | 1.100 | 70 / 311 | 0,28 | 20,2 con batería | 62,5 cm (S); existe versión L, pero S37 no da su largo | 10 × 6,5 | **2.699 €** con batería de 1.080 Wh y cargador [VERIFICADO: S37] |

³ S48 es la ficha de la Protruar 1.0. Los 5,9 kg y los 900 mm son de la 1.0; de la 3.0 la tienda solo muestra nombre, potencia, empuje y precio. Peso y pata de la 3.0: buscar: Haswing Protruar 3.0 24V weight shaft length.
⁴ Tracción a punto fijo medida por Boote: "Torqeedo with 0.31 kN … ePropulsion with only 0.29 kN" [VERIFICADO: S60, texto crudo]. El test usó la Spirit 1.0 anterior (batería de 1.080 Wh), no la Evo.

Otros datos verificados:
- **Rendimiento total máximo** (batería → potencia propulsiva): Travel 503 44 % (manual) a 48 % (ficha), Travel 1003 48 %, Travel 1103 C 49 % [VERIFICADO: S34, S35]; Spirit 1.0 Evo 55 % [VERIFICADO: S31]. El proyecto calcula hoy **29 %** en el caso de diseño (`resultados/sizing_tablas.md` al 2026-10-01; la versión anterior de este informe decía 34 %).
- **rpm de hélice a plena carga:** Travel 503 875 (700 según el manual DK), 1003 1.125 (1.200 según el manual DK), 1103 C 1.450 [VERIFICADO: S34, S35]; Spirit Evo 1.200 [VERIFICADO: S31]; Haswing Protruar 1.0 (600 W) 1.250 [VERIFICADO: S48, S49]. **Ninguno de los fuerabordas eléctricos de ~1 kW revisados gira la hélice por encima de 1.450 rpm.** El Navy 3.0 de ePropulsion (3 kW) llega a 2.400 rpm [VERIFICADO: S67].
- **Ficha inconsistente de Haswing:** S49 declara "SHAFT POWER 1HP" (746 W) con "POWER - MAX 600W". Una potencia al eje mayor que la de entrada es imposible, y refuerza el veredicto de B.2 [VERIFICADO: S49].

### B.2 ¿Son creíbles los empujes declarados? (control por teoría de cantidad de movimiento)

Empuje ideal a punto fijo: T_id = (2·ρ·A·P_eje²)^(1/3), con ρ = 1.013 kg/m³. Los "figures of merit" reales de hélices marinas a punto fijo andan en 0,6–0,75 [ESTIMADO: memoria técnica, no verificado], así que exigir FM ≥ 0,9 ya es poco realista. FM_req = (T_declarado / T_id)^1,5 [CALCULADO]:

| Motor | D hélice | P_eje (η_motor 0,75–0,85) | T_id N | Declarado N | FM requerido | Veredicto |
|---|---|---|---|---|---|---|
| Haswing Protruar 1.0 | 9,3" [S49] | 450–510 W | 262–285 | 289 | **1,02–1,16** | **imposible con η_motor ≤ 0,85**; con η 0,9 el FM requerido sigue en 0,97 |
| Rhino VX65 | 10" [SUPUESTO] | 420–476 W | 263–285 | 289 | 1,02–1,16 | imposible con 10" y η ≤ 0,85; requiere ≥ 12" |
| Newport NT300 | 9,8" [S47] | 975–1.105 W | 454–494 | 489 | 0,99–1,12 | inflado |
| Minn Kota Riptide 55 | 10" [SUPUESTO] | 450–510 W | 275–299 | 245 | 0,74–0,84 | optimista (≈ 10–20 %) |
| Watersnake SXW 54 | 10" [SUPUESTO] | 486–551 W | 289–315 | 240 | 0,67–0,76 | creíble en el límite |
| Torqeedo 1103 C | 11" [SUPUESTO] | 825–935 W | 439–477 | 311 (**medido 310**) | 0,53–0,60 | coherente con la medición |
| ePropulsion Evo | 280 mm [S31] | 750–850 W | 412–448 | 316 (**medido 290**) | 0,59–0,67 | coherente |

**Conclusiones:**
- Las dos únicas mediciones independientes dan **0,28–0,29 N/W a 1,0–1,1 kW** [VERIFICADO: S60].
- Los 0,45–0,52 N/W de trolling motors de 12 V y 560–600 W **no son creíbles** en los modelos Rhino, Haswing y Watersnake 65. Como el empuje escala con P^(2/3), lo esperable a 600 W con una hélice de 10" es ~0,33–0,38 N/W [CALCULADO: 0,29 × (1.050/600)^(1/3) = 0,35].
- **Para el proyecto:** el bollard que calcula hoy es **280 N avante** (`resultados/sizing_tablas.md` al 2026-10-01; la versión anterior decía 297 N). Queda un 3–10 % por debajo del Torqeedo y del ePropulsion medidos (290–310 N). Es un objetivo realista; no hace falta perseguir los "55–65 lb" de catálogo.
- *Nota de verificación:* S60 no dice a qué potencia se midió el bollard. Las cifras en N/W suponen la potencia nominal de entrada (1,0 y 1,1 kW) [SUPUESTO].

### B.3 Efecto del diámetro de hélice (relevante para elegir entre la de fueraborda de 7,8" y la de 10–11")

| D | T a punto fijo con P_eje 450 W, FM 0,7 | η ideal a 6 km/h, T = 100 N | η ideal a 6 km/h, T = 150 N |
|---|---|---|---|
| 198 mm (7,8") | 184 N | 0,71 | 0,64 |
| 236 mm (9,3") | 207 N | 0,76 | 0,70 |
| 254 mm (10") | 217 N | 0,78 | 0,72 |
| 280 mm (11", como la Spirit) | 231 N | 0,81 | 0,75 |

[CALCULADO: η_i = 2 / (1 + √(1 + C_T)), C_T = T / (½ρAv²), v = 1,667 m/s.] Pasar de 7,8" a 10–11" sube el empuje a punto fijo un 18–26 % y baja la energía de crucero un 9–15 % para la misma eficiencia relativa. Los dos fueraborda eléctricos de referencia usan hélices de ~10–11" y 1.200–1.450 rpm [VERIFICADO: diámetro de 280 mm en S31; 10 × 6,5 en S37; Travel de 1,1 kW con 10,2 × 6,6 en S67; rpm en S31 y S34. S34 no da el diámetro].

### B.4 Referencia de costo y prestaciones

| Solución "comprada" | Costo DK/EU | Batería | Qué entrega |
|---|---|---|---|
| Trolling de agua salada 55 lb, 12 V | 5.499 kr (Riptide C2 55, S42); 3.199 SEK (Watersnake SXW 54, S44); USD 239,99 (Newport NV 55, S46) | 12 V aparte | ~0,6 kW. Sin basculación con protección ante golpes; pata de 30–42" larga para un espejo de 381 mm |
| Fueraborda eléctrico de 1 kW completo | **21.886 kr** en DK (ePropulsion Evo S con batería, caña y cargador, S32); 2.549 € en DE con lo mismo (S33); 2.699 € (Torqeedo Travel con batería y cargador, S37) | 1,08–1,28 kWh integrada | 7,6–7,8 km/h con 2 personas en un F-RIB de 2,75 m (S62); 7,8–8,0 km/h en un inflable de 8 ft (S61); basculación ante golpes, marcha atrás, IP67, display |
| Petrol 2,3–2,5 hp | £579–760 [VERIFICADO: S62] | — | 8,1–9,3 km/h con 2 personas en un bote de 2,75 m (§C) |

**El techo de costo del DIY** es lo que cuesta el ePropulsion completo: **~21.900 kr ≈ 2.930 € comprado en DK** [CALCULADO: 21.886 / 7,4755, el tipo de `inputs.yaml`], o 2.549 € ≈ 19.050 kr comprado en DE (S33; envío a DK no verificado). *Corrección:* la versión anterior decía ~18.600 kr porque omitía la caña (2.578 kr) y el cargador (719 kr), que Watski vende aparte. El piso es un trolling de agua salada de 55 lb con batería LiFePO₄ de 12 V. Para que el DIY tenga sentido tiene que cumplir dos cosas a la vez: (a) costar bastante menos que ~2.550–2.930 € (≈ 19.000–21.900 kr) con batería incluida, y (b) dar el ~1 kW, la basculación con protección y la marcha atrás que un trolling de 600 W no da.

---

## Parte C — Velocidad contra potencia medida en botes chicos (para calibrar R(v))

### C.1 Datos

Wh/km = P / v. R se despeja como R = η·P / v, con η batería→propulsión entre 0,40 y 0,50, tomado de los rendimientos máximos de B.1 menos una pérdida a carga parcial [ESTIMADO].

| # | Fuente | Casco · carga | Motor | P eléc. W | v km/h | Wh/km | R (η 0,40–0,50) N | Calidad |
|---|---|---|---|---|---|---|---|---|
| 1 | Cruising World [S61] | **inflable West Marine de 8 ft (2,44 m)** · carga no declarada; viento de 5 kn y ola chica en la máxima | Spirit 1.0 Evo | 100 | 4,26 (2,3 kn) | 23 | 34–42 | A (prueba de revista) |
| 2 | ídem | ídem | Spirit 1.0 Evo | **500** | **6,11** (3,3 kn) | **82** | **118–147** | A |
| 3 | ídem | ídem | Spirit 1.0 Evo | 1.000 [ESTIMADO: potencia nominal a fondo; S61 no da los W medidos] | 7,78 (4,2 kn) | 129 | 185–231 | A |
| 4 | ídem | ídem | Torqeedo 1103 S | 500 | 6,67 (3,6 kn) | 75 | 108–135 | A |
| 5 | ídem | ídem | Torqeedo 1103 S | 1.000 [ESTIMADO: igual que #3] | 7,96 (4,3 kn) | 126 | 181–226 | A |
| 5b | ídem (agregado en la verificación) | ídem | **Mercury de gasolina de 2,5 hp**, a fondo | — (≈ 1,86 kW al eje nominal) | **8,52 (4,6 kn)** | — | — | A. Contraste: 2,5 hp de gasolina dan solo +7–10 % de velocidad sobre 1 kW eléctrico en este casco [VERIFICADO: S61; CALCULADO: 4,6/4,3 y 4,6/4,2] |
| 6 | MBY [S62, texto crudo] | **mini-RIB plegable F-RIB de 2,75 m · 2 personas** | Torqeedo 1103 C | 1.100 | **7,78** (4,2 kn) | 141 | 204–255 | A |
| 7 | ídem | ídem · 2 personas | Spirit 1.0 Plus | 1.000 | **7,59** (4,1 kn) | 132 | 190–237 | A |
| 8 | ídem | ídem · 1 persona | Torqeedo / Spirit | 1.100 / 1.000 | 8,70 / 7,96 | 126 | 181–227 | A |
| 9 | ídem | ídem · 2 personas | **petrol 2,3–2,5 hp** (1,7–1,9 kW al eje) | — | **8,1–9,3** (4,4–5,0 kn) | — | 254–403 (η_prop 0,35–0,5) | A |
| 10 | ídem | ídem · 1 persona | Yamaha 2,5 / Selva 2,5 | — | **17,6 / 14,8 (planeo)** | — | — | A |
| 11 | Boote [S60, texto crudo] | dos inflables de alta presión de 3,20 m · carga no declarada | Torqeedo 1103 C / Spirit 1.0 | 186 / 200 | 5,0 | 37 / 40 | 54–72 | A |
| 12 | ídem | ídem | Torqeedo / Spirit, potencia máxima | 1.100 / 1.000 | 9,0 / 7,6 | — | — | A |
| 13 | PBO [S63] | tender de GRP Tuffy de 3 m | Spirit 1.0 | 1.000 (máx) | 7,4 (4 kn); 1,4 kn al 20 % | — | — | B (sin carga declarada; **contra 2 kn de marea** según S63, así que no está claro si es velocidad sobre el agua o sobre el fondo) |
| 14 | Torqeedo, ficha [S34] | "Inflatable, dinghy, daysailer up to 1.5 tons" (bote sin especificar) | Travel 1103 C, 915 Wh | 46 / 153 / 1.098 [CALCULADO: 915 Wh / tiempo de marcha de la ficha (20:00 / 06:00 / 00:50); la ficha no da los W] | 3,7 / 5,5 / 10,0 | 12 / 28 / 110 | 18–22 / 40–50 / 158–198 | C (catálogo) |
| 15 | ePropulsion, tabla [S30] | **bote de aluminio de 12 ft (3,66 m), 1 operador, lago en calma** (nota al pie de S30; *corregido*: antes decía "bote sin especificar") | Spirit 1.0 | 125 / 250 / 500 / 750 / 1.000 (también 35 W → 3,5 km/h y 65 W → 4,3 km/h) | 5,6 / 7,1 / 8,5 / 9,2 / 10,0 | 22 / 35 / 59 / 82 / 100 | 32–40 / 51–63 / 85–106 / 117–147 / 144–180 | C (catálogo; casco más largo con 1 persona) |
| 16 | Electrek, Avator 7.5e [S70] | Veer X13 | Mercury Avator 7.5e, 1 kWh | ~1.000 / ~53 | 8 / 2,9 (8 km en 60 min; 55 km en 19 h) | ~125 / ~18 | — | B |
| 17 | Seahopper [S64] | **Seahopper Scamp de 2,03 × 1,27 m** · 2 personas | Newport de 46 lb y 12 V, batería de plomo de 90 Ah | ~81–108 promedio [CALCULADO: 15–20 % × 90 Ah × 12 V / 2 h], "mostly around half-throttle" | 7,2 (4,5 mph, "timed run"; no necesariamente a esa potencia) | — | — | C (anécdota; consumo estimado por % de batería) |
| 18 | iboats [S65] | Gheenoe de 15' · aguas planas | 55 lb de proa / 55 lb 12 V de popa | ~600 máx | 4,8 / 6,4 (3 / 4 mph, GPS) | — | — | C |
| 19 | boatdesign [S66] | bote de remo de 17 ft, ~350 kg en total (la serie de 300 m con ~400 kg da lo mismo: 4,75 kn con 600 W) | Torqeedo Cruise 2.0 | 600 | **8,8** | 68 | — | B (contraste: casco largo) |

### C.2 Lectura de los datos

- **Las tablas de los fabricantes (#14, #15) piden 2–3 veces menos energía** que las pruebas reales en botes de 2,4–2,75 m: a ~6 km/h dan 22–28 Wh/km, pero el inflable de 8 ft necesitó 75–82 Wh/km (#2, #4) [CALCULADO]. *Matiz de la verificación:* la tabla de ePropulsion (#15) se midió en un aluminio de 12 ft (3,66 m) con **1** persona en lago calmo (S30). Buena parte de la diferencia viene de un casco 1,5 veces más largo y con la mitad de carga, no solo de optimismo. Igual no conviene calibrar R(v) con ellas para un casco de 2,44 m con 2 personas.
- **Pendiente:** en las tablas, P ∝ v^k con k = 2,9–3,0 por debajo de ~7 km/h y k = 3,5–5 por encima [CALCULADO con S30, S34]. Equivale a R ∝ v² en desplazamiento y a R ∝ v^2,5–4 cerca de la joroba.
- **Velocidad de casco:** con LWL de 2,0 m, el criterio 1,34·√LWL[ft] kn da **6,36 km/h**. A 6 km/h, Fn = 0,376; a 8 km/h, 0,50; a 12 km/h, **0,75** [CALCULADO]. El crucero de 6 km/h ya está en la velocidad de casco.
- **Techo de 1 kW:** en un casco de 2,4–2,75 m, con 1 o 2 personas, 1–1,1 kW eléctricos dan **7,6–8,0 km/h** (#3, #5, #6, #7). El techo es la joroba de resistencia, no la potencia: con 2 personas, los petrol de 2,3–2,5 hp (~1,8 kW al eje) solo llegan a 8,1–9,3 km/h y **no planean** (#9). Con una persona, dos de ellos sí planean (#10).
- **El largo del casco manda:** un bote de remo de 17 ft y ~350 kg anda a 8,8 km/h con 600 W (#19), mientras que un RIB de 2,75 m necesita 1.000–1.100 W para 7,6–7,8 km/h. Eso es +14 % de velocidad con ~0,57 veces la potencia [CALCULADO: 8,8/7,7 y 600/1.050].

### C.3 Banda propuesta de R(v) para el jon boat de 2,44 m con 2 adultos (Δ ≈ 290 kg)

[ESTIMADO: interpolación de #1–#11 con R ∝ v^2…3; el jon boat tiene LWL más corta (~2,0 m) que el F-RIB (2,75 m LOA) y proa de pram, así que me paro en la mitad alta de las bandas.]

| v km/h | R N (banda) | P eléc. con η_tot 0,45 (comercial) | P eléc. con η_tot 0,34 (diseño anterior del proyecto; hoy es 0,29, ver abajo) |
|---|---|---|---|
| 4 | 35–60 | 86–148 W | 114–196 W |
| 5 | 55–85 | 170–262 W | 225–347 W |
| **6** | **95–150** | **352–556 W** | **466–735 W** |
| 7 | 140–210 | 605–907 W | 801–1.201 W |
| 8 | 200–280 | 988–1.383 W | 1.307–1.830 W |
| 9 | 260–400 | 1,4–2,2 kW | 1,9–2,9 kW |
| 12 | 350–600 (zona de planeo; incierto) | 2,6–4,4 kW | 3,4–5,9 kW |

[CALCULADO: P = R·v / η.] **Contraste con `resultados/sizing_tablas.md` (valores vigentes al 2026-10-01, actualizados en la verificación):** el proyecto usa R(6 km/h) = **135 N nominal y 156 N de diseño**, P_bat = **759 W nominal y 910 W de diseño** y η_tot de diseño = **0,29**. La versión anterior citaba 130/169 N, 578/819 W y 0,34. El R nominal cae dentro de la banda y el de diseño queda ~4 % por encima del tope. Con η 0,29 la banda de 6 km/h da 546–862 W [CALCULADO], y los 910 W de diseño quedan ~6 % por encima. La V máx que calcula hoy el proyecto (**6,7 km/h de diseño con batería baja; 7,4 km/h nominal**) queda **por debajo** de los 7,6–8,0 km/h que los comerciales de 1–1,1 kW logran en #3, #5, #6 y #7.

**Energía para 2 h a 6 km/h, con 20 % de reserva:** 0,88–1,39 kWh con η 0,45; 1,17–1,84 kWh con η 0,34; y **1,37–2,16 kWh con η 0,29** [CALCULADO]. Los 2,30 kWh usables del proyecto cubren la banda con η 0,29, pero `sizing_tablas.md` da hoy una energía requerida de diseño de 2.426 Wh, un 5 % más que los 2.304 Wh usables (aunque la autonomía de diseño figura en 2,53 h). El margen para viento y corriente es **escaso**, no "amplio".

---

## D. Fuentes abiertas con éxito en esta sesión

| Id | URL | Qué respalda |
|---|---|---|
| S1 | https://alumacraft.com/Alumacraft-Boat.php?action=view&id=780 | Alumacraft 1032: 10'2", 47", 99 lb, 2 p., 375 lb, 3 hp, espejo 15", chapa 0,059" |
| S2 | https://www.trackerboats.com/jon.html | Grizzly 10: 3 m, 1,32 m, 3,5 hp, USD 1.495 |
| S3 | https://aquarib.com/shop/12-jolle/118-aquarib-jolle-alu-360---12-fod/ | Aquarib ALU-360 (contexto DK: 3,60 m, 60 kg, 2 mm, 15.995 kr) |
| S4 | https://www.boats-from-au.com/stacer/stacer-3m-skimmer-tinnie-punt-car-topper-aluminium-boat-new-36283 | Stacer 3m Skimmer |
| S5 | https://aluminium-boat.com/tender-boat-285/ | La Maltière 285 (verificado con texto crudo) |
| S6 | https://aluminium-boat.com/tender-boat-2700/ | La Maltière 2700 |
| S7 | https://www.verus-boote.de/Aluminiumboot-MARINE-JON-12 | Marine 12 Jon |
| S8 | https://aquarib.com/shop/12-aluminium-baade/330-aquarib-aluminium---model-aquarib-3000/ | Aquarib 3000 |
| S9 | https://batmagneten.se/kimple-330-angler/ | Kimple 330 Angler, espejo 38 cm |
| S10 | https://www.princecraft.com/us/en/products/Fishing-Boats/2026/Jon-Boats.aspx | Princecraft PR 1032 |
| S11 | https://waves.com.au/products/seacraft-minitinny-210 | Mini Tinny 210, peso máx en espejo 35 kg |
| S12 | https://waves.com.au/products/seacraft-mini-tinny-295 | Mini Tinny 295 |
| S13 | https://www.i69marine.com/Power-Boats-Outboard-Lowe-L1032-Jon-2026-Union-City-TN-c36d5dc7-6a53-45a7-82d2-b398009dc82f | Lowe L1032: 275 lb, 80 lb, espejo 1'3" |
| S14 | https://www.petomarine.com.au/listing/car-topper-series/ | Stessco 309: espejo short 15", 35 kg máx en espejo |
| S15 | https://www.bantamboats.co.uk/bantam-range/ | Bantam 10 |
| S16 | https://www.rubrikannoncer.dk/brande/baade/baade/joller-og-gummibaade/ad18551 | SeaExplorer 370 + trolling de 55 lb para agua salada, 18.500 kr (contexto DK) |
| S17 | https://www.dabad.dk/brande/baade/joller-og-gummibaade/ad8434 | SeaExplorer 400UL (contexto DK) |
| S18 | https://www.targ.dk/brande/aade/baade/joller-og-gummibaade/an330147 | SeaExplorer 310 ALU, motor ≤ 18,2 kg |
| S19 | https://www.ostfynsbaadhandel.dk/seaexplorer-aluminium/156-seaexplorer-310-alu-marine | SeaExplorer 310 ALU (concesionario DK) |
| S20 | https://www.seahopperfoldingboats.com/specifications/ | Seahopper Scamp y Lighter |
| S21 | https://forums.iboats.com/threads/10-ft-jon-boat-trolling-motor.298761/ | Appleby 10 ft: 245 lb |
| S22 | https://www.obparts.com/the-outboard-blog/guide-to-boat-transom-heights-outboard-shaft-lengths/ | Cómo medir el espejo; 15/20/25" |
| S23 | https://boatbuildercentral.com/support-tutorials/Tutorials/outboard-shaft-lengths-and-transoms.pdf | Estándar 15/20/25"; placa 2–3" bajo el fondo en dinghies |
| S24 | https://www.law.cornell.edu/cfr/text/33/183.53 | Tabla de hp de la USCG; regla de fondo plano |
| S25 | https://unitedstatesvessel.us/code-of-federal-regulations/33-cfr-part-183-subpart-c-safe-loading/ | Carga máx = (desplazamiento máx − peso del bote) / 5; 141 lb por persona |
| S26 | https://www.easyce.de/en/ce-directives-overview/applying-rc-directive-201353eu.html | Alcance de la directiva: 2,5–24 m |
| S30 | https://www.epropulsion.com/products/electric-outboards/spirit-1 | Spirit 1.0: tabla de W, km/h y autonomía |
| S31 | https://www.epropulsion.com/wp-content/uploads/2021/04/User-Manual_Spirit-1.0-Evo.pdf | 20,8 A, 55 %, 1.200 rpm, hélice 280 mm × 5,8", espejo de 28–63 mm de espesor y 400–500 mm de alto |
| S32 | https://www.watski.dk/Epropulsion-Spirit-10-EVO-3hk-11cIP | Precios DK: 9.199 / 8.930 kr el motor, 9.390 kr la batería |
| S33 | https://greenboatsolutions.com/shop/motor/outboard/epropulsion-spirit-1-evo | 2.549 € completo; 71 lb |
| S34 | https://www.unisafe.dk/wp-content/uploads/2021/06/torqeedo-product-datablad.pdf | Datos técnicos de Travel 503/1003/1103 C y tabla de velocidad y autonomía |
| S35 | https://media.torqeedo.com/downloads/manuals/torqeedo-Travel-manual-DK-NL.pdf | Datos técnicos (manual en danés) |
| S36 | https://greenboatsolutions.com/shop/motor/outboard/torqeedo-travel-1103 | 1103: descontinuado, 70 lb |
| S37 | https://greenboatsolutions.com/shop/motor/outboard/torqeedo-travel | Torqeedo Travel 2024: 2.699 € con batería |
| S38 | https://tbnation.net/products/minn-kota-riptide-rt80-t-saltwater-transom-mount-24v-80lb-42 | Riptide RT80: 24 V, 56 A |
| S39 | https://www.trollingmotors.net/products/minn-kota-riptide-80-transom | Riptide 80: 40 lb, USD 999,99 |
| S40 | https://greenboatsolutions.com/shop/motor/stern-drive/minn-kota-riptide-transom-55-sc | Riptide 55 SC: 0,6 kW, 9,6 kg, 659 € |
| S41 | https://e-badsmotorer.dk/shop/motorer/bagmotor/minn-kota-riptide-transom-55-sc | ídem (sitio DK, precio en €) |
| S42 | https://www.watski.dk/minn-kota-riptide-endura-c2-11Twl | Riptide Endura C2 55: 50 A, 620 W, 5.499 kr |
| S43 | https://www.watersnake.com.au/products/watersnake-venom-sxw-transom-mount-motors | Venom SXW: corrientes y pesos |
| S44 | https://www.fiskejournalen.se/watersnake-venom-sxw-54-aktermonterad-elmotor-for-saltvatten-54-lb-24-5-kg-106-cm | SXW 54: 3.199 SEK |
| S45 | https://www.kayaks2fish.com/watersnake-asp-t24-transom-mount-electric-trolling | ASP T24: 9–20 A |
| S46 | https://newportvessels.com/products/nv-series-saltwater-trolling-motor | Newport NV: corrientes y pesos |
| S47 | https://newportvessels.com/products/nt300-electric-outboard-motor | NT300 |
| S48 | https://www.echolotzentrum.de/en/shop/haswing-protruar-1-0-elektro-aussenborder-900mm/ | Haswing Protruar 1.0/3.0/5.0, precios |
| S49 | https://haswingoutdoor.com/products/protruar-brushless-motor-1-0-12v | Protruar 1.0: hélice 9,3", 1.250 rpm, agua salada |
| S50 | https://drev.se/produkt/haswing-protruar-5-0-24-volt/ | Protruar 5.0: 14 kg, 10,7", 7.995 SEK |
| S51 | https://www.echolotzentrum.de/en/shop/zebco-rhino-vx-65-v2-elektrischer-aussenbordmotor/ | Rhino VX65: 560 W, 47 A, 439,99 € |
| S52 | https://fishingtackleireland.ie/products/rhino-vx-65-v2-electric-outboard-motor | Rhino VX65: 489,99 € |
| S60 | https://www.boote-magazin.de/en/motors/electric-motors/motors-test-electric-outboard-comparison/ | Bollard de 0,31 y 0,29 kN; 5 km/h con 186 y 200 W; inflables de 3,20 m (verificado con texto crudo) |
| S61 | https://www.cruisingworld.com/gear/gear-test-electric-motors-for-dinghy-engines/ | Inflable de 8 ft: W y kn de Spirit Evo y Torqeedo 1103 |
| S62 | https://www.mby.com/video/best-2-3hp-outboard-motors-electric-petrol-group-test-117786 | F-RIB de 2,75 m: velocidades con 1 y 2 personas, petrol y eléctricos (verificado con texto crudo) |
| S63 | https://www.pbo.co.uk/gear/epropulsion-electric-outboard-on-test-how-it-performs-long-term-76278 | Tuffy de 3 m: 4 kn a máxima |
| S64 | https://www.seahopperfoldingboats.com/2021/01/26/should-you-electrify-your-seahopper/ | Scamp + Newport de 46 lb: 4,5 mph |
| S65 | https://forums.iboats.com/threads/multi-trolling-motors-on-same-boat-disappointing-performance.564756/ | Gheenoe: 3–4 mph con trolling de 55 lb |
| S66 | https://www.boatdesign.net/threads/small-electric-outboard-endurance-%E2%80%93-real-world-experience.53817/ | 17 ft: 8,8 km/h con 600 W |
| S67 | https://smallcraftadvisor.substack.com/p/diy-outboards-pt-5-props | DIY de 1,8 kW: la APC 10×10 fue la hélice más eficiente; empuje medido < calculado |
| S68 | https://www.practical-sailor.com/systems-propulsion/outboards/practical-sailor-tests-4-horsepower-electric-outboard/ | (contexto: velero de 2.000 lb, 4 kn con 22 A a 48 V) |
| S69 | https://www.boatdesign.net/threads/how-many-lbs-of-thrust-is-equal-to-1-hp.24964/ | Reglas de lb por hp (contexto) |
| S70 | https://electrek.co/2023/04/20/mercury-avator-electric-outboard-motor-performance/ | Avator 7.5e: 60 min y 8 km a máxima; 19 h y 55 km al 25 % |
| S71 | https://www.practical-sailor.com/systems-propulsion/outboards/practical-sailor-compares-3-electric-outboards/ | (contexto: T-1003 a 7–8 kn en un dinghy liviano) |
| S72 | https://waves.com.au/collections/aluminium-boats/products/240-pathfinder | Horizon 240 Pathfinder: 2,40 m, 1,45 m, 50 kg, 2 personas, 5 hp long shaft, AUD 3.319 solo casco (agregada en la verificación) |

No abiertas, solo pistas: buscar: Lund 1040 jon specs transom; buscar: Minn Kota Endura bracket max transom thickness; buscar: ISO 14946 maximum load includes outboard motor; buscar: tinboats 8 ft jon boat trolling motor speed GPS.

---

## Verificación (adversarial)

Hecha el 2026-10-01. Se reabrieron las 61 URLs citadas: 56 con curl (HTML crudo o pdftotext) y S2, S5, S6, S15 y S35 con WebFetch, porque curl recibe 403, 503 o CAPTCHA. Las 61 abrieron, ninguna quedó sin abrir. Se agregó una URL nueva (S72). Se recalcularon todas las cuentas de A.3, B.2, B.3, C.1, C.2 y C.3.

| Afirmación / URL | Estado | Nota |
|---|---|---|
| S1 Alumacraft 1032 (10'2", 47", 99 lb, 375 lb, 3 hp, espejo 15", 0,059") | OK | Texto literal |
| S2 Tracker Grizzly 10 (9'10", 1,32 m, 3,5 hp, USD 1.495) | OK | Con WebFetch (curl da 403). El precio es del modelo 2027 |
| S3 Aquarib ALU-360 (3,60 m, 60 kg, 2 mm, 15.995 kr) | OK | — |
| S4 Stacer 3 m (44 kg, 1,2 mm, 6 hp, AUD 950) | corregido | "motor ≤ 28 kg" es en la fuente "Main Motor Weight: 28kg"; queda como interpretación [ESTIMADO] |
| S5 La Maltière 285 (1,22 m, 0,41 m, 42 kg, 220 kg, calado 10 cm) | OK | WebFetch literal: "Width: 4.002625" ft = 1,22 m. Un resumen de WebFetch volvió a convertir mal (dio 1,40 m), lo que confirma la advertencia de §0 |
| S6 La Maltière 2700 | OK / corregido | Los valores incoherentes (1,148 m de manga y de alto; 97,6 lb de carga) están en la fuente; bien descartados. "Soldado" no figura (la fuente habla de juntas de silicona): se quitó |
| S7 Marine 12 Jon (3,70 m, 37 kg, 278 kg, 3 p., 3,5 PS, cat. D, 2.035 €) | OK | La página nombra un "10 JON" sin dar su eslora; nota agregada en A.1 |
| S8 Aquarib 3000 (300×128×50, ~50 kg, 200 kg, 6 hp con 2,5 recomendado, 5052-H32, 12.995 kr) | OK | Precio tomado de itemprop="price" 12995.00 |
| S9 Kimple 330 (3,30 m, 1,16 m, 45 kg, 220 kg, 38 cm, 1,4 mm, 18.900 SEK) | OK | — |
| S10 Princecraft PR 1032 (3,04 m, 36 kg, 2 p., 3,5 hp) | OK | — |
| S11 / S12 Mini Tinny 210 / 295 | OK | Además, ambas páginas listan el **Horizon 240** (< 2,5 m), que faltaba. Agregado con S72 |
| "Lo único < 2,5 m que encontré es…" (A.1) | corregido | Se agrega el Horizon 240 Pathfinder: 2,40 × 1,45 m, 50 kg, 5 hp **long shaft** (S72) |
| S13 Lowe L1032 (10'0", 4'0", 80 lb, 1'3", 275 lb, 2 asientos) | OK | — |
| S14 Stessco 309 (3.100 / 1.440 / 500 mm, 1,6 mm, 6 hp, 35 kg en espejo, short 15", 65 kg, POA) | OK | — |
| S15 Bantam 10 (3,0 m, 44", 15", 38 kg, 168 kg, 5 hp, 1,2 mm, £1.199) | corregido | Valores OK con WebFetch (curl recibe CAPTCHA). "Fondo plano" no figura en la fuente: se quitó del rótulo |
| S16 / S17 SeaExplorer 370 + trolling (18.500 kr) / 400UL | OK | Contexto |
| S18 / S19 SeaExplorer 310 (3,08 m, 41 kg, 218 kg, 4 hk, motor ≤ 18,2 kg, 1,2 mm H36, cat. D, 14.500 / 18.900 kr) | OK | Texto literal en las dos |
| S20 Seahopper Scamp "22 kg casco" | **eliminado** | S20 solo da 32 kg (con 3 asientos y remos). El material ("madera") tampoco figura: se quitó |
| S21 Appleby 10 ft, 245 lb | OK | — |
| S22 / S23 pata de 15/20/25"; placa 2–3" bajo el fondo en dinghies y cascos de desplazamiento | OK | — |
| S24 USCG 183.53 (factor 0–35 → 3 hp; fondo plano: bajar un escalón) | OK | 3 hp es el escalón mínimo de la tabla |
| S25 USCG 183.35 (1/5) y 183.41 (+32 lb / 141 lb) | OK + agregado | Se agrega 183.37: 3/10 para botes clasificados ≤ 2 hp (fila nueva en A.3) |
| S26 RCD 2,5–24 m | OK | La fuente dice "generally have a hull length from 2.5 to 24 metres" |
| S30 tabla de ePropulsion (125–1.000 W; 5,6–10 km/h) | **corregido** | Valores OK, pero el casco **no** está "sin especificar": es "12-foot aluminium boat, one operator… calm lake". Cambia la lectura de C.2 |
| S31 manual de la Evo (20,8 A, 55 %, 1.200 rpm, 280 mm / 5,8", 28–63 mm, espejo de 400–500 mm, 10,2 kg S) | OK / corregido | El cable de seguridad "is recommended", no es obligatorio. El manual da 10,6 kg para la L (no 11,3) |
| S32 Watski: "18.589 kr completo" | **corregido** | El motor "leveres uden batteri og betjening". Completo: 9.199 + 9.390 + 2.578 (caña) + 719 (cargador) = **21.886 kr**. Motor "Ikke på lager" (sin stock) el día de la consulta |
| S33 GBS: Evo 2.549 € con batería y cargador; 71 lb; 19,4 kg | OK | Configurado con caña |
| S34 ficha de Torqeedo: W de la fila #14 | corregido | La ficha da km/h, autonomía y tiempo de marcha, no W. Los W salen de 915 Wh / tiempo [CALCULADO]. S34 no da el diámetro de hélice |
| S35 manual DK de Torqeedo (44 %, 700 / 1.200 / 1.450 rpm, trim 0/7/14/21°) | OK | Con WebFetch (curl da 503); PDF leído con pdftotext |
| S36 / S37 Travel 1103 descontinuado; Travel 2024 a 2.699 € (36 V, 70 lb, 1.450 rpm, 20,2 kg, 10 × 6,5) | OK | S37 no da el largo de la pata L (75 cm) |
| S38 / S39 Riptide RT80 (24 V, 56 A, 80 lb, 42", USD 999,99–1.105,59) | OK | — |
| RT80 "18,1 kg (40 lb)" | **no verificado** | En S39 es "9"H x 22"W x 59"L WT: 40.0lbs", o sea el peso con caja |
| S40 / S41 Riptide 55 SC (600 W, 9,6 kg, 107 cm, 659 €) | OK | — |
| S42 Riptide Endura C2 55 (24,9 kg, 620 W / 50 A, 107 cm, 5.499 kr) | OK | Hélice Power Prop |
| S43 / S44 / S45 Watersnake (A, kg, AUD; 3.199 SEK) | OK | Los W de la tabla son V × I [CALCULADO]; se etiquetaron |
| S46 Newport NV 55 "desde USD 169,99" | **corregido** | 169,99 es el de 36 lb. El de 55 lb cuesta USD 239,99 y el de 86 lb USD 359,99 (JSON de variantes de la página) |
| S47 Newport NT300 (1.300 W, 37 A, 110 lb, 23,8 lb, 24,6" / 29", 9,8" 2 palas, USD 1.299,99) | OK | — |
| S48 Haswing 1.0 (29,5 kgf, 600 W, 50 A, 5,9 kg, 900 mm, 1.250 rpm, 429 €); 3.0 699,01 €; 5.0 999 € | OK / corregido | El peso y la pata de la 3.0 no figuran: [NO VERIFICADO] |
| S49 Haswing 1.0 (9,3", 1.250 rpm, 6,6 kg, USD 319,99) | OK + agregado | La misma ficha declara "SHAFT POWER 1HP" con 600 W de entrada: incoherente |
| S50 Haswing 5.0 (160 lb, 10,7", 1.450 rpm, 2.520 W, 1.000 mm, 14 kg, 7.995 SEK) | OK | — |
| S51 / S52 Rhino VX65 V2 (560 W, 47 A, 79 cm, 10,0 kg, 439,99 € / 489,99 €) | OK | — |
| S60 Boote (0,31 / 0,29 kN; 3,20 m; 186 / 200 W a 5 km/h; 9,0 / 7,6 km/h; 2.249 / 1.699 €) | OK | No dice a qué potencia se midió el bollard |
| S61 Cruising World (8 ft; Evo 2,3 / 3,3 / 4,2 kn con ~100 / ~500 W / a fondo; Torqeedo 3,6 / 4,3 kn) | OK + agregado | Los "1.000 W" a fondo son nominales, no leídos. Se agrega el Mercury de 2,5 hp de gasolina a 4,6 kn en el mismo casco (fila 5b) |
| S62 MBY (F-RIB de 2,75 m; 4,2 / 4,1 kn de a dos; gasolina 4,4–5,0 kn; planeo 9,5 / 8,0 kn de a uno; £579–760) | OK | Texto crudo. La URL es de una página de video, pero todos los datos salen del artículo escrito; no se cita contenido del video. La fuente se contradice en el Torqeedo: £2.109 en el texto y £2.019 en la ficha |
| S63 PBO (4 kn a fondo; 1,4 kn al 20 %) | OK + nota | Medido "against 2 knots of tide" |
| S64 Seahopper (Scamp, Newport de 46 lb, 4,5 mph, 15–20 % en 2 h) | OK | Testimonio de un dueño (Jim); 4,5 mph sobre una milla cronometrada |
| S65 Gheenoe (3 / 4 mph) | OK | — |
| S66 boatdesign, 17 ft "~400 kg" | corregido | La serie de 600 W y 8,8 km/h se hizo con ~350 kg en total |
| S67 / S68 / S69 / S70 / S71 | OK | Contexto; Avator: 8 km en 60 min y 55 km en 19 h |
| Cuentas de A.3, B.2 (FM requerido), B.3 (T y η_i), C.1 (Wh/km, R), C.2 (Fn, k), C.3 (P, energía) | OK | Recalculadas en Python; coinciden con ±1 en el último dígito |
| B.2 "físicamente imposible" (Haswing) | corregido (matiz) | Imposible solo si η_motor ≤ 0,85. Con η 0,9 hace falta FM 0,97, igual no creíble |
| Valores del proyecto citados (130/169 N, 578/819 W, η 34 %, bollard 297 N, placa 250 kg, 7,46 DKK/EUR) | **corregido** | Desactualizados. Hoy `sizing_tablas.md` da 135/156 N, 759/910 W, η 29 %, bollard 280 N y V máx 6,7–7,4 km/h; `inputs.yaml` usa placa de 160 kg y 7,4755 DKK/EUR |
| Contenido de videos, números de pieza, propiedades de materiales | OK | No hay contenido de video presentado como visto ni números de pieza inventados. Los materiales (5052-H32, H36) son citas de las fichas. El FM de 0,6–0,75 sigue como [ESTIMADO: memoria técnica, no verificado] |

## Hallazgos que cambian el diseño

- **La placa de carga es el riesgo número 1, no la potencia.** Los aluminio de fondo plano con norma CE o USCG cargan **34–63 kg por m² de LOA × manga**. Para 2,44 × 1,20 m eso da **~100–185 kg** (regla USCG 183.35 ≈ 160 kg), y la cifra incluye motor y equipo. `inputs.yaml` ya usa una placa de 160 kg [ESTIMADO]. `sizing_tablas.md` da una **carga útil de 248 kg frente a 160 kg de placa (155 %)**: con 2 adultos y la propulsión, la placa estimada se pasa por 88 kg. Hay que medir el bote real y leer su placa. Si es < 250 kg, o se limita a 1 adulto + equipo, o se baja la masa de propulsión y batería. **No vale subir la placa por cálculo propio.** La regla de 3/10 de USCG 183.37 (≈ 240 kg) solo aplica si el fabricante clasificó el casco para ≤ 2 hp (S25). Además, un casco < 2,5 m queda fuera del marcado CE (S26) y puede no traer placa.
- **Masa colgada del espejo ≤ 18–28 kg, con 35 kg como tope absoluto.** Es el límite que publican los fabricantes de cascos de 2,1–3,1 m (S11, S12, S14, S4, S18). El conjunto motor + soporte con cardán + correa + eje y tubo de 1,3 m + hélice tiene que pesar ≤ ~20 kg [SUPUESTO: meta]. **La batería va al centro o adelante**, nunca en el espejo. Con 2 personas sentadas atrás, el francobordo de popa ya es de ~12–18 cm [ESTIMADO: francobordo medio de 0,18 m (A.4) menos el trimado a popa].
- **El espejo puede medir 381 mm (15") o 508 mm (20").** Uno de los dos aluminios < 2,5 m con ficha (Horizon 240, 50 kg) pide "long shaft" (S72); el otro (Mini Tinny 210) pide "short shaft" (S11). El soporte de popa tiene que admitir alturas de espejo de **330–510 mm** (agujeros o corredera de ajuste vertical de ≥ 180 mm) [CALCULADO: 510 − 330, rango de A.4].
- **La meta de 8–12 km/h "por ratos" hay que bajarla.** Con 1,0–1,1 kW, los comerciales llegan a **7,6–7,8 km/h con 2 personas** en un F-RIB de 2,75 m (S62) y a 7,8–8,0 km/h en un inflable de 8 ft (S61). Un Mercury de gasolina de 2,5 hp hace 8,5 km/h en ese mismo inflable (S61). Los de gasolina de 2,3–2,5 hp (~1,8 kW al eje) no pasan de 8,1–9,3 km/h y no planean con dos a bordo (S62). El diseño actual del proyecto calcula **6,7–7,4 km/h** de máxima. Llegar a 12 km/h exigiría ~2,6–5,9 kW eléctricos y planear [ESTIMADO, banda C.3], fuera de batería, correa y presupuesto razonables para un casco de ≤ 3 hp de placa (S24).
- **Calibración de R(6 km/h) = 95–150 N.** P_bat = 350–560 W con η 0,45 y **546–862 W con el η 0,29 actual**. El mejor análogo de largo es un inflable de 8 ft, que necesitó **500 W a 6,1–6,7 km/h** (S61). El R nominal de 135 N del proyecto queda dentro de la banda y el de diseño (156 N) apenas encima (+4 %). Las tablas de fabricante (ePropulsion 125 W a 5,6 km/h en un aluminio de 12 ft **con 1 persona**; Torqeedo 153 W a 5,5 km/h) piden 2–3 veces menos energía y **no sirven** para un casco de 2,44 m con 2 personas.
- **Energía: el margen es escaso.** Para 2 h a 6 km/h con 20 % de reserva hacen falta 1,37–2,16 kWh con η 0,29 [CALCULADO]. El proyecto tiene 2,30 kWh usables, pero su propio requerimiento de diseño es de 2,43 kWh (−5 %, `sizing_tablas.md`). Cada 5 puntos de η_tot que se ganen (de 0,29 a 0,34) ahorran **~15 %** de batería [CALCULADO: 1 − 0,29/0,34].
- **Hélice: 10–11" en vez de 7,8", y ≤ 1.200–1.450 rpm a plena potencia.** Las referencias usan 280 mm × 5,8" a 1.200 rpm (S31) y 10 × 6,5 o 10,2 × 6,6 a 1.450 rpm con 1,1 kW (S37, S67, S34). Frente a la de 7,8" (198 mm), una de 10–11" da **+18–26 % de empuje a punto fijo** y **−9 a −15 % de energía en crucero** [CALCULADO B.3]. Conviene el diámetro máximo que permita el calado. Con 381 mm de espejo, la placa anticavitación iría ~50–75 mm bajo el fondo (S23), y la basculación protege en la arena.
- **Bollard objetivo: ~290–310 N a ~1 kW, lo mismo que se mide en los comerciales** (0,28–0,29 N/W, S60). El proyecto calcula hoy 280 N, un 3–10 % menos. Los "65 lb a 600 W" (0,48–0,52 N/W) de Haswing y Rhino exigen FM ≥ 1,02 con η_motor ≤ 0,85, y Haswing además declara 1 hp al eje con 600 W de entrada (S49). **No son creíbles**: no sirven como meta ni como argumento de compra.
- **El techo de costo del DIY es el ePropulsion Spirit 1.0 Evo completo: 21.886 kr en DK** (motor 9.199 + batería de 1.276 Wh 9.390 + caña 2.578 + cargador 719 kr; Watski, S32), o **2.549 € en Alemania** con batería, caña y cargador (S33). *Corregido:* antes decía 18.589 kr. El piso es un trolling de 55 lb para agua salada: 5.499 kr el Riptide Endura C2 55 (S42), 3.199 SEK el Watersnake SXW 54 (S44) o USD 239,99 el Newport NV 55 (S46). El DIY se justifica solo si, con batería incluida, cuesta bastante menos que ~19.000–21.900 kr **y** da ~1 kW, basculación con protección, marcha atrás y pasador de corte.
- **Montaje:** el espejo puede ser de chapa desnuda de 1,2 mm (Stacer, S4). En ese caso el soporte de popa necesita un taco o contraplaca (madera dura o HDPE de ≥ 25 mm [SUPUESTO]) que reparta la carga, y una abrazadera para **20–65 mm** (la de ePropulsion va de 28 a 63 mm, S31). Agregar el **cable de seguridad** del soporte al bote que recomienda el manual de ePropulsion (S31).
