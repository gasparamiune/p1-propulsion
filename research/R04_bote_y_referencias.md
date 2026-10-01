# R04 — Jon boats de aluminio < 2,5 m y referencias comerciales (trolling motors / fueraborda eléctricos)

Fecha de consulta de todas las fuentes: 2026-10-01. Alcance: (A) geometría, peso, capacidad y espejo de botes de aluminio de fondo plano chicos; (B) motores comerciales aptos para agua salada como referencia de empuje, consumo, peso y costo; (C) datos medidos de velocidad contra potencia en botes chicos, para calibrar R(v).

## 0. Método y convenciones

- **Etiquetas:** [VERIFICADO: Sx] = leído en la fuente Sx (lista en §D) abierta en esta sesión; [CALCULADO] = cuenta hecha aquí con datos verificados (fórmula indicada); [ESTIMADO: base]; [SUPUESTO]. "buscar: …" = no se pudo abrir ninguna fuente que lo respalde.
- **Unidades:** 1 lbf = 4,448 N; 1 lb = 0,4536 kg; 1 in = 25,4 mm; 1 kn = 1,852 km/h; 1 mph = 1,609 km/h. Para pasar EUR a DKK uso 7,46 DKK/EUR [ESTIMADO: valor que ya usa `inputs.yaml`]. Los precios en SEK, GBP, USD y AUD quedan en su moneda; no los convierto porque no verifiqué el tipo de cambio.
- **Control de calidad:** WebFetch resume las páginas con un modelo y **se equivocó al menos una vez**: en La Maltière 285 dio una manga de 1,35 m, pero el texto crudo dice 4,0026 ft = 1,22 m. Los números de las tres fuentes con más peso en las conclusiones (Boote, MBY y La Maltière 285) los revisé contra el HTML crudo con curl. Los PDF de Torqeedo, ePropulsion y BoatBuilderCentral los leí con pdftotext. El resto viene del resumen de WebFetch.
- **Bloqueados (403, Cloudflare o tollbit):** lundboats.com, minnkota.johnsonoutdoors.com, tinboats.net, forum.crappie.com, bassresource, thehulltruth, microskiff, svb24, la página de Lowe, seajayboats y proalimarinepunts. Ningún dato sale de ellas.

---

## Parte A — Botes de aluminio de fondo plano chicos

### A.1 Hallazgo de mercado

- **Casi no existen jon boats de aluminio < 2,5 m en catálogos actuales.** Los modelos más chicos de Tracker, Lowe, Alumacraft, Princecraft y Marine (CZ) miden 3,0–3,1 m [VERIFICADO: S1, S2, S10, S13, S7]. En Dinamarca, los aluminio de fondo plano a la venta arrancan en 3,0–3,08 m (Aquarib 3000, SeaExplorer 310 ALU) [VERIFICADO: S8, S18, S19]. Lo único < 2,5 m que encontré es el SeaCraft Mini Tinny 210 (AU, 2,10 m) y dos plegables de madera, Seahopper Scamp (2,03 m) y Lighter (2,40 m) [VERIFICADO: S11, S20].
- **Consecuencia:** el bote del usuario es probablemente un 8 ft estadounidense viejo, un *car-topper* australiano o chino, o algo casero. No hay ficha de fábrica confiable, así que **hay que medirlo**: eslora, manga, ancho de fondo, puntal, alto y espesor de espejo, y placa de capacidad si la tiene.
- **Marco legal:** la Directiva 2013/53/UE de embarcaciones de recreo cubre "a hull length from 2.5 to 24 metres" [VERIFICADO: S26]. Un bote con casco < 2,5 m queda **fuera del marcado CE**, así que puede no traer categoría de diseño ni placa de carga máxima [ESTIMADO: inferencia del alcance; buscar: Søfartsstyrelsen fritidsfartøjer under 2,5 m krav].

### A.2 Tabla de cascos (de menor a mayor eslora)

| Modelo (origen) | LOA m | Manga m | Puntal m | Peso vacío kg | Personas | Carga máx kg | hp máx | Espejo | Chapa mm | Precio (fuente) |
|---|---|---|---|---|---|---|---|---|---|---|
| Seahopper Scamp (UK, **madera plegable**, ref. geométrica) | 2,03 | 1,27 | — | 22 casco / 32 equipado | 3 (remo/motor) | 250 | — | — | (madera) | — [VERIFICADO: S20] |
| SeaCraft Mini Tinny 210 (AU) | 2,10 | 1,16 | — | 22 | 2 | — | 5 (3,5 recom.) | short shaft; **peso máx en espejo 35 kg** | 1,2 fondo/costados | AUD 1.999 [VERIFICADO: S11] |
| Seahopper Lighter (UK, madera plegable) | 2,40 | 1,27 | — | 34 | 4 (remo/motor) | 325 | — | — | (madera) | — [VERIFICADO: S20] |
| La Maltière Tender 2700 (FR, soldado) | 2,70 (8,86 ft) | ilegible¹ | ilegible¹ | 31 | 2 | ilegible¹ | 1–3 cv, short shaft | — | 2,0 fondo / 1,5 costados nervados | 1.709 € [VERIFICADO: S6] |
| La Maltière Tender 285 (FR, fondo plano, proa aguda) | 2,85 | 1,22 | 0,41 (alto) | 42 | 2–3 | 220 | 3–5, short shaft | — | — | desde 2.139 €; **calado 10 cm** [VERIFICADO: S5, texto crudo] |
| SeaCraft Mini Tinny 295 (AU) | 2,95 | 1,19 | — | ~30 | 2 | — | 5 | short shaft; peso máx en espejo 35 kg | 1,2/1,2 | AUD 2.199 [VERIFICADO: S12] |
| Bantam 10 (UK, fondo plano) | 3,0 | 1,1 (44") | 0,38 (proa 15") | 38 | 2 | 168 | 5 | — | 1,2 | £1.199 [VERIFICADO: S15] |
| Aquarib 3000 (DK) | 3,00 | 1,28 | 0,50 | ~50 | 2 | 200 | 6 (recom. ≤ 2,5) | short shaft | 2,0 (5052-H32), cat. C | 12.995 kr [VERIFICADO: S8] |
| Tracker Grizzly 10 Jon (US) | 3,0 (9'10") | 1,32 | — | — | — | — | 3,5 | — | — | USD 1.495 [VERIFICADO: S2] |
| Princecraft PR 1032 (CA) | 3,04 | — | — | 36 (80 lb) | 2 | — | 3,5 | — | — | — [VERIFICADO: S10] |
| Lowe L1032 Jon 2026 (US, remachado) | 3,05 (10'0") | 1,22 (4'0") | — | 36 (80 lb) | 2 | **125 (275 lb)** | no figura² | **381 mm (1'3")** | — | — [VERIFICADO: S13] |
| Stacer 3m Skimmer (AU) | 3,07 (casco 2,97) | 1,30 | 0,45 | 44 | 2 | — | 6 (motor ≤ 28 kg) | S/S | **1,2 fondo/costados/espejo** | AUD 950 (aviso) [VERIFICADO: S4] |
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
| Peso vacío / (LOA × manga) | 8,3–14,6 kg/m²; mediana ≈ 11 | [CALCULADO: 12 cascos de aluminio de A.2] |
| Carga máx / (LOA × manga), aluminio con norma CE o USCG | 34–63 kg/m²; mediana ≈ 52 | [CALCULADO: Lowe 33,6 · Alumacraft 46 · Bantam 51 · Aquarib 52 · SeaExplorer 53 · Kimple 57 · Marine 63 · La Maltière 63] |
| Carga máx / área, plegables Seahopper (sin norma) | 97–107 kg/m² | [CALCULADO: S20]: las placas varían ×2 según quien las fije |
| Regla USCG 33 CFR 183.35 | carga máx ≤ (desplazamiento máximo − peso del bote) / 5 | [VERIFICADO: S25] |
| Regla USCG 183.41 (personas) | (carga + 32 lb) / 141 lb por persona | [VERIFICADO: S25]: supone **64 kg por persona** |
| Regla USCG 183.53 (hp) | factor L × ancho de espejo (ft) ≤ 35 → 3 hp; fondo plano de pantoque duro: "reduce one capacity limit" | [VERIFICADO: S24]. 8 ft × 3 ft = 24 → **≤ 3 hp** |

### A.4 Rangos de diseño para el jon boat del proyecto (LOA ≤ 2,5 m)

| Parámetro | Mín | Típico | Máx | Base |
|---|---|---|---|---|
| LOA | 2,03 | 2,44 | 2,50 | [VERIFICADO: S20, S11] + límite del proyecto |
| Eslora en flotación (LWL) | 1,7 | 2,0 | 2,3 | [ESTIMADO: LOA − 0,2…0,5 m de proa lanzada tipo pram/jon] |
| Manga máxima | 1,10 | 1,20 | 1,30 | [VERIFICADO: 1,16 (S11), 1,27 (S20); clase 3 m 1,10–1,34] |
| Ancho de fondo (pantoque) | 0,75 | 0,90 | 1,05 | [ESTIMADO: manga − 2 × abocinado de 0,10–0,20 m; no encontré ningún dato verificado] |
| Puntal (costado) | 0,33 | 0,38 | 0,45 | [ESTIMADO: alto de espejo 0,38 (S1, S9, S13); clase 3 m 0,45–0,55 (S4, S8, S18) es mayor] |
| Peso vacío | 22 | 32 | 45 | [VERIFICADO: 22 kg Mini Tinny 210 (S11)] + [CALCULADO: 8,5–14,6 kg/m² × 2,93 m² = 25–43] |
| Carga máx de placa (personas + motor + equipo) | ~100 | ~150 | ~185 (250+ en plegables) | [CALCULADO: 34–63 kg/m² × 2,93 m²; caja 2,44 × 1,2 × 0,38 con Cb 0,75 → desplazamiento máx ≈ 845 kg → (845 − 45)/5 = **160 kg** por regla USCG] |
| Altura de espejo | 330 | **381** (15") | 430 | [VERIFICADO: 381 mm Alumacraft/Lowe (S1, S13), 38 cm Kimple (S9), "short 15"" (S14), estándar 15/20/25" (S23)]; mín y máx [SUPUESTO] |
| Espesor de espejo | ~1,2 (chapa desnuda) | 30–45 (chapa + taco) | 63 | [VERIFICADO: espejo de 1,2 mm en Stacer (S4); abrazadera ePropulsion 28–63 mm (S31)]; típico [ESTIMADO: memoria técnica, no verificado] |
| Calado cargado (Δ 250–330 kg) | 0,10 (vacío + 1 p.) | 0,17 | 0,22 | [VERIFICADO: 10 cm La Maltière 285 (S5)] + [CALCULADO: Δ / (ρ × A_flot) con A_flot 1,5–1,9 m²] |
| Francobordo cargado | 0,12 | 0,18 | 0,25 | [CALCULADO: puntal − calado] |
| Espesor de chapa | 1,2 | 1,5 | 2,0 | [VERIFICADO: S1, S4, S6, S8, S11, S14, S18] |
| **Peso máx colgado del espejo** | 18 | 28 | 35 | [VERIFICADO: motor ≤ 18,2 kg (S18); ≤ 28 kg (S4); "max transom weight 35 kg" (S11, S12, S14)] |
| Potencia máx de placa | 3 hp | 3,5–5 hp | 6 hp | [VERIFICADO: S1, S2, S4, S11, S13, S18; USCG ≤ 3 hp (S24)] |

### A.5 Montaje en el espejo

- **Altura de la hélice:** en cascos lentos o de desplazamiento, la placa anticavitación de un fueraborda chico de bote auxiliar suele ir "2 or 3" below the bottom" (51–76 mm), para no airear la hélice cuando el bote cabecea [VERIFICADO: S23]. El largo de pata se mide desde el interior de la abrazadera hasta la placa anticavitación; los estándares son 15/20/25" (381/508/635 mm) [VERIFICADO: S23].
- **ePropulsion Spirit 1.0 Evo:** abrazadera para espejos de **28–63 mm** de espesor; la pata S (625 mm) se recomienda para espejos de **400–500 mm** de alto y la L para > 500 mm [VERIFICADO: S31]. En un jon boat de 381 mm, la S queda unos 20 mm más honda que lo recomendado, lo que es aceptable a baja velocidad según S23 [CALCULADO]. El manual también pide **un cable de seguridad del motor al bote** [VERIFICADO: S31].
- **Torqeedo Travel:** pata S de 62,5 cm o L de 75 cm, con trim manual 0/7/14/21° [VERIFICADO: S34, S35].

---

## Parte B — Referencias comerciales

### B.1 Tabla de motores (bollard N/W = empuje declarado o medido / potencia eléctrica máxima)

| Motor | Tipo · agua salada | Tensión | I máx A | P eléc. máx W | Empuje lb / N | **N/W** [CALCULADO] | Peso motor kg | Pata | Hélice | Precio (fuente, 2026-10-01) |
|---|---|---|---|---|---|---|---|---|---|---|
| Minn Kota Riptide Endura C2 55 | trolling · sí | 12 | 50 | 620 | 55 / 245 (24,9 kgf) | 0,40 | — | 107 cm | "Power Prop" | **5.499 kr** [VERIFICADO: S42] |
| Minn Kota Riptide Transom 55 SC | trolling · sí (ánodo de zinc, inoxidable) | 12 | — | 600 | 55 / 245 | 0,41 | 9,6 | 107 cm | plástico | 659 € (≈ 4.916 kr) [VERIFICADO: S40, S41] |
| Minn Kota Riptide RT80/T | trolling · sí | 24 | 56 | 1.344 | 80 / 356 | 0,26 | 18,1 (40 lb) | 42" | Weedless Wedge 2 | USD 999,99–1.105,59 [VERIFICADO: S38, S39] |
| Watersnake Venom SXW 54/42 | trolling · sí | 12 | 13–54 | 648 | 54 / 240 | 0,37 | 8,5 | 42" (106 cm) | 3 palas | 3.199 SEK [VERIFICADO: S43, S44]; AUD 359 [S43] |
| Watersnake Venom SXW 65/42 | trolling · sí | 12 | 13–50 | 600 | 65 / 289 | 0,48 ⚠ | 10,0 | 42" | 3 palas | AUD 440 [VERIFICADO: S43] |
| Watersnake ASP T24 | trolling kayak · sí | 12 | 9–20 | 240 | 24 / 107 | 0,45 | — | 61 cm | — | AUD 189 [VERIFICADO: S45] |
| Newport NV 55 | trolling con escobillas · sí | 12 | 52 | 624 | 55 / 245 | 0,39 | 10,4 (23 lb) | 30" | 3 palas | desde USD 169,99 [VERIFICADO: S46] |
| Newport NV 86 | trolling con escobillas · sí | 24 | 48 | 1.152 | 86 / 383 | 0,33 | 11,3 (25 lb) | 36" | 3 palas | [VERIFICADO: S46] |
| Rhino VX65 V2 | trolling · "saltwater compatible" | 12 | 47 | 560 | 65 / 289 | **0,52 ⚠** | 10,0 | 79 cm | — | 439,99 € [VERIFICADO: S51]; 489,99 € [S52] |
| Haswing Protruar 1.0 | sin escobillas · sí según fabricante | 12 | 50 | 600 | 65 / 289 | **0,48 ⚠** | 5,9–6,6 | 900 mm (S: más corta) | 3 palas 9,3", 1.250 rpm | 429 € [VERIFICADO: S48]; USD 319,99 [S49] |
| Haswing Protruar 3.0 | sin escobillas | 24 | 60 | 1.440 | 110 / 489 | 0,34 | (5,9 publicado, dudoso³) | 900 mm | 3 palas | 699,01 € [VERIFICADO: S48] |
| Haswing Protruar 5.0 | sin escobillas | 24 | — | 2.520 | 160 / 712 | 0,28 | 14 | 1.000 mm | 3 palas 10,7", 1.450 rpm | 999 € [S48]; 7.995 SEK [VERIFICADO: S50] |
| Newport NT300 | fueraborda sin escobillas · sí | 36 | 37 | 1.300 | 110 / 489 | 0,38 ⚠ | 10,8 (23,8 lb) | 24,6" / 29" | 2 palas 9,8" | USD 1.299,99 [VERIFICADO: S47] |
| **ePropulsion Spirit 1.0 Evo** | fueraborda integrado · sí | 48 nom. (39–60) | **20,8 nominal** | 1.000 | 71 / 316 declarado; **290 medido⁴** | 0,32 declarado / **0,29 medido** | 10,2 (S) – 11,3 sin batería; batería 8,7–8,8 | 625 / 750 mm | **280 mm × 5,8" (147 mm), 2 palas, 1.200 rpm máx** | **9.199 kr motor + 9.390 kr batería 1.276 Wh = 18.589 kr** [VERIFICADO: S32]; 2.549 € con batería y cargador [S33] |
| **Torqeedo Travel 1103 C** (descontinuado) | fueraborda integrado · sí | 29,6 | — | 1.100 (propulsiva 540) | 70 / 311 declarado; **310 medido⁴** | 0,28 / **0,28** | 11,3 (S) + batería 6,0 = 17,3 | 62,5 / 75 cm | v10/p1100, 1.450 rpm | "on request" [VERIFICADO: S34, S36]; 2.249 € en el test [S60] |
| Torqeedo Travel (2024) | fueraborda · sí | 36 | — | 1.100 | 70 / 311 | 0,28 | 20,2 con batería | 62,5 / 75 cm | 10 × 6,5 | **2.699 €** con batería de 1.080 Wh y cargador [VERIFICADO: S37] |

³ La página repite 5,9 kg para la 3.0 de 24 V; parece copiado de la 1.0.
⁴ Tracción a punto fijo medida por Boote: "Torqeedo with 0.31 kN … ePropulsion with only 0.29 kN" [VERIFICADO: S60, texto crudo]. El test usó la Spirit 1.0 anterior (batería de 1.080 Wh), no la Evo.

Otros datos verificados:
- **Rendimiento total máximo** (batería → potencia propulsiva): Travel 503 44 % (manual) a 48 % (ficha), Travel 1003 48 %, Travel 1103 C 49 % [VERIFICADO: S34, S35]; Spirit 1.0 Evo 55 % [VERIFICADO: S31]. El proyecto calcula hoy 34 % en el caso de diseño (`resultados/sizing_tablas.md`).
- **rpm de hélice a plena carga:** Travel 503 875 (700 según el manual DK), 1003 1.125 (1.200 según el manual DK), 1103 C 1.450 [VERIFICADO: S34, S35]; Spirit Evo 1.200 [VERIFICADO: S31]. **Ningún fueraborda eléctrico de 1 kW gira la hélice por encima de 1.450 rpm.**

### B.2 ¿Son creíbles los empujes declarados? (control por teoría de cantidad de movimiento)

Empuje ideal a punto fijo: T_id = (2·ρ·A·P_eje²)^(1/3), con ρ = 1.013 kg/m³. Los "figures of merit" reales de hélices marinas a punto fijo andan en 0,6–0,75 [ESTIMADO: memoria técnica, no verificado], así que exigir FM ≥ 0,9 ya es poco realista. FM_req = (T_declarado / T_id)^1,5 [CALCULADO]:

| Motor | D hélice | P_eje (η_motor 0,75–0,85) | T_id N | Declarado N | FM requerido | Veredicto |
|---|---|---|---|---|---|---|
| Haswing Protruar 1.0 | 9,3" [S49] | 450–510 W | 262–285 | 289 | **1,02–1,16** | **físicamente imposible** |
| Rhino VX65 | 10" [SUPUESTO] | 420–476 W | 263–285 | 289 | 1,02–1,16 | imposible con 10"; requiere ≥ 12" |
| Newport NT300 | 9,8" [S47] | 975–1.105 W | 454–494 | 489 | 0,99–1,12 | inflado |
| Minn Kota Riptide 55 | 10" [SUPUESTO] | 450–510 W | 275–299 | 245 | 0,74–0,84 | optimista (≈ 10–20 %) |
| Watersnake SXW 54 | 10" [SUPUESTO] | 486–551 W | 289–315 | 240 | 0,67–0,76 | creíble en el límite |
| Torqeedo 1103 C | 11" [SUPUESTO] | 825–935 W | 439–477 | 311 (**medido 310**) | 0,53–0,60 | coherente con la medición |
| ePropulsion Evo | 280 mm [S31] | 750–850 W | 412–448 | 316 (**medido 290**) | 0,59–0,67 | coherente |

**Conclusiones:**
- Las dos únicas mediciones independientes dan **0,28–0,29 N/W a 1,0–1,1 kW** [VERIFICADO: S60].
- Los 0,45–0,52 N/W de trolling motors de 12 V y 560–600 W **no son creíbles** en los modelos Rhino, Haswing y Watersnake 65. Como el empuje escala con P^(2/3), lo esperable a 600 W con una hélice de 10" es ~0,33–0,38 N/W [CALCULADO: 0,29 × (1.050/600)^(1/3) = 0,35].
- **Para el proyecto:** el bollard que calcula hoy (297 N avante) iguala al Torqeedo y al ePropulsion medidos. Es un objetivo realista; no hace falta perseguir los "55–65 lb" de catálogo.

### B.3 Efecto del diámetro de hélice (relevante para elegir entre la de fueraborda de 7,8" y la de 10–11")

| D | T a punto fijo con P_eje 450 W, FM 0,7 | η ideal a 6 km/h, T = 100 N | η ideal a 6 km/h, T = 150 N |
|---|---|---|---|
| 198 mm (7,8") | 184 N | 0,71 | 0,64 |
| 236 mm (9,3") | 207 N | 0,76 | 0,70 |
| 254 mm (10") | 217 N | 0,78 | 0,72 |
| 280 mm (11", como la Spirit) | 231 N | 0,81 | 0,75 |

[CALCULADO: η_i = 2 / (1 + √(1 + C_T)), C_T = T / (½ρAv²), v = 1,667 m/s.] Pasar de 7,8" a 10–11" sube el empuje a punto fijo un 18–26 % y baja la energía de crucero un 9–15 % para la misma eficiencia relativa. Los dos fueraborda eléctricos de referencia usan hélices de ~10–11" y 1.200–1.450 rpm [VERIFICADO: S31, S34, S37].

### B.4 Referencia de costo y prestaciones

| Solución "comprada" | Costo DK/EU | Batería | Qué entrega |
|---|---|---|---|
| Trolling de agua salada 55 lb, 12 V | 5.499 kr (Riptide C2 55, S42); 3.199 SEK (Watersnake SXW 54, S44); USD 169,99 (Newport NV 55, S46) | 12 V aparte | ~0,6 kW. Sin basculación con protección ante golpes; pata de 30–42" larga para un espejo de 381 mm |
| Fueraborda eléctrico de 1 kW completo | **18.589 kr** (ePropulsion Evo S, S32); 2.549 € (S33); 2.699 € (Torqeedo Travel con batería, S37) | 1,08–1,28 kWh integrada | 7,6–8,0 km/h con 2 personas en un bote de 2,75 m (§C); basculación ante golpes, marcha atrás, IP67, display |
| Petrol 2,3–2,5 hp | £579–760 [VERIFICADO: S62] | — | 8,1–9,3 km/h con 2 personas en un bote de 2,75 m (§C) |

**El techo de costo del DIY** es lo que cuesta el ePropulsion completo: ~18.600 kr ≈ 2.490 € [CALCULADO con 7,46]. El piso es un trolling de agua salada de 55 lb con batería LiFePO₄ de 12 V. Para que el DIY tenga sentido tiene que cumplir dos cosas a la vez: (a) costar bastante menos que ~2.500 € con batería incluida, y (b) dar el ~1 kW, la basculación con protección y la marcha atrás que un trolling de 600 W no da.

---

## Parte C — Velocidad contra potencia medida en botes chicos (para calibrar R(v))

### C.1 Datos

Wh/km = P / v. R se despeja como R = η·P / v, con η batería→propulsión entre 0,40 y 0,50, tomado de los rendimientos máximos de B.1 menos una pérdida a carga parcial [ESTIMADO].

| # | Fuente | Casco · carga | Motor | P eléc. W | v km/h | Wh/km | R (η 0,40–0,50) N | Calidad |
|---|---|---|---|---|---|---|---|---|
| 1 | Cruising World [S61] | **inflable West Marine de 8 ft (2,44 m)** · carga no declarada; viento de 5 kn y ola chica en la máxima | Spirit 1.0 Evo | 100 | 4,26 (2,3 kn) | 23 | 34–42 | A (prueba de revista) |
| 2 | ídem | ídem | Spirit 1.0 Evo | **500** | **6,11** (3,3 kn) | **82** | **118–147** | A |
| 3 | ídem | ídem | Spirit 1.0 Evo | 1.000 | 7,78 (4,2 kn) | 129 | 185–231 | A |
| 4 | ídem | ídem | Torqeedo 1103 S | 500 | 6,67 (3,6 kn) | 75 | 108–135 | A |
| 5 | ídem | ídem | Torqeedo 1103 S | 1.000 | 7,96 (4,3 kn) | 126 | 181–226 | A |
| 6 | MBY [S62, texto crudo] | **mini-RIB plegable F-RIB de 2,75 m · 2 personas** | Torqeedo 1103 C | 1.100 | **7,78** (4,2 kn) | 141 | 204–255 | A |
| 7 | ídem | ídem · 2 personas | Spirit 1.0 Plus | 1.000 | **7,59** (4,1 kn) | 132 | 190–237 | A |
| 8 | ídem | ídem · 1 persona | Torqeedo / Spirit | 1.100 / 1.000 | 8,70 / 7,96 | 126 | 181–227 | A |
| 9 | ídem | ídem · 2 personas | **petrol 2,3–2,5 hp** (1,7–1,9 kW al eje) | — | **8,1–9,3** (4,4–5,0 kn) | — | 254–403 (η_prop 0,35–0,5) | A |
| 10 | ídem | ídem · 1 persona | Yamaha 2,5 / Selva 2,5 | — | **17,6 / 14,8 (planeo)** | — | — | A |
| 11 | Boote [S60, texto crudo] | dos inflables de alta presión de 3,20 m · carga no declarada | Torqeedo 1103 C / Spirit 1.0 | 186 / 200 | 5,0 | 37 / 40 | 54–72 | A |
| 12 | ídem | ídem | Torqeedo / Spirit, potencia máxima | 1.100 / 1.000 | 9,0 / 7,6 | — | — | A |
| 13 | PBO [S63] | tender de GRP Tuffy de 3 m | Spirit 1.0 | 1.000 (máx) | 7,4 (4 kn); 1,4 kn al 20 % | — | — | B (sin carga declarada) |
| 14 | Torqeedo, ficha [S34] | "dinghy, daysailer up to 1.5 t" (bote sin especificar) | Travel 1103 C, 915 Wh | 46 / 153 / 1.098 | 3,7 / 5,5 / 10,0 | 12 / 28 / 110 | 18–22 / 40–50 / 158–198 | C (catálogo, optimista) |
| 15 | ePropulsion, tabla [S30] | bote sin especificar | Spirit 1.0 | 125 / 250 / 500 / 750 / 1.000 | 5,6 / 7,1 / 8,5 / 9,2 / 10,0 | 22 / 35 / 59 / 82 / 100 | 32–40 / 51–63 / 85–106 / 117–147 / 144–180 | C (catálogo, optimista) |
| 16 | Electrek, Avator 7.5e [S70] | Veer X13 | Mercury Avator 7.5e, 1 kWh | ~1.000 / ~53 | 8 / 2,9 (8 km en 60 min; 55 km en 19 h) | ~125 / ~18 | — | B |
| 17 | Seahopper [S64] | **Seahopper Scamp de 2,03 × 1,27 m** · 2 personas | Newport de 46 lb y 12 V, batería de plomo de 90 Ah | ~81–108 promedio [CALCULADO: 15–20 % × 90 Ah × 12 V / 2 h], "mostly around half-throttle" | 7,2 (4,5 mph, "timed run"; no necesariamente a esa potencia) | — | — | C (anécdota; consumo estimado por % de batería) |
| 18 | iboats [S65] | Gheenoe de 15' · aguas planas | 55 lb de proa / 55 lb 12 V de popa | ~600 máx | 4,8 / 6,4 (3 / 4 mph, GPS) | — | — | C |
| 19 | boatdesign [S66] | bote de remo de 17 ft, ~400 kg | Torqeedo Cruise 2.0 | 600 | **8,8** | 68 | — | B (contraste: casco largo) |

### C.2 Lectura de los datos

- **Las tablas de los fabricantes (#14, #15) son 2–3 veces optimistas** frente a pruebas reales en botes de 2,4–2,75 m: a ~6 km/h dan 22–28 Wh/km, pero el inflable de 8 ft necesitó 75–82 Wh/km (#2, #4) [CALCULADO]. No conviene calibrar R(v) con ellas.
- **Pendiente:** en las tablas, P ∝ v^k con k = 2,9–3,0 por debajo de ~7 km/h y k = 3,5–5 por encima [CALCULADO con S30, S34]. Equivale a R ∝ v² en desplazamiento y a R ∝ v^2,5–4 cerca de la joroba.
- **Velocidad de casco:** con LWL de 2,0 m, el criterio 1,34·√LWL[ft] kn da **6,36 km/h**. A 6 km/h, Fn = 0,376; a 8 km/h, 0,50; a 12 km/h, **0,75** [CALCULADO]. El crucero de 6 km/h ya está en la velocidad de casco.
- **Techo de 1 kW:** en un casco de 2,4–2,75 m, con 1 o 2 personas, 1–1,1 kW eléctricos dan **7,6–8,0 km/h** (#3, #5, #6, #7). El techo es la joroba de resistencia, no la potencia: con 2 personas, los petrol de 2,3–2,5 hp (~1,8 kW al eje) solo llegan a 8,1–9,3 km/h y **no planean** (#9). Con una persona, dos de ellos sí planean (#10).
- **El largo del casco manda:** un bote de remo de 17 ft y ~400 kg anda a 8,8 km/h con 600 W (#19), mientras que un RIB de 2,75 m necesita 1.000–1.100 W para 7,6–7,8 km/h. Eso es +14 % de velocidad con ~0,57 veces la potencia [CALCULADO: 8,8/7,7 y 600/1.050].

### C.3 Banda propuesta de R(v) para el jon boat de 2,44 m con 2 adultos (Δ ≈ 290 kg)

[ESTIMADO: interpolación de #1–#11 con R ∝ v^2…3; el jon boat tiene LWL más corta (~2,0 m) que el F-RIB (2,75 m LOA) y proa de pram, así que me paro en la mitad alta de las bandas.]

| v km/h | R N (banda) | P eléc. con η_tot 0,45 (comercial) | P eléc. con η_tot 0,34 (diseño actual del proyecto) |
|---|---|---|---|
| 4 | 35–60 | 86–148 W | 114–196 W |
| 5 | 55–85 | 170–262 W | 225–347 W |
| **6** | **95–150** | **352–556 W** | **466–735 W** |
| 7 | 140–210 | 605–907 W | 801–1.201 W |
| 8 | 200–280 | 988–1.383 W | 1.307–1.830 W |
| 9 | 260–400 | 1,4–2,2 kW | 1,9–2,9 kW |
| 12 | 350–600 (zona de planeo; incierto) | 2,6–4,4 kW | 3,4–5,9 kW |

[CALCULADO: P = R·v / η.] **Contraste con `resultados/sizing_tablas.md`:** el proyecto usa R(6 km/h) = 130 N nominal y 169 N de diseño, y P_bat = 578 W nominal y 819 W de diseño. El nominal cae dentro de la banda y el de diseño queda ~13 % por encima del tope (conservador). La V máx de 7–8 km/h que calcula el proyecto coincide con lo medido en #3, #5, #6 y #7.

**Energía para 2 h a 6 km/h, con 20 % de reserva:** 0,88–1,39 kWh con η 0,45, y 1,17–1,84 kWh con η 0,34 [CALCULADO]. Los 2,3 kWh usables que eligió el proyecto cubren el caso de diseño con margen para viento y corriente.

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

No abiertas, solo pistas: buscar: Lund 1040 jon specs transom; buscar: Minn Kota Endura bracket max transom thickness; buscar: ISO 14946 maximum load includes outboard motor; buscar: tinboats 8 ft jon boat trolling motor speed GPS.

---

## Hallazgos que cambian el diseño

- **La placa de carga es el riesgo número 1, no la potencia.** Los aluminio de fondo plano con norma CE o USCG cargan **34–63 kg por m² de LOA × manga**. Para 2,44 × 1,20 m eso da **~100–185 kg** (regla USCG ≈ 160 kg), y la cifra incluye motor y equipo. El proyecto supone 250 kg de placa y una carga útil de 248 kg. Hay que medir el bote real y leer su placa (si tiene). Si la placa es < 250 kg, o bien se limita a 1 adulto + equipo, o bien se reduce la masa de propulsión. **No vale subir la placa por cálculo propio.** Además, un casco < 2,5 m queda fuera del marcado CE (S26) y puede no traer placa.
- **Masa colgada del espejo ≤ 18–28 kg, con 35 kg como tope absoluto.** Ese es el límite que publican los fabricantes de cascos de 2,1–3,1 m (S11, S12, S14, S4, S18). El conjunto motor + soporte con cardán + correa + eje y tubo de 1,3 m + hélice tiene que pesar ≤ ~20 kg [SUPUESTO: meta]. **La batería va al centro o adelante**, nunca en el espejo; con 2 personas sentadas atrás, el francobordo de popa ya es de ~12–18 cm [ESTIMADO: francobordo medio de 0,18 m (A.4) menos el trimado a popa].
- **La meta de 8–12 km/h "por ratos" hay que bajarla a 8–9 km/h.** Con 1,0–1,1 kW, los comerciales llegan a 7,6–8,0 km/h con 2 personas en un bote de 2,75 m. Los petrol de 2,5 hp (~1,8 kW al eje) no pasan de 8,1–9,3 km/h y no planean con dos a bordo (S62). Llegar a 12 km/h exigiría ~2,6–5,9 kW eléctricos y planear [ESTIMADO, banda C.3]. Eso queda fuera de batería, correa y presupuesto razonables para un casco de ≤ 3 hp de placa (S24).
- **Calibración de R(6 km/h) = 95–150 N y P_bat = 350–560 W** (η 0,45; 470–735 W con η 0,34). El mejor análogo de largo es un inflable de 8 ft, que necesitó **500 W a 6,1–6,7 km/h** (S61). El R nominal de 130 N del proyecto queda validado y el de diseño (169 N) queda conservador. **No hay que usar** las tablas de fabricante (ePropulsion 125 W a 5,6 km/h; Torqeedo 153 W a 5,5 km/h): para este casco son 2–3 veces optimistas.
- **Hélice: 10–11" en vez de 7,8", y ≤ 1.200–1.450 rpm a plena potencia.** Los dos fuerabordas eléctricos de referencia usan 280 mm × 147 mm de paso a 1.200 rpm y 1.450 rpm a 1,1 kW (S31, S34). Frente a la de 7,8" (198 mm), una de 10–11" da **+18–26 % de empuje a punto fijo** y **−9 a −15 % de energía en crucero** [CALCULADO B.3]. Elegir el diámetro máximo que permita el calado. A 381 mm de espejo, la placa anticavitación iría ~50–75 mm bajo el fondo (S23), y la basculación protege en la arena.
- **Bollard objetivo: ~290–310 N a ~1 kW, lo mismo que se mide en los comerciales** (0,28–0,29 N/W, S60). Los "65 lb a 600 W" (0,48–0,52 N/W) de Haswing y Rhino exigen FM > 1 y **no son físicamente posibles** [CALCULADO B.2]. No sirven como meta ni como argumento de compra.
- **Rendimiento total:** los comerciales logran 49–55 % máximo (S31, S34). El proyecto calcula hoy 34 % en el caso de diseño. Cada 5 puntos que se ganen (por ejemplo, con hélice más grande o menos pérdida en la correa) ahorran ~13 % de batería a 6 km/h [CALCULADO: 0,34 → 0,39].
- **El techo de costo del DIY es el ePropulsion Spirit 1.0 Evo completo: 18.589 kr** (motor 9.199 kr + batería de 1.276 Wh 9.390 kr; Watski DK, S32), o 2.549 € en Alemania (S33). El piso es un trolling de 55 lb para agua salada: 5.499 kr el Riptide Endura C2 55 (S42) o 3.199 SEK el Watersnake SXW 54 (S44). El DIY se justifica solo si, con batería incluida, cuesta bastante menos que ~2.500 € **y** da ~1 kW, basculación con protección, marcha atrás y pasador de corte.
- **Montaje:** el espejo puede ser de chapa desnuda de 1,2 mm (Stacer, S4). En ese caso el soporte de popa necesita un taco o contraplaca (madera dura o HDPE de ≥ 25 mm) que reparta la carga, y una abrazadera para **20–65 mm** (la de ePropulsion va de 28 a 63 mm, S31). Agregar el **cable de seguridad** del soporte al bote que pide el manual de ePropulsion (S31).
