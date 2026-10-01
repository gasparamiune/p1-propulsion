# R05: materiales FDM en agua salobre y sellado

Consulta: 2026-10-01. Autor: subagente de investigación P1.

**Alcance.**
- **Parte A (materiales):** PETG, ASA, PC y PC-blend, PA-CF y PETG-CF, y recubrimiento epoxi, impresos en una Ender-3 S1 (≤260 °C, sin cerramiento) para servicio en agua salobre (Als Fjord). Factores de reducción de diseño, insertos roscados y compatibilidad química.
- **Parte B (sellado):** O-rings según Parker ORD 5700, ISO 3601-2 y Trelleborg; rugosidad FDM; sellos de eje; motor inundado, sellado o seco; prensaestopas y conectores IP68.

Complementa a R01 (videos), R02 (fueraborda y long-tail) y R03 (jet, rim y eFoil). Donde esos archivos ya verificaron algo, remito a ellos.

---

## 0. Método, etiquetas y fuentes

**Etiquetas.**
- `[VERIFICADO: Sx]`: el dato está en la fuente Sx de la tabla de abajo. La abrí en esta sesión (PDF bajado con `curl` y leído con `pdftotext`, o página leída con WebFetch).
- `[CALCULADO: …]`: cuenta mía con datos verificados o de `inputs.yaml` y `resultados/sizing_tablas.md`.
- `[ESTIMADO: base]` y `[SUPUESTO]`: lo que dicen. `[ESTIMADO: memoria técnica, no verificado]` = lo recuerdo, pero no lo encontré en una fuente abierta.

**Límites de lo leído.**
- ScienceDirect, MDPI (sitio), Springer y BSSA respondieron 403 o un desafío anti-bot.
- De tres papers leí **solo el resumen**: S12 (vía OUCI), S13 y S14 (vía la API de DOAJ).
- Los TDS de fabricantes son valores "típicos", medidos sobre probetas chicas con 100 % de relleno y casi siempre **ventilador apagado**. No son valores de diseño; lo dicen los propios TDS [VERIFICADO: S2, S5].
- **No vi ningún video.** El ensayo de adhesivos de Cosel y el de Half-Baked-Research los cito solo por el resumen de Hackaday (S23, S35).

| Id | Fuente (abierta en esta sesión) | URL |
|---|---|---|
| S1 | Prusament PETG, TDS v1.1 (2022) | https://www.prusa3d.com/file/2765253/prusament-petg-technical-data-sheet.pdf |
| S2 | Polymaker PolyLite PETG, TDS V6.0 (2026) | https://polymaker.com/wp-content/uploads/TDS_Polymaker_PolyLite-PETG_V6.0_2026-06-09_EN.pdf |
| S3 | Bambu Lab PETG Basic, TDS V3.0 | https://store.bblcdn.com/s1/default/cb94589bf7994fdcbfa833badefae9cd/Bambu_PETG_Basic_Technical_Data_Sheet.pdf |
| S4 | Polymaker Fiberon PETG-rCF08, TDS V1.0 | https://fiberon.polymaker.com/wp-content/uploads/TDS_FIBERON-PETG-rCF08_V1.0_EN.pdf |
| S5 | Polymaker ASA, TDS (wiki) | https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/abs-asa/polymaker-tm-asa.md |
| S6 | Polymaker PolyLite PC, TDS (wiki) | https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/polycarbonate/polylite-tm-pc.md |
| S7 | Polymaker PC-PBT, TDS (wiki) | https://wiki.polymaker.com/polymaker-products/more-about-our-products/documents/technical-data-sheets/polycarbonate/polymaker-pc-pbt.md |
| S8 | Polymaker Fiberon PA6-CF20, TDS V1.1 | https://cdn.shopify.com/s/files/1/0548/7299/7945/files/TDS_FIBERON_PA6-CF20_V1.1_EN.pdf?v=1733846088 |
| S9 | Polymaker Fiberon PA12-CF10, TDS V1.1 | https://cdn.shopify.com/s/files/1/0548/7299/7945/files/TDS_FIBERON_PA12-CF10_V1.1_EN.pdf?v=1740427088 |
| S10 | Polymaker wiki, PA6-CF20 (requisitos de impresión) | https://wiki.polymaker.com/polymaker-products/polymaker-filaments/fiberon-tm/fiberon-tm-pa6-cf20.md |
| S11 | Moreno Nieto et al., *Polymers* 2021, PLA/PETG en agua dulce, salada y azucarada | https://pmc.ncbi.nlm.nih.gov/articles/PMC8036839/ |
| S12 | Gama et al., *J. Polym. Res.* 2026, PETG FFF con UV y agua (solo resumen) | https://ouci.dntb.gov.ua/en/works/420Ggj6V/ |
| S13 | "Experimental investigation of degradation in the marine environment of FDM-based 3D printed specimens", *IJLMM* 2026, doi 10.1016/j.ijlmm.2025.08.002 (solo resumen, DOAJ) | https://doaj.org/api/search/articles/title%3A%22degradation%20in%20the%20marine%20environment%20of%20FDM%22?pageSize=8 |
| S14 | Chaudhary, Li y Matos, *Results in Materials* 2023, doi 10.1016/j.rinma.2023.100381 (solo resumen, DOAJ) | https://doaj.org/api/search/articles/title%3A%22thermoplastics%20in%20seawater%22 |
| S15 | Stankevics et al., *Polymers* 2025, fluencia viscoelástica de PETG impreso | https://pmc.ncbi.nlm.nih.gov/articles/PMC12349189 |
| S16 | Martins et al., *Polymers* 2024, PLA y PETG: tracción y curvas S-N | https://pmc.ncbi.nlm.nih.gov/articles/PMC11243948/ |
| S17 | Rodrigues et al., *Polymers* 2026, fatiga de ASA, PA12, PC y PC-ABS impresos | https://pmc.ncbi.nlm.nih.gov/articles/PMC12845617/ |
| S18 | Albaşkara y Gerçekcioğlu, *Micromachines* 2026, rugosidad de PLA, PETG y ABS impresos | https://pmc.ncbi.nlm.nih.gov/articles/PMC13028808/ |
| S19 | Abas et al., *Polymers* 2023, rugosidad por cara en nylon-CF impreso | https://pmc.ncbi.nlm.nih.gov/articles/PMC10489770/ |
| S20 | Smooth-On XTC-3D, boletín técnico | https://www.smooth-on.com/tb/files/XTC3D_TB.pdf |
| S21 | West System 105/205-206-207, TDS | https://www.westsystem.com/app/uploads/2022/09/105_205-207-Combined.pdf |
| S22 | Prusa, "Watertight 3D printing part 2" | https://blog.prusa3d.com/watertight-3d-printing-part-2_53638/ |
| S23 | Hackaday 2026-05-30, ensayos de impermeabilización (resumen de Half-Baked-Research) | https://hackaday.com/2026/05/30/testing-various-ways-to-waterproof-fdm-printed-parts/ |
| S24 | Parker O-Ring Handbook ORD 5700 (copia en sealingdevices.com) | https://sealingdevices.com/wp-content/uploads/ORD-5700-Parker_O-Ring_Handbook.pdf |
| S25 | ISO 3601-2:2016, muestra pública (iTeh) | https://cdn.standards.iteh.ai/samples/69880/b3ae61dbff9a4402a74175cde66389fc/ISO-3601-2-2016.pdf |
| S26 | Trelleborg, catálogo "O-Rings and Back-up Rings" (junio 2024) | https://www.trelleborg.com/-/media/tss-media-repository/tss_website/pdf-and-other-literature/catalogs/o_ring_gb_en.pdf |
| S27 | CNC Kitchen, helicoils, insertos y tuercas embebidas en PETG | https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment |
| S28 | CNC Kitchen, consejos para insertos térmicos | https://www.cnckitchen.com/blog/tipps-amp-tricks-fr-gewindeeinstze-im-3d-druck-3awey |
| S29 | PennEngineering, catálogo SI (insertos para plásticos) | https://www.pemnet.com/wp-content/uploads/sites/9/2022/06/sidata.pdf |
| S30 | Brassland, guía de corrosión del latón | https://brassland.com/resources/corrosion/ |
| S31 | Henkel, LOCTITE 243, TDS (abril 2025) | https://datasheets.tdx.henkel.com/LOCTITE-243-en_GL.pdf |
| S32 | Henkel, LOCTITE 425, TDS | https://datasheets.tdx.henkel.com/LOCTITE-425-en_GL.pdf |
| S33 | Henkel, *Loctite Design Guide for Bonding Plastics*, vol. 6 | https://www.ellsworth.com/globalassets/literature-library/manufacturer/henkel-loctite/henkel-loctite-design-guide-plastic-bonding.pdf |
| S34 | Eastman, guía de fabricación de Spectar (PETG en placa), TRS-236A | https://www.professionalplastics.com/professionalplastics/Spectar-Fabricating.pdf |
| S35 | Hackaday 2025-01-30, adhesivos para PETG (resumen del ensayo de Cosel) | https://hackaday.com/2025/01/30/comparing-adhesives-for-gluing-petg-prints/ |
| S36 | Sika, Sikaflex-291i, PDS (DK, 04-2023) | https://industry.sika.com/content/dam/dms/dk01/j/sikaflex_-291i.pdf |
| S37 | SKF, retenes HMS5 y HMSA10 | https://www.skf.com/skf/campaign/newindustrialoffers/upload/products/Radial%20Shaft%20Seals%20for%20catalogue%20gearboxes/Maximizing%20bearing%20performance.pdf |
| S38 | Boletín de Trey Bull, mantenimiento de prensaestopas | https://sites.google.com/site/treybullemlnewsletter/taking-care-of-your-boat/servicing-your-stuffing-box |
| S39 | Blue Robotics, propulsor T200 (motor inundado) | https://bluerobotics.com/store/thrusters/t100-t200-thrusters/t200-thruster-r2-rp/ |
| S40 | LAPP SKINTOP ST-M, hoja de datos (2023) | https://storage.tameson.com/asset/Products/Tameson/Electrical/Connectors,%20Cables/Wire%20And%20Cable%20Management/Cable%20And%20Mesh%20Grip/Cable%20Gland/Lapp/S-7DJU%20-%20EC000441/Image/e3tej_chr_en_2.pdf |
| S41 | Bulgin, serie 900 Buccaneer | https://www.bulgin.com/products/pub/media/import/attachments/900%20Series.pdf |
| S42 | ASSDA, inoxidable en ambiente marino | https://www.assda.asn.au/component/content/article?id=170...in-marine |
| S43 | Polymers 2026, PETG y PETG+CF expuestos a aceite mineral (PMC12986719) | https://pmc.ncbi.nlm.nih.gov/articles/PMC12986719/ |

---

## 1. Resumen ejecutivo

1. **PETG sigue siendo el material correcto para P1.** Absorbe poca agua: ~0,3 % a saturación [VERIFICADO: S11] y <1 % aun a 70 °C [VERIFICADO: S12]. Se imprime bien en la Ender-3 S1 y no requiere cerramiento.
   - **Sí pierde resistencia en agua de mar: −17 a −28 % a 30 días** [VERIFICADO: S13]. El `f_water = 0,85` de `inputs.yaml` es optimista: propongo **0,75**.
2. **Entre capas (Z) el PETG es débil y muy variable.** Según la fuente, Z vale **38 %** [VERIFICADO: S1, "interlayer adhesion" 18 ± 4 MPa contra 47 MPa en XY], 69 % [VERIFICADO: S3] u 84 % [VERIFICADO: S2] de XY. Propongo `f_z = 0,40` (hoy 0,55).
3. **Fatiga: es el hallazgo más fuerte.**
   - PETG impreso a R = 0,2 rompe en 0,8–1,9·10⁵ ciclos al **30 % de su UTS** [VERIFICADO: S16]. Extrapolado (Basquin), queda en ~8 % de la UTS a 10⁷ ciclos y ~4 % a 10⁸ [CALCULADO].
   - En P1, la frecuencia de paso de pala es de ~50 Hz: **~5·10⁷ ciclos en 300 h** [CALCULADO].
   - El `f_fatigue = 0,30` de `inputs.yaml` es **~5× no conservador**. Propongo **0,06**: las piezas impresas no deben quedar en la ruta de carga alterna.
   - *Corrección (verificación adversarial):* con las rpm actuales de `resultados/sizing_tablas.md` (1491 rpm de hélice en crucero, no 991), el paso de pala es **~75 Hz** y suma **~8·10⁷ ciclos en 300 h** [CALCULADO]. A 8·10⁷ el ajuste da **4,2 %** de la UTS, así que 0,06 queda ~1,4× por encima de la propia extrapolación; ver §A6.
4. **Temperatura.** El PETG tiene HDT de **68 °C** (Prusament y Bambu) [VERIFICADO: S1, S3] o **75 °C** (PolyLite, a 1,8 MPa) [VERIFICADO: S2]. La epoxi de laminado común (West 105/205) tiene **HDT de 48 °C** [VERIFICADO: S21].
   - Límite para PETG cargado: **50 °C**. Nada impreso debe tocar el motor ni el disipador del ESC.
5. **Con la impresora de P1 solo se pueden imprimir PETG y PETG-CF.**
   - PA6-CF y PA12-CF piden boquilla de 280–300 °C [VERIFICADO: S8, S9, S10].
   - PC pide cámara de 70–100 °C [VERIFICADO: S6] y ASA pide cerramiento [VERIFICADO: S5].
   - El PETG-CF no gana temperatura (HDT 65,7 °C) y es frágil en Z (1,9 % de elongación) [VERIFICADO: S4].
6. **Uniones roscadas.**
   - Los insertos de latón se descincifican en agua salada (Zn > ~15 %) [VERIFICADO: S30].
   - Una **tuerca A4 cautiva en bolsillo de fondo** resistió **166 kg**, más que el inserto térmico (**119 kg**) [VERIFICADO: S27]. Es más barata y de inoxidable.
   - Loctite 243 **no se recomienda sobre termoplásticos** (stress cracking) [VERIFICADO: S31].
7. **Sellado.**
   - Una superficie impresa tiene Ra/Sa de ~2–24 µm [VERIFICADO: S18, S19]. Un sello estático pide Ra ≤ 0,8 µm (Parker) o ≤ 1,6 µm (Trelleborg) [VERIFICADO: S24, S26].
   - Conclusión: **sello axial (de cara) con O-ring de 3,53 mm** en cara refrentada en el torno, o junta blanda. Evitar sellos radiales impresos: piden excentricidad ≤ 0,05 mm [VERIFICADO: S24].
8. **La cola larga de P1 no necesita ningún sello dinámico sumergido.** Bujes lubricados por agua + motor seco arriba. Solo quedan sellos estáticos de salpicadura (caja del ESC) y excluidores de arena. Es una ventaja fuerte frente al pod sumergido.

---

# PARTE A — MATERIALES

## A1. Propiedades de los candidatos (TDS de fabricante)

Probetas de los TDS: 100 % de relleno, 2 perímetros (Bambu no declara perímetros). En los de Polymaker PETG, ASA, PC, PA6-CF y PA12-CF, además, ventilador apagado [VERIFICADO: S2, S5, S6, S8, S9]. *Corregido:* en PETG-rCF08 las probetas se hicieron con ventilador al 0–50 % [VERIFICADO: S4], no apagado. ASA y PC se imprimieron con **cámara a 90 °C** [VERIFICADO: S5, S6]: esos valores **no son alcanzables** en una Ender-3 S1 abierta.

| Material (fuente) | Tg [°C] | HDT 0,45 / 1,8 MPa [°C] | Agua (condición) | σt XY [MPa] | σt Z [MPa] | Z/XY | E XY [MPa] | Boquilla [°C] | Cámara | ¿Ender-3 S1? |
|---|---|---|---|---|---|---|---|---|---|---|
| Prusament PETG (S1) | — | 68 / 68 | 0,07 % 24 h; 0,10 % 7 d (24 °C, 22 % HR) | 47 ± 2 (horizontal) | **18 ± 4** ("interlayer adhesion") | **0,38** | 1500 | 250 ± 10 | no | **Sí** |
| PolyLite PETG (S2) | 81 | 78 / 75 | 0,54 % equil. (70 % HR, 23 °C) | 50,8 ± 0,9 | 42,8 ± 2,8 | 0,84 | 2117 | 230–260 | no | **Sí** |
| Bambu PETG Basic (S3) | 69 | 71 / 68 | 0,45 % sat. (25 °C, 55 % HR) | 51 ± 1 | 35 ± 6 | 0,69 | 2780 | 230–260 | recomienda 35–50 °C (impresoras Bambu cerradas) | **Sí** |
| Fiberon PETG-rCF08 (S4) | 69,7 | 68,6 / 65,7 | 0,55 % equil. (70 % HR) | 59,8 ± 0,3 | 41,1 ± 4,1 | 0,69 | 3710 | 240–270 | no | Sí, con **boquilla endurecida** |
| Polymaker ASA (S5) | 98 | 103 / 100 | (curva; sin número en texto) | 43,8 ± 0,8 | 32 ± 1,8 | 0,73 | 2379 | 230–260 | **sí** ("Needed") | Solo con cerramiento |
| PolyLite PC (S6) | 113 | 111 / 107 | (curva) | 69,1 ± 3,0 | 52,8 ± 1,7 | 0,76 | 2497 | 250–270 | **sí, 70–100 °C** | **No** |
| Polymaker PC-PBT (S7) | 140 | 107 / 91 | (curva) | 50,4 ± 0,6 | 37,9 ± 0,3 | 0,75 | 1940 | 260–280 | **sí, 100–110 °C** | **No** |
| Fiberon PA6-CF20 seco (S8) | 74,2 | 215 / 173 | 3,3 % equil. | 109,3 ± 2,4 | 54,0 ± 5,2 | 0,49 | 8637 | **280–300** | no | **No** (hotend) |
| PA6-CF20 **húmedo** (5,3 % agua) (S8) | — | — | — | **54,7** (−50 %) | **25,5** (−53 %) | 0,47 | **2508** (−71 %) | | | |
| Fiberon PA12-CF10 seco (S9) | 55 | 131 / 105 | 1,5 % equil. | 77,4 ± 1,1 | 52,2 ± 0,8 | 0,67 | 3311 | **280–300** | no | **No** (hotend) |
| PA12-CF10 **húmedo** (2,92 % agua) (S9) | — | — | — | **71,7** (−7 %) | **42,1** (−19 %) | 0,59 | 3132 | | | |
| Epoxi West 105/205 (S21) | 54 onset / 61 último | — / **48** (118 °F) | — | 54,5 (7900 psi) | — | — | 2810 (4,08·10⁵ psi) | — | — | recubrimiento |

Notas:
- Para PA6-CF20 y PA12-CF10 los TDS piden además **recocido de 100 °C × 16 h** y boquilla endurecida. Una boquilla de latón dura **~9 h** [VERIFICADO: S8, S9; S10 solo dice "hardened nozzle"].
- "Húmedo" = sumergido 48 h a 60 °C [VERIFICADO: S8, S9]. Los porcentajes son [CALCULADO] contra el valor seco.
- Que la Ender-3 S1 llegue a ≤260 °C es dato del usuario (`inputs.yaml`). Que su boquilla de serie sea de latón es [SUPUESTO: verificar].
- La HDT de PETG varía según la marca: entre 65,7 y 75 °C a 1,8 MPa [VERIFICADO: S1–S4]. **Comprar PETG con HDT(1,8 MPa) ≥ 70 °C** declarada; PolyLite cumple (75 °C) [VERIFICADO: S2].

## A2. PETG en agua de mar o salobre: estudios

| Estudio | Exposición | Absorción | Efecto mecánico | Etiqueta |
|---|---|---|---|---|
| Moreno Nieto 2021 (S11) | Agua destilada, salmuera 28 % p/p, azúcar; 20 °C; semanal | **~0,3 %**; se estabiliza a las **7–9 semanas** (salada: semana 7) | Sin ensayos mecánicos | [VERIFICADO: S11] |
| Gama 2026 (S12, resumen) | Destilada y salina, **70 °C, 10 semanas**; UV hasta **1000 h** | **<1 %** | Baja el módulo de almacenamiento y "levemente" la Tg (plastificación **reversible**). La tracción sube un poco. Con UV, cambios moleculares menores. | [VERIFICADO: S12] |
| IJLMM 2026 (S13, resumen) | Agua de mar artificial y natural, 30 días | — | Tracción **PETG −17 a −28 %**; Nylon −31 a −44 %; ABS −15 a −25 %; PLA −26 a −35 % | [VERIFICADO: S13] |
| Chaudhary 2023 (S14, resumen) | Agua de mar a temperatura elevada (acelerado); Nylon, ABS, PLA, PCTG, PETG, ASA | Las estructuras impresas tienen **difusividad "extremadamente alta" frente al material macizo** | Las propiedades bajan en todos; la rigidez cae en proporción a la masa absorbida | [VERIFICADO: S14] |

Lectura para P1:
- Una pieza impresa se satura en semanas, no en años (porosidad) [VERIFICADO: S11, S14]. Hay que **diseñar con propiedades saturadas desde el día 1**.
- S12 y S13 discrepan en la pérdida de resistencia. Para diseño tomo la peor: **−28 % → f_water = 0,72 ≈ 0,75** [CALCULADO].
  - *Corrección (verificación):* redondear 0,72 a 0,75 **no** es tomar la peor; es ~4 % no conservador. El peor caso estricto de S13 es **0,72**. Si se mantiene 0,75, que sea una decisión explícita.
- Hay que validarlo con probetas propias (§A9.4).

**UV.** PETG mantuvo la estructura con hasta 1000 h de UV de laboratorio [VERIFICADO: S12]. ASA se vende por su "improved weather resistance… UV resistance" [VERIFICADO: S5]. La equivalencia entre esas 1000 h y temporadas reales en Dinamarca no está establecida [SUPUESTO]. Para piezas al sol: **colores claros**, inspección anual.

## A3. Anisotropía (Z frente a XY)

| Fuente | Z/XY | Condición |
|---|---|---|
| Prusament (S1) | **0,38** (18/47) | Ensayo propio de adhesión entre capas. Es el más pesimista. |
| Bambu PETG Basic (S3) | 0,69 (35/51); flexión 0,75; impacto 0,31 (10,5/34,2) | Probeta Z con 100 % de relleno |
| Polymaker PETG (S2) | 0,84 (42,8/50,8); elongación Z 3,3 % contra 8,4 % | Ventilador apagado, 2 perímetros |
| Stankevics 2025 (S15) | **0,45** **en el plano**, entre cordones (22,48/50,44 MPa, dispersión ±4,61) | Relleno unidireccional, 0,1 mm, 235 °C |
| Polymaker PETG-rCF08 (S4) | 0,69; elongación Z **1,9 %** | La fibra empeora la ductilidad en Z |

- **Propuesta: `f_z = 0,40`** [ESTIMADO: entre el mínimo de S1 (0,38) y el de S15 (0,45)]. La Ender-3 S1 imprime abierta y con ventilador, y las piezas de P1 son grandes (capas que se enfrían más que en una probeta).
- La anisotropía también existe **dentro de la capa** entre cordones [VERIFICADO: S15]. Por eso, en piezas cargadas: ≥ 6–8 perímetros siguiendo el contorno de carga y relleno ≥ 60 % [ESTIMADO].

## A4. Temperatura de servicio

- HDT a 1,8 MPa: Prusament 68 °C, Bambu 68 °C, PolyLite 75 °C, PETG-rCF08 65,7 °C [VERIFICADO: S1–S4]. El agua baja algo la Tg [VERIFICADO: S12].
- **Propuesta para `t_service_max_c`:** 50 °C en piezas de PETG **con carga**; 60 °C en tapas sin carga [ESTIMADO: HDT mínima 65,7–68 °C menos ~15–18 K de margen por creep y humedad]. Hoy está en 60 °C; bajar a 50 °C.
- **Cerca del motor y del ESC.**
  - El estator y la campana de un outrunner pueden pasar de 60–80 °C con carga sostenida [ESTIMADO: memoria técnica, no verificado].
  - Soporte de motor de **aluminio**, separadores y arandelas aislantes.
  - Que **ninguna pieza de PETG toque la campana, la brida del motor ni el disipador del ESC**.
  - Medir con el termopar del multímetro en la primera prueba de 2 h.
- **Al sol.** Una superficie oscura puede pasar de 60 °C al sol de verano [ESTIMADO: memoria técnica, no verificado]. Usar PETG blanco, gris claro o natural en la abrazadera de espejo y los soportes.
- **Epoxi como recubrimiento:** la West 105/205 tiene HDT de 48 °C y Tg última de 61 °C [VERIFICADO: S21]. Sirve para sellar o alisar piezas frías; **no** para piezas calientes.
- **f_temp** (resistencia relativa a 23 °C) [ESTIMADO: memoria técnica de copoliésteres amorfos, no verificado]:
  - 0,85 hasta 40 °C (el valor de `inputs.yaml` es razonable);
  - 0,70 hasta 50 °C;
  - no usar con carga por encima de 50 °C.

## A5. Fluencia (creep)

Datos de S15 (PETG, 21 °C, 39 % HR) [VERIFICADO: S15]:
- Al **50 % de la resistencia** (25 MPa en X), el creep a 5 h es "roughly 5% of the sample elastic strain", y "In 20 h, this strain had doubled" (~10 %).
- Al **70 %** (35 MPa), llega al **25 % a 5 h en X** (7 % en Y) y sube a **30 % (X) y 8 % (Y)**: comportamiento no lineal. *Corregido:* la versión anterior atribuía la duplicación a 20 h al caso del 70 %; en S15 corresponde al caso del 50 %.
- Hay deformación plástica por encima de ~0,1 % de creep en X y ~0,05 % en Y.

Extrapolar a cargas de meses, mojado y a 30–40 °C:
- **`f_creep = 0,35`** para carga sostenida >100 h [ESTIMADO: el umbral no lineal de S15 es ~50 % a 21 °C y en seco; le resto margen por agua (S12) y temperatura]. Hoy está en 0,50.
- **Precarga de tornillos sobre PETG.** El plástico fluye y la precarga se pierde. En las uniones de la abrazadera de espejo y del cardán, usar **casquillos limitadores de compresión metálicos**: tubo de inox o aluminio atravesando el plástico, con el tornillo apretando metal contra metal [ESTIMADO: práctica estándar en plásticos].
  - Eastman recomienda arandelas para repartir la carga y no apretar de más [VERIFICADO: S34].

## A6. Fatiga a 10⁷–10⁸ ciclos

**Ciclos en P1** [CALCULADO]:
- Hélice a 991 rpm en crucero × 3 palas = **49,6 Hz**.
- Son **3,6·10⁵ ciclos por salida de 2 h** y **5,4·10⁷ en 300 h** de vida.
- Motor a ~2970 rpm (49,6 Hz de desbalanceo, relación 3:1). Engrane de correa: ~790 Hz.
- Fuente: rpm de `resultados/sizing_tablas.md`.
- *Corrección (verificación, contra `sizing_tablas.md` del 2026-10-01 14:07):* hoy la tabla da **1491 rpm** de hélice en crucero y correa **20T:40T = 2,00**. Recalculado [CALCULADO]:
  - paso de pala **74,6 Hz** (3 palas, `inputs.yaml` Z = 3 [ESTIMADO]);
  - **5,4·10⁵ ciclos por salida de 2 h** y **8,1·10⁷ en 300 h**;
  - motor a ~2980 rpm (49,7 Hz de desbalanceo); engrane de correa con polea de 20 dientes: **~990 Hz**.

**Datos:**

| Fuente | Material y condición | Resultado |
|---|---|---|
| Martins 2024 (S16) | PETG FFF a 45°, R = 0,2, 7 Hz, boquilla **215–220 °C** (baja), UTS 32,9 MPa | σmax 60 % → 1,2–1,5·10⁴ ciclos; 45 % → 1,7–4,1·10⁴; **30 % (10,2 MPa) → 0,8–1,9·10⁵** [VERIFICADO: S16] |
| Rodrigues 2026 (S17) | FFF en Stratasys, R = 0,05, 10 Hz, límite = **runout a 10⁶** | ASA **25 %·σR (8 MPa)**; PA12 17 % (7,4 MPa); PC-ABS 15 % (4,7 MPa); **PC 7 % (3,6 MPa)** [VERIFICADO: S17] |

**Ajuste de Basquin a S16** [CALCULADO: medias geométricas de los tres niveles]:
- σmax = 367·N^−0,306 MPa. (*Corregido:* decía 362. El ajuste por mínimos cuadrados log-log sobre las medias geométricas 13 290 / 29 123 / 124 158 ciclos de la Tabla 2 de S16 da A = 367; la tabla de abajo ya usaba ese valor.)
- Nota: en S16 los niveles 20,4 / 15,3 / 10,2 MPa son el 60 / 45 / 30 % de ~34 MPa, no de la UTS de 32,9 MPa (que es de probetas a 0°; las de fatiga son a ±45°) [VERIFICADO: S16, Tablas 1 y 2]. Los "% de la UTS" de abajo pueden estar ~3 % altos.

| N | σmax PETG (S16, UTS 32,9) | % de la UTS | Escalado a UTS 45 MPa | σa (R = 0,2) |
|---|---|---|---|---|
| 10⁶ | 5,3 MPa | 16 % | 7,2 MPa | 2,9 MPa |
| 10⁷ | 2,6 MPa | 8 % | 3,6 MPa | 1,4 MPa |
| 10⁸ | 1,3 MPa | 4 % | 1,8 MPa | 0,7 MPa |

- El 16 % de la UTS a 10⁶ coincide con el rango de 7–25 % que S17 mide en otros termoplásticos impresos. Es un **cruce de verificación razonable** [CALCULADO].
- Extrapolar 2,7 décadas más allá del último dato es incierto. Un codo de fatiga podría dar algo mejor, pero no hay datos de PETG impreso a 10⁷–10⁸ [SUPUESTO].
- **Propuesta: `f_fatigue = 0,06`** (σmax/UTS para 10⁸ ciclos, R entre 0 y 0,2) [ESTIMADO: entre el 4 % (10⁸) y el 8 % (10⁷) del ajuste]. Hoy está en 0,30.
  - *Corrección (verificación):* con 8,1·10⁷ ciclos (rpm actuales), el ajuste da σmax = 1,39 MPa = **4,2 %** de la UTS [CALCULADO]. Para ser coherente con la vida real, `f_fatigue` debería estar en **~0,045**; 0,06 es ~1,4× más alto que la propia extrapolación.
- **Regla de diseño:** con agua y temperatura, **σa ≤ 0,5 MPa en XY y ≤ 0,2 MPa a través de capas** [CALCULADO: 45 × 0,06 × 0,75 × 0,85 = 1,7 MPa de σmax → σa ≈ 0,77 MPa → /1,5 = 0,52 MPa; × f_z 0,40 = 0,21 MPa].
  - Aclaración: σa = 0,45·σmax supone **R = 0,1** (punto medio de 0–0,2). Con R = 0,2, σa = 0,4·σmax = 0,69 MPa → 0,46 MPa (XY) y 0,18 MPa (Z) [CALCULADO]. Con `f_fatigue` = 0,045, quedan ~0,35 MPa (XY) y ~0,14 MPa (Z) [CALCULADO].

**Consecuencia práctica.** Ninguna pieza impresa puede ser la ruta de carga alterna:
- de la hélice al espejo (tubo, cardán, pivote);
- de la correa (tensión fluctuante en el soporte del motor);
- del desbalanceo del motor.

Esas rutas van en **aluminio o inox**. Lo impreso queda para carenados, tapas, cajas y el protector de hélice. Y aun así el protector recibe pulsos de presión a ~75 Hz (antes decía ~50 Hz; ver corrección de rpm arriba) cerca de las puntas. R02 y R03 documentan una hélice de PETG, ~4 meses en agua de mar, a la que se le **fisuró una pala al desmontarla** para inspección. Por eso el protector se trata como **consumible inspeccionable**: paredes ≥ 4 mm, fijación con flejes metálicos e inspección mensual de fisuras [ESTIMADO].

## A7. Factores de reducción propuestos (actualizar `inputs.yaml`)

| Factor | `inputs.yaml` hoy | **Propuesto** | Base |
|---|---|---|---|
| f_water | 0,85 | **0,75** (peor caso estricto: 0,72) | −17 a −28 % a 30 días en agua de mar [VERIFICADO: S13]; saturación en semanas [VERIFICADO: S11, S14] |
| f_temp (≤40 °C) | 0,85 | 0,85 (≤40 °C); **0,70 (≤50 °C)** | [ESTIMADO: memoria técnica, no verificado]; HDT 65,7–75 °C [VERIFICADO: S1–S4] |
| f_process | 0,80 | 0,80 | [ESTIMADO]; validar con probetas propias (§A9.4) |
| f_creep (>100 h) | 0,50 | **0,35** | Creep no lineal desde ~50 % de la resistencia a 21 °C [VERIFICADO: S15] + agua y temperatura [ESTIMADO] |
| f_fatigue (10⁷–10⁸) | 0,30 | **0,06** (~0,045 con 8·10⁷ ciclos; ver §A6) | Basquin sobre S16 [CALCULADO]; contraste con S17 [VERIFICADO] |
| f_z | 0,55 | **0,40** | Z/XY = 0,38 (S1), 0,45 en el plano (S15), 0,69 (S3), 0,84 (S2) |
| t_service_max_c | 60 | **50** (con carga) | §A4 |
| sigma_t_xy_mpa | 45 | 45, **solo si la probeta propia da ≥ 40** | TDS 47–51 [VERIFICADO: S1–S3]; impreso frío da 32,9 [VERIFICADO: S16] |
| sigma_t_z_mpa | 25 | **18** | 18 ± 4 [VERIFICADO: S1] |

**Tensiones admisibles resultantes, PETG** [CALCULADO: 45 MPa × f_water 0,75 × f_temp 0,85 × f_process 0,80 = 23,0 MPa característica, en XY]:

| Caso | XY sin FS | XY con FS 3 | Z sin FS | Z con FS 3 |
|---|---|---|---|---|
| Pico de corto plazo (golpe de kick-up, maniobra) | 23,0 | **7,7** | 9,2 | **3,1** |
| Sostenida >100 h (precarga, peso) | 8,0 | **2,7** | 3,2 | **1,1** |
| Alterna a 10⁸ ciclos (σa) | 0,77 | **0,5** (FS 1,5) | 0,31 | **0,2** (FS 1,5) |

En fatiga el FS 1,5 ya va sobre un límite inferior extrapolado. Aplicarle FS 3 es redundante [SUPUESTO: lo decide quien diseña]. Con los factores actuales, la sostenida con FS 3 en XY daba 4,3 MPa: los nuevos son **~40 % más bajos** [CALCULADO].

## A8. ¿Qué material para qué pieza de P1?

| Pieza | Material | Por qué |
|---|---|---|
| Protector de hélice y patín | **PETG** claro, paredes ≥ 4 mm, 100 % de relleno en fijaciones; ASA si se hace un cerramiento | Consumible. Fatiga a ~75 Hz (§A6, rpm corregidas). Fisuras documentadas en R02 y R03. |
| Caja del ESC | PETG + **tapa o placa base de aluminio** (disipador) + sello axial (§B3) | El ESC calienta; el PETG no debe tocar el disipador (§A4) |
| Tapa de correa y cubierta del motor | PETG o ASA, **sin sellar, con drenaje** | Salpicadura; un sello atrapa agua (R02 §lecciones: "drenaje y no solo sellos") |
| Soporte de motor, cardán, abrazadera de espejo, pivote de kick-up | **Aluminio e inox**. Lo impreso solo como carenado o separador **a compresión** con limitadores metálicos | Fatiga (§A6) y creep (§A5) |
| Bujes del tubo (en agua) | **POM-C torneado** (decisión ya tomada en `inputs.yaml`), no impreso | Desgaste con arena; tolerancia de buje [ESTIMADO] |
| Mango del timón | PETG, 8 perímetros [SUPUESTO] | Cargas humanas estáticas; verificar con FS 3 |
| Piezas rígidas no calientes (placas, nervios) | PETG-CF (solo con boquilla endurecida) | +75 % de módulo XY (3710 contra 2117 MPa) [VERIFICADO: S2, S4], sin ganancia térmica y frágil en Z |
| Nylon-CF | **Descartado** con esta impresora | Pide 280–300 °C [VERIFICADO: S8, S9]. El PA6-CF pierde 50–71 % mojado [VERIFICADO: S8]. El PA12-CF10 sería el mejor en agua (−7 % XY mojado [VERIFICADO: S9]) **solo si se tercerizara**. |
| PC / PC-PBT | **Descartados** | Cámara de 70–110 °C [VERIFICADO: S6, S7]; PC con fatiga de solo 7 % de σR [VERIFICADO: S17]; Sikaflex prohíbe PC (stress cracking) [VERIFICADO: S36] |

## A9. Recubrimiento epoxi

### A9.1 Datos

| Producto | Datos verificados | Uso en P1 |
|---|---|---|
| Smooth-On XTC-3D (S20) | Mezcla 2A:1B en volumen; 350 cps; vida útil 10 min; curado 3,5 h en capa fina; **Shore 80D**; "works with PLA, ABS, **PetG**"; "does not melt plastic"; 28,3 g cubren 651 cm² a 0,4 mm [VERIFICADO: S20] | Alisar caras de sello antes de lijar; capa < 0,4 mm |
| West System 105/205 (S21) | 54,5 MPa; elongación 3,4 %; **HDT 48 °C**; Tg onset 54 °C, última 61 °C; "superior moisture barrier" (afirmación del fabricante) [VERIFICADO: S21] | Impregnación y barrera en piezas frías; **no** cerca del motor o del ESC |
| 3M Scotch-Weld DP-100 | Eastman lo recomienda para pegar Spectar (PETG) consigo mismo [VERIFICADO: S34] | Pegado estructural PETG-PETG |

### A9.2 Adhesión y estanqueidad

- **Prusa:**
  - el PETG sin tratar "leaked really quickly through the seams and contact points between perimeters and solid infill";
  - con epoxi lograron "perfect watertightness";
  - aplicarla sobre **≥ 4 perímetros y ≥ 60 % de relleno**, porque con 1–2 perímetros la capa "will most likely crack";
  - con O-rings, el método "the best, easiest, and most proven".
  - *Agregado en la verificación:* en el ensayo de Prusa, "the worst results came with untreated PETG and acetone smoothed ASA", mientras que PLA, PCCF y resina SLA "worked great without post-processing – even 20 meters". **El PETG sin tratar fue de los peores en estanqueidad**: en P1, toda caja de PETG que deba ser estanca necesita epoxi interior.
  - [VERIFICADO: S22]
- **Half-Baked-Research** (vía Hackaday), a 1 bar: las ganadoras fueron la epoxi y dos PU **aplicadas por dentro**; la epoxi "held up the best after repeated abuse" [VERIFICADO: S23].
- **Eastman** recomienda para PETG: CA, acrílicos 2K, **PU 2K y epoxi 2K** [VERIFICADO: S34].
- **No encontré un dato numérico verificado de adhesión epoxi–PETG impreso** (lap shear). → buscar: "PETG epoxy lap shear 3D printed adhesion". Ensayarlo con el dinamómetro (§A9.4).
- **Absorción de agua de la epoxi:** el TDS de West no la da en número [VERIFICADO: S21, no figura]. R02 cita a un constructor de pod: "many epoxies … absorb water, swell and turn to jelly" [VERIFICADO en R02: S17 de R02]. Usar epoxi de laminado o recubrimiento marino, no epoxi de ferretería de 5 min [ESTIMADO].
- **Preparación:** lijar P120–P180 y limpiar con IPA:agua 50:50. Eastman pide lijar "with a 120-grit or finer paper" y limpiar con esa mezcla [VERIFICADO: S34]. **Nunca MEK:** MEK es *solvente* de PETG; Eastman lo usa para pulir y soldar por solvente [VERIFICADO: S34].
  - *Corregido:* la acetona **no** figura en S34. Prusa dice que disolver PETG solo es posible "using dangerous chemicals (Dichloromethane)" [VERIFICADO: https://help.prusa3d.com/article/petg_2059]. Que la acetona ataque el PETG queda [NO VERIFICADO]. Evitarla igual como limpiador es una precaución razonable [ESTIMADO].

### A9.3 Rugosidad lograble con epoxi y lijado

No encontré dato medido. Estimo **Ra ≤ 0,8 µm** con epoxi + lijado al agua P600→P1200 [ESTIMADO: memoria técnica, no verificado]. Verificarlo por comparación visual y táctil contra una pieza torneada.
- *Corregido:* ISO 3601-2 §5.3.3 admite "a visual inspection using master parts" solo cuando, por la **longitud de medición corta**, la rugosidad exacta no es medible [VERIFICADO: S25]. No es un permiso general para reemplazar el rugosímetro. La comparación visual y táctil de P1 es un [SUPUESTO: protocolo propio].

### A9.4 Probetas propias (con el dinamómetro)

Lo pido porque todos los factores de §A7 dependen de σt XY y Z reales:
- 5 probetas de tracción en XY y 5 en Z, con el perfil real de la Ender-3 S1.
- La mitad, **30 días en agua del fjord**.
- Tirar con el dinamómetro usando mordazas impresas con insertos.
- Si σ_XY medido < 40 MPa, reescalar §A7 [SUPUESTO: protocolo].

## A10. Insertos y uniones roscadas en PETG

### A10.1 Datos medidos

| Fuente | Unión | Arrancamiento | Torque máx. |
|---|---|---|---|
| CNC Kitchen (S27), **PETG**, 4 perímetros, 100 % de relleno, **M3** | Rosca directa | 118 kg (~1160 N) | 1 N·m |
| ″ | Inserto térmico | 119 kg | **3 N·m** |
| ″ | Helicoil | 120 kg | 1 N·m |
| ″ | Tuerca en bolsillo lateral | 86 kg | 2 N·m |
| ″ | **Tuerca en bolsillo de fondo** | **166 kg** | 2 N·m |
| PEM SI (S29), ABS y PC **inyectados**, IUA/IUB M4-1 | Inserto | ABS 912 N; PC 1312 N | ABS 2,0; PC 2,3 N·m |
| ″ M4-2 (largo) | Inserto | ABS 1646 N; PC 2869 N | 2,1 / 2,3 N·m |
| ″ IUT M4 | Inserto | ABS 963 N; PC 1710 N | 4,1 / 5,9 N·m |
| ″ IUT M5 | Inserto | ABS 1197 N; PC 1691 N | 5,4 / 7,7 N·m |
| ″ IUT M6 | Inserto | ABS 2130 N; PC 2660 N | 11,7 / 14,9 N·m |

- CNC Kitchen: "1 Nm torque on an M3 bolt already results in more than 1500 N in pretension" [VERIFICADO: S27].
- Instalación: soldador a **245 °C para PETG** (10–20 °C sobre la temperatura de impresión). Hundir el 90 % con la punta y el último tramo con una herramienta plana. Agujero ~1 mm más profundo que el inserto. Los agujeros impresos salen más chicos que en el CAD [VERIFICADO: S28].
- *Corregido (cita inexistente):* Eastman **no** dice "Avoid tapping a drilled hole…". Lo que dice es "Do not overly tighten screws or use self-tapping screws", "Use metal inserts if frequent assembly/reassembly is involved" e "Inserts are not recommended where thermal expansion and contraction may occur" [VERIFICADO: S34]. Que la rosca con macho en PETG sirva solo para montajes que no se desarman es [ESTIMADO], no de Eastman.

### A10.2 Latón contra inoxidable en agua salada

- **Descincificación:** el latón con Zn > ~15 % pierde zinc y queda cobre poroso, en capa o en "tapón" [VERIFICADO: S30]. Los latones DZR (CW602N, CW724R, C69300, ISO 6509-1) son la elección "for any installation that combines water contact, elevated temperature, and chloride exposure" [VERIFICADO: S30; cita completada, antes la elipsis omitía "elevated temperature"].
  - Matiz: para **agua de mar** Brassland recomienda **latón al aluminio C68700**; los DZR, para agua dulce [VERIFICADO: S30]. Refuerza la regla de no usar latón mojado en P1.
- Los insertos térmicos comerciales son de latón de aleación no declarada. El "free-machining leaded brass" de PEM es el típico [VERIFICADO: S29]; no son DZR [ESTIMADO].
- **Galvánico:**
  - el 316 pasivo es "slightly more noble — minor risk to brass" [VERIFICADO: S30];
  - latón dentro de aluminio: "the aluminium corrodes rapidly"; aislar con buje de PTFE o sellador no conductivo [VERIFICADO: S30].
- **Hay insertos en inoxidable:** PEM los fabrica en "300 series stainless steel… passivated" (código "C"), además de latón y aluminio [VERIFICADO: S29]. Precio y stock en Dinamarca: buscar "PEM SI stainless heat staking insert".

### A10.3 Recomendación P1

1. **Por defecto: tuerca hexagonal A4 cautiva en bolsillo de fondo**, con el tornillo entrando desde el lado opuesto. Es la unión más fuerte del ensayo de CNC Kitchen [VERIFICADO: S27], la más barata y del mismo metal que el tornillo, así que no hay par galvánico.
2. Donde haga falta un inserto (acceso de un solo lado), **inserto inox 300**, instalado a ~250–260 °C [ESTIMADO: 245 °C de S28 + margen]. El inox conduce peor el calor que el latón y tarda más en calentar [ESTIMADO: memoria técnica, no verificado].
3. **Latón solo en zona seca** (dentro de la caja del ESC) y nunca en contacto con aluminio mojado.
4. **Torque de apriete** sobre inserto o tuerca cautiva en PETG [ESTIMADO: ~50 % del torque de rotura de S27 y S29; validar con el dinamómetro y un brazo de palanca]:
   - M3: 0,5 N·m;
   - M4: 1,0 N·m;
   - M5: 2,0 N·m.
   Sujeciones que deban conservar precarga: limitador de compresión metálico (§A5).
5. **Fijador de roscas.** Loctite 243 "is not normally recommended for use on plastics (particularly thermoplastic materials where stress cracking of the plastic could result)" [VERIFICADO: S31]. Usar:
   - tuercas autoblocantes (nyloc) A4; o
   - **Loctite 425** (cianoacrilato de baja resistencia "for locking metal and plastics fasteners", −54 a +85 °C) [VERIFICADO: S32].
   - El 243 solo en roscas metal-metal donde no pueda chorrear sobre el PETG.

## A11. Compatibilidad química con PETG

| Sustancia | Veredicto para PETG | Evidencia |
|---|---|---|
| Agua de mar | OK, con pérdida de resistencia (§A2) | [VERIFICADO: S11–S13] |
| Aceites y grasas (en general) | "Good" (PolyLite); "resistant to most kinds of oil and grease" (Bambu) | [VERIFICADO: S2, S3] |
| Aceite mineral de motor SAE 15W-40, 7 días a 25 °C | **Tracción −16,9 %** (PETG con 30 % de relleno); PETG+CF sin cambio significativo | [VERIFICADO: S43]. → No sumergir PETG en aceite mineral; la grasa en film fino es otra cosa [ESTIMADO]. |
| Grasa de silicona | Compatible con NBR, EPDM y FKM (rating 1). Con O-rings de **silicona**, "3" (dudoso). | [VERIFICADO: S24, tabla de compatibilidad]. Sobre PETG: [ESTIMADO: compatible, "oils and grease good" en S2]. |
| Grasa PTFE en base mineral | **Prohibida con EPDM** (aceite de petróleo: EPDM "4", insatisfactorio); NBR y FKM "1" | [VERIFICADO: S24] |
| Fijador anaeróbico (Loctite 243 y similares) | **Evitar sobre PETG**: riesgo de stress cracking | [VERIFICADO: S31] |
| Cianoacrilato | En PET, CA y acrílicos son "normally compatible" sin stress cracking; Eastman lo recomienda para PETG. **Pero** "some superglues seem to weaken PETG". El CA sin curar sí agrieta ABS, ASA y PC. | [VERIFICADO: S33, S34, S35]. Ensayar la marca. Usar poco y quitar el exceso. |
| Epoxi 2K | Recomendada por Eastman (DP-100) | [VERIFICADO: S34] |
| PU 2K o 1K (Sikaflex-291i) | Eastman recomienda PU 2K. El PU Bostik P580 fue el **más fuerte** en el ensayo de PETG (*matiz de la verificación:* el resumen de Hackaday dice "a construction polyurethane glue is the absolute winner", pero el cuerpo del texto dice que "MMA (Methyl Methacrylate) and similar score the highest". No vi el gráfico ni el video: el podio queda **ambiguo**. Con epoxi 2K y CA rompió el sustrato de PETG antes que la unión). Sikaflex-291i resiste agua de mar, pero **"must not be used to seal plastics that are prone to stress cracking (e.g. PMMA, PC)"**; servicio −50 a 90 °C. | [VERIFICADO: S34, S35, S36]. PETG no figura en la lista negra de Sika: probar en un retazo con tensión. |
| MS polímero / STP | Sin dato verificado | [ESTIMADO: sin solventes, bajo riesgo de ESC; probar]. buscar: "MS polymer sealant PETG compatibility" |
| Silicona RTV (sellador) | Sin dato verificado. La acética libera ácido acético (ácidos débiles: "Good" en S2). Adhiere mal sin imprimación. | [ESTIMADO: preferir curado neutro; sirve como junta moldeada (S22), no como adhesivo] |
| MEK, ciclohexanona, THF, cloruro de metileno | **Disuelven el PETG.** Eastman los usa para soldar o pulir por solvente. | [VERIFICADO: S34]. Limpiar con IPA:agua 50:50 [VERIFICADO: S34]. |
| Acetona | *Corregido:* S34 **no** la menciona. Prusa: disolver PETG solo con "dangerous chemicals (Dichloromethane)". | [NO VERIFICADO] que la ataque; https://help.prusa3d.com/article/petg_2059 sugiere que no la disuelve. No usarla igual como limpiador [ESTIMADO: precaución]. |
| Ácidos y álcalis fuertes | "Poor" | [VERIFICADO: S2] |

## A12. Metales asociados (lo que toca a los materiales impresos)

- **316 sumergido:**
  - "crevice corrosion can be expected in grade 316 at temperatures above 10–15 °C in seawater";
  - "propeller shafts made from 316 are usually galvanically protected";
  - "Stagnant, aerated sea water is a very corrosive medium… design to self drain";
  - "wash down with clean water".
  - [VERIFICADO: S42]
- El agua salobre del fjord es menos salina que el mar abierto [ESTIMADO: memoria técnica, no verificado]. Aun así, conviene suponer riesgo de corrosión en rendija en verano.
- **En P1:**
  - el eje de 316 dentro de bujes de POM y bajo O-rings forma **rendijas**;
  - guardar la cola **basculada fuera del agua**, enjuagar con agua dulce y dejar escurrir;
  - la hélice de aluminio sobre el eje de 316 actúa como ánodo y se come primero [ESTIMADO: deducido de S42];
  - considerar un ánodo de zinc en el tubo.
- Los rodamientos inox "S6801Z" suelen ser 440C, que se oxida más que el 316 en agua salobre (ver R01). Mantenerlos en zona seca.

---

# PARTE B — SELLADO

## B1. Qué hay que sellar en la cola larga de P1

| Zona | Exposición | Solución recomendada | Sello dinámico sumergido |
|---|---|---|---|
| Motor outrunner (arriba) | Salpicadura y spray salino | Cubierta con **drenaje**, sin sellar. Estator con barniz o epoxi y enjuague (R03 §motor). | No |
| Correa HTD-5M y poleas | Salpicadura | Tapa con drenaje; no encerrar agua (R02) | No |
| Boca superior del tubo del eje | Agua que sube por el tubo y spray | **V-ring o retén "excluidor"** sobre el eje + drenaje bajo la polea | Sí, pero **fuera del agua** y a baja presión |
| Bujes del tubo (dentro del agua) | Inmersión y arena | **Lubricados por agua; sin sello**. Opcional: labio excluidor de arena en el buje inferior. | Solo excluidor, no estanco |
| Caja del ESC y de las conexiones | Salpicadura e inmersión breve si se vuelca agua en la cubierta | **Sello axial (de cara)** O-ring 3,53 o junta blanda + prensaestopas IP68 | No |
| Batería con BMS | En el bote | Caja comercial; conectores IP67/68 | No |
| Kill switch | Salpicadura | Comercial marino | No |

**Ventaja de arquitectura:** un pod sumergido exige sello dinámico de eje o motor inundado, y O-rings bajo presión hidrostática y bombeo térmico. R03 documenta agua pasando el sello en eFoils con aceite y succión por bombeo térmico. La cola larga **elimina todo eso**.

## B2. Reglas de diseño de O-rings (fuentes primarias)

| Parámetro | Parker ORD 5700 (S24) | Trelleborg 2024 (S26) | ISO 3601-2 (S25, muestra) |
|---|---|---|---|
| Compresión estática | Máx. "most elastomers is **30 %**"; en sello de cara "a 30 % squeeze is often beneficial"; **mínima 0,2 mm** (0,007"), sin importar la sección | **Axial estático 13–36 %**; radial estático 10–35 % | Rango por sección en la Figura 8 (no incluida en la muestra) |
| Compresión dinámica | Máx. **~16 %** (hasta 25 % en secciones chicas) | Radial dinámico 6–27 % | — |
| Llenado de ranura | **60–85 %**, óptimo **75 %**, "at least a 10 % void" | ≤ 85 % | — |
| Rugosidad de la cara de sello (estático) | ≤ **32 µin RMS (~0,8 µm)**; 16 RMS para gases y vacío; flancos de ranura 63 RMS (~1,6 µm) | Superficie de contacto estática **Ra ≤ 1,6, Rz ≤ 6,3, Rt ≤ 10 µm**; flancos y fondo de ranura **Rt ≤ 16 µm** | Tabla 1 (no incluida en la muestra); **Rmr 50–80 %** en superficies de contacto |
| Rugosidad (dinámico) | 10–20 µin (0,25–0,5 µm); <5 µin no recomendado | Contacto **Ra ≤ 0,4** (rectificado sin espiral) | — |
| Dirección de las marcas | Las marcas de torno **paralelas** a la ranura sellan aun rugosas; las transversales (fresado) no | — | — |
| Chaflán de entrada | — | Ra ≤ 0,8, Rz ≤ 6,3 µm | **15–20°**, bordes redondeados |
| Concentricidad (radial) | Excentricidad máx. 0,002" (0,05 mm) para 2,62 mm | — | Run-out Y = 0,025 (Ø ≤ 50) / 0,05 (Ø > 50) |
| Estiramiento instalado | >5 % no recomendado | — | — |

Todo [VERIFICADO: S24 §3.6, §3.7, §4.1, Design Chart 4-2 y 4-3; S26 §B.2.4, Tablas 19–20; S25 §5.2–5.5].

*Agregado en la verificación:*
- **Trelleborg contradice a Parker en las marcas de mecanizado:** "Fundamentally grooves, scratches, pit marks, concentric or spiral machining scores, etc. are not permissible" [VERIFICADO: S26, apartado "Surfaces"]. Una cara refrentada en el torno debe quedar **sin surcos visibles** (avance fino y pasada final) y dentro de Ra ≤ 1,6 µm. No alcanza con que las marcas sean concéntricas.
- Trelleborg recomienda ajuste **H8/f7** para aplicaciones estáticas [VERIFICADO: S26].
- La excentricidad máxima de Parker (Design Chart 4-2) es 0,002" (0,05 mm) para 2,62 mm y **0,003" (0,08 mm) para 3,53 mm** [VERIFICADO: S24].

## B3. Dimensiones de alojamiento (P1)

**Parker, sello de cara (Design Chart 4-3)** [VERIFICADO: S24; conversión a mm CALCULADA]:

| Sección W | Profundidad L | Compresión | Ancho G (líquidos) | Radio de fondo |
|---|---|---|---|---|
| 1,78 mm | 1,27–1,37 mm | 19–32 % | 2,57–2,72 mm | 0,13–0,38 mm |
| **2,62 mm** | **1,88–2,03 mm** | 20–30 % | **3,45–3,61 mm** | 0,13–0,38 mm |
| **3,53 mm** | **2,57–2,72 mm** | 20–30 % | **4,50–4,75 mm** | 0,25–0,64 mm |

**Parker, sello radial estático (Design Chart 4-2):**
- 2,62 mm: profundidad 2,06–2,11 mm, compresión 17–24 %, **holgura diametral 0,05–0,13 mm**, ancho 3,56–3,68 mm, **excentricidad máx. 0,05 mm**.
- 3,53 mm: profundidad 2,82–2,87 mm, compresión 16–23 %, holgura 0,08–0,15 mm, ancho 4,75–4,88 mm.
- [VERIFICADO: S24]

**Sensibilidad a la tolerancia FDM** [CALCULADO: objetivo 25 % de compresión; la tolerancia de profundidad impresa es mía, ±0,15 mm, ESTIMADO]:

| Sección | Profundidad nominal | Ancho al 75 % de llenado | Compresión con ±0,10 mm | ±0,15 mm | ±0,20 mm |
|---|---|---|---|---|---|
| 2,5 mm (hoy en `inputs.yaml`) | 1,88 | 3,49 | 21–29 % | 19–31 % | **17–33 %** (fuera de 20–30) |
| 2,62 mm | 1,97 | 3,66 | 21–29 % | 19–31 % | 17–33 % |
| **3,53 mm** | 2,65 | 4,93 | 22–28 % | **21–29 %** | 19–31 % |

Además, la sección del propio O-ring tiene tolerancia ±0,08 mm (2,62) o ±0,10 mm (3,53) [VERIFICADO: S24, ±.003"/±.004"].

**Recomendación:**
1. Pasar `oring_cs_mm` a **3,53 mm** (AS568 serie 2-2xx). Es la medida más tolerante a la imprecisión FDM y sigue siendo de stock.
2. Usar **sello de cara** con **bridas metal-metal o plástico-plástico a tope**: la profundidad de la ranura fija la compresión, no el apriete. Así el creep de la brida de PETG (§A5) no afloja el O-ring.
3. **No usar sellos radiales en alojamientos impresos.** Piden holgura de 0,05–0,13 mm y excentricidad ≤0,05 mm para 2,62 mm (0,08–0,15 mm y ≤0,08 mm para 3,53 mm) [VERIFICADO: S24], fuera del alcance de una Ender-3 sin torno. Si hacen falta, tornear después las dos superficies.

## B4. Rugosidad FDM contra rugosidad requerida, y cómo lograr el sello

| Superficie | Medido | Fuente |
|---|---|---|
| PETG, Sa por capa (0,12 / 0,15 / 0,18 / 0,21 mm) | 9,6–11,7 / 10,9–12,8 / 16,7–20,9 / **19,9–24,4 µm** | [VERIFICADO: S18] |
| Nylon-CF, Ra cara superior / pared / cara de cama | 3,12–16,75 / 4,37–23,55 / **2,12–4,02 µm**; óptimo 2,82 / 3,95 / **1,92 µm** (capa 0,1 mm) | [VERIFICADO: S19] |
| Requerido, estático (Parker / Trelleborg) | ≤ 0,8 / ≤ 1,6 µm Ra | [VERIFICADO: S24, S26] |

**Brecha** [CALCULADO]:
- La pared impresa a 0,2 mm es **10–30× más rugosa** que lo admisible.
- La mejor cara FDM (la que apoya en la cama) queda en ~1,2–2,5× el límite de Trelleborg.
- Las líneas de capa de una pared vertical son **paralelas** a un O-ring radial. Parker considera favorables las marcas de torno paralelas a la ranura; extenderlo a las líneas de capa FDM es una extrapolación [ESTIMADO]. Trelleborg, además, no admite surcos concéntricos (§B2). La **costura Z** y los poros entre perímetros son caminos de fuga **transversales** [VERIFICADO: S22, PETG "leaked… through the seams"].

**Métodos, de mejor a peor para P1:**

| Método | Ra esperada | Pros | Contras | Etiqueta |
|---|---|---|---|---|
| **Refrentar o tornear** en el torno la cara de sello y la ranura | ~0,8–3,2 µm, con marcas **circunferenciales** (favorables según Parker) | Herramienta disponible; geometría exacta (profundidad = compresión) | Solo piezas de revolución o con cara plana que entre en el torno | [ESTIMADO: Ra de torneado de plástico, memoria técnica]; dirección de marcas [VERIFICADO: S24] |
| **Sellar contra metal o acrílico:** la ranura impresa (pide Rt ≤ 16 µm) y la cara de sello en una tapa de aluminio | La tapa comercial ya cumple | La pieza impresa solo necesita el fondo de ranura razonable; el aluminio hace de disipador para la caja del ESC | El fondo de ranura impreso puede seguir algo rugoso → imprimirlo **boca abajo sobre la cama** o refrentarlo | [VERIFICADO: S26 Rt ≤ 16 µm; S19 cara de cama 1,9–4 µm] |
| **Epoxi + lijado al agua** (XTC-3D o West) | ≤ 0,8 µm | Sella poros y costura | Paso manual; HDT 48 °C (West) | [VERIFICADO: S20–S22]; Ra [ESTIMADO] |
| **Junta blanda** (EPDM o neopreno celular cerrado, o silicona 20–40 Shore A, 2–3 mm, 25–40 % de compresión) | Se adapta a 10–25 µm | Lo más barato; tolera planitud FDM | Pierde precarga por creep del PETG → usar limitadores. Junta **impresa en TPU: falló** (Prusa). | [VERIFICADO: S22, gasket impreso falló]; resto [ESTIMADO] |
| **Junta de silicona moldeada en molde impreso** | Se adapta | Forma libre; en la linterna roscada funcionó a 30 m | Curado; adhesión. En la carcasa de cámara de Prusa "the silicone gasket … always leaked no matter how much it was squeezed" | [VERIFICADO: S22] |
| **No sellar: drenar** | — | Cubiertas de motor y correa | Solo donde la inmersión no importa | R02 |

**Configuración de impresión de zonas de sello** [ESTIMADO, salvo lo indicado]:
- ≥ 4 perímetros [VERIFICADO: S22] y 100 % de relleno en 5 mm alrededor de la ranura;
- capa de 0,12–0,15 mm (Sa 10–13 µm contra 20–24 µm a 0,21 mm) [VERIFICADO: S18];
- costura Z alineada lejos del cruce con el O-ring, y caras de sello hacia la cama cuando se pueda.

## B5. Material del O-ring y lubricante

| Elastómero | Agua de mar | Grasa de silicona | Aceite de petróleo | Uso |
|---|---|---|---|---|
| **NBR 70** | 1 | 1 | 1 | **Por defecto** (lo que ya prevé `inputs.yaml`) |
| EPDM | 1 | 1 | **4** | Bien en agua, pero **nunca con grasa mineral** |
| FKM | 1 | 1 | 1 | Si hace falta temperatura (caja junto al ESC) |
| Neopreno CR | 2 | 1 | 2 | Juntas planas de salpicadura |
| Silicona | X (sin dato en "Brine (Seawater)"; "Water": 1) | **3** | 2 | Evitar con grasa de silicona |
| Poliuretano AU | X (sin dato en "Brine (Seawater)"; **"Water": 4**) | 1 | 2 | **No usar mojado** |

Escala: 1 satisfactorio, 2 aceptable (estático en general), 3 dudoso, 4 insatisfactorio, X sin dato [VERIFICADO: S24, tablas de compatibilidad, Sección VII; filas "Brine (Seawater)", "Water", "Silicone Greases" y "Petroleum Oil, Below 250°F"].
- *Corregido en la verificación:* la tabla anterior daba "1" para silicona y "2" para PU en agua de mar, y "—" para PU en aceite. En S24, la fila "Brine (Seawater)" tiene **X** para silicona y para AU, la fila "Water" tiene **4** para AU, y "Petroleum Oil" tiene **2** para AU. NBR, EPDM, FKM y CR coinciden con la versión anterior.

- **Lubricante:** grasa de silicona en cada montaje; Prusa recomienda engrasar "before every use" [VERIFICADO: S22]. Parker Super-O-Lube es "a high-viscosity silicone oil" [VERIFICADO: S24].

## B6. Sellos de eje

**Velocidad periférica en P1** [CALCULADO]: eje de Ø16 mm a 991 rpm = **0,83 m/s**; a 1211 rpm máx. = **1,01 m/s (200 fpm)**.
- *Corregido (rpm actuales de `sizing_tablas.md`: 1491 en crucero, 1777 máx.):* **1,25 m/s (246 fpm) en crucero y 1,49 m/s (293 fpm) a máxima** [CALCULADO]. P1 **supera** el umbral de 200 fpm de Parker. Entre 200 y 400 fpm, Parker admite O-rings rotativos de sección ≤ 0,139" (3,53 mm), con su diseño de sello rotativo [VERIFICADO: S24, tabla "O-Ring Sections for Rotary Seals"].

| Opción | Datos verificados | Aplicable a P1 |
|---|---|---|
| **Retén radial (lip seal) NBR, tipo HMS5/HMSA10** | Hasta 14 m/s; **máx. 0,03 MPa**; lubricado con aceite o grasa; −40 a +100 °C. Eje: **Ra 0,2–0,8 µm (DIN 3760) o 0,2–0,5 (ISO 6194), ≥ 45 HRC, rectificado en plongée sin espiral**; alojamiento H8, Ra 1,6–6,3 µm. | Un **eje de 316 no es templable** (≪45 HRC) [ESTIMADO: memoria técnica]: el labio le hace surco, peor con arena. En el tubo **no**. En la boca superior, como excluidor engrasado: aceptable, con camisa endurecida o de cerámica si se gasta [ESTIMADO]. [VERIFICADO: S37] |
| **O-ring como sello rotativo** | Parker: por debajo de 200 fpm (1,02 m/s) la sección "usually not critical"; eje **no mayor que el DI libre** del O-ring (sin estiramiento, por el efecto Gow-Joule). Trelleborg: DI **2–5 % mayor** que el eje y "does not recommend the use of O-Rings as rotary seals". | *Corregido:* con las rpm actuales, P1 **pasa** los 200 fpm (246–293 fpm). Solo como excluidor de baja exigencia y con sección ≤ 3,53 mm. Parker además prefiere ejes templados (~55 HRC, "desirable, but not mandatory"). [VERIFICADO: S24 §5.27, S26 §B.2.4] |
| **Prensaestopas** (empaquetadura) | Debe gotear **2–3 gotas/min** girando, porque el agua lubrica. Con más de **8–10 gotas/min**, servicio. Apretar de más hace surco en el eje. | Solo si hubiera un **paso de casco** (pod o jet interior). La cola larga no atraviesa el casco. [VERIFICADO: S38] |
| **V-ring / sello axial de labio** | Sin hoja abierta en esta sesión (buscar: "V-ring seal VA VS data sheet speed") | Mi candidato para la boca superior del tubo: sella contra una cara (arandela inox pulida), tolera desalineación [ESTIMADO] |
| **Bujes lubricados por agua sin sello** | — | **Diseño base de P1** (ver R01 y R02). Sin sello que falle. |

## B7. Motor inundado, sellado seco, acople magnético o seco arriba (P1)

| Opción | Cómo funciona | Pros | Contras | Evidencia |
|---|---|---|---|---|
| **Seco arriba del agua (P1)** | Outrunner en el aire; eje largo al agua | Sin sellos dinámicos sumergidos; motor barato de RC o e-bike; refrigeración por aire; mantenimiento visible | Spray salino en rodamientos e imanes → cubierta, barniz y enjuague; eje largo con velocidad crítica (calculada en `sizing_tablas.md`: hoy 5834 contra 1777 rpm; antes decía 5936 contra 1211) | R02, R03; [CALCULADO] |
| **Motor inundado** | Bobinado y estator encapsulados, imanes y rotor recubiertos, bujes plásticos lubricados por agua | "eliminates the need for shaft seals, magnetic couplings, and air- or oil-filled compartments"; refrigerado por agua | Hay que encapsular un motor que no lo trae (epoxi de alta temperatura en 2 capas, ver R03) y recubrir los imanes; la arena entra al entrehierro; los rodamientos de bolas sumergidos se corroen | [VERIFICADO: S39] T200: 390 W a 16 V, solo partes inox 316 expuestas |
| **Sellado seco o con aceite** | Carcasa estanca + sello de eje (labio o cerámico) | Motor estándar | Sello dinámico bajo presión; **bombeo térmico** (pod caliente que se enfría en agua fría succiona agua); aceite anual; agua pasando el sello | R03 (Lift/FR, Flipsky 65161) |
| **Acople magnético** | El motor seco gira imanes a través de una pared estática; el rotor húmedo gira la hélice | Sello **100 % estático** (O-ring de cara); desliza al trabarse, como protección de sobrecarga | Par limitado por imanes y entrehierro; corrientes parásitas si la pared es metálica; volumen, costo e imanes de NdFeB en agua salada; los rodamientos del lado húmedo siguen en agua | [ESTIMADO: memoria técnica, no verificado]; buscar: "magnetic coupling underwater thruster efficiency eddy loss" |

**Veredicto:** el **seco arriba** es el de menor riesgo de sellado y menor costo para P1. Las tres alternativas sumergidas trasladan el problema al sello o al encapsulado.

## B8. Prensaestopas de cable y conectores IP68

**LAPP SKINTOP ST-M** (poliamida) [VERIFICADO: S40]:
- **IP66, IP68 (5 bar/30 min), IP69**;
- junta de cierre de **CR (resistente a ozono y UV)**;
- −40 a +100 °C estático y −20 a +100 °C dinámico;
- M20×1,5 para cable de **6–13 mm** (o 4–10 mm con la junta reductora STR-M);
- cuerpo negro RAL 9005 resistente a UV.

En P1:
- **un cable redondo por prensaestopas**. Dos cables sueltos o un cable plano no sellan [ESTIMADO: el IP68 se certifica con cable redondo];
- la rosca M20 en PETG debe ser **pasante con contratuerca** y la junta debe apoyar sobre una **cara plana refrentada o con epoxi** (§B4); no confiar en una rosca impresa como sello;
- el agua viaja **por dentro** de un cable multifilar si su extremo queda mojado. Sellar las puntas con termocontraíble con adhesivo [ESTIMADO: memoria técnica].

**Bulgin 900 Buccaneer** [VERIFICADO: S41]:
- IP68 ensayado a **1,054 kg/cm² (10 m) durante 2 semanas**, e IP69K;
- niebla salina EN 60068-2-52 "Marine Severity";
- **32 A** con 2–7 contactos (10 A con 10); 600 V CA/CC con 2–5 contactos;
- −40 a +85 °C; tapas para mantener IP68 desconectado.

En P1 el motor está **seco** y fuera del agua: alcanza con conectores de fase de alta corriente (sin IP) dentro de la caja o la cubierta drenada. Un 32 A no cubre la corriente de fase pico del motor de P1 con margen; la de batería es de 62 A pico (`sizing_tablas.md` actual; antes decía 67 A). Un conector IP68 solo hace falta si se pasa a un pod.

## B9. Plan de verificación (barato, con las herramientas del usuario)

1. **Probetas de tracción en XY y Z**, secas y tras 30 días en agua del fjord, con el dinamómetro (§A9.4).
2. **Probeta de tuerca A4 cautiva e inserto inox**: arrancamiento con el dinamómetro y torque de rotura con llave y brazo de palanca.
3. **Prueba de estanqueidad de la caja del ESC** [ESTIMADO: protocolo]:
   - con papel absorbente adentro, sumergirla 30 min a 0,3 m;
   - después, aire a +0,2 bar con agua jabonosa;
   - repetir tras 20 ciclos de abrir y cerrar.
4. **Termopar** en la cara del soporte de motor y en la caja del ESC durante 2 h a crucero: confirmar < 50 °C en todo lo impreso (§A4).
5. **Inspección mensual** de fisuras del protector de hélice y de la zona de fijación (§A6).

---

## Hallazgos que cambian el diseño

- **`f_fatigue` de 0,30 a 0,06.**
  - PETG impreso: 0,8–1,9·10⁵ ciclos al 30 % de la UTS [VERIFICADO: S16]; extrapolado, ~8 % a 10⁷ y ~4 % a 10⁸ [CALCULADO].
  - P1 suma ~5·10⁷ ciclos de paso de pala en 300 h (49,6 Hz) [CALCULADO]. *Corregido con las rpm actuales (1491 rpm): **~8·10⁷ ciclos (74,6 Hz)**; a esa vida el ajuste da 4,2 % → `f_fatigue` ≈ **0,045** sería lo coherente* [CALCULADO].
  - → **σa admisible ≈ 0,5 MPa (XY) y 0,2 MPa (Z)** con R = 0,1 y f_fatigue 0,06; **≈ 0,35 / 0,14 MPa** con 0,045 [CALCULADO]. Ninguna pieza impresa en la ruta de carga alterna: hélice → tubo → cardán → espejo, correa → soporte de motor. Esa ruta va en aluminio o inox.
- **`f_water` de 0,85 a 0,75** (−17 a −28 % a 30 días en agua de mar [VERIFICADO: S13]). El peor caso estricto es **0,72**; 0,75 es un redondeo ~4 % no conservador.
- **`f_z` de 0,55 a 0,40**, y `sigma_t_z_mpa` de 25 a **18** (adhesión entre capas 18 ± 4 MPa [VERIFICADO: S1]).
- **`f_creep` de 0,50 a 0,35.** La admisible sostenida con FS 3 baja de 4,3 a **2,7 MPa en XY** y a **1,1 MPa en Z** [CALCULADO]. Uniones con precarga: **limitadores de compresión metálicos**.
- **`t_service_max_c` de 60 a 50 °C** para PETG cargado. Las HDT verificadas están entre 65,7 y 75 °C [VERIFICADO: S1–S4] y la epoxi West tiene HDT de 48 °C [VERIFICADO: S21]. Soporte de motor y base del ESC de **aluminio**; PETG de color claro al sol. Comprar PETG con **HDT(1,8 MPa) ≥ 70 °C** (PolyLite: 75 °C).
- **Materiales descartados con la Ender-3 S1 (≤260 °C, abierta):**
  - PA6-CF y PA12-CF piden 280–300 °C [VERIFICADO: S8, S9]; el PA6-CF además pierde **−50 % de resistencia y −71 % de módulo** mojado.
  - PC y PC-PBT piden cámara de 70–110 °C [VERIFICADO: S6, S7]; ASA, cerramiento [VERIFICADO: S5].
  - El PETG-CF solo sirve para rigidez (+75 % de E) con boquilla endurecida (la de latón dura ~9 h [VERIFICADO: S4]).
- **Uniones roscadas: tuerca A4 cautiva en bolsillo de fondo como estándar.**
  - Resistió 166 kg contra 119 kg del inserto térmico en PETG [VERIFICADO: S27].
  - Insertos inox 300 donde haga falta [VERIFICADO: S29]; latón solo en zona seca (descincificación con Zn > 15 % [VERIFICADO: S30]).
  - **Nada de Loctite 243 sobre PETG** [VERIFICADO: S31]: usar nyloc A4 o Loctite 425 [VERIFICADO: S32].
  - Torques de partida: M3 0,5, M4 1,0, M5 2,0 N·m [ESTIMADO, validar].
  - Limpiar con IPA:agua 50:50 y nunca con MEK [VERIFICADO: S34]. Acetona: evitarla por precaución, pero que ataque el PETG es [NO VERIFICADO].
  - Las cajas estancas de PETG necesitan **epoxi interior**: en el ensayo de Prusa, el PETG sin tratar estuvo entre los peores [VERIFICADO: S22].
- **O-ring: `oring_cs_mm` de 2,5 a 3,53 mm.**
  - Con ±0,15 mm de tolerancia FDM, la compresión queda en 21–29 % (con 2,5 mm: 19–31 %, y 17–33 % con ±0,2) [CALCULADO].
  - Ranura de cara de **2,57–2,72 mm de profundidad × 4,50–4,75 mm de ancho**, compresión 20–30 % [VERIFICADO: S24]; llenado 60–85 %, óptimo 75 % [VERIFICADO: S24]. `oring_squeeze_frac 0,25` y `gland_fill 0,75` quedan **verificados**.
  - **Solo sellos de cara con bridas a tope**; ningún sello radial en alojamiento impreso (excentricidad ≤ 0,05 mm [VERIFICADO: S24]).
- **Rugosidad: la superficie impresa (Sa 10–24 µm [VERIFICADO: S18]) no sella contra Ra ≤ 0,8–1,6 µm [VERIFICADO: S24, S26].**
  - Refrentar en el torno la cara y la ranura (marcas circunferenciales, favorables según Parker [VERIFICADO: S24]), o sellar contra una tapa de aluminio, o epoxi y lijado. Trelleborg no admite surcos concéntricos visibles [VERIFICADO: S26]: hacer una pasada final fina.
  - Zonas de sello: ≥ 4 perímetros [VERIFICADO: S22], 100 % de relleno y capa de 0,12–0,15 mm.
  - No imprimir juntas en TPU (fallaron [VERIFICADO: S22]).
- **O-rings NBR 70 + grasa de silicona.** Nunca grasa mineral con EPDM (rating 4 [VERIFICADO: S24]). Nada de O-rings de poliuretano mojados ("Water": 4 [VERIFICADO: S24]).
- **Cero sellos dinámicos sumergidos en la cola larga.**
  - El eje de 316 (<45 HRC) no sirve para un retén estándar (pide ≥ 45 HRC y Ra 0,2–0,8 [VERIFICADO: S37]).
  - En la boca superior del tubo, V-ring o retén engrasado como **excluidor**, con drenaje. *Corregido:* con las rpm actuales, el eje de Ø16 gira a **1,25–1,49 m/s (246–293 fpm)**, por encima de los 200 fpm de Parker [CALCULADO]. Si se usa un O-ring, de sección ≤ 3,53 mm y DI ≥ eje [VERIFICADO: S24].
  - Es una ventaja decisiva frente al pod: sello dinámico, bombeo térmico (R03) o encapsulado del motor (S39).
- **316 sumergido:** corrosión en rendija por encima de 10–15 °C en agua de mar [VERIFICADO: S42]. Guardar la cola **fuera del agua** y escurrida, enjuagar con agua dulce y considerar un ánodo de zinc. La hélice de aluminio actúa de ánodo y se come primero.
  - *Agregado en la verificación:* ASSDA dice que eso hace al 316 "unsuitable for immersed applications where crevices exist", y que "propeller shafts made from 316 are usually galvanically protected" [VERIFICADO: S42]. El eje de 316 dentro de bujes de POM sumergidos es exactamente ese caso. El ánodo pasa de "considerar" a **obligatorio**, o se cambia a un inox de mayor PREN (dúplex 2205) [ESTIMADO: memoria técnica, no verificado].
- **Prensaestopas LAPP SKINTOP ST-M M20 (IP68 5 bar/30 min, junta CR anti-UV [VERIFICADO: S40]).** Un cable redondo por prensaestopas, contratuerca y junta sobre cara refrentada. El motor seco no necesita conectores IP68.

---

## Verificación (adversarial)

Fecha: 2026-10-01. Método: volví a bajar las **43 URLs** con `curl`. Los PDF los leí con `pdftotext`; HTML, JSON y Markdown, como texto plano. **42 abrieron** (HTTP 200). S11 devolvió un desafío reCAPTCHA y S12 un error 502 con curl; las dos se leyeron bien con WebFetch. Después contrasté cada número clave contra el texto de su fuente. Los valores [CALCULADO] los recalculé contra `resultados/sizing_tablas.md` tal como está hoy (generado el 2026-10-01 14:07). Agregué una fuente nueva, abierta en esta verificación: Prusa Knowledge Base, PETG (https://help.prusa3d.com/article/petg_2059).

### Correcciones aplicadas al texto

| Afirmación (sección) / URL | Estado | Nota |
|---|---|---|
| "Ventilador apagado" en todas las probetas Polymaker, incl. S4 (§A1) | **corregido** | S4 (PETG-rCF08): "Cooling fan 0-50%". En S2, S5–S9 sí dice OFF. |
| Creep: "al 70 % … se duplica a 20 h" (§A5) | **corregido** | En S15 la duplicación a 20 h es del caso **50 %** (~5 % → ~10 %). Al 70 %: 25 % (X) y 7 % (Y) a 5 h, que suben a 30 % y 8 %. |
| Basquin σmax = 362·N^−0,306 (§A6) | **corregido** | Recalculado desde la Tabla 2 de S16: **A = 367**, b = −0,306. Los valores de la tabla (5,3 / 2,6 / 1,3 MPa) ya correspondían a 367. |
| Hélice a 991 rpm, 49,6 Hz, 5,4·10⁷ ciclos/300 h; relación 3:1; correa ~790 Hz (§1, §A6, §A8, Hallazgos) | **corregido** | `sizing_tablas.md` actual: 1491 rpm y correa 2:1 → **74,6 Hz, 8,1·10⁷ ciclos**; motor ~2980 rpm; engrane ~990 Hz. Se mantuvo el texto viejo, marcado. |
| `f_fatigue` = 0,06 "entre 4 % y 8 %" (§A6, §A7) | **corregido (bandera)** | Con 8,1·10⁷ ciclos el propio ajuste da **4,2 %**. 0,06 es ~1,4× alto; lo coherente es ~0,045. `inputs.yaml` hoy usa 0,06. |
| σa = 0,77 MPa a partir de σmax = 1,7 MPa (§A6, §A7) | **aclarado** | Supone R = 0,1 (σa = 0,45·σmax), sin decirlo. Con R = 0,2: 0,69 → 0,46 / 0,18 MPa. |
| f_water "tomo la peor: 0,72 ≈ 0,75" (§A2, §A7) | **corregido (bandera)** | Redondear hacia arriba no es tomar el peor caso. Estricto: 0,72. |
| Eastman: "Avoid tapping a drilled hole or using self-tapping screws" (§A10.1) | **corregido: cita inexistente** | S34 dice "Do not overly tighten screws or use self-tapping screws" y "Use metal inserts if frequent assembly/reassembly is involved". Lo de roscar con macho queda [ESTIMADO]. |
| Acetona "ataca o disuelve el PETG" [VERIFICADO: S34] (§A9.2, §A11, Hallazgos) | **no verificado** | S34 no menciona la acetona. Prusa KB: disolver PETG solo con diclorometano. MEK, ciclohexanona, THF y cloruro de metileno sí están en S34. |
| Parker, compatibilidad en agua de mar: silicona "1", PU "2"; PU en aceite "—" (§B5) | **corregido** | Fila "Brine (Seawater)": silicona **X**, AU **X**. Fila "Water": AU **4**. "Petroleum Oil <250°F": AU **2**. NBR, EPDM, FKM y CR OK. |
| Eje Ø16 a 1,01 m/s "justo en el límite de 200 fpm" (§B6, Hallazgos) | **corregido** | Con 1491–1777 rpm: **1,25–1,49 m/s (246–293 fpm)**, por encima de 200. Parker admite W ≤ 0,139" entre 200 y 400 fpm (tabla de S24). |
| Velocidad crítica 5936 / 1211 rpm; batería 67 A pico (§B7, §B8) | **corregido** | `sizing_tablas.md` actual: **5834 / 1777 rpm** y **62 A**. |
| ISO 3601-2 "admite inspección visual cuando la rugosidad no es medible" (§A9.3) | **corregido (matiz)** | §5.3.3 lo admite solo por longitud de medición corta. No reemplaza un rugosímetro. |
| Brassland: DZR "for any installation that combines water contact… and chloride exposure" (§A10.2) | **corregido (cita completada)** | La elipsis omitía "elevated temperature". Para agua de mar Brassland recomienda latón al aluminio C68700. |
| Hackaday S35: "Bostik P580 el más fuerte" (§A11) | **corregido (matiz)** | El resumen dice "absolute winner", pero el cuerpo dice que MMA y similares "score the highest". Gráfico y video **no vistos**. |
| "Las líneas de capa… Parker considera favorable" (§B4) | **corregido** | Parker habla de marcas de torno, no de capas FDM: pasa a [ESTIMADO]. Trelleborg prohíbe "concentric or spiral machining scores" (S26), cosa que no se citaba. |
| Excentricidad radial ≤ 0,05 mm (§B3) | **completado** | 0,05 mm es para 2,62 mm. Para 3,53 mm: 0,003" = 0,08 mm (S24, Design Chart 4-2). |
| Boquilla de latón ~9 h [VERIFICADO: S8, S9, S10] (§A1) | **corregido** | Está en S4, S8 y S9; S10 solo pide "hardened nozzle". |
| Hélice PETG "se fisuró a los 4 meses" (§A6) | **corregido (matiz)** | Según R02 y R03, la pala se fisuró **al desmontarla** para inspección, tras ~4 meses. |
| Prusa S22: PETG sin tratar (§A9.2, §B4) | **agregado** | "the worst results came with untreated PETG and acetone smoothed ASA". La junta de silicona moldeada falló en la carcasa de cámara y funcionó en la linterna. |

### Fuentes reabiertas (43 de 43)

| Id / URL | Estado | Números chequeados |
|---|---|---|
| S1 prusa3d.com Prusament PETG TDS | OK | HDT 68/68; 47 ± 2; interlayer 18 ± 4; E 1,5 GPa; 0,07 / 0,10 % (24 °C, 22 % HR); 250 ± 10 °C; 2 perímetros. Ventilador de las probetas: 50 %. |
| S2 polymaker.com PolyLite PETG V6.0 | OK | Tg 81; HDT 78/75; 0,54 %; 50,8 / 42,8 MPa; E 2116,8; 230–260 °C; ventilador OFF; "should not be used for design". Aceite y grasa "Good"; ácidos y álcalis fuertes "Poor". |
| S3 bblcdn Bambu PETG Basic V3.0 | OK | Tg 69; HDT 71/68; 0,45 %; 51 / 35 MPa; E 2780; flexión 75/56; impacto 34,2/10,5; cámara 35–50 °C. |
| S4 fiberon PETG-rCF08 | OK, salvo ventilador (corregido) | 69,7; 68,6/65,7; 0,55 %; 59,8 / 41,1; E 3710; elongación Z 1,9 %; latón ~9 h. |
| S5 wiki Polymaker ASA | OK | 98; 103/100; 43,8 / 32; E 2379; "Closure Chamber: Needed"; probetas a 90 °C. |
| S6 wiki PolyLite PC | OK | 113; 111/107; 69,1 / 52,8; E 2497; cámara 70–100 °C. |
| S7 wiki PC-PBT | OK | 140; 107/91; 50,4 / 37,9; E 1940; 260–280 °C; cámara 100–110 °C. |
| S8 PA6-CF20 TDS V1.1 | OK | 74,2; 215/173; 3,3 %; seco 109,3 / 54,0 / E 8636,5; húmedo 54,7 / 25,5 / 2508,1 (5,30 %); 280–300 °C; 100 °C × 16 h. |
| S9 PA12-CF10 TDS V1.1 | OK | 55; 131/105; 1,5 %; 77,4 / 52,2 / 3311; húmedo 71,7 / 42,1 / 3131,7 (2,92 %). |
| S10 wiki PA6-CF20 | OK | 280–300 °C; hotend all-metal 280 °C+; recocido 100 °C × 16 h. |
| S11 PMC8036839 | OK (por WebFetch; curl → reCAPTCHA) | 28,05 % p/p; 20 °C; ~0,3 %; estable en semana 7 (salada), 8 (destilada) y 9 (azúcar); sin ensayos mecánicos. |
| S12 ouci.dntb.gov.ua | OK (por WebFetch; curl → 502) | 70 °C, 10 semanas, <1 %, UV 1000 h; tracción "modest increase". |
| S13 DOAJ API (IJLMM 2026) | OK | 30 días; PETG −17 a −28 %; Nylon −31 a −44; ABS −15 a −25; PLA −26 a −35. |
| S14 DOAJ API (Results in Materials 2023) | OK | Nylon, ABS, PLA, PCTG, PETG y ASA; "extremely high diffusivity"; rigidez proporcional a la masa absorbida. |
| S15 PMC12349189 | OK, salvo creep al 70 % (corregido) | X 50,44 ± 0,09; Y 22,48 ± 4,61; 235 °C; 0,1 mm; 21,3 °C, 39 % HR; umbrales 0,1 % (X) y 0,05 % (Y). |
| S16 PMC11243948 | OK | R = 0,2; 7 Hz; 215–220 °C; UTS XY 32,9; ciclos 60 / 45 / 30 % = 1,2–1,5·10⁴ / 1,7–4,1·10⁴ / 0,8–1,9·10⁵. |
| S17 PMC12845617 | OK | R = 0,05; 10 Hz; runout 10⁶; ASA 25 % (8 MPa), PA12 17 % (7,4), PC-ABS 15 % (4,7), PC 7 % (3,6). Los límites figuran como Δσ (≈ 0,95·σmax con R = 0,05). |
| S18 PMC13028808 | OK | Sa (perfilómetro óptico): 9,6–11,7 / 10,9–12,8 / 16,7–20,9 / 19,9–24,4 µm. |
| S19 PMC10489770 | OK | Ra: pared 4,37–23,55, cara superior 3,12–16,75, cara inferior 2,12–4,02; óptimos 3,95 / 2,82 / 1,92 µm. |
| S20 smooth-on XTC-3D | OK | 2A:1B; 350 cps; 10 min; 3,5 h; 80D; "PetG"; 28,3 g → 651 cm² a 0,04 cm. |
| S21 westsystem 105/205 | OK | 7900 psi (54,5 MPa); 3,4 %; 4,08·10⁵ psi; HDT 118 °F (48 °C); Tg 129 / 142 °F (54 / 61 °C). |
| S22 blog.prusa3d.com | OK + agregado | Todas las citas textuales están; se agregó "worst results… untreated PETG". |
| S23 hackaday 2026-05-30 | OK | 1 bar; epoxi y 2 PU interiores; "epoxy held up the best". Video **no visto** (declarado). |
| S24 Parker ORD 5700 | OK, salvo filas de compatibilidad (corregido) | 30 % / 16 % / 25 %; 0,2 mm; 60–85 %, 75 %, 10 % de vacío; 32 / 16 / 63 RMS; 10–20 µin; Charts 4-2 y 4-3 (todas las cotas en mm coinciden); ±.003 / ±.004; 200 fpm; Super-O-Lube. |
| S25 ISO 3601-2 (muestra iTeh) | OK, salvo matiz §5.3.3 | Rmr 50–80 %; 15–20°; Y 0,025 / 0,05. |
| S26 Trelleborg O-rings 2024 | OK + agregado | 13–36 / 10–35 / 6–27 %; ≤ 85 %; Tabla 19 (Ra 1,6, Rz 6,3, Rt 10; Rt 16; dinámico Ra 0,4); chaflán Ra 0,8 / Rz 6,3; DI 2–5 %; "does not recommend". |
| S27 cnckitchen helicoils | OK | M3, PETG, 4 perímetros, 100 %; 118 / 119 / 120 / 86 / **166 kg**; 1 / 3 / 1 / 2 / 2 N·m; ">1500 N". |
| S28 cnckitchen insert tips | OK | PETG 245 °C; +10–20 °C; 90 %; ~1 mm más profundo; agujeros más chicos que en CAD. |
| S29 pemnet SI | OK | Todas las cifras M4–M6 en ABS y PC coinciden; "B = Free-machining, leaded brass"; "C = 300 series stainless… Passivated". |
| S30 brassland corrosion | OK, salvo cita incompleta (corregido) | Zn > ~15 %; capa y tapón; 316 "slightly more noble"; Al "corrodes rapidly"; PTFE. |
| S31 Loctite 243 TDS | OK | "not normally recommended for use on plastics… stress cracking". |
| S32 Loctite 425 TDS | OK | Cianoacrilato de baja resistencia; "locking metal and plastics fasteners"; −54 a +85 °C. |
| S33 Henkel Design Guide vol. 6 | OK | PET "Normally Compatible" con CA y acrílicos; ABS, ASA y PC agrietados por CA sin curar. |
| S34 Eastman Spectar TRS-236A | OK, salvo cita inventada y acetona (corregido) | DP-100; CA, acrílicos 2K, PU 2K, epoxi 2K; IPA:agua 50:50; 120 grit; MEK y cloruro de metileno; arandelas. |
| S35 hackaday 2025-01-30 | OK, salvo podio ambiguo (corregido) | "Some superglues seem to weaken PETG". Video de Cosel **no visto** (declarado). |
| S36 Sika 291i PDS | OK | Agua de mar; "must not be used to seal plastics that are prone to stress cracking (e.g. PMMA, PC, etc.)"; −50 a 90 °C. |
| S37 SKF HMS5 / HMSA10 | OK | 14 m/s; 0,03 MPa; −40 a +100 °C; Ra 0,2–0,8 (DIN) y 0,2–0,5 (ISO); ≥ 45 HRC; rectificado en plongée; H8. |
| S38 Trey Bull, prensaestopas | OK | 2–3 gotas/min; > 8–10 → servicio; surco en el eje por sobreapriete. |
| S39 bluerobotics T200 | OK | Cita "eliminates the need for shaft seals…"; 390 W a 16 V; solo 316 expuesto. |
| S40 LAPP SKINTOP ST-M | OK | IP66 / IP68 (5 bar / 30 min) / IP69; CR; −40 / −20 a +100 °C; M20: 6–13 mm (STR-M: 4–10); RAL 9005. |
| S41 Bulgin 900 | OK | 1,054 kg/cm², 10 m, 2 semanas; IP69K; EN 60068-2-52; 32 A (2–7 contactos), 10 A (10); 600 V (2–5 contactos); −40 a +85 °C; tapas. |
| S42 ASSDA marino | OK + agregado | 10–15 °C; ejes "usually galvanically protected"; "self drain"; "wash down". Agregado: "unsuitable for immersed applications where crevices exist". |
| S43 PMC12986719 | OK | SAE 15W-40; 7 días; 25 ± 2 °C; hexagonal al 30 %; −16,9 %; PETG+CF sin cambio significativo. |

### Lo que no pude cerrar
- Los ratings de compatibilidad de Parker los leí por posición de columna en el texto extraído del PDF. Revisé la alineación con dos encabezados, pero conviene confirmarlo en el PDF.
- La tabla 3 de S19 se extrajo desordenada: confirmé los extremos de los rangos, no cada fila.
- Gráfico de Cosel (S35) y video de Half-Baked-Research (S23): no vistos.
- Acetona contra PETG: sin una fuente que lo cuantifique. buscar: "Eastman copolyester chemical resistance acetone".
