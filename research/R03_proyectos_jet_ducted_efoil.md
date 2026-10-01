# R03: proyectos comparables (waterjets impresos, toberas y protectores, rim-driven, eFoil DIY y papers de hélices FDM)

Consulta: 2026-10-01. Autor: subagente de investigación P1.

Alcance: proyectos reales y papers que sirven para decidir entre tres opciones:
- la cola larga de P1 (motor seco arriba, correa HTD-5M, eje 316 inclinado, hélice comercial de ~7,8" a 10");
- un waterjet o una hélice entubada o rim-driven;
- el diseño del protector de hélice y la protección contra la corrosión.

Complementa a R02, que ya cubre fueraborda impresos, trolling, long-tail y la hélice PETG de Arcada.

## 0. Método y convenciones

**Etiquetas.**
- `[VERIFICADO: Sx]`: el dato está en la fuente Sx. Abrí la página en esta sesión y la URL completa está en §8.
- `[CALCULADO: …]`: cuenta mía con datos verificados o con entradas de `inputs.yaml` y `resultados/sizing_tablas.md`.
- `[ESTIMADO: base]` y `[SUPUESTO]`: lo que dicen.

**Cómo se leyó cada fuente.**

| Fuente | Cómo la leí |
|---|---|
| foil.zone (Discourse) | WebFetch, o la API `/t/<id>.json` (con límite de pedidos). |
| Endless Sphere | `curl` (WebFetch bloqueado). |
| MakerWorld | API `makerworld.com/api/v1/design-service/design/<id>`. |
| Thingiverse | Solo la `og:description` del HTML. |
| GitHub | `raw.githubusercontent.com`. |
| ScienceDirect, ResearchGate, MDPI | Responden 403. De dos papers de Elsevier en acceso abierto leí **solo el resumen** vía la API de DOAJ. |
| Tesis de Ladd (OSU, 1976) | PDF escaneado; extraje el texto con `pdftotext`. |
| YouTube | Solo verifiqué **títulos** vía oEmbed. **No vi el contenido de ningún video.** |

**Calidad de los datos.**
- Las cifras de foros son lo que declara cada autor.
- Las cifras de fabricantes (FluxJet, Minn Kota, Fliteboard, Torqeedo) son marketing o ficha técnica; no son ensayos independientes.
- Unidades: 1 lb = 0,4536 kg; 1 mph = 1,609 km/h; 1 kn = 1,852 km/h; 1" = 25,4 mm.

**Referencia de P1** (de `resultados/sizing_tablas.md`):

| Magnitud | Valor |
|---|---|
| R a 6 km/h (nominal / diseño) | 130 / 169 N |
| Empuje en el eje a crucero | 203 N |
| Hélice: J / η0 | ≈ 0,35 / 0,45 |
| Potencia al eje | 664 W |
| Potencia de batería (nominal / diseño) | 578 / 819 W |
| Bollard (avante / reversa) | 297 N / 94 N |
| Protector modelado como | aro no perfilado, holgura radial 10 mm, `thrust_loss_frac` = 0,06 |

---

## 1. Tabla resumen (proyectos y papers)

Relevancia para P1: **A** = alta, **M** = media, **B** = baja.

| # | Proyecto o paper | Tipo | Escala | Potencia y tensión | Resultado medido | Qué falló | Rel. |
|---|---|---|---|---|---|---|---|
| J1 | MaXi100000: jet de flujo mixto de 80 mm (Thingiverse 5247333) [S2][S3] | Waterjet impreso | Kayak, 1 p. | 6S (22 V), motor de 420 kV, ~2,5 kW | Estático: **4 kg a 270 W**. Kayak: **~12 km/h a ~2,5 kW**, sin llegar a planear | Tobera 2/3 sumergida; el autor duda de sus propias cifras | **A** |
| J2 | PRO-JET 80 (MakerWorld 3122772) [S4] | Waterjet impreso de 80 mm | SUP de 12', 90 kg en total | 26 V / 40 A / **1100 W** | **11,5 km/h**; 40 A a 10 km/h | Rotor contra estator a alta rpm (tuvo que llevar el gap a 3 mm); rozamiento rotor-carcasa | **A** |
| J3 | Endless Sphere: jet impreso de 80 mm + TP100 de 350 kV [S5] | Jetboard | Tabla | 8S, 180 A, ESC Maytech de 300 A | **78–80 lb (35–36 kgf) estáticos a 10 000 rpm** | — | M |
| J4 | Endless Sphere: jet impreso de 85 mm + outrunner rebobinado [S6] | Jetboard o foilboard | Tabla | 14S; Flipsky 75350 con VESC; 250 A de motor | **49,8 kgf** estáticos | Corte del VESC por saturación de duty (~89 %) a ~9100–9500 rpm (falla 18) | M |
| J5 | Ivan Miranda, Hackaday [S1] | Jet impreso en PLA | Bote a pedal | BLDC | Sin medición de empuje | Rodamientos sumergidos que requieren mantenimiento | B |
| J6 | boatdesign: "is a DIY jet drive feasible?" [S8] | Discusión técnica + impulsor ABS | — | — | Jet militar: de 42 a 35 kn en meses | **Palas de ABS que deflectaron**; desgaste del huelgo pala-carcasa; cavitación en toma, rotor y estator | **A** |
| J7 | RCLifeOn: bote jet impreso de 5 kW [S45] | Jet RC | <2 kg | 5 kW, 12S | — | Los jets DIY fallaron y usó una turbina comercial; **el acople impreso falló** | B |
| J8 | FluxJet: kayak con "jet" de motor anular [S13][S14] | Rim-jet comercial | Kayak de 40 kg | 12 V / 24 V, 1 kW | 12 V: 5,6–6,1 km/h a ~150 W. 24 V: 7,9–8,0 km/h a ~700 W. Su hélice de comparación: 7,1 km/h a 500–600 W | (marketing propio) | M |
| D1 | Puzzler300, tobera Kort impresa [S17] | Tobera impresa | Hélice de ROV de 40×57 mm | Outrunner de 700 kV | Avante: **3,60 → 6,00 lb (+67 %)**. Reversa: **2,03 → 2,00 lb (−1 %)** | Tobera "Rice" acortada con gap grande: "very ineffective" | **A** |
| D2 | Ladd 1976, tesis OSU [S10] | Protector "weed guard" vs tobera 19A corta | Bote planeador de 16 ft, hélice de ~8,8" [CALCULADO: 0,4"/4,5 %] | Fueraborda | Weed guard: **K_T −25 %** a J = 0,75. Tobera 19A: drag excelente, pero **K_Q +11,7 %**. Con álabes: **K_Q +23 %** | El weed guard no perfilado, con holgura del 4,5 % de D, es "dismal" | **A** |
| D3 | superlefax, foil.zone: anillo solidario a la hélice, impreso [S19][S20] | Rim-prop impreso (anillo que gira) | eFoil | 12S, 44–46 V | **38 A → 100 A a 20 km/h (×2,6)** | Rozamiento del anillo que gira | **A** (descarte) |
| D4 | Flo, foil.zone: ducto protector impreso para 6384 [S20] | Protector impreso | eFoil | — | "only good for protection … an effective brake"; pesa 550 g | Freno hidrodinámico | **A** |
| D5 | tunnelvision y pacificmeister, foil.zone [S21][S22] | Hélice con ducto | eFoil de 105 kg | 530 kV, reducción 6,67:1 | Con ducto: 32–35 A a 26 mph. "Big drop in efficiency above 12 mph". El ducto suma ~10 A | — | M |
| R1 | Wikipedia: rim-driven thruster [S23] | Referencia | 500 kW – 3 MW comerciales | — | — | Rozamiento en el gap rotor-estator; motor sumergido con bujes lubricados por agua | M |
| E1 | NextLevel, foil.zone: eFoil barato en el mar [S24] | Motor sumergido "estanco" | eFoil | — | — | **18 meses, 1–3 usos por semana en el mar, enjuagado tras cada uso**: eje agarrotado, óxido interno, fuga a masa del bobinado, ESC muerto | **A** |
| E2 | Hilo de mantenimiento del Flipsky 65161 [S25] | Inrunner con aceite y sello cerámico | eFoil | 6 kW | 2–3 temporadas: rodamientos ruidosos o trabados; mantenimiento anual | Tornillos inox trabados en aluminio por sal; agua entre sello y rodamiento | **A** |
| E3 | Sello del motor Lift/FR [S26] | Motor con aceite | eFoil | — | Probado a 9 psi en fábrica; rellenar aceite una vez por año | **Bombeo térmico**: motor frío + exterior caliente → succiona agua | **A** |
| E4 | Flipsky 7070 "waterproof" [S27] | Outrunner inundado | Foil-assist | — | Imanes sin recubrir oxidados tras **10 sesiones en el mar** con enjuague | Corrosión de imanes; "hardly be saved" | **A** |
| E5 | Impermeabilizar un outrunner [S28] | Outrunner inundado | eFoil | 6384 de 170 kV | Epoxi caliente (~60 °C), 2 capas | — | M |
| E6 | derekhearst/efoil-v2 (GitHub) [S33][S34] | eFoil DIY completo, agua dulce | 30 kg de equipo | 14S, 65161 | Despegue **4169 W** medido; FET a 47,4 °C como máximo | Fugas en la tapa (agua dulce) | M |
| P1p | OpenThruster (HardwareX 2025) [S35] | Propulsor *open-source* impreso en FDM (motor A2212 de 1000 kV) | Propulsor chico de ROV/USV | 12 V, 310 W | **18 N a 310 W**. Hélice SLA **+35 %** de empuje vs PLA FDM | Durabilidad "intentionally given lower priority" | M |
| P2p | Kiss-Nagy et al. 2024 [S36] | Hélices PLA entubadas de <100 mm (FSI) | <100 mm | — | Deformación no significativa salvo palas finas o skew/rake > 10° | — | M |
| P3p | Rochester ME205 2024 [S37] | Réplica impresa en PLA de una hélice Solar Splash | Bote solar | — | **−61 % de empuje a 300 rpm**. Flecha en FEA: **6,1 mm (PLA) vs 0,16 mm (Al)** | Deflexión de pala y acabado | **A** |
| P4p | Neşer et al. 2024, *Polymers* [S38] | Hélice FFF de HDPE + 15 % de fibra larga de carbono | Modelo de 257 mm, 5 palas | 16 rps | Flecha de punta: **89 mm** sin recubrir (J = 0,3) → 20 mm con prepreg | Flexibilidad excesiva | M |
| P5p | Singaravel et al. (IJLMM 2025) [S39] | Probetas FDM en agua de mar, 30 días | Probeta | — | Tracción **PETG −17–28 %**, PLA −26–35 %, ABS −15–25 %, Nylon −31–44 % | Hidrólisis | **A** |
| P6p | Chaudhary, Li, Matos 2023, *Results in Materials* [S40] | Termoplásticos FDM en agua de mar a alta temperatura | Probeta | — | Las piezas impresas difunden agua "extremely high" vs el material macizo; el módulo baja en todos | — | M |
| P7p | Arcada UAS 2025 [S41] (también en R02) | Hélice PETG de bow thruster, 6 palas | Bote, agua de mar | — | **+25 % de empuje**, sin cavitación, **4 meses** | **Pala fisurada**; percebes | **A** |

---

## 2. Waterjet frente a hélice abierta a 6–12 km/h

### 2.1 Datos medidos o declarados

| Caso | Condición | Empuje o velocidad | Potencia | g/W estático | Fuente |
|---|---|---|---|---|---|
| J1 jet 80 mm | Estático | 4 kgf | 270 W | **14,8** [CALCULADO] | [VERIFICADO: S2] |
| J1 jet 80 mm | Kayak, 1 p. | ~12 km/h | ~2,5 kW ("questionable") | — | [VERIFICADO: S2] |
| J2 PRO-JET 80 | SUP, 90 kg en total | 11,5 km/h | 1100 W (26 V × 40 A) | — | [VERIFICADO: S4] |
| J2 PRO-JET 80 | SUP | 10 km/h | 40 A a 26 V ≈ 1,04 kW [CALCULADO] | — | [VERIFICADO: S4] |
| J3 jet 80 mm impreso | Estático | 35,4–36,3 kgf | 8S × 180 A ≈ 5,3 kW [CALCULADO con SUPUESTO: los 180 A son de batería y 3,7 V por celda] | **≈ 6,6–6,8** | [VERIFICADO: S5] |
| J4 jet 85 mm impreso | Estático | 49,8 kgf | 14S; 250 A de motor (potencia no declarada) | — | [VERIFICADO: S6] |
| OpenThruster (propulsor chico de alta rpm, A2212 de 1000 kV) | Bollard | 18 N | 310 W | **≈ 5,9** [CALCULADO] | [VERIFICADO: S35] |
| Minn Kota Endura C2 30 (hélice grande y lenta) | Bollard (ficha) | 30 lb = 13,6 kgf | 12 V × 30 A = 360 W | **≈ 37,8** [CALCULADO; ficha del fabricante] | [VERIFICADO: S43] |
| FluxJet 12 V | Kayak de 40 kg | 5,6–6,1 km/h | ~150 W | — | [VERIFICADO: S13][S14] (fabricante) |
| FluxJet 24 V | Kayak | 7,9–8,0 km/h | ~700 W | — | [VERIFICADO: S13] (fabricante) |
| Su "prop motor" de 24 V | Kayak | 7,1 km/h | 500–600 W | — | [VERIFICADO: S13] (fabricante) |

**Lectura.** El empuje estático por vatio lo dicta la carga de disco. Un jet de 80 mm o un propulsor chico de alta rpm (OpenThruster, con un motor A2212 de 1000 kV) dan **6–15 g/W**. Un trolling de 30 lb (hélice grande y lenta) da **~38 g/W** según la ficha [CALCULADO]. Esto es coherente con la elección de P1: hélice grande y lenta con reducción por correa.

### 2.2 Teoría y fuentes técnicas

- Propeller vs waterjet: "The propulsive coefficient of a typical underwater propeller at 16 knots is about 65 percent while that of a waterjet at the same 16 knots would be only about 40 percent." [VERIFICADO: S9]
  - Según la misma fuente, el jet está "severely outclassed … up to about 25 knot", con una recuperación de presión en la toma de ~70 % [VERIFICADO: S9].
- Ladd (1976):
  - con un coeficiente de pérdidas del ducto K = 0,6–1,0, el rendimiento ideal del jet queda limitado a **0,5–0,6**;
  - "Open marine propellers can have real efficiencies approaching 0.80" [VERIFICADO: S10];
  - instalar un jet en un bote convencional "is a major undertaking" [VERIFICADO: S10].
- Fueraborda con pata jet (comercial):
  - "Approximately a 30% HP loss – multiply your motor HP by .7" [VERIFICADO: S11];
  - planeo "in the mid 20 MPH range and up";
  - casco mínimo de **14 ft × 48"** de fondo [VERIFICADO: S12];
  - **en desplazamiento** hacen falta "about 12 inches of clearance between the bottom of the jet and river bed to maneuver" [VERIFICADO: S12], es decir ~305 mm.
- eFoil: Fliteboard admite que "Flite Jet 2 consumes more power than propeller systems" [VERIFICADO: S15]. Los "jets" de Lift y JetWave son en realidad hélices entubadas con huelgo de punta muy chico ("It's a ducted fan!") [VERIFICADO: S25].

### 2.3 Cálculo para P1 a 6 km/h (T = 203 N, V0 = 1,667 m/s, ρ = 1010 kg/m³)

Modelo de cantidad de movimiento:
- jet: T = ρ·A_j·V_j·(V_j − V0), con potencia hidráulica = ρQ·[(1+K)V_j² − V0²]/2;
- hélice: disco actuador, η_i = 2/(1 + √(1 + C_T)).

Todo [CALCULADO: momentum ideal; K de [S10]; η de bomba 0,75 = ESTIMADO: impulsor chico impreso].

| Propulsor | V_j [m/s] | η ideal (K = 0) | η con K = 0,6–1,0 | P al eje con η_bomba = 0,75 |
|---|---|---|---|---|
| Hélice abierta D = 198 mm (7,8") | — | 0,59 | — | (sizing real: 664 W con η0 = 0,45) |
| Hélice abierta D = 254 mm (10") | — | 0,68 | — | — |
| Jet, tobera de 40 mm | 13,5 | 0,22 | 0,11–0,14 | 2,1–4,1 kW |
| Jet, tobera de 55 mm (PRO-JET) | 10,1 | 0,28 | 0,14–0,18 | 1,6–3,2 kW |
| Jet, tobera de 70 mm | 8,1 | 0,34 | 0,17–0,21 | 1,3–2,7 kW |
| Jet, tobera de 100 mm (Q = 47 L/s) | 6,0 | 0,44 | 0,21–0,27 | 1,0–2,2 kW |

**Conclusión.** A 6 km/h con 2 personas, un jet impreso necesita **1,6–6 veces** la potencia al eje de la cola larga [CALCULADO]. Con la batería de P1 (2304 Wh útiles), la autonomía de crucero caería de ~2,8–4,0 h a **<1 h** [CALCULADO]. Los datos empíricos lo confirman en orden de magnitud: un kayak de 1 persona necesitó ~2,5 kW para 12 km/h (J1) y una SUP ~1,1 kW para 11,5 km/h (J2), con cascos de mucha menos resistencia que un jon boat cargado.

### 2.4 Qué funcionó y qué falló en los jets impresos

**Funcionó:**
- impulsor de flujo mixto impreso "hot" para la adhesión entre capas, pared de 1,8 mm, rodamientos 608-2RS inox [VERIFICADO: S2];
- rodamientos inox híbridos cerámicos (S6000-2RS y S608-2RS) y eje inox de 8 mm [VERIFICADO: S4];
- motor 6374/6384 con epoxi en rotor y estator [VERIFICADO: S4].

**Falló o costó:**
- holgura dinámica: "3D-printed dynamic blades may hit the static blades at high speeds", así que tuvo que llevar la separación a 3 mm [VERIFICADO: S4];
- impulsor de ABS que deflectó bajo carga [VERIFICADO: S8];
- desgaste del huelgo, que baja la velocidad máxima de 42 a 35 kn [VERIFICADO: S8];
- acople impreso roto [VERIFICADO: S45];
- ESC de jetboard "blowed up due to water and low quality components" [VERIFICADO: S16];
- límite de duty del VESC a ~89 % con outrunner a alta rpm [VERIFICADO: S6].

**Arena, algas y fondo bajo.** La toma succiona del fondo y en desplazamiento necesita ~30 cm de agua libre [VERIFICADO: S12]. La ventaja "sin pata" solo aparece planeando. **No aplica a P1**, que es un jon boat de <2,5 m en desplazamiento.

---

## 3. Toberas Kort y protectores: ganancia o pérdida de empuje

| Fuente | Configuración | Resultado | Lectura para P1 |
|---|---|---|---|
| Wikipedia [S18] | Tobera 19A/37 (MARIN) | "Bollard pull can increase up to 30%". Pierden la ventaja a "about ten knots (18.5 km/h)". Algas u objetos se traban y son "much more difficult to clear". Peor gobierno en reversa | P1 a 6–12 km/h está en la zona donde la tobera ayuda [CALCULADO: 12 < 18,5 km/h] |
| Puzzler300 [S17] | Tobera impresa "arbitrary" (con curvatura) | Avante 3,60→6,00 lb (+67 %); reversa 2,03→2,00 lb (−1 %) [CALCULADO: % sobre lb de S17] | La ganancia es casi toda en avante; P1 necesita reversa |
| Puzzler300 [S17] | Tobera "Rice" de 6,4 cm | Avante 3,60→5,00 lb (+39 %); reversa 2,03→2,6 lb (+28 %) [CALCULADO] | Un perfil bidireccional es posible |
| Puzzler300 [S17] | Rice acortada a 3,1 cm, con gap grande | Avante 4,08 lb (+13 %); reversa 2,34 lb (+15 %) [CALCULADO]: "very ineffective" | **La holgura de punta manda** |
| Ladd 1976 [S10] | Weed guard de fundición, no perfilado, holgura 0,4" = **4,5 % de D** | **K_T −25 %** a J = 0,75; K_Q +2 % | El protector actual de P1 (aro no perfilado, 10 mm = **5 % de D** con 198 mm) es de esta familia |
| Ladd 1976 [S10] | Tobera 19A, L/D = 0,275, holgura **0,5 % de D** | Drag "excellent"; **K_Q +11,7 %** | Un aro perfilado y corto casi no penaliza, pero carga más al motor |
| Ladd 1976 [S10] | 19A + álabes de pre-rotación | **K_Q +23 %** | No poner rejas ni álabes delante |
| Ladd 1976 [S10] | Modelo de planeador de 11 500 lb y 265 hp | 34,6 kn abierto. Weed guard: 25,5 kn (**−26 %**). Tobera: 32,3 kn (**−7 %**). Tobera + álabes: 27,4 kn (−21 %). Canasta: drag **+50 %**, velocidad −1/3 | Ordena las opciones: perfilado ≫ aro romo ≫ jaula |
| Flo, foil.zone [S20] | Ducto protector impreso para eFoil | "It works as an effective brake" | Mismo mensaje que Ladd con el aro romo |
| superlefax, foil.zone [S22] | Ducto fijo en eFoil | ~+10 A en todo el rango de 20–30 km/h | Pérdida a velocidades más altas que las de P1 |
| tunnelvision, foil.zone [S21] | Hélice impresa en PC-Max con ducto (Kort o perfil puro) | "Both don't seem to generate a lot of drag". 32–35 A de crucero a 26 mph (≈ 42 km/h) | Un ducto bien perfilado es viable |

**Régimen de P1.**
- A crucero la hélice está muy cargada (J ≈ 0,35; C_T ≈ 2,9–4,7 [CALCULADO]).
- La tabla 3.1 de Ladd da la ganancia de rendimiento **ideal** de una tobera aceleradora, sin contar su drag [VERIFICADO: S10]:

  | C_T | Ganancia ideal |
  |---|---|
  | 1 | +2,0 % |
  | 2 | +4,4 % |
  | 4 | +7,8 % |
  | 10 | +13,8 % |

  Según Ladd, los remolcadores operan con C_T ≈ 10, los superpetroleros con ~4 y los planeadores con <1 [VERIFICADO: S10].
- Para P1 la ganancia ideal sería de **+6 % a +8,5 % a crucero** [CALCULADO: interpolación lineal]. Restado el drag de la tobera, el neto queda en ~0 a +5 % [ESTIMADO]. La ganancia grande (hasta +30 % [S18]) está solo en bollard, donde C_T → ∞.
- Las condiciones para que la tobera sume son: perfil hidrodinámico, holgura chica (Ladd: 0,5 % de D) y sin rejas.
- Con hélice comercial de tolerancia desconocida, cola basculante y PETG que flexa y pierde 17–28 % de resistencia en agua de mar, una holgura ≤1 % de D (≤2 mm) no es realista. Es más razonable apuntar a **4–6 mm** (2–3 % de D) [ESTIMADO].

---

## 4. Rim-driven: estado y por qué no sirve para P1

- **Teoría:** "friction losses in the gap between the rotor and its surrounding stator"; la desventaja es "manufacturing high-output submerged motors with water-lubricated bearings" [VERIFICADO: S23]. Los comerciales están entre 500 kW y 3 MW [VERIFICADO: S23].
- **DIY impreso:** la hélice con anillo solidario (equivalente hidráulico al rotor de un rim-drive) pasó de **38 A a 100 A a 20 km/h** [VERIFICADO: S19][S20]. Antes, un anillo protector pegado a las palas "did not work, it was too inefficient" [VERIFICADO: S20].
- **Comercial chico:** FluxJet usa un "ring-type electromagnetic motor surrounding the impeller". Las palas unidas a un anillo eliminan el gap donde se aloja la arena, y el kayak cuesta US$2999 [VERIFICADO: S14]. No hay ensayos independientes.
- **Hydromea DiskDrive 80:** no pude abrir la ficha técnica (403); `buscar: Hydromea DiskDrive 80 datasheet thrust current`. El concepto impreso en Printables 681590 advierte que la arena atasca el rim (ver R02, C5).
- **Para P1:** imanes y bobinado en agua salobre + arena de playa en el gap + rozamiento del anillo + bobinar un motor anular. **Se descarta.**

---

## 5. eFoil DIY: motores inundados o "estancos" en agua salada

| Caso | Medio y uso | Vida observada | Modo de falla | Fuente |
|---|---|---|---|---|
| eFoil chino Tame Billow | Mar, 1–3 por semana, enjuague con agua dulce tras cada uso, guardado seco | ~18 meses | Eje agarrotado, pintura ampollada sobre aluminio corroído, óxido interno, fuga a masa del bobinado; ESC muerto (US$365 + 185 de envío) | [VERIFICADO: S24] |
| Flipsky 65161 (aceite + sello cerámico) | Mar, ~3 años | Corrosión en el rodamiento superior; mantenimiento anual | Agua por el eje; "few drops of water past the seal". Rodamiento NSK 6001DDU (28×12×8 mm). Tornillos trabados por sal | [VERIFICADO: S25] |
| Flipsky 65161 (otro usuario) | 2 veranos | Rodamientos ruidosos y luego eje trabado tras una semana parado | Agua por el eje "just enough to kill the bearings" | [VERIFICADO: S25] |
| Lift/FR | Mar | Rellenar aceite una vez por año | Sello de un labio que se abre con el uso. O-ring de tapa gastado. **Bombeo térmico** (pod caliente al sol + agua fría → succiona agua). Juego axial >2 mm: no usar | [VERIFICADO: S26] |
| Flipsky 7070 "waterproof" (outrunner) | Mar, enjuague abundante | **10 sesiones** | Imanes sin recubrir oxidados. Otro usuario perdió varios motores por corrosión de imanes | [VERIFICADO: S27] |
| 6384, 10S, rider de 105 kg | Agua dulce | Varias temporadas | Los rodamientos originales se corroyeron y hubo que pasar a inox | [VERIFICADO: S29] |

**Prácticas que funcionan:**

| Práctica | Detalle | Fuente |
|---|---|---|
| Recubrir el estator | Tapar los rodamientos, calentar a ~60 °C, 2 capas de epoxi de alta temperatura con curado parcial de 4–6 h entre capas | [VERIFICADO: S28] |
| Si no se recubre | "A thin coat of normal epoxy works well" | [VERIFICADO: S28] |
| Alternativa a la epoxi | Epoxi térmica en el estator, o baño periódico en Corrosion-X | [VERIFICADO: S31] |
| Rodamientos | Inox o cerámicos | [VERIFICADO: S31] |
| Tras cada salida | Sacar el rotor, enjuagar rotor y estator, secar y lanolina | [VERIFICADO: S27] |
| Tornillos inox en aluminio | Pasta de zinc o Duralac. "Aluminium and stainless steel in salt water is a bad combination…" | [VERIFICADO: S25] |
| Lo que **no** hacer en esos tornillos | Loctite solo; el que lo usó terminó perforando tornillos | [VERIFICADO: S25] |
| Diagnóstico temprano | Medir resistencia entre las fases y la carcasa: debe ser circuito abierto | [VERIFICADO: S24] |
| VESC | Conformal coating (MG 422B) en ambas caras del PCB. "Salt air and humidity will corrode your VESC within weeks"; recubrir de nuevo cada año | [VERIFICADO: S32] |
| Ajustes de VESC | Regeneración de batería entre −10 y −20 A (−8 a −10 A en packs chicos). Reducción por temperatura desde 80 °C, corte a 100 °C | [VERIFICADO: S32] |
| Caja estanca | Respiradero de membrana (GORE PolyVent 316L, IP69K, niebla salina) en lugar de un "IP68" genérico | [VERIFICADO: S33] |

**Refrigeración.** Un outrunner inundado admite ">100A" contra su hoja de datos, gracias al agua [VERIFICADO: S31]. Es la única ventaja real frente al motor seco de P1. A la potencia de crucero de P1 (~0,7–0,8 kW) no hace falta: R02 ya registra motores secos con ventilación forzada.

**Comparación de energía (solo referencia).** Los mejores eFoil DIY gastan **41–52 Wh/km a 20–23 km/h** con ~95–105 kg [VERIFICADO: S30]. P1 de diseño gasta 136 Wh/km a 6 km/h [CALCULADO: sizing]. Son regímenes distintos (hidroala vs casco en la velocidad de casco); no es un argumento para P1.

---

## 6. Hélices y piezas FDM en agua: lo que dicen los papers

| Hallazgo | Número | Fuente |
|---|---|---|
| FDM (PLA) vs SLA vs metal (SLM AlSi10Mg) en un propulsor chico | SLA **+35 %** y SLM **+18 %** de empuje vs PLA; los motores varían ±11 % sin significancia estadística | [VERIFICADO: S35] |
| Réplica de hélice en PLA vs original | **−61 % de empuje a 300 rpm**; flecha en FEA de 6,1 mm vs 0,16 mm en aluminio; ~15 h por impresión | [VERIFICADO: S37] |
| Hélices PLA entubadas de <100 mm | La deformación no afecta K_T ni K_Q "except for extreme geometries (e.g., thin blades, skew, or rake more than 10°)"; la anisotropía de impresión cuenta | [VERIFICADO: S36] |
| Hélice FFF de compuesto, 257 mm, túnel de cavitación de Newcastle | Flecha de punta de 88,97 mm (J = 0,3) sin recubrir → 20,09 mm con prepreg; E de 3125 → 14 258 MPa | [VERIFICADO: S38] |
| PETG en agua de mar, 30 días | Tracción **−17 a −28 %** (artificial y natural) | [VERIFICADO: S39] |
| Termoplásticos impresos en agua de mar | Difusividad "extremely high" frente al material macizo; el módulo baja en todos, en proporción a la masa absorbida | [VERIFICADO: S40] |
| Hélice PETG en servicio real en el mar | +25 % de empuje y sin cavitación, pero **fisura** a los 4 meses y percebes; la pintura plástica no alcanzó | [VERIFICADO: S41] |
| Hélice PETG de eFoil impresa (agua dulce) | 160 mm, 0,12 mm de capa, **100 % de relleno**, epoxi + lijado + balanceo, 4–5 repuestos; **pasador de arrastre que actúa como fusible** | [VERIFICADO: S33][S34] |
| Toberas PLA (no marino) | Rompen por encima de **3 bar**, así que hubo que engrosar la pared localmente | [VERIFICADO: S42] |

**Implicación.**
- Una hélice impresa **no** sirve como hélice principal de P1. Rinde menos (rigidez y acabado), se fisura en agua salada y P1 ya usa una hélice comercial de metal o compuesto.
- Las piezas impresas sumergidas (protector, patín, carenado del tubo) deben dimensionarse con una pérdida de resistencia por agua de mar del orden del 30 % [ESTIMADO: límite superior de [S39] redondeado].

---

## 7. Qué aplica a P1, por arquitectura

| Arquitectura | Veredicto | Motivo principal (con números) |
|---|---|---|
| Cola larga, motor seco (candidata) | **Se mantiene** | La hélice grande y lenta da ~38 g/W contra 6–15 g/W de jets o hélices chicas rápidas [CALCULADO: §2.1]. Sin imanes en agua salada |
| Waterjet impreso | **Descartar** | 1,6–6× la potencia a 6 km/h [CALCULADO: §2.3]. Necesita ~30 cm de agua en desplazamiento [S12]. Pierde ~30 % aun planeando [S11]. Casco mínimo de 14 ft [S12] |
| Rim-driven impreso | **Descartar** | ×2,6 de corriente con anillo impreso [S19]. Rozamiento del gap [S23]. Arena e imanes |
| Hélice entubada (Kort 19A) | **Experimento para P2** | Ganaría bollard (≤30 % [S18]; +39–67 % en estático chico [S17]), pero la reversa no mejora con todas las toberas [S17] y las algas son difíciles de quitar [S18] |
| Pod sumergido inundado o con aceite | Penalizar | Vida de 10 sesiones a 3 años en el mar, siempre con mantenimiento anual [S24–S27] |

---

## 8. Fuentes abiertas en esta sesión

| Id | URL | Qué se leyó |
|---|---|---|
| S1 | https://hackaday.com/2019/04/30/3d-printing-a-water-jet-drive/ | Artículo |
| S2 | https://www.thingiverse.com/thing:5247333 | og:description |
| S3 | https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=GCxNEKDq0gM&format=json | Solo el título: "Electric Jet Kayak Project - with 3d printed jet pump" (rcandfun). También el título de `lBnK8atXRMY`: "15 HP Electric Jet Kayak - 3d printed (Update)". **Contenido no visto** |
| S4 | https://makerworld.com/en/models/3122772 (vía https://makerworld.com/api/v1/design-service/design/3122772) | Descripción y bitácora |
| S5 | https://endless-sphere.com/sphere/threads/electric-surf-board.41960/page-30 | Posts |
| S6 | https://endless-sphere.com/sphere/threads/diy-3d-printed-electric-waterjet-hitting-duty-cycle-limit-at-89-9-600-rpm-foc-cutout-fault-18-anyone-dealt-with-this.130965/ | Posts |
| S8 | https://www.boatdesign.net/threads/is-a-diy-jet-drive-feasible.55677/ | Posts |
| S9 | https://www.globalsecurity.org/military/systems/ship/systems/waterjet.htm | Artículo |
| S10 | https://ir.library.oregonstate.edu/downloads/cn69m652n | Ladd, D. M., *Power performance of planing boats with the effect of propeller selection and propeller guard design*, MSc OSU, junio de 1976 (texto con pdftotext) |
| S11 | https://www.outboardjets.com/faqs/will-i-lose-horsepower-if-i-convert-my-prop-to-a-jet/ | FAQ |
| S12 | https://www.outboardjets.com/boat-selection/ | Guía |
| S13 | https://fluxjetkayaks.com/blogs/the-current/fluxjet-speed-trials-12v-vs-24v-real-world-performance | Blog del fabricante |
| S14 | https://newatlas.com/boats-watersports/fluxjet-jet-drive-kayak/ | Nota |
| S15 | https://fliteboard.com/blogs/news/jet-vs-propeller | Blog del fabricante |
| S16 | https://forum.e-surfer.com/t/5-years-of-work-building-my-own-electric-jetboard/3816 | Posts |
| S17 | https://www.homebuiltrovs.com/rovforum/viewtopic.php?f=3&start=10&t=1464 | Posts de Puzzler300, dic. de 2014. Nota: el autor convirtió 5,00 lb como 2,10 kg; correcto: 2,27 kg |
| S18 | https://en.wikipedia.org/wiki/Ducted_propeller | Artículo |
| S19 | https://foil.zone/t/propeller-with-the-duct-integrated-vs-propeller-a-duct/3137 | Posts |
| S20 | https://foil.zone/t/any-prop-guard-duct-options-for-a-6384-motor/17461 | Posts |
| S21 | https://foil.zone/t/propellers-and-ducts/38 | Posts |
| S22 | https://foil.zone/t/superlefax-real-world-propeller-comparison/4093 | Posts |
| S23 | https://en.wikipedia.org/wiki/Rim-driven_thruster | Artículo |
| S24 | https://foil.zone/t/early-check-for-corrosion-water-leak/22446 | Posts |
| S25 | https://foil.zone/t/65161-maintenance/19330 | Posts 1–75 |
| S26 | https://foil.zone/t/lift-fr-motor-water-tightness/13103 | Posts |
| S27 | https://foil.zone/t/flipsky-7070-waterproof-motor-no-coating-on-magnets-issue/20192 | Posts |
| S28 | https://foil.zone/t/fastest-way-to-waterproof-outrunner/18515 | Posts |
| S29 | https://foil.zone/t/completed-efoil-build-with-6384-motor-on-10s-with-100-kg-rider/17237 | Posts |
| S30 | https://foil.zone/t/efoil-efficiency/9072 | Posts |
| S31 | https://e-surfer.com/en/blog/build-your-own-e-foilboard-diy-e-foil-part-2/ | Guía |
| S32 | https://pacificmeister.github.io/blog-efoil-vesc-guide.html | Guía |
| S33 | https://github.com/derekhearst/efoil-v2 (README y `docs/v1/efoil-3-propulsion.md` vía raw.githubusercontent.com) | Documentación |
| S34 | https://makerworld.com/en/models/433274 (vía API) | Descripción |
| S35 | https://pmc.ncbi.nlm.nih.gov/articles/PMC12337201/ | Fernandes, Sahoo, Kothari, *OpenThruster*, HardwareX 2025 |
| S36 | https://pp.bme.hu/me/article/view/23795 | Kiss-Nagy, Simongáti, Ficzere, *Periodica Polytechnica Mech. Eng.* 2024, doi 10.3311/ppme.23795 |
| S37 | https://www.hajim.rochester.edu/senior-design-day/wp-content/uploads/2024/05/GateD_FDR_Propeller_ME205.pdf | Informe ME205 (U. Rochester, 2024) |
| S38 | https://pmc.ncbi.nlm.nih.gov/articles/PMC11085731/ | Neşer et al., *Polymers* 2024 |
| S39 | https://doaj.org/api/articles/85a038b9c02e46399264ee8d54463e03 | Solo el resumen. Singaravel et al., *Int. J. Lightweight Mater. Manuf.*, doi 10.1016/j.ijlmm.2025.08.002 |
| S40 | https://doaj.org/api/articles/82cbb5ab0261477890163082f94ad69a | Solo el resumen. Chaudhary, Li, Matos, *Results in Materials* 2023, doi 10.1016/j.rinma.2023.100381 |
| S41 | https://www.arcada.fi/en/article/blog/2025-12-18/designing-and-3d-printing-bow-thruster-propeller | Blog académico |
| S42 | https://pmc.ncbi.nlm.nih.gov/articles/PMC12471428/ | Madejski, Buksa, Bryk, *Materials* 2025 |
| S43 | https://www.campingworld.com/minn-kota-endura-c2-30-trolling-motor-w-battery-meter---12v---30lb---30-365929.html | Ficha |
| S45 | https://hackaday.com/2019/11/14/5-kilowatts-in-a-3d-printed-jet-boat/ | Artículo |

**No abiertos** (quedan como búsqueda):
- `buscar: Hydromea DiskDrive 80 datasheet`
- `buscar: "Analysis Design Results of Kort Nozzle on Yamaha 15 HP Outboard"` (academia.edu devolvió 403)
- `buscar: "Long-term mechanical performance of 3D printed thermoplastics in seawater" texto completo`: el dato de "<1 % de absorción para PETG" que circula **no** lo verifiqué.

---

## Hallazgos que cambian el diseño

- **Waterjet y rim-drive salen de la matriz como opciones viables.**
  - A 6 km/h con T = 203 N, un jet de tobera de 40–100 mm tiene η ideal de 0,22–0,44, y de 0,11–0,27 con pérdidas de ducto K = 0,6–1,0. Una hélice abierta de 198–254 mm tiene 0,59–0,68 [CALCULADO: §2.3].
  - Eso son **1,0–4,1 kW al eje vs 664 W**, y la autonomía baja de ~2,8–4,0 h a <1 h con la misma batería.
  - En desplazamiento el jet necesita ~305 mm de agua para maniobrar [S12]; la ventaja en aguas poco profundas no existe para P1.
  - El rim impreso multiplicó la corriente ×2,6 (38 → 100 A) [S19].
  - → En `03_arquitectura.md`, puntuar jet y rim con la menor nota en autonomía y en arena.
- **El protector de `inputs.yaml` está subestimado.**
  - `guard.type: ring` con `radial_clearance_mm: 10` (5 % de D con hélice de 198 mm) es geométricamente el "weed guard" de Ladd (holgura 4,5 % de D, no perfilado), que perdió **25 % de K_T** a J = 0,75 [S10]. El `thrust_loss_frac: 0.06` es optimista.
  - Opción A (recomendada): rediseñar como **aro perfilado tipo 19A / NACA 4415**:
    - L/D ≈ 0,3;
    - holgura radial de 4–6 mm (2–3 % de D);
    - 2–3 brazos perfilados finos y **ninguna barra o reja delante del disco**: con álabes, Ladd midió K_Q +23 % y la canasta da +50 % de drag.
    - Presupuestar **K_Q +12 %** sobre el motor [S10].
  - Opción B: mantener el aro romo pero cargar `thrust_loss_frac` = 0,20–0,25.
  - En ambos casos, ampliar el barrido de sensibilidad de "pérdida por protector" a **0–25 %** (hoy es ±50 % sobre 0,06).
- **Ensayo obligatorio con el dinamómetro (bollard).** Medir empuje avante y reversa y la corriente de batería en tres configuraciones: sin protector, con aro perfilado y con aro romo, a 3 niveles de acelerador.
  - Puzzler300 mostró que la reversa puede quedar igual (−1 %) mientras el avante sube 67 % [S17]. P1 tiene una reversa de diseño de solo 94 N, así que esto hay que verificarlo, no suponerlo.
  - Criterio: aceptar el protector si la pérdida de empuje en avante a corriente igual es ≤10 % y la reversa es ≥90 N [SUPUESTO].
- **Tobera Kort como mejora, no como base.**
  - A crucero (C_T ≈ 2,9–4,7) la ganancia ideal es de solo **+6–8,5 %** antes de restar el drag [S10, tabla 3.1; CALCULADO]. El neto estimado es de 0 a +5 % de autonomía.
  - La ganancia grande (hasta +30 %) es en bollard [S18]. Los 6–12 km/h de P1 están debajo del límite de ~18,5 km/h [S18].
  - Pero:
  - exige una holgura de ~0,5 % de D (≈1 mm) [S10], incompatible con PETG que flexa, kick-up y una hélice comercial;
  - traba algas [S18].
  - → Pasarla a `07_roadmap_P2.md` como experimento con banco de ensayo.
- **Corrosión: aunque el motor de P1 esté arriba, tratarlo como en niebla salina.** Un motor "waterproof" perdió los imanes en 10 sesiones [S27]; uno de aceite y sello mató rodamientos en 2–3 temporadas [S25]; un eFoil enjuagado tras cada uso quedó agarrotado a los 18 meses [S24]. Para P1:
  1. Recubrir **estator e imanes** con 2 capas finas de epoxi (método de [S28]).
  2. Rodamientos del motor y de los soportes en inox o híbridos cerámicos (tipo S608/S6000-2RS, como en [S4]) **o** reemplazo anual en el checklist.
  3. Todo tornillo inox en aluminio con pasta de zinc, Duralac o Tef-Gel, nunca solo Loctite [S25].
  4. Agregar al checklist mensual la **prueba de aislamiento fase-carcasa con el multímetro**: debe dar circuito abierto [S24].
  5. VESC con conformal coating MG 422B en ambas caras y recubrimiento anual [S32].
  6. Cajas de ESC y batería con **respiradero de membrana 316L** contra el bombeo térmico [S26][S33].
  7. Regeneración de batería ≤ −10 A y reducción por temperatura desde 80 °C [S32]. Coincide con lo que R02 dice del BMS.
- **Agregar un factor por agua de mar a las piezas impresas sumergidas.** PETG pierde **17–28 % de tracción en 30 días** de agua de mar [S39]; en servicio, una pala PETG se fisuró a los 4 meses [S41].
  - Sumar a `materials.design_factors` un factor de **0,70** (o menor) para protector, patín, carenado y aleta.
  - Inspeccionar fisuras cada 5 salidas [SUPUESTO] y reponer las piezas sumergidas cada temporada [ESTIMADO].
- **No imprimir la hélice principal; la impresa queda solo como repuesto de emergencia.**
  - Una réplica en PLA dio **−61 %** de empuje [S37]; el PLA FDM rinde 26 % menos que el SLA [S35, CALCULADO: 1/1,35].
  - Si se imprime un repuesto: PETG al 100 % de relleno con capa de 0,12 mm, epoxi + balanceo [S33], palas gruesas, skew y rake ≤10° [S36], y el mismo pasador de corte.
- **La reducción por correa queda validada frente a la tracción directa de alta rpm.** El empuje estático por vatio de las soluciones chicas y rápidas (6–15 g/W: jets de 80 mm y el propulsor chico OpenThruster) es 2,5–6 veces peor que el de una hélice grande y lenta (~38 g/W según ficha) [CALCULADO: §2.1]. Mantener la reducción 3:1 y la hélice de ≥198 mm del sizing; no bajar el diámetro para facilitar el protector.
