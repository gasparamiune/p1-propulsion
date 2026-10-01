# 01 — Investigación

> Síntesis de los informes de [`research/`](research/) (R01–R09, consulta 2026-10-01). Cada informe trae
> el detalle, las URLs abiertas en esta sesión y, en R01–R06, una verificación adversarial.
> Etiquetas: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO]. Los números del diseño
> vigente salen de `resultados/*.json` (marcadores que regenera `docgen.py`). Cuando un informe recomendó
> algo distinto de lo que se terminó haciendo, se indica la decisión que prevaleció (D-nn, [decisiones.md](decisiones.md)).

## 0. Resumen

1. Los videos V1 y V2 son **bombas waterjet de PETG sin ningún ensayo**: no aportan datos de rendimiento, solo técnicas constructivas (R01).
2. Los comparables tripulados más parecidos hacen 5,6–7 km/h con 2 personas; planear un bote chico cuesta 7–14 kW (R02).
3. La **capacidad del bote** (~160 kg) es el riesgo n.º 1: la carga útil de diseño es <!--V:sizing.masses.payload_kg:.0f-->248<!--/V--> kg (R04).
4. R(6 km/h) = 95–150 N, banda estimada desde mediciones en botes de 2,4–2,75 m; con ~1 kW los eléctricos comerciales llegan a 7,6–8,0 km/h (R04).
5. Waterjet, rim-drive y pod sumergido salen de la matriz; la **cola larga con motor seco** no tiene sellos dinámicos ni electrónica bajo el agua (R03, R05, R06).
6. PETG impreso en agua salobre: −17 a −28 % de tracción en 30 días y fatiga ≈ 6 % de la UTS a 10⁷–10⁸ ciclos → nada impreso en la ruta de carga alterna (R05).
7. Eléctrica: LiFePO4, corte de emergencia por **contactor monoestable** con cordón cerrado con clip, fusible ≤ 7 in del borne, sistema flotante (R06).
8. Dinamarca: sin licencia, matrícula ni CE para este bote, pero **≤ 5 kn a < 300 m de la costa** (R07).
9. Sourcing: motor y ESC con link abierto solo desde Flipsky (China, +25 % IVA); la PPWR cortó los envíos a DK de al menos una tienda alemana; la hélice OEM chica es de 7,4", no de 7,8" (R08a, R08b).
10. Métodos: B-series, Holtrop (espejo), ITTC-57, Keller y Burrill verificados en fuente abierta; ninguna serie sistemática cubre un casco con L/∇^⅓ ≈ <!--V:sizing.hydrostatics.slenderness_L_over_vol13:.2f-->3.02<!--/V--> → calibrar R(v) por remolque (R09).

| Archivo | Tema | Fuentes | Verificación | Estado |
|---|---|---|---|---|
| [R01_videos.md](research/R01_videos.md) | Videos V1 y V2, canal y referencias cruzadas | 16 URLs (página, ASR, comentarios, storyboards) | Adversarial: 16 URLs reabiertas | Completo |
| [R02_proyectos_outboard.md](research/R02_proyectos_outboard.md) | Fuerabordas impresos, trolling, long-tail y surface drive | S1–S34 | Adversarial: 34 fuentes reabiertas, 50 afirmaciones | Completo |
| [R03_proyectos_jet_ducted_efoil.md](research/R03_proyectos_jet_ducted_efoil.md) | Waterjets, toberas, rim-drive, eFoil, papers de hélices FDM | S1–S45 | Adversarial: 43 ids / 46 URLs | Completo |
| [R04_bote_y_referencias.md](research/R04_bote_y_referencias.md) | Jon boats < 2,5 m, motores comerciales, R(v) medida | S1–S72 (61 URLs) | Adversarial: 61 URLs reabiertas; texto crudo en las 3 fuentes clave | Completo |
| [R05_materiales_sellado.md](research/R05_materiales_sellado.md) | Materiales FDM en agua salobre, O-rings, sellos, insertos | S1–S43 | Adversarial: 43 URLs reabiertas; 3 papers solo resumen | Completo |
| [R06_electrica.md](research/R06_electrica.md) | BLDC/VESC, corte de emergencia, baterías, normas, galvánica | 43 URLs | Adversarial: 43 URLs reabiertas; código fuente del VESC leído | Completo |
| [R07_dinamarca.md](research/R07_dinamarca.md) | Normativa DK y condiciones de Als Fjord | BEK, politi.dk, DMI, Copernicus | Estadística propia sobre datos crudos | Completo |
| [R08a_bom_electrica.md](research/R08a_bom_electrica.md) | Sourcing eléctrico con envío a DK | Tiendas DK/UE/CN | Precios con fecha 2026-10-01 | Completo |
| [R08b_bom_mecanica.md](research/R08b_bom_mecanica.md) | Sourcing mecánico con envío a DK | Tiendas DK/DE | Precios con fecha 2026-10-01 | Completo |
| [R09_metodos.md](research/R09_metodos.md) | Métodos de cálculo (resistencia, hélice, cavitación, eje, térmico) | S1–S31 | B-series comparada término a término | Completo |

## 1. Videos V1 y V2 (R01)

V1 = https://youtu.be/Z41FAXVMdKs · V2 = https://youtu.be/CkUiNuAfPL8 (canal "Clean Energy"). Se leyó: metadatos, descripción, pista ASR de V1 (709 s), todos los comentarios (V1 66/66, V2 56/56) y los storyboards de 320×180 px. No se pudo bajar el video completo (descarga trabada, después 429 / bot-check).

| Ítem | V1 ("3D Printed Jet Engine") | V2 ("3D printed waterjet engine") | Estado |
|---|---|---|---|
| Tipo real | Bomba **waterjet** que el autor llama "turbo jet" (ASR 00:55) | Waterjet con rampa de toma, estator, tobera y deflector | [VERIFICADO: R01 §3.2, §4.3] |
| Narración | Voz IA (lo admite el autor) | Sin narración ni subtítulos: **no existe transcripción** | [VERIFICADO: R01 §2] |
| Escala | Largo 61 cm, álabes 9 cm, eje Ø1 cm, abertura de toma 22 cm; 2–3 kg; 5 días de impresión | Sin medidas rotuladas | [VERIFICADO-visual: R01 §3.3]; masa y días por audio [VERIFICADO: R01 §3.2] |
| Material | PETG (respuesta del autor); eje "stainless" (02:07) **contradicho** por "aluminum shaft" (10:29) | Varilla M8 inox (~4:13); rodamientos S6900Z ×3 (~6:27) y S6801Z (~10:45); impulsor **metálico** de 4 álabes | [VERIFICADO: R01 §3–4] |
| Rodamientos | "Stainless" sin modelo (02:07); 2 en el estator (05:11) | S6900-ZZ 10×22×6 y S6801-ZZ 12×21×5 = AISI 440C en catálogo; grado real del video no verificado | [VERIFICADO: R01 §3.2, §4.3, catálogo minibearings] |
| Sellado / lubricación | Retenes en los extremos del eje, junta en el estator, grasa + aceite inyectado, toma de refrigeración desde la cámara de presión | Tubo que aloja un rodamiento, fijado con tornillo radial | [VERIFICADO: R01 §3.2; V2 visual §5] |
| Motor, batería, potencia | **Ninguno**; "7000 RPM" es una pregunta retórica; "no exact specs for now" | Ninguno | [VERIFICADO: R01 §1] |
| Rendimiento / ensayo | **Ninguno** (termina en "test runs … upcoming videos") | Termina con la unidad sobre la mesa | [VERIFICADO: R01 §5] |
| Fallas señaladas | Por terceros: empuje axial sobre PETG, toma chica, tobera frágil, porosidad, sin reversa | — | Comentarios: NO VERIFICADO |

**No verificado:** motor/KV/potencia, diámetro de tobera (se mide con calibre en V1 ~9:34 sin rótulo), origen de las tomas de lancha del inicio (marca de agua ajena), impresora usada, ensayo en agua de 8FAkgcQPcco (su descripción lo promete y el storyboard no lo muestra). Credibilidad del canal: baja (publica "Perpetual Engine" y "Unlimited Free Energy"; reclamo de STL pagos no recibidos) [VERIFICADO: R01 §6].

**Lecciones para P1:**
- Waterjet descartado como propulsión principal: a 6 km/h su η ideal es 0,27–0,44 contra 0,59–0,75 de una hélice de 7,8–9", es decir 1,6–2,4× la energía [ESTIMADO: R01 §7.2, disco actuador]. Además perfora el fondo y no admite basculación ni reversa sin cuchara.
- Sí se adoptan patrones de construcción: segmentos impresos con tirantes pasantes, **refrentado en torno** de las caras de unión, **empuje axial a metal** (crítica de @nachou1454) y rodamientos de bolas solo en zona seca.
- HDT del PETG Prusament 68 °C [VERIFICADO: R01, TDS Prusament] (65,7–75 °C según marca, R05) → ninguna pieza de PETG cargada cerca del motor.
- No comprar los STL del canal (20 USD por e-mail, sin repositorio).
- Referencia cruzada: el long-tail de DK The Welder (https://www.youtube.com/watch?v=zTpj2lwR2Zs) usa un BLDC **sumergido** en la punta del tubo; la ficha de AliExpress que muestra coincide con un Flipsky 56115 de 1,535 kg [VERIFICADO: R01 §6.1, ficha Flipsky; identidad NO VERIFICADA]. Masa en la punta y motor en agua salobre → no se adopta.

## 2. Proyectos comparables (R02, R03)

Las cifras de foro son las que declara cada autor; las de mejor calidad tienen wattímetro + GPS (MCDenny, ElectricKayak, Irie). Ningún dato sale del contenido de un video (solo se verificaron títulos).

| # | Proyecto | Arquitectura · bote · agua | Potencia | Resultado medido | Modo de falla | Lección para P1 | Etiqueta |
|---|---|---|---|---|---|---|---|
| R02-A1 | [Olly Epsom, Johnson 2 hp → BLDC](https://www.pbo.co.uk/expert-advice/build-diy-electric-outboard-motor-engine-60467) | Motor seco + pata original · dinghy inflable 2 p. · salada (Clyde) | 1 kW, 48 V | ~3 kn "generally"; canoa: > 10 km en < 2 h con 1 kWh | Controlador quemado; cargador incendiado; hélice medio afuera (bajó 150 mm); agua en la caja de batería | ESC con margen; altura de hélice regulable; cargador certificado; drenaje | [VERIFICADO: R02 [S1]] |
| R02-A2 | ["Infinity", Johnson 4W76M](https://endless-sphere.com/sphere/threads/outboard-to-brushless-conversion.52800/) | Motor seco + pata · inflable pesado 2 p. · dulce | C80100 130 kV, 24 V plomo | 7 km/h máx (GPS) | C8085 se recalentó a ~40 A; quitó el resorte del acelerador | Cordón de hombre al agua obligatorio; acelerador con retorno | [VERIFICADO: R02 [S3]] |
| R02-A4 | [Dominic Peters, E-Kayak](https://www.dominicpeters.ca/projects/ekayak.html) | Motor seco, eje vertical, cónicos 2:1 Al + PLA · kayak · dulce | 6374 168 kV, 12S | Crucero ~300 W, 1,5–2 h con ~500 Wh | Eje cortado en el cónico; prisioneros rotos; acelerador rozado con la hélice en arena → cónicos dañados | Pasador pasante, no prisionero; armado con acelerador en cero; pasador de corte; ESC sobre placa de Al (+10–15 °C) | [VERIFICADO: R02 [S6]] |
| R02-B1 | [ElectricKayak, boatdesign](https://www.boatdesign.net/threads/efficient-solar-powered-electric-kayak.52833/page-6) | Trolling → long-tail con eje flexible y motor seco · kayak · dulce | SK3-6374-149 kV, ESC 120 A | 5 km/h: 45 W (trolling optimizado) → 30 W (long-tail) | Eje flexible pandeó a 11 km/h (lo resolvió acortándolo o engrosándolo) | Ganancia firme −33 % [CALCULADO: 30/45]; eje rígido soportado | [VERIFICADO: R02 [S9]] |
| R02-B2 | [Sean d'Epagnier, 2 etapas HTD-5M](https://hackaday.io/project/174537-solar-powered-boat) | Motor seco + correas con poleas impresas · trimarán 33 ft | 6350 270 kV, 12 V LFP | 120 W → 2 kn | Chaveta en plástico "impossible"; polea patina; correa salta dientes (≤ 70 W) | Poleas de aluminio; tensor; ajuste de alineación | [VERIFICADO: R02 [S10]] |
| R02-B4 | [blisspacket, Endless Sphere](https://endless-sphere.com/sphere/threads/electric-boat-research.19115/page-2) | Long-tail directo, outrunners de RC · bote 15 ft | 2× 6374, 24 V, sin reducción | — | Quemó 2 motores 6374 y varios ESC sin llegar a plena potencia | Reducción y límite de corriente obligatorios | [VERIFICADO: R02 [S12]] |
| R02-B5 | [Irie, surface drive](https://www.boatdesign.net/threads/diy-electric-surface-drive.56617/page-2) | Eje inclinado con trim · aluminio 12', 1 p. · dulce | ME1004, 48 V | 16 mph a 8,9 kW; 25 mph a 13,7 kW | A 15° sin cup ventilaba por encima de 8 mph; a 20° duplicó la velocidad | Ángulo ≥ 20° y regulable; bocina lubricada por agua abajo + empuje arriba | [VERIFICADO: R02 [S14]] |
| R02-B6 | [Bazaki](https://endless-sphere.com/sphere/threads/my-new-electric-outboard-motor-hub-motor-silent-and-fast.53697/) | Correa por la pata · inflable en V | 90 V 80 A (~7 kW) | 20 km/h a 7–8 kW (con otro motor sobre la pata original) | Hub motor de la versión con correa quemado | Planear cuesta kW, no cientos de W | [VERIFICADO: R02 [S16]] |
| R02-C1 | [Anton, Crescent 5 hp](https://hackaday.com/2022/11/29/this-electric-outboard-conversion-makes-for-a-quiet-day-on-the-water/) | Pod sumergido con BLDC rebobinado | — | — | Entrada de agua (problema principal); "many epoxies … absorb water" | Motor seco arriba | [VERIFICADO: R02 [S17]] |
| R02-C2 | [Bare Naked Embedded](https://barenakedembedded.com/diy-electric-kayak/) | Motor estanco de eFoil + deriva impresa · kayak inflable · dulce probable | Flipsky 5062, 24 V 480 Wh | 2 p.: 5,6 km/h con ~170–185 W [CALCULADO]; 22,5 km en 3,5 h con 1 p. | Algas detuvieron el motor; VESC > 50 °C dentro de la caja de batería | ESC fuera de la caja de batería y sobre metal; protector que no haga de peine | [VERIFICADO: R02 [S18]] |
| R02-C3 | [Igor, Printables 1833248](https://www.printables.com/model/1833248-flipsky-85135-motor-75350-esc-outboard-mount) | Motor estanco en carcasa PETG | Flipsky 85135, 84 V | Sin datos | 2 hélices compradas desbalanceadas; carcasa de ~2 kg = 3 días de impresión | Balancear la hélice; segmentar piezas grandes | [VERIFICADO: R02 [S19]] |
| R02-D1 | [MCDenny, Minn Kota Endura 36](https://www.boatdesign.net/threads/efficient-electric-boat.27996/page-17) | Trolling + PWM + APC 10×6 + carenado · canoa 14' LWL, 300 lb | 12 V | 6,9 km/h: 330 W de serie → 190 W modificado | Puntas finas de la hélice de aeromodelo se mellan | Tubo con perfil; hélice robusta de trolling o fueraborda | [VERIFICADO: R02 [S22]] |
| R02-E1 | [Arcada UAS, hélice PETG](https://www.arcada.fi/en/article/blog/2025-12-18/designing-and-3d-printing-bow-thruster-propeller) | Hélice de bow thruster impresa · agua de mar | — | +25 % de empuje (otro diseño), 4 meses | Pala fisurada al desmontarla; percebes | Hélice comprada; piezas sumergidas impresas = consumibles inspeccionables | [VERIFICADO: R02 [S24]] |
| R02-R2 | [Backwater SWOMP E-Series](https://www.backwaterinc.com/swomp-e-series.html) | Long-tail eléctrico comercial, "Direct, no belts, no gears" | 56–72 V, hasta 200 A | Sin datos publicados | — | La arquitectura existe en el mercado (MV7: US$5650 con batería) | [VERIFICADO: R02 [S26]] |
| R03-J1 | [MaXi100000, jet de 80 mm](https://www.thingiverse.com/thing:5247333) | Waterjet impreso · kayak 1 p. | 6S, ~2,5 kW | Estático 4 kgf a 270 W; ~12 km/h a ~2,5 kW | El autor duda de sus cifras | Jet: 6–15 g/W contra ~38 g/W de una hélice grande y lenta [CALCULADO: R03 §2.1] | [VERIFICADO: R03 [S2]] |
| R03-J2 | [PRO-JET 80](https://makerworld.com/en/models/3122772) | Waterjet impreso · SUP, 90 kg | 26 V, 1100 W | 11,5 km/h | Rotor tocaba el estator a alta rpm (gap llevado a 3 mm) | El jet no sirve a 6 km/h con 2 personas | [VERIFICADO: R03 [S4]] |
| R03-D1 | [Puzzler300, tobera Kort impresa](https://www.homebuiltrovs.com/rovforum/viewtopic.php?f=3&start=10&t=1464) | Tobera sobre hélice de ROV de 40 mm | 700 kV | Avante +67 %; reversa −1,5 % (balanza de equipaje) | Tobera acortada con gap grande: "very ineffective" | La holgura manda; la reversa no mejora con todas las toberas (con la "Rice" sí, +28 %) → tobera a P2 | [VERIFICADO: R03 [S17]] |
| R03-D2 | [Ladd 1976, tesis OSU](https://ir.library.oregonstate.edu/downloads/cn69m652n) | Weed guard vs tobera 19A · planeador de 16 ft, hélice 8,75" | Fueraborda | Aro romo con holgura 4,5 % D: K_T −25 % a J = 0,75; tobera 19A: K_Q +11,7 % | — | Aro perfilado, holgura 2–3 % D, nada delante del disco | [VERIFICADO: R03 [S10]] |
| R03-D3 | [superlefax, anillo solidario](https://foil.zone/t/propeller-with-the-duct-integrated-vs-propeller-a-duct/3137) | Rim-prop impreso · eFoil | 12S | 38 A → 100 A a 20 km/h | Rozamiento del anillo | Rim-drive descartado | [VERIFICADO: R03 [S19]] |
| R03-E1 | [eFoil Tame Billow](https://foil.zone/t/early-check-for-corrosion-water-leak/22446) | Motor sumergido "estanco" · mar, 1–3 usos/semana | — | ~18 meses | Eje agarrotado, fuga a masa del bobinado, ESC muerto; **el usuario recibió una descarga** de la carcasa | Sistema flotante y prueba de aislamiento fase-carcasa | [VERIFICADO: R03 [S24]] |
| R03-E4 | [Flipsky 7070 "waterproof"](https://foil.zone/t/flipsky-7070-waterproof-motor-no-coating-on-magnets-issue/20192) | Outrunner inundado · mar | — | 10 sesiones | Imanes sin recubrir corroídos | Motor seco, enjuague, imanes protegidos | [VERIFICADO: R03 [S27]] |
| R03-P3p | [U. Rochester ME205](https://www.hajim.rochester.edu/senior-design-day/wp-content/uploads/2024/05/GateD_FDR_Propeller_ME205.pdf) | Réplica PLA de una hélice | — | −61 % de empuje a 300 rpm | Deflexión y acabado | No imprimir la hélice principal | [VERIFICADO: R03 [S37]] |

**Patrones que se repiten** [VERIFICADO: R02 §6; ids de R02]: unión eje–polea que patina (B2, A4) → pasador pasante y pasador de corte; motor/ESC quemado sin reducción o con sobrecarga (B4, B6, A2, A1) → reducción + límite de corriente; ESC encerrado que recalienta (R02-D2 "Current", C2) → placa de Al; agua en el motor sumergido (C1) → motor seco; algas (C2, R02-D2) → protector sin barras paralelas; ventilación con eje inclinado (B5) → ángulo y profundidad regulables; kick-up que se levanta en reversa (Torqeedo) → traba. **Energía:** cascos largos y finos gastan 6–50 Wh/km a 5–8 km/h; los medidos con 2 personas o carga equivalente quedan en 170–330 W a 5,6–6,9 km/h, con cascos más finos que un jon boat [CALCULADO: R02 §5].

## 3. Jon boats < 2,5 m y referencias comerciales (R04)

### 3.1 Casco y capacidad

Casi no hay jon boats de aluminio < 2,5 m en catálogo: los más chicos de Tracker, Lowe, Alumacraft y Princecraft miden 3,0–3,1 m. De aluminio < 2,5 m solo aparecieron el SeaCraft Mini Tinny 210 (2,10 × 1,16 m, 22 kg, 2 personas, chapa 1,2 mm, ≤ 35 kg en el espejo, pata corta) y el Horizon 240 Pathfinder (2,40 × 1,45 m, 50 kg, 2 personas, **pata larga**: espejo de ~508 mm) [VERIFICADO: R04 §A.1–A.2, S11, S72]. Un casco < 2,5 m queda fuera de la Directiva 2013/53/UE [VERIFICADO: R04 S26], por lo que puede no traer placa de carga [ESTIMADO: R04 §A.1]. → **Medir el bote real**, incluida la altura del espejo, y leer la placa (PENDIENTES P0.1–P0.2); `run_all.py` recalcula el largo de cola con lo medido (D-01).

| Parámetro | Rango | Valor de diseño P1 (D-01) | Etiqueta |
|---|---|---|---|
| LOA / manga | 2,03–2,50 m / 1,10–1,45 m | 2,44 / 1,20 m (D-01) | [VERIFICADO: R04 S11, S20, S72] + [ESTIMADO: D-01] |
| LWL | 1,7–2,3 m | 2,0 m | [ESTIMADO: R04 §A.4] |
| Peso del casco | 22–50 kg | 45 kg (D-01) | [VERIFICADO: R04 S11, S72] + [CALCULADO: R04 §A.4, 24–43 kg por área] |
| Altura de espejo | 330–430 mm (508 si pide pata larga); 381 mm (15") típico | 381 mm | [VERIFICADO: R04 S1, S13, S23, S72]; 330/430 [SUPUESTO: R04 §A.4] |
| Espesor de espejo | 1,2 mm chapa desnuda a 63 mm con taco | abrazadera 20–65 mm | [VERIFICADO: R04 S4, S31] |
| Peso máx. colgado del espejo | 18–28 kg; 35 kg tope absoluto | unidad completa <!--V:verify.unit_mass.cad_kg:.2f-->8.85<!--/V--> kg (CAD) contra 18 kg de `inputs.yaml` | [VERIFICADO: R04 S4, S11, S18] + [CALCULADO: verify.json] |
| Carga máx. de placa | 34–63 kg/m² → **100–185 kg** | 160 kg (USCG 33 CFR 183.35) | [CALCULADO: R04 §A.3–A.4] |

**Riesgo n.º 1.** La regla USCG da carga máx = (desplazamiento máx − peso del bote)/5 ≈ (845 − 45)/5 = 160 kg [CALCULADO: R04 §A.4]. P1 lleva <!--V:sizing.masses.payload_kg:.0f-->248<!--/V--> kg de carga útil contra <!--V:sizing.masses.capacity_kg:.0f-->160<!--/V--> kg (×<!--V:sizing.masses.capacity_ratio:.2f-->1.55<!--/V-->), con calado <!--V:sizing.hydrostatics.draft_m:.3f-->0.198<!--/V--> m y francobordo <!--V:sizing.hydrostatics.freeboard_m:.3f-->0.182<!--/V--> m [CALCULADO]. No se sube la placa por cálculo propio (D-16).

### 3.2 R(v) medida en botes chicos

| Fuente | Casco · carga | Motor | P eléctrica | v | Etiqueta |
|---|---|---|---|---|---|
| [Cruising World](https://www.cruisingworld.com/gear/gear-test-electric-motors-for-dinghy-engines/) | Inflable de 8 ft (2,44 m), carga no declarada | Spirit 1.0 Evo / Torqeedo 1103 | 500 W | 6,11 / 6,67 km/h | [VERIFICADO: R04 S61] |
| ídem | ídem | ídem, a fondo | ~1000 W [ESTIMADO: nominal, no leído] | 7,78 / 7,96 km/h | [VERIFICADO: R04 S61] |
| [MBY](https://www.mby.com/video/best-2-3hp-outboard-motors-electric-petrol-group-test-117786) | F-RIB 2,75 m, **2 personas** | Torqeedo 1103 C / Spirit 1.0 Plus | 1100 / 1000 W | 7,78 / 7,59 km/h | [VERIFICADO: R04 S62] |
| ídem | ídem, 2 personas | Nafta 2,3–2,5 hp (~1,8 kW al eje) | — | 8,1–9,3 km/h, **no planea** | [VERIFICADO: R04 S62] |
| [Boote](https://www.boote-magazin.de/en/motors/electric-motors/motors-test-electric-outboard-comparison/) | Inflables de 3,20 m | Torqeedo / Spirit | 186 / 200 W | 5,0 km/h | [VERIFICADO: R04 S60] |
| Tablas de fabricante | Spirit: aluminio de 12 ft, 1 persona, lago calmo; Torqeedo: bote sin especificar | Spirit 1.0 / Travel 1103 C | 125 / 153 W (Torqeedo [CALCULADO: Wh / tiempo]) | 5,6 / 5,5 km/h | [VERIFICADO: R04 S30, S34]; piden **2–3× menos energía** que las pruebas en 2,4–2,75 m (casco más largo y menos carga) [CALCULADO: R04 §C.2] |

Banda propuesta para el jon boat de 2,44 m con 2 adultos: **R(6 km/h) = 95–150 N** [ESTIMADO: R04 §C.3, interpolación de las filas 1–11 de §C.1]. El modelo vigente da <!--V:sizing.cruise.nominal.R:.0f-->135<!--/V--> N nominal y <!--V:sizing.cruise.design.R:.0f-->156<!--/V--> N de diseño [CALCULADO]: el nominal cae dentro de la banda y el de diseño queda apenas por encima (conservador). La V máx nominal de <!--V:sizing.vmax.nominal_vnom.V_kmh:.1f-->7.1<!--/V--> km/h queda algo por debajo de lo medido a ~1 kW en cascos de 2,4–2,75 m (7,6–8,0 km/h) [VERIFICADO: R04 §C.2].

### 3.3 Motores comerciales y comparación con P1

| Motor | P máx | Hélice / rpm | Empuje a punto fijo | η máx batería→propulsión | Precio | Etiqueta |
|---|---|---|---|---|---|---|
| ePropulsion Spirit 1.0 Evo | 1000 W, 48 V | 280 mm × 5,8", 1200 rpm | 316 N declarado; **290 N medido** (Spirit 1.0) | 55 % | 21.886 kr completo en DK: motor 9.199 + batería 1.276 Wh 9.390 + caña 2.578 + cargador 719 kr ([Watski](https://www.watski.dk/Epropulsion-Spirit-10-EVO-3hk-11cIP)); 2.549 € completo en DE | [VERIFICADO: R04 S31, S32, S33, S60] |
| Torqeedo Travel 1103 C | 1100 W, 29,6 V | 1450 rpm | 311 N declarado; **310 N medido** | 49 % | 2.249 € (test) | [VERIFICADO: R04 S34, S60] |
| Minn Kota Riptide Endura C2 55 | 620 W, 12 V | "Power Prop" | 245 N declarado | — | 5.499 kr | [VERIFICADO: R04 S42] |
| Haswing Protruar 1.0 | 600 W, 12 V | 9,3", 1250 rpm | 289 N declarado → FM 1,02–1,16: **imposible con η_motor ≤ 0,85** (con 0,9 pide FM 0,97: no creíble) | — | 429 € | [VERIFICADO: R04 S48–S49] + [CALCULADO: R04 §B.2] |

| Magnitud | P1 (diseño vigente) | Comerciales medidos | Etiqueta |
|---|---|---|---|
| Bollard avante | <!--V:sizing.bollard_fwd.T_horiz:.0f-->253<!--/V--> N | 290–310 N (0,28–0,29 N/W) | [CALCULADO] / [VERIFICADO: R04 S60] |
| Rendimiento total batería → R·V (crucero, diseño) | <!--V:sizing.cruise.design.eta_total:.0%-->30%<!--/V--> | 49–55 % máx | [CALCULADO] / [VERIFICADO: R04 S31, S34] |
| Energía de batería (P1 usable / comercial nominal) | <!--V:sizing.battery.E_usable_wh:.0f-->2304<!--/V--> Wh | 1.080–1.276 Wh | [CALCULADO] / [VERIFICADO: R04 §B.1] |
| Costo del sistema | <!--V:bom.total_eur:.0f-->2281<!--/V--> € (BOM con envíos, IVA y contingencia; sin equipo de seguridad, que suma hasta <!--V:bom.total_with_gear_eur:.0f-->2550<!--/V--> €) | 2.549 € (DE) a ~2.930 € (DK) el Spirit Evo completo | [CALCULADO: bom.py] / [VERIFICADO: R04 S33] + [CALCULADO: R04 §B.4, 21.886 kr / 7,4755] |

Lectura: P1 queda 3–10 % por debajo del empuje comercial medido y casi duplica la energía, pero su rendimiento total es bastante menor (hélice de trolling, η0 <!--V:sizing.cruise.design.prop_eta0:.2f-->0.41<!--/V-->; protector; eje a 25°) y su costo queda cerca del techo que fijó R04 ("bastante menos que ~2.550–2.930 €"). La ventaja de P1 es autonomía, basculación con pasador de corte y reparabilidad, no el precio.

## 4. Materiales FDM en agua salobre y sellado (R05)

### 4.1 PETG en agua salobre

- Absorbe ~0,3 % a saturación (estable a las 7–9 semanas) y < 1 % aun a 70 °C [VERIFICADO: R05 S11, S12]; las piezas impresas se saturan en semanas por porosidad [VERIFICADO: R05 S14] → diseñar con propiedades saturadas desde el día 1.
- Tracción **−17 a −28 %** tras 30 días en agua de mar (Nylon −31 a −44 %) [VERIFICADO: R05 S13].
- Entre capas: Z/XY = 0,38 (Prusament, 18 ± 4 MPa) a 0,84 (PolyLite) [VERIFICADO: R05 S1–S3].
- Fatiga: 0,8–1,9·10⁵ ciclos al 30 % de la UTS (R = 0,2) [VERIFICADO: R05 S16]; Basquin → ~8 % a 10⁷ y ~4 % a 10⁸ [CALCULADO: R05 §A6]. Con la MKP-32 (2 palas [ESTIMADO]) el paso de pala es <!--V:sizing.loadcases.LC6_ola_vibracion.f_blade_hz:.1f-->49.7<!--/V--> Hz → ~5·10⁷ ciclos en 300 h [CALCULADO]. R05 estimó 8·10⁷ con 3 palas; a esa vida el ajuste da 4,2 % y `f_fatigue` 0,06 quedaría ~1,4× alto (R05 §A6) → si la hélice medida tiene 3 palas, revisar `f_fatigue`.
- HDT a 1,8 MPa: 65,7–75 °C según marca; epoxi West 105/205: HDT 48 °C [VERIFICADO: R05 S1–S4, S21].
- Con la Ender-3 S1 (≤ 260 °C, abierta) solo son viables PETG y PETG-CF: PA-CF pide 280–300 °C, PC cámara de 70–110 °C, ASA cerramiento [VERIFICADO: R05 S5–S10; R08b §8].

### 4.2 Factores de diseño adoptados (D-29)

| Factor | Antes | Adoptado | Base | Etiqueta |
|---|---|---|---|---|
| f_water | 0,85 | **0,75** (peor caso estricto 0,72) | −17 a −28 % a 30 días | [VERIFICADO: R05 S13] |
| f_temp | 0,85 | 0,85 (R05 propone 0,85 hasta 40 °C y **0,70 hasta 50 °C**) | memoria técnica de copoliésteres | [ESTIMADO: R05 §A4] |
| f_process | 0,80 | 0,80 | validar con probetas P1.5 | [ESTIMADO] |
| f_creep (> 100 h) | 0,50 | **0,35** | creep no lineal desde ~50 % de la resistencia a 21 °C | [ESTIMADO sobre VERIFICADO: R05 S15] |
| f_fatigue (10⁷–10⁸) / LCF (10⁵–10⁶) | 0,30 | **0,06 / 0,15** | Basquin sobre S16 | [CALCULADO: R05 §A6] |
| f_z | 0,55 | **0,40** | Z/XY 0,38–0,45 | [ESTIMADO sobre VERIFICADO: R05 S1, S15] |
| T de servicio con carga | 60 °C | **50 °C**; comprar PETG con HDT(1,8 MPa) ≥ 70 °C | HDT 65,7–75 °C | [ESTIMADO: R05 §A4] |

Admisibles resultantes sin FS, con σ_XY = <!--V:est.allowables_MPa.sigma_xy:.0f-->47<!--/V--> MPa: corta <!--V:est.allowables_MPa.short:.1f-->24.0<!--/V--> MPa, sostenida <!--V:est.allowables_MPa.sust:.1f-->8.4<!--/V--> MPa, fatiga <!--V:est.allowables_MPa.fat:.2f-->1.44<!--/V--> MPa, LCF <!--V:est.allowables_MPa.lcf:.1f-->3.6<!--/V--> MPa [CALCULADO: structural.py]; piezas fuera de FS: <!--V:est.n_fail:d-->0<!--/V-->. Consecuencia: placa motriz y cartucho del rodamiento pasan a aluminio (D-25). Dos puntos abiertos: (1) σ_XY = 47 MPa es el TDS de Prusament; R05 recomienda 45 MPa y solo si la probeta propia P1.5 da ≥ 40 MPa → reescalar con el ensayo; (2) la temperatura de servicio admitida es 50 °C, pero f_temp 0,85 vale hasta 40 °C según R05 → las piezas que puedan pasar de 40 °C (caja ESC, capó, cuna junto a la placa) deben verificarse con 0,70 o medirse ≤ 40 °C en T2.3/T2.5 de 06.

### 4.3 Sellado

- **O-ring:** sello de cara con bridas a tope; Parker pide compresión estática 20–30 % (mín. 0,2 mm), llenado 60–85 % (óptimo 75 %) y cara de sello Ra ≤ 0,8 µm; Trelleborg Ra ≤ 1,6 µm [VERIFICADO: R05 S24, S26]. Con ±0,15 mm de tolerancia FDM, el cordón de 3,53 mm queda en 21–29 % y el de 2,5 mm en 19–31 % [CALCULADO: R05 §B3] → **NBR 70 Ø3,53 mm**, ranura 2,57–2,72 × 4,50–4,75 mm (D-23). Nunca sellos radiales en alojamiento impreso (excentricidad ≤ 0,05 mm).
- **Rugosidad:** PETG impreso Sa 10–24 µm según la capa [VERIFICADO: R05 S18] → refrentar en el torno (marcas circunferenciales: favorables para Parker; Trelleborg no admite surcos concéntricos visibles → pasada final fina) [VERIFICADO: R05 S24, S26], sellar contra la tapa de aluminio o epoxi + lijado. Juntas impresas en TPU: fallaron; PETG sin tratar fue de los peores en estanqueidad → epoxi interior en cajas estancas [VERIFICADO: R05 S22].
- **Lubricante:** grasa de silicona; EPDM nunca con grasa mineral (rating 4) [VERIFICADO: R05 S24].
- **Sellos de eje:** un retén radial pide eje ≥ 45 HRC y Ra 0,2–0,8 µm [VERIFICADO: R05 S37]; el 316 no se templa [ESTIMADO] → **cero sellos dinámicos sumergidos**; en la boca superior del tubo solo excluidor + drenaje. Un prensaestopas de empaquetadura gotea 2–3 gotas/min girando [VERIFICADO: R05 S38]: solo aplicaría a un paso de casco, que P1 no tiene.
- **Prensaestopas de cable:** LAPP SKINTOP ST-M IP68 (5 bar/30 min), junta CR anti-UV [VERIFICADO: R05 S40]; un cable redondo por prensaestopas, contratuerca y junta sobre cara refrentada [ESTIMADO]. P1 usa los Biltema M16/M20 IP68 (R08a §8).

### 4.4 Insertos y uniones

Tuerca A4 cautiva en bolsillo de fondo: 166 kg de arrancamiento contra 119 kg del inserto térmico (M3 en PETG) [VERIFICADO: R05 S27]. El latón con Zn > ~15 % se descincifica en agua salada [VERIFICADO: R05 S30]. Loctite 243 "is not normally recommended for use on plastics" [VERIFICADO: R05 S31]; Loctite 425 sí [VERIFICADO: R05 S32]. Limpiar con IPA:agua 50:50; MEK disuelve el PETG [VERIFICADO: R05 S34]; que la acetona lo ataque no está verificado, pero se evita por precaución [ESTIMADO: R05 §A9.2]. → D-18.

**No se pudo verificar:** adhesión epoxi–PETG impreso (lap shear), Ra lograble con epoxi + lijado, absorción de agua de la epoxi West, ficha de V-ring, compatibilidad de MS polímero con PETG, acople magnético, f_temp, equivalencia de 1000 h de UV de laboratorio con temporadas danesas, efecto de la acetona sobre el PETG y que la boquilla de serie de la Ender-3 S1 sea de latón [SUPUESTO] (R05 §A–B).

## 5. Eléctrica (R06, R08a)

### 5.1 Motor y VESC

- **Motor seco arriba:** un outrunner inundado exige desarmar y enjuagar rotor y estator **tras cada uso**, según instrucciones para el Maytech 6579 publicadas por un usuario de foil.zone (no atribuidas explícitamente al fabricante) [VERIFICADO: R06 §1.1]. El inrunner sellado FS65161 depende de un sello dinámico (punto único de falla); R03 documenta agua pasando ese sello en 2–3 temporadas [VERIFICADO: R03 S25].
- **VESC** (Flipsky 75100 V2.0, 14–84 V, 100 A) [VERIFICADO: R08a §2]. Defaults inútiles para un bote [VERIFICADO: R06 §2.4, código `mcconf_default.h` / `appconf_default.h`]: corte de batería 10,0/8,0 V (en 8S LFP poner 24,0/22,4 V [CALCULADO: 8 × 3,0/2,8 V por celda, ESTIMADO en R06]); `l_in_current_max` 99 A genérico y 100 A en el target 75_100 (bajar a ≤ 80 % del BMS: ≤ 80 A con BMS de 100 A); rampas 0,3/0,1 s (R06 pide ~0,5–1 s para no invertir el torque de golpe sobre la correa [ESTIMADO: R06 §2.6]; P1 lo resuelve en el MCU con rampa de subida de 1 s y 0,5 s en cero antes de invertir, 04_diseno/electronica/README.md §5); en ADC "Current Reverse Center" con `voltage_min` = 0,0 V un cursor cortado da **reversa máxima**.
- `KILL_SW_MODE` aparece recién en FW 5.03; Flipsky pide **apagar el filtro de fase** con FW ≥ 5.03 o el ESC se daña [VERIFICADO: R06 §2.2; R08a §2]. En el firmware oficial ≥ 6.00 el target 75_100 ya trae el filtro apagado, pero hay que **releerlo en VESC Tool** tras el asistente [VERIFICADO: R06 §2.2]. Timeout PPM 1000 ms → rueda libre + safe start [VERIFICADO: R06 §2.5].
- Hélice fuera del agua en modo corriente → embalamiento hasta `l_max_erpm` [ESTIMADO: R06 §2.6]; P1 fija un tope de <!--V:sizing.legal_speed.erpm_cap:.0f-->30164<!--/V--> ERPM, que además es el límite legal (D-30).

### 5.2 Baterías

| Propiedad | LiFePO4 | Li-ion NMC | LiPo (RC) | Etiqueta |
|---|---|---|---|---|
| Tensión nominal por celda | 3,20–3,30 V | 3,60–3,70 V | 3,6–3,7 V | [VERIFICADO: R06, Battery University]; LiPo [ESTIMADO] |
| Energía específica (celda) | 90–120 Wh/kg | 150–220 Wh/kg | 150–200 Wh/kg (LCO) | [VERIFICADO: R06, Battery University] |
| Pack comercial | ~128 Wh/kg | — | — | [CALCULADO: R06, LiTime 36 V] |
| Ciclos | ≥ 2000 (4000+ según LiTime) | 1000–2000 | 500–1000 | [VERIFICADO: R06] |
| Runaway, ensayo ARC 18650 al 100 % SOC | **no detectado**; T máx 239 °C | NCM811: inicio 147 °C, T máx 463 °C | LCO: inicio 180 °C, T máx 545 °C | [VERIFICADO: R06, [PMC10963544](https://pmc.ncbi.nlm.nih.gov/articles/PMC10963544/)] |
| Gas en runaway | 1,14 L/Ah | 2,4 L/Ah (NMC MH1) | — | [VERIFICADO: R06, PMC11927001] |
| BMS | Integrado en packs náuticos | Requiere BMS | RC: normalmente sin BMS | [ESTIMADO: R06, mercado] |

**Por qué LiFePO4:** el mismo estudio ordena el peligro "LCO > NCA > NCM811 >> LFP"; en un bote abierto la inmersión en agua salada es posible y el agua salada puentea bornes y puede disparar el runaway días o semanas después [VERIFICADO: R06 §4.2, fuente comercial]. La penalidad es masa: P1 lleva <!--V:sizing.battery.mass_kg:.1f-->22.0<!--/V--> kg de batería [CALCULADO]. LiPo descartada (sin BMS, pouch blanda). **Tensión:** R06 recomendó 12S (≤ 50 V de ISO 16315, MRBF 58 V, SW80 48 V); 16S LFP llega a 58,4 V y supera todo eso [VERIFICADO: R06 §4.3]. R08a mostró que 8S (29,2 V cargada) es compatible con los accesorios marinos baratos (portafusibles de 32 V, desconectadores ≤ 48 V) → **2 × Power Queen 12 V 100 Ah en serie**, <!--V:sizing.battery.E_nom_wh:.0f-->2560<!--/V--> Wh nominales, BMS 100 A (D-19); 12S queda documentado (D-28). Carga en frío: LiTime corta bajo 0 °C y la Power Queen 24 V 50 Ah bajo 5 °C [VERIFICADO: R08a §4]. Para la **PQ 12 V 100 Ah elegida**, R08a no encontró ni el corte en frío ni el grado IP ("—" / "buscar") → hasta leer la ficha: cargar solo en interior a ≥ 5 °C y tratarla como **no estanca** (caja cerrada y elevada) [SUPUESTO: criterio conservador].

### 5.3 Corte de emergencia fail-safe

| Elemento | Dato | Consecuencia en P1 | Etiqueta |
|---|---|---|---|
| Antichispa MOSFET | Caso de foro con un antichispa Buildkit Boards: "MOSFETs failed short-circuit" → queda siempre encendido; extrapolado a Flipsky por mismo principio | Solo arranque suave, aguas abajo del contactor | [VERIFICADO: R06 §3.1, [esk8.news](https://forum.esk8.news/t/right-as-i-finished-the-build-i-broke-the-anti-spark-switch/22247)]; Flipsky [ESTIMADO] |
| Cordón "normalmente abierto" de fueraborda de nafta | Clip arrancado cierra el contacto; cable cortado = motor sigue | No sirve | [VERIFICADO: R06 §3.2] |
| Cordón **cerrado con clip** | Clip afuera o cable cortado = circuito abierto | En serie con la bobina del contactor y la seta | [VERIFICADO: R06 §3.2] |
| Relé biestable / "remote battery switch" | Conserva el estado sin bobina; Albright lista su opción de enclavamiento como "Not fail safe" | No es fail-safe: pedir el contactor sin enclavamiento | [VERIFICADO: R06 §3.2, ficha SW80] |
| Contactor monoestable (clase Albright SW80) | 100 A; corte 600 A @ 48 V; bobina 7–13 W; apertura 50 ms con diodo, 8–20 ms con diodo + R | Contactor de emergencia (D-22) | [VERIFICADO: R06 §3.3, ficha SW80] |
| Watski "Dødmands kontakt universal" | Polos M cerrados con el clip puesto; 12 V – 15 A; 74 DKK | Se usa a 24 V con ≤ 0,6 A de bobina: ensayo T0 de 200 aperturas | [VERIFICADO: R08a §3] + D-33 |

Kill por software del VESC (`KILL_SW_MODE_ADC2_HIGH`, pull-up a 3,3 V) solo como redundancia: un cortocircuito por agua salada lo anula [VERIFICADO: R06 §2.5]. No hay contactor DC de servicio continuo con link abierto en DK/UE; los relés baratos no publican capacidad de corte DC [VERIFICADO: R08a §3] → la BOM lleva un contactor clase SW80 con bobina de 24 V (B-CONT, 90 € [ESTIMADO: R08a §3, 60–100 €]; buscar: Albright SW80 24V coil price EU). R06 detectó además que un contactor aguas arriba energiza el antichispa Pro ya enclavado en ON, contra la indicación de Flipsky ("Make sure the switch is off before applying power") [VERIFICADO: R06 §3.4] → P1 pone una resistencia de precarga en paralelo con el contactor y deja el antichispa como opcional (04_diseno/electronica/README.md §1).

### 5.4 Fusible, cable y normas

Fusible a ≤ 7 in del borne, o ≤ 72 in si el conductor va enfundado (ABYC E-11 11.10.1.1.1) [VERIFICADO: R06 §5.1]. El extracto de ABYC escribe "seven inches (175mm)" (7 in = 177,8 mm [CALCULADO]); D-21 y 06 usan 178 mm → **medir ≤ 175 mm** cumple las dos lecturas. El fusible no puede superar la ampacidad del cable (ABYC 11.10.2.3) [VERIFICADO: R06 §5.2]. P1: MIDI <!--V:sizing.fuse.rating_a:d-->80<!--/V--> A de 58 V (IMAXX midiOTO + portafusible HMD4-MG1-H) y cable de <!--V:sizing.cables.dc.section_mm2:d-->16<!--/V--> mm² (ampacidad <!--V:sizing.fuse.cable_ampacity_a:d-->100<!--/V--> A en el modelo) (D-21, D-33).

| Norma (como figura en R06) | Alcance verificado | Cláusulas citadas | Uso en P1 |
|---|---|---|---|
| [ISO 13297:2020](https://cdn.standards.iteh.ai/samples/69551/4f5da7667b4642e2880fe10a27cd4c70/ISO-13297-2020.pdf), 5ª ed. | CC ≤ 50 V en embarcaciones ≤ 24 m; no cubre propulsión eléctrica (→ ISO 16315) | 4.1 casco metálico no es conductor; 5.1 excepción para propulsión aislada; 5.5 caída ≤ 10 %; 8.1 baterías en lugar seco, ventilado, sobre el agua de sentina | Buena práctica (bote fuera de la RCD) |
| ISO 16315:2026, 2ª ed. | Propulsión eléctrica CC < 1500 V, ≤ 24 m | Índice: 5.1.2 Emergency stop, 6.3 monitoreo de falla a tierra en CC aislado; **texto no accesible** | Referencia; buscar: ISO 16315 emergency stop requirement text |
| ISO 16315:2016, def. 3.1 | — | "safety voltage" ≤ 50 V CC; reducirlo en ambiente mojado | Argumento contra 16S |
| [ABYC E-11](https://www.paneltronics.com/images/technical/E11Excerpts.pdf), extracto 2008 | Sistemas CA/CC en botes (edición vigente no verificada) | 11.10.1.1.1 fusible ≤ 7 in; 11.14.2.6 caída ≤ 3 % / 10 %; Tabla VI-A de ampacidad | Fusible y cable |
| RCD 2013/53/UE | Cascos 2,5–24 m; "propulsion engine" = combustión | — | P1 fuera de alcance |

### 5.5 Galvánica

En agua de mar: inox 316 pasivo −150 mV, activo (en grietas o tubos sin oxígeno) −550 mV, aluminio marino −820 mV, zinc −1050 mV; más de 200 mV de diferencia exige medidas [VERIFICADO: R06 §6.1, Gerr]. En salobre conviene ánodo de **aluminio**; el magnesio sobreprotege el aluminio [VERIFICADO: R06 §6.3]. R06 recomendó sistema flotante (BAT− sin conexión al casco), aislar eje y casco y un ánodo de Al junto a la hélice. P1 adoptó lo primero y **no** el ánodo: grupo giratorio todo 316, tubo de Al aislado por bujes en portabujes PETG, tornillería A4 con Tef-Gel (D-36). **Riesgo que D-36 no cubre:** el 316 encerrado en un tubo o bajo bujes pasa a "activo" (−550 mV) y sufre picado [VERIFICADO: R06 §6.2, Gerr]; ASSDA lo declara "unsuitable for immersed applications where crevices exist", con corrosión en rendija desde 10–15 °C, y los ejes de 316 "are usually galvanically protected" [VERIFICADO: R05 §A12, S42]. La verificación de R05 pasó el ánodo de "considerar" a **obligatorio, o dúplex 2205** [ESTIMADO: R05 Hallazgos]. Es corrosión en rendija, no galvánica: el aislamiento no la evita. Mínimo exigible: cola fuera del agua y enjuagada tras cada uso, e inspección de picaduras bajo los bujes cada temporada (06).

## 6. Normativa danesa y condiciones de Als Fjord (R07)

Todo "a confirmar con la autoridad local" (Syd- og Sønderjyllands Politi, Søfartsstyrelsen, Sønderborg Havn).

| Tema | Regla | ¿Aplica a P1? | Etiqueta |
|---|---|---|---|
| Registro | Obligatorio desde 20 BT; < 20 BT no se puede registrar | No | [VERIFICADO: R07 §1.2] |
| Licencia (speedbådsbevis) | Casco < 4 m "planende" (fondo plano en el tercio de popa lo es): licencia con ≥ 19 kW / 25 HK | No: motor 3,5 kW máx. de catálogo [VERIFICADO: R08a §1]; pico de batería <!--V:sizing.vmax.nominal_vnom.P_bat:.0f-->1323<!--/V--> W [CALCULADO] | [VERIFICADO: [Søfartsstyrelsen](https://www.soefartsstyrelsen.dk/fritidssejlads/beviser-og-certifikater/speedbaadsbevis)] |
| **Velocidad** | ≤ 5 kn (9,26 km/h) a < 300 m de la costa, todo el año, toda motorbåd (§4); excepción para maniobrar con seguridad | **Sí, siempre** | [VERIFICADO: [Sejladsreglement](https://politi.dk/politikredse/syd-og-soenderjyllands-politi/sejladsreglement)] |
| Chalecos | Llevar uno por persona, CE o ratmærke, talla y peso correctos; usarlo no es obligatorio | Sí; política: puesto y con cuello | [VERIFICADO: [BEK 765/2024 §5](https://www.lovtidende.dk/api/pdf/242869)] |
| Equipo de seguridad | "i fornødent omfang": sin lista cerrada | Sí (criterio del patrón) | [VERIFICADO: BEK 765/2024 §4] |
| Kill cord | No figura en BEK 765/2024; RCD 5.1.6 solo para motores de combustión con caña | Requisito del proyecto | [VERIFICADO: R07 §1.2] |
| CE / RCD | Cascos 2,5–24 m; excluye construcción propia no vendida en 5 años | No | [VERIFICADO: R07 §1.2] |
| Seguro | Obligatorio solo para speedbåde y vandscootere | Opcional (revisar seguro de hogar) | [VERIFICADO: R07 §1.2] |
| Alcohol | 0,50 ‰ fijo solo para botes con certificado; prohibición general de navegar sin plena capacidad | Política 0,0 ‰ [SUPUESTO] | [VERIFICADO: R07 §1.2] |
| Luces | Regla 23(d)(ii): < 7 m y ≤ 7 kn → luz blanca todo horizonte | Solo si oscurece; política: solo de día | [VERIFICADO: [COLREG](https://www.navcen.uscg.gov/navigation-rules-amalgamated)] |
| Señal sonora | Regla 33(b): < 12 m, algún medio eficaz | Silbato | [VERIFICADO: R07 §1.2] |
| Puerto, Natura 2000, orilla alemana | No verificados | buscar: Sønderborg Havn havnereglement fart knob; vildtreservat Nybøl Nor sejlads | — |

| Condición (Als Fjord / Sønderborg) | Dato | Etiqueta |
|---|---|---|
| Temperatura del agua (media diaria, Fynshav 2015–2025) | may 11,4 · jun 15,7 · jul 17,7 · ago 18,6 · sep 17,2 · oct 13,3 °C; < 15 °C en ≥ 90 % de los días de oct–may; máx. diario 23,3 °C, instantáneo 26,4 °C | [VERIFICADO: R07 §3.1, DMI, cálculo propio] |
| Salinidad superficial | Media mensual 13,6–17,6 PSU; p10–p90 11,3–20,5 PSU; densidad 1010–1016 kg/m³ | [VERIFICADO: R07 §2, Copernicus BAL] + [ESTIMADO: EOS-80] |
| Viento may–sep, de día | ≤ 6 m/s el 57 % (Kegnæs Fyr, expuesto) a 79 % (Sønderborg Lufthavn) de las horas; con > 8 m/s domina SW (32,7 %) y W (18,6 %) = viento de tierra en la costa E de Als | [VERIFICADO: R07 §4.1, DMI] |
| Ola | Als Fjord con 6 m/s: Hs ≈ 0,15–0,3 m, Tp 1,2–1,8 s, λ ≈ 2–5 m (≈ eslora); Sønderborg Bugt may–sep de día: p50 0,26 m, p90 0,64 m | [ESTIMADO: CEM, fetch] / [VERIFICADO: R07 §4.2, Open-Meteo] |
| Nivel del mar (Sønderborg Havn) | p1 −52 cm, p99 +75 cm; extremos −158 / +210 cm; marea astronómica despreciable | [VERIFICADO: R07 §4.3, DMI] |
| Corriente en Als Sund | Sin dato abierto; el proyecto usa 0,5 m/s | [ESTIMADO] |
| Viento de proa 6 m/s a 6 km/h | F_aire ≈ 27 N (18–29 % de R) → empuje +45–55 % con ola | [ESTIMADO: R07 §4.5] |

**Temporada y salida** [SUPUESTO: R07 §3.4]: 15 jun – 15 sep sin traje térmico; viento medio ≤ 6 m/s (≤ 5 m/s de tierra), ráfaga ≤ 10 m/s, Hs ≤ 0,3 m, solo de día con regreso ≥ 1 h antes del ocaso, chaleco puesto, cordón conectado y alguien en tierra que conoce el plan. Con agua < 15 °C la apnea voluntaria cae a segundos y la incapacitación llega en 2–30 min [VERIFICADO: R07 §3.3]. **Equipo mínimo:** 2 chalecos con cuello, cordón del kill switch al chaleco, remos o pagaya, ancla con cabo ≥ 3× profundidad, achicador, teléfono en bolsa estanca (112) o VHF, silbato, luz blanca todo horizonte, manta térmica (D-35).

## 7. Sourcing (R08a, R08b)

### 7.1 Logística a Sønderborg

| Hecho | Consecuencia | Etiqueta |
|---|---|---|
| Kugellager-Shop dejó de enviar a DK por la **PPWR** (vigente desde agosto de 2026) | Rodamientos inox de esa tienda solo vía paketshop en Flensburg/Harrislee [SUPUESTO] | [VERIFICADO: [kugellager-shop.net](https://www.kugellager-shop.net/kugellager-versand/)] |
| Dold Mechatronik envía a Europa; 3DJake lista DK; Watski entrega en 1–3 días hábiles | Poleas, correa y PETG sin problema | [VERIFICADO: R08b §1] |
| Flipsky (CN): precio y envío sin impuestos; su FAQ sugiere sub-declarar | IVA 25 % + envío [ESTIMADO 45 €] → el trío motor/ESC/antichispa pasa de 196 € a ≈ 302 € [ESTIMADO]; **declarar el valor real** | [VERIFICADO: [flipsky.net](https://flipsky.net/pages/about-tariffs)] + D-32 |
| LiTime (almacén alemán) y Power Queen (tienda .de) envían gratis a la UE | Batería y cargador con IVA incluido | [VERIFICADO: R08a §0] |

### 7.2 Productos elegidos

| Bloque | Producto | Precio 2026-10-01 | Etiqueta | Decisión |
|---|---|---|---|---|
| Motor | Flipsky 6374 Battle Hardened 190 KV (0,98 kg, 85 A, 3500 W, eje 8 mm) | 87 USD | [VERIFICADO: R08a §1] | D-32 |
| ESC | Flipsky 75100 V2.0 (14–84 V, 100 A, BEC 5 V 1 A) | 88 USD | [VERIFICADO: R08a §2] | D-32 |
| Antichispa | Flipsky Antispark Pro, caja de Al (3–14S) | 48 USD | [VERIFICADO: R08a §3] | D-22 |
| Batería | 2 × [Power Queen 12 V 100 Ah](https://www.ipowerqueen.de/products/power-queen-12-v-100-ah-lifepo4-deep-cycle-batterie) en serie | 475,18 € el par (186 €/kWh) | [VERIFICADO: R08a §4] | D-19 |
| Cargador | Power Queen 29,2 V 20 A (salida Anderson) | 102,99 € | [VERIFICADO: R08a §5] | D-19 |
| Protecciones | midiOTO 80 A 58 V + HMD4-MG1-H; desconectador Biltema AFD (12–48 V, 275 A, IP65); cordón Watski; Anderson SB50 | 2,52 + 12,55 €; 159 DKK; 74 DKK; 90 DKK c/u | [VERIFICADO: R08a §3, §6, §8] | D-33 |
| Contactor de emergencia | Clase Albright SW80, NA, bobina 24 V continua, sin enclavamiento | 90 € [ESTIMADO: R08a §3] | Ficha [VERIFICADO: R06 §3.3]; producto con link: no hallado | D-22 |
| Hélice | [Minn Kota MKP-32 Weedless Wedge 2](https://www.watski.dk/MKP-32-propel-wedges-2-11cE4), con tuerca y pin | 485 kr | [VERIFICADO: R08b §5]; D, paso y bore [ESTIMADO] | D-06 |
| Bujes sumergidos | [igus iglidur H370SM-1618-20](https://www.igus.eu/product/35?artNr=H370SM-1618-20) (igus lo recomienda bajo agua) | 3,10 € c/u | [VERIFICADO: R08b §3] | D-38 |
| Rodamientos (zona seca) | 6202-2RS acero al cromo, Biltema | 36,90 kr c/u | [VERIFICADO: R08b §3] | D-37 |
| Transmisión | Poleas HTD-5M 15 mm Dold (<!--V:sizing.selection.z_motor:d-->20<!--/V--> T : <!--V:sizing.selection.z_shaft:d-->48<!--/V--> T) + correa de <!--V:sizing.mech.belt.length_std_mm:.0f-->425<!--/V--> mm | 20 T: 10,00–13,90 €; 40 T: [ESTIMADO] | [VERIFICADO: R08b §4] | D-39 |
| Antigalvánico | Tikal Tef-Gel 10 g | 16,99 € | [VERIFICADO: R08b §6] | D-36 |
| Filamento | eSUN PETG+ 1 kg (BOM); alternativa PolyLite PETG 1 kg | 15,99 € / 19,99 € | [VERIFICADO: R08b §8]; HDT: eSUN **no verificada**, PolyLite 75 °C [VERIFICADO: R05 S2] | D-29 exige HDT(1,8 MPa) ≥ 70 °C: comprar eSUN solo si su ficha lo declara; si no, PolyLite |

### 7.3 Descartados y no encontrados

| Producto | Motivo | Etiqueta |
|---|---|---|
| Rodamientos "inox" S6201–S6203 / S7202 | Son **AISI 420**, no 316, y la tienda no envía a DK | [VERIFICADO: R08b §3] |
| Eje 1.4301 (V2A) | No sirve sumergido en agua salobre; barra 316 Ø14–16 no hallada en tienda abierta → metalgrossist | [ESTIMADO: R08b §2] |
| Tubo-pata 316 Ø25 × 1,2 + ánodo de collar Ø25 | El tubo cede con el momento de impacto → tubo Al 6061-T6 Ø40×3 (D-09); sin ánodo (D-36) | [VERIFICADO: R08b §2, §6] + [CALCULADO: D-09] |
| Hélice Tohatsu 309B64107-0 (7,4" × 6, Al) | Bore y pasador no publicados; con bore ~12 mm el asiento no llega a FS 2 | [VERIFICADO: R08b §5] + D-06 |
| Hélices Al 7½–7¾" de Watski | 9–12 estrías, sin pasador de corte | [VERIFICADO: R08b §5] |
| Relés FREI FRC3 70 A / Zettler AZ160; contactor Lewmar 24 V | Sin capacidad de corte DC publicada / servicio de molinete | [VERIFICADO: R08a §3] |
| Portafusibles ANL Biltema y Blue Sea AMI/MIDI | 32 V: cerrarían la puerta a 12S | [VERIFICADO: R08a §6] |
| LiTime 24 V 50 Ah | BMS de 50 A y 1.280 Wh: no cumple energía | [VERIFICADO: R08a §4] + D-19 |
| Cargador Biltema 12/24 V | LiFePO4 solo en el modo 12 V | [ESTIMADO: lectura de la ficha, R08a §5] |
| Insertos ruthex | Latón: solo zona seca | [VERIFICADO: R08b §7] |
| ASA y filamentos cargados | Sprite de serie ≤ 260 °C; ASA pide 260 ± 5 °C, cama 110 °C y cerramiento | [VERIFICADO: R08b §8] |
| Maytech MTO6374 | Menos corriente; eje de 26 mm de saliente | [VERIFICADO: R08a §1] + D-32 |

**No encontrados con link abierto:** barra 316/316L Ø14–16, contactor DC de servicio continuo en DK/UE, hélice 10 × 8 de 3 palas con pasador, barra de POM-C, inserto roscado inoxidable, spring plunger inox, tubo de fibra pultruido (todos con "buscar:" en R08a y en R08b §11). BOM vigente: <!--V:bom.total_eur:.0f-->2281<!--/V--> € ≈ <!--V:bom.total_dkk:.0f-->17052<!--/V--> DKK con envíos, IVA y contingencia; <!--V:bom.verified_frac_of_subtotal:.0%-->71%<!--/V--> del subtotal con precio verificado [CALCULADO: bom.py].

## 8. Métodos de cálculo (R09)

| Método | Estado | Uso en P1 | Etiqueta |
|---|---|---|---|
| Fricción ITTC-1957 | Verificado (ya incluye ~12 % de factor de forma) | R_F de `hydro.py` | [VERIFICADO: R09 S18] |
| ΔC_F y C_A de la ITTC-78 | Verificados, pero **dan ΔC_F < 0 con L = 2 m** (−0,00127 a 6 km/h) | No se usan: `delta_cf` queda como calibración | [VERIFICADO: R09 S20] + [CALCULADO] |
| Factor de forma Holtrop 1984 (C_stern "pram" −25) | c₁₄ y tabla verificados; exponentes con OCR dañado; da 1+k ≈ 1,47 extrapolado | P1 usa k = 0,20 (1+k = 1,2) [ESTIMADO], dentro de 1,0–1,5 | [VERIFICADO parcial: R09 S16] |
| (1+k) = 1,0 para lanchas con espejo (ITTC HSMV); Prohaska no vale con espejo mojado | Verificados | El remolque mide R(v) **total** | [VERIFICADO: R09 S18, S19] |
| Espejo sumergido Holtrop-Mennen 1982 (R_TR, c₆, F_nT) | Verificado; coincide con `hydro.py` | R_TR ≈ 40 de 134 N a 6 km/h (30 %): el término con menos base empírica | [VERIFICADO: R09 S15] + [CALCULADO: R09 §1.4] |
| Olas Holtrop 1982/84 | Estructura verificada; rango Fn 0,15–0,45 (fuente secundaria) | Forma semiempírica calibrable | [VERIFICADO: R09 S16, S31] |
| Gerr SLR máx = 8,26/DL^0,311 (piso 1,34) | Verificado; DL ≈ 1010 → piso → 6,4 km/h | Confirma el muro de resistencia (velocidad de casco <!--V:sizing.hull_speed.v_hull_kmh:.2f-->6.36<!--/V--> km/h) | [VERIFICADO: R09 S22] |
| Fórmula de potencia de Gerr | **No verificada**; sobreestima 1,5–2× | Solo techo | [ESTIMADO: R09 §1.7] |
| Savitsky 2003 (regímenes) / Savitsky 1964 (planeo) | 2003 verificado; 1964 de memoria y **no aplica** (pre-planeo, espejo mojado) | No se usa | [VERIFICADO: R09 S21] |
| Wageningen B-series (39 + 47 términos) | Verificada término a término contra el escaneo de Bernitsas 1981 (85/86 idénticos, 1 difiere 4·10⁻⁵) | Dentro de rango; MKP-32 (P/D ≈ 0,4) queda fuera → modelo lineal calibrado [ESTIMADO] | [VERIFICADO: R09 S13, S14] + D-40 |
| Corrección de escala y rugosidad ITTC-78 (Holtrop) | Verificada; Rn 5,7–7,7·10⁵ < 2·10⁶ | `efficiency_factor` 0,95 (banda 0,93–0,98) | [VERIFICADO: R09 S15] |
| Burrill 5 % y 10 % (digitalizado de Carlton) | Verificado en código abierto; A_P/A_E = 1,067 − 0,229·P/D **no** verificado | Tabla 5 % en vez del ajuste 0,3σ^0,6 (+15 a +81 % no conservador) | [VERIFICADO: R09 S17] |
| Keller (K = 0,2 un eje) | Verificado | AE/A0 mín. | [VERIFICADO: R09 S15, S30] |
| Velocidad crítica (Euler-Bernoulli, Rayleigh, Dunkerley) | Formas verificadas; biapoyada derivada; regla "n_máx ≤ 75 % de n_crít" (Wikipedia, sin cita) | Tramo entre bujes ≤ 0,6 m; R09 pedía n_crít/n_máx > 4 | [VERIFICADO: R09 S1, S7] + [ESTIMADO: R09 §5.1] |
| Goodman / Soderberg / Gerber | Verificado | Fatiga del eje y del pasador | [VERIFICADO: R09 S3] |
| Pasador de corte τ_u ≈ 0,65 UTS (Al) / 0,75 UTS (acero) | Relaciones verificadas; ecuación derivada | Ø del pasador | [VERIFICADO: R09 S6] |
| Eje inclinado (long-tail a 12°) | Verificado hasta 12°; P1 está a 25° (extrapolado) | T horizontal = 0,906·T (−9,4 %) | [VERIFICADO: R09 S23] + [CALCULADO] |
| Pérdidas MOSFET; α del cobre 3,93·10⁻³ K⁻¹ | Verificados | Térmico de ESC y motor (+23,6 % de R a 80 °C) | [VERIFICADO: R09 S28, S9] |
| Mercier-Savitsky, Series 62, B-series 4 cuadrantes, R_th de outrunner, pasadores OEM | **No encontrados** | — | buscar: términos en R09 §7 |

**En el diseño vigente** [CALCULADO, con la geometría de la MKP-32 aún ESTIMADA]: η0 de crucero <!--V:sizing.cruise.design.prop_eta0:.2f-->0.41<!--/V--> a J = <!--V:sizing.cruise.design.prop_J:.2f-->0.23<!--/V--> y <!--V:sizing.cruise.design.prop_n_rpm:.0f-->1491<!--/V--> rpm; Burrill en crucero τc = <!--V:sizing.cavitation.cruise.tau_c:.3f-->0.114<!--/V--> contra un límite de <!--V:sizing.cavitation.cruise.tau_limit:.3f-->0.261<!--/V--> y en punto fijo <!--V:sizing.cavitation.bollard.tau_c:.3f-->0.247<!--/V--> contra <!--V:sizing.cavitation.bollard.tau_limit:.3f-->0.279<!--/V-->; tramo máximo entre bujes <!--V:sizing.mech.shaft.max_span_mm:.0f-->563<!--/V--> mm con velocidad crítica <!--V:sizing.mech.shaft.n_crit_rpm:.0f-->5834<!--/V--> rpm contra <!--V:sizing.mech.shaft.n_max_rpm:.0f-->1713<!--/V--> rpm máximas (×<!--V:sizing.mech.shaft.crit_ratio:.1f-->3.4<!--/V-->): cumple la regla del 75 % de S1, pero no el "> 4" que pedía R09 y que repite D-07, porque la MKP-32 gira más rápido que la 10 × 8 supuesta en R09. R09 había comparado hélices a T = 169 N: 7,8" η0 0,42, 10 × 8 η0 0,49, 11 × 8 η0 0,52 [CALCULADO: R09 §2.3, sizing anterior]; la MKP-32 elegida (P/D ≈ 0,4) da η0 0,41, sin mejora sobre la 7,8": la ganancia de una 10 × 8 queda pendiente de encontrar el producto (D-06). Agua poco profunda: con h = 0,6 m a 8 km/h Frh = 0,92 → en los bajos ir a ≤ 6 km/h y remolcar con h ≥ 1,5 m [CALCULADO: R09 §1.8].

## 9. Hallazgos que cambian el diseño

| # | Hallazgo (fuente) | Qué cambió en P1 | Decisión / archivo |
|---|---|---|---|
| 1 | V1 no es turbojet sino waterjet de PETG sin ensayo; un jet necesita 1,35–5,4× la potencia al eje a 6 km/h (R01, R03 §2.3) | Waterjet y combustión fuera; arquitectura A3 cola larga (<!--V:arch.totals.A3:.2f-->4.25<!--/V--> puntos, gana en el <!--V:arch.mc_win_frac.A3:.0%-->86%<!--/V--> de los pesos aleatorios) | D-03, 03_arquitectura |
| 2 | Empuje axial sobre PETG = falla prevista (R01); fatiga del PETG 0,06 (R05) | Empuje y tiro de correa a metal: placa motriz Al 6 mm y cartucho de Al | D-25, D-08 |
| 3 | Capacidad 100–185 kg, USCG ≈ 160 kg (R04) | Riesgo n.º 1; P0.2 antes de comprar; plan con 1 adulto o batería chica | D-16, PENDIENTES P0.2 |
| 4 | Masa colgada del espejo ≤ 18–28 kg, 35 kg tope (R04) | Batería al centro, nunca en el espejo; unidad completa <!--V:verify.unit_mass.cad_kg:.2f-->8.85<!--/V--> kg (CAD) contra 18 kg de diseño | inputs `max_transom_hang_kg`, verify.json |
| 5 | R(6 km/h) = 95–150 N (banda estimada desde mediciones); tablas de fabricante piden 2–3× menos energía (R04) | Modelo por componentes con banda [0,75; 1,15], diseño con el borde alto | D-05 |
| 6 | ΔC_F ITTC-78 negativa con L = 2 m; Prohaska no vale; (1+k) entre 1,0 y 1,47 (R09) | Remolque mide R(v) total con h ≥ 1,5 m y ajusta `wave_cw` | PENDIENTES P0.3–P0.4 |
| 7 | 1 kW → 7,6–8,0 km/h; 2,5 hp de nafta no planea con 2 (R04); Gerr 6,4 km/h; Savitsky no aplica (R09) | No se dimensiona para 12 km/h; meta de V máx blanda 8 km/h, que el diseño **no alcanza** (<!--V:sizing.vmax.nominal_vnom.V_kmh:.1f-->7.1<!--/V--> km/h nominal) y se acepta | inputs `vmax_target_kmh` [SUPUESTO], 02 §4.1 |
| 8 | ≤ 5 kn a < 300 m de la costa (R07) | Tope de ERPM "modo costa" <!--V:sizing.legal_speed.erpm_cap:.0f-->30164<!--/V--> (con 1 persona el bote haría <!--V:sizing.legal_speed.vmax_light_low_kmh:.1f-->9.5<!--/V--> km/h) | D-30 |
| 9 | Eléctricos de 1 kW usan hélices de 10–11" a 1200–1450 rpm; 7,8" rinde η0 0,42 contra 0,49 de 10 × 8 (R04, R09) | Hélice de ~254 mm (MKP-32, medidas [ESTIMADO]; η0 0,41, sin ganancia sobre la 7,8"); 10 × 8 de 3 palas como objetivo no comprable | D-06 |
| 10 | Hélice OEM de 2,5–3,5 hp = 7,4"; bore y pasador no publicados (R08b) | Comprar y medir la hélice antes de tornear el eje | D-06, PENDIENTES P0.7 |
| 11 | Hélice impresa: −61 % de empuje (PLA); pala de PETG fisurada al desmontarla tras 4 meses en el mar (R02, R03) | Hélice comprada; PRP-03 es solo volumen barrido | D-06, 02 §4.4 |
| 12 | 6374 en directo quemó 2 motores (R02 B4) | Reducción <!--V:sizing.selection.z_motor:d-->20<!--/V-->:<!--V:sizing.selection.z_shaft:d-->48<!--/V--> + `l_in_current_max` ≤ 80 % del BMS | D-39, PENDIENTES P2.2 |
| 13 | Polea impresa patina; chaveta en plástico imposible (R02 B2) | Poleas de Al Dold; la de 40 T re-mandrinada a Ø15 H7; tensado por colisos | D-39 |
| 14 | Eje fino vibra; eje flexible pandea; tramo ≤ 0,6 m (R02, R09) | Eje 316 Ø16/Ø15 con 3 portabujes y pila apretada; tramo <!--V:sizing.mech.shaft.max_span_mm:.0f-->563<!--/V--> mm, n_crít/n_máx = <!--V:sizing.mech.shaft.crit_ratio:.1f-->3.4<!--/V--> (no llega al > 4 de R09) | D-07, D-38 |
| 15 | A 15° la hélice ventila; a 20° duplicó la velocidad (R02 B5) | Eje a 25°, trimado ±5°, placa antiventilación | D-04, D-27 |
| 16 | Kick-up + reversa necesita traba (Torqeedo, R02) | Retén de bola + gravedad; reversa limitada al 50 % | D-10 |
| 17 | Acelerador rozado con la hélice en arena rompió la transmisión (R02 A4) | Pasador de corte 316 Ø<!--V:sizing.mech.shear_pin.d_std_mm:.1f-->2.0<!--/V--> mm (corta a <!--V:sizing.mech.shear_pin.Q_shear_Nm:.1f-->12.4<!--/V--> N·m en el asiento Ø<!--V:sizing.mech.shaft.d_prop_seat_mm:.1f-->12.7<!--/V--> mm [ESTIMADO: bore no medido]; calibrar con el ensayo P1.9) + armado solo con acelerador en cero | D-11, 04_diseno/electronica |
| 18 | Aro romo con holgura 4,5 % D pierde 25 % de K_T; sin rejas delante (R03 Ladd) | Aro perfilado NACA 15 %, holgura 6 mm, pérdida 10 % (sensibilidad 0–25 %) | D-26 |
| 19 | Tobera Kort: hasta +30 % solo en bollard, la reversa no mejora con todas las toberas, holgura ≤ 0,5 % D (R03, R09) | Tobera a P2 con banco de ensayo | 07_roadmap_P2, 02 §4.5 |
| 20 | PETG: agua −28 %, Z 0,38, fatiga 0,06, creep desde 50 % (R05) | Factores D-29; ninguna pieza impresa en la ruta de carga alterna | D-29, 02 §9 |
| 21 | HDT del PETG 65,7–75 °C; epoxi West HDT 48 °C (R05) | T de servicio 50 °C; PETG con HDT ≥ 70 °C; capó ventilado; tapa de Al con disipador ≤ <!--V:sizing.thermal_esc.heatsink.R_hs_required_K_W:.2f-->0.44<!--/V--> K/W | D-29, D-20 |
| 22 | Superficie FDM 10–30× más rugosa que lo que pide un O-ring (R05) | O-ring NBR 70 Ø3,53 mm de cara contra cara refrentada y tapa de Al | D-23 |
| 23 | Retén radial pide eje ≥ 45 HRC; pod con sello falla por bombeo térmico (R03, R05) | Cero sellos dinámicos sumergidos; bujes igus H370 lubricados por agua | D-03, D-38 |
| 24 | Tuerca A4 cautiva > inserto; Loctite 243 puede fisurar termoplásticos; latón descincifica (R05) | Tuerca A4 cautiva estándar; latón solo M4 en zona seca | D-18 |
| 25 | Rodamientos "inox" baratos = 440C / AISI 420; PPWR corta envíos (R01, R08b) | 6202-2RS de cromo solo en zona seca, cambio por temporada | D-37 |
| 26 | Tubo 316 Ø25 × 1,2 era lo comprable (R08b), pero cede con el impacto (cálculo de D-09); barra 316 no hallada (R08b) | Tubo Al 6061-T6 Ø40×3; eje 316 pedido a metalgrossist | D-09, D-07 |
| 27 | Antichispa MOSFET falla en corto (R06) | Contactor monoestable + cordón cerrado con clip + seta; antichispa solo arranque suave | D-22, D-33 |
| 28 | Defaults del VESC peligrosos; filtro de fase daña el 75100 con FW ≥ 5.03 (R06, R08a) | Configuración obligatoria antes del agua | PENDIENTES P2.2, 04_diseno/electronica |
| 29 | LFP sin runaway en ARC; 16S supera 58 V; accesorios de 32–48 V (R06, R08a) | LiFePO4 8S, <!--V:sizing.battery.E_nom_wh:.0f-->2560<!--/V--> Wh; 12S documentado | D-19, D-28 |
| 30 | Fusible ≤ 7 in (ABYC: 175 mm) del borne y ≤ ampacidad del cable; portafusibles MIDI de 58 V baratos (R06, R08a) | MIDI <!--V:sizing.fuse.rating_a:d-->80<!--/V--> A 58 V; D-21 dice ≤ 178 mm → montar a ≤ 175 mm | D-21, D-33 |
| 31 | Casco metálico no es conductor; eFoil con fuga a masa le dio una descarga al usuario (R03, R06) | Sistema flotante; prueba de aislamiento fase/BAT− contra casco | D-36, 04_diseno/electronica §1 |
| 32 | R06 recomienda ánodo de Al; la verificación de R05 lo pasó a "obligatorio, o dúplex 2205"; ambos alertan picado/rendija del 316 bajo bujes (R05 S42, Gerr) | **Desvío consciente:** sin ánodo, aislamiento por diseño (no evita la rendija); ánodo solo si la hélice final es de Al; inspección de picaduras bajo los bujes cada temporada | D-36, 06 |
| 33 | Pasador de Al 6061 Ø3 propuesto (R09) es ánodo frente al eje 316 | Pasador 316; FS Goodman en crucero <!--V:sizing.mech.shear_pin.fatigue_cruise.fs_goodman:.2f-->1.46<!--/V--> → cambio cada 10 h [SUPUESTO] | D-11, 02 §7 |
| 34 | B-series verificada; ajuste de Burrill no conservador; corrección ITTC-78 (R09) | Polinomios B-series, tabla de 5 %, η0 × 0,95 | D-40, 02 §4.2–4.3 |
| 35 | VESC limita a 85 °C; cobre +23,6 % a 80 °C (R09) | `t_winding_max_c` 85 °C y R en caliente | D-41 |
| 36 | Agua < 15 °C en ≥ 90 % de los días de oct–may; máx. 23,3 °C (R07) | Temporada 15 jun–15 sep; T máx. 24 °C para cavitación | D-31 |
| 37 | Viento fuerte SW/W de tierra; ola corta del largo del bote (R07) | Remos, ancla y chalecos en la BOM; salida ≤ 6 m/s; +25 % de R por ola | D-35, inputs `wave_added_frac` |
| 38 | LiTime corta la carga < 0 °C y la Power Queen 24 V < 5 °C; en la PQ 12 V 100 Ah elegida no están verificados ni el corte en frío ni el IP (R08a §4) | Cargar en interior a ≥ 5 °C; batería removible, tratada como no estanca hasta leer la ficha | 02 §6, 06 PU.5 |
| 39 | Carcasa de ~2 kg = 3 días de impresión → segmentar a ≤ 12–16 h por impresión [ESTIMADO]; hélice comprada desbalanceada (R02 C3) | Protector en 6 segmentos; **sin aplicar** a MNT-01 (103 h) ni MNT-05 (65 h) [CALCULADO: manifest.json]; balanceo de la hélice en el torno: **pendiente** de incorporar a 06 | D-26, 05_fabricacion, 06 |
| 40 | Techo de costo = ePropulsion completo 2.549 € (DE) a ~2.930 € (DK) (R04) | BOM de <!--V:bom.total_eur:.0f-->2281<!--/V--> €: la justificación de P1 es autonomía y basculación, no precio | bom.csv, 03_arquitectura |

### 9.1 Qué deja abierto la investigación (hacer antes de comprar, mecanizar o salir)

1. Medir el bote (LOA, manga, alto y espesor de espejo, peso) y leer la placa (PENDIENTES P0.1–P0.2). Si la placa es menor que la carga útil: 1 adulto o batería chica (D-16).
2. Comprar la MKP-32 y medir D, paso, n.º de palas, bore y pin **antes** de tornear el eje (P0.7) → cargar en `inputs.yaml` y correr `run_all.py`.
3. Remolque con dinamómetro a 2–8 km/h con h ≥ 1,5 m para calibrar R(v) total (P0.3–P0.4); recién después comprar la batería (P0.5).
4. Leer en la ficha de la Power Queen 12 V 100 Ah el grado IP y el corte de carga en frío (§5.2); hasta entonces, batería no estanca y carga en interior a ≥ 5 °C.
5. Confirmar HDT(1,8 MPa) ≥ 70 °C del filamento antes de comprarlo; si la ficha no lo declara, PolyLite (D-29, §7.2).
6. Configurar el VESC antes del agua (P2.2): filtro de fase apagado, `voltage_min` ≈ 0,3 V, corte 24,0/22,4 V, `l_in_current_max` ≤ 80 % del BMS, parámetros de 04_diseno/electronica/README.md §6 y tope de <!--V:sizing.legal_speed.erpm_cap:.0f-->30164<!--/V--> ERPM (§5.1).
7. Balancear la hélice en el torno antes de montarla (R02 C3) y montar el fusible a ≤ 175 mm del borne (§5.4).
8. Cada temporada: desmontar el eje e inspeccionar picaduras bajo los bujes (§5.5); si aparecen, ánodo o eje dúplex (D-36).
9. Medir temperaturas en T2.3/T2.5 de 06: el modelo da <!--V:sizing.thermal.cruise_design.T_motor_steady_C:.0f-->80<!--/V--> °C estacionarios en el motor en crucero de diseño (> 85 °C del VESC, H-7 de 06), y las piezas impresas deben quedar ≤ 40 °C con f_temp 0,85 (§4.2).
