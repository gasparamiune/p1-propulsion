# R01 — Videos de referencia V1 y V2 (canal "Clean Energy", @cleanenergy6271)

Consulta: 2026-10-01. Alcance: metadatos, descripción, transcripción, comentarios, observación visual (storyboards/miniaturas), videos relacionados y aplicabilidad a P1.

**Leyenda de etiquetas**
- `[VERIFICADO: url]`: texto o dato leído en esta sesión (descripción, pista ASR, comentario, ficha técnica).
- `[VERIFICADO-visual: url, ~mm:ss]`: observado por mí en el storyboard oficial de YouTube (cuadros de 160×90 px en V1/V2 y de 320×180 px en los otros videos, uno cada ~5–10 s) o en la miniatura de 1280×720. El dato es real, pero la resolución es baja y puede faltar algo entre cuadro y cuadro.
- `[ESTIMADO: base]` · `[SUPUESTO]` · `[ESTIMADO: memoria técnica, no verificado]`.
- **NO VERIFICADO**: lo afirma el autor o un tercero, pero ninguna medición, prueba ni documento lo respalda.

**Método (cómo se obtuvo cada cosa)**

| Dato | Vía | Resultado |
|---|---|---|
| Título, fecha, vistas, descripción | `curl` a la página watch, parseo de `ytInitialData` (el `ytInitialPlayerResponse` devolvió `LOGIN_REQUIRED` "Sign in to confirm you're not a bot") | OK en V1 y V2 |
| Duración, likes, n.º de comentarios, tags, pistas de subtítulos | `yt-dlp --dump-json` (clientes visionos/mweb) | OK |
| Transcripción V1 | URL `timedtext` (pista ASR `en-orig`, json3) obtenida de yt-dlp y bajada con curl | OK: 709 s de pista |
| Transcripción V2 | Sin pistas `captions`/`automatic_captions` y sin `getTranscriptEndpoint` en la respuesta `next` | **No existe**: video sin narración, solo música y rótulos |
| `youtube-transcript-api` 1.2.4 | `api.list()` | `RequestBlocked` (IP bloqueada por YouTube) |
| Comentarios | `yt-dlp --write-comments` (top, con respuestas) | V1: 63 de ~66; V2: 55 de ~56 |
| Visual | Sprites de storyboard `i.ytimg.com/sb/<id>/storyboard3_L2/M*.jpg` y miniatura `maxresdefault.jpg` | OK |
| Video completo (para leer rótulos en HD) | yt-dlp formato 231/134 | **Falló** (descarga trabada, después 429/bot-check) |

---

## 1. Resumen ejecutivo

1. **V1 NO es un turbojet de combustión.** Es una **bomba waterjet impresa (jet pump)** que el autor llama "turbo jet". Lo dice la transcripción en 00:53–00:57: *"I'm building a turbo jet engine. Yes, a mini water jet engine for a small boat"*. Lo confirman el tag `water jet propulsion` y el autor en los comentarios: *"where I'm from we call it a turbojet"* [VERIFICADO: https://www.youtube.com/watch?v=Z41FAXVMdKs].
2. **Ninguno de los dos videos muestra la unidad funcionando** con motor, en agua ni con carga. V1 termina en *"I'll be showing you the test runs … in my upcoming videos"* (11:16). Cuando le piden specs, el autor responde *"This is just a test version … no exact specs for now"*. V2 termina con el ensamblaje en la mesa.
3. **No hay ningún dato de motor, potencia, batería, tensión, velocidad, empuje ni consumo** en las descripciones, en la transcripción ni en las respuestas del autor. Las "7000 RPM" de V1 son una pregunta retórica, no una medición.
4. **Lo verificado y útil:** carcasa de PETG (lo confirma el autor), eje y rodamientos "stainless" (V2 rotula S6801Z, que el proveedor da como AISI 440C), varillas roscadas M8 inox como tirantes, retenes de agua, grasa + inyección de aceite, toma de agua de refrigeración desde la cámara de presión, caras de unión refrentadas en torno, peso de 2–3 kg y 5 días de impresión.
5. **Para P1:** el waterjet de V1/V2 queda descartado como propulsión principal. A 6 km/h su rendimiento ideal es ~0,30–0,44, contra ~0,64–0,75 de una hélice de 7,8–9" (§7.2). Además va en el fondo del casco, lo que choca con la basculación (kick-up), no da marcha atrás útil y no tiene ensayo que lo respalde. **Sí sirven patrones de construcción**: carcasa en segmentos apilados con tirantes pasantes, refrentado en torno, toma de agua para lubricar o enfriar, eje metálico con el empuje axial tomado por metal.

---

## 2. Fichas de metadatos

| Campo | V1 | V2 |
|---|---|---|
| URL | https://youtu.be/Z41FAXVMdKs | https://youtu.be/CkUiNuAfPL8 |
| Título | "Will My 3D Printed Jet Engine Explode at Full Speed - DIY Turbojet with 3D Printed" | "This is how I built a 3D printed waterjet engine for my beloved boat" |
| Canal | Clean Energy (@cleanenergy6271, channel_id UCCnontkVGammTnsgxJJfI5w), 3,38 K suscriptores | ídem |
| Publicado | 2025-05-23 | 2025-12-30 |
| Duración | 11:48 (708 s) | 13:59 (839 s) |
| Vistas (al 2026-10-01) | 111.919 | 31.985 |
| Likes | 1.672 | 491 |
| Comentarios | 66 | 56 |
| Idioma / narración | en-US; voz IA (lo admite el autor en los comentarios) | Sin narración (no hay pistas de subtítulos) |
| Subtítulos | Solo ASR automático (`en-orig` + 157 traducciones automáticas) | Ninguno |
| Capítulos | Ninguno | Ninguno |
| Links en la descripción | **Ninguno** (sin Printables/Thingiverse/MakerWorld ni lista de piezas) | **Ninguno** |
| Tags | `3D printed jet engine`, `turbojet DIY`, `water jet propulsion`, `high RPM test`, `7000 RPM`, `DIY boat engine`, … | (vacío) |
| Archivos | STL "for 20 USD" por e-mail (respuesta del autor en V1) | No se ofrecen en V2; en otros videos del canal, 20 USD por e-mail |

Fuentes de toda la tabla: [VERIFICADO: https://www.youtube.com/watch?v=Z41FAXVMdKs] y [VERIFICADO: https://www.youtube.com/watch?v=CkUiNuAfPL8].

---

## 3. V1 — "3D Printed Jet Engine" (en realidad, una bomba waterjet)

### 3.1 Descripción (texto literal relevante)
> "designing and building a mini turbojet engine for a small boat — completely 3D printed! From crafting thick, high-angle fan blades to installing stainless steel bearings and shafts…"
> "The goal: Can this plastic jet engine survive spinning at 7000 RPM without flying apart?"
> "Tech Highlights: Full 3D printed fan and housing · High pitch blade angle for maximum thrust at low speeds · Stainless steel shaft and bearings · Custom water seal design · Grease + oil lubrication"

[VERIFICADO: https://www.youtube.com/watch?v=Z41FAXVMdKs]

### 3.2 Transcripción: frases clave con timestamp (ASR automático, voz IA)

| t | Cita textual | Lectura técnica |
|---|---|---|
| 00:53 | "I'm building a turbo jet engine. Yes, a mini water jet engine for a small boat." | Tipo real: **waterjet** |
| 01:59 | "about 5 days in total to finish the entire turbo jet assembly, and yep, it's fully 3D printed" | **5 días** de impresión |
| 02:07 | "I used stainless steel bearings and a solid stainless steel shaft" | Eje y rodamientos inox |
| 02:20 | "At the shaft ends, I've designed water seals to prevent any leakage so no water can get into the boat." | Retenes en el paso del eje al casco |
| 02:32 / 02:43 | "apply a layer of grease to the moving parts" / "I'll be injecting oil directly into the shaft area. This ensures continuous lubrication" | Grasa en el armado + aceite inyectado |
| 03:08 | "I designed the blades with a very steep angle of attack, much more aggressive than what you'd typically see." | Paso alto |
| 03:38 | "That's why I made the blades extra thick to make sure they can withstand the intense compression forces" | Álabes gruesos (PETG) |
| 03:57 | "At around 7,000 revolutions per minute, do you think these plastic blades will hold up or are they going to shatter" | 7000 rpm: **pregunta retórica, sin ensayo** |
| 04:29 | "I put it on the lathe and gave it a good finish. Now, it's got a clean, flat surface." | Refrentado en torno de las caras de unión |
| 05:00 | "the stator or the fixed blades. Its job is to guide the flow of water" | Estator impreso |
| 05:11 | "inside this section, there are two bearings and a water sealing gasket" | 2 rodamientos + junta en el estator |
| 06:52 | "it's actually a flow diverter. It draws a tiny amount of water from the compression chamber and redirects it to help cool the engine." | Toma de refrigeración (niple de bronce visible en la miniatura) |
| 08:46 | "it's not exactly small. This one's pretty big. Now, it's time to take some measurements" | — |
| 10:23 | "the whole thing weighs around 2 to 3 kg" | Masa de **2–3 kg** (sin motor) |
| 10:29 | "I used plastic for the casing and aluminum shaft for strength, chrome alloy parts … and stainless steel screws" | **Contradice 02:07** (eje inox vs. aluminio) |
| 10:47 | "the back section can actually stick out a bit beyond the hull … I'm planning to design an additional protective plate that will be mounted underneath" | Montaje bajo el casco con la tobera saliente |
| 11:16 | "I'll be showing you the test runs and more exciting projects in my upcoming videos." | **No hay prueba en V1** |

[VERIFICADO: pista ASR `https://www.youtube.com/api/timedtext?v=Z41FAXVMdKs&…&kind=asr&lang=en&fmt=json3` (URL firmada, obtenida para https://www.youtube.com/watch?v=Z41FAXVMdKs)]

### 3.3 Rótulos y observación visual (storyboard, ~5 s/cuadro)

| ~t | Observación | Etiqueta |
|---|---|---|
| 00:05–00:20 | Tomas de una lancha jet en un río, con una marca de agua amarilla distinta a la del canal. **No es la unidad impresa**; origen sin verificar | [VERIFICADO-visual: https://youtu.be/Z41FAXVMdKs, ~0:05] |
| 00:30–01:05 | Unidad jet metálica (estator fundido o soldado) montada en un casco; también es material ajeno al build | ídem |
| 01:10–01:30 | Rebanador con impulsor helicoidal, cuerpo de bomba y anillo; impresora cartesiana de cama móvil, sin cerramiento (modelo no identificable) | ídem |
| 01:30–07:30 | Unidad negra en segmentos apilados con varillas roscadas pasantes y tuercas; impulsor helicoidal impreso de 2–3 álabes de gran envolvente; eje de acero pulido; estator con buje; prueba del eje girado a mano y con taladro inalámbrico | [VERIFICADO-visual: https://i.ytimg.com/vi/Z41FAXVMdKs/maxresdefault.jpg] y storyboard |
| ~08:50–09:20 | Rótulos amarillos, legibles en parte: "The fan shaft is **1** centimeter in diameter" · "The total length is **6?** centimeters" (segundo dígito ilegible) · "The fan blades are **8?** centimeters long" · la cinta métrica marca "**22 cm**" sobre la placa de toma | [VERIFICADO-visual: storyboard https://youtu.be/Z41FAXVMdKs, ~9:00; **dígitos inciertos**] |

### 3.4 Comentarios: respuestas del autor (@cleanenergy6271) y críticas técnicas

| Quién | Texto (extracto literal) | Valor |
|---|---|---|
| Autor | "I used PETG filament" / "petg e" | **Material: PETG** [VERIFICADO] |
| Autor | "I intended for it to be mounted beneath the hull of the boat—meaning the motor will be fully submerged in water. That way, there's no need for priming." | Montaje bajo el casco, sumergido |
| Autor | "This type of propeller has a very steep pitch, and based on my calculations, it will work well with low-RPM motors … All the bearings and metal components are made of stainless steel." | Contradice el "7000 RPM" de la descripción |
| Autor | "This is just a test version I'm still working on it, so no exact specs for now." | **Sin specs** |
| Autor | "My voice isn't very pleasant, so I use an AI voice" | Narración con voz IA |
| Autor | "The price for all the STL files is 20 USD … contact me via my email" | Modelo pago, sin repositorio público |
| @nachou1454 | "a small amount of air inside the propeler chamber … will cause cavitation" · "all the force generated by the propeller will be applied to a small portion of plastic and will eventually wear out, i would suggest … some type of thrust bearing with a circlip" | **Falla prevista: el empuje axial descansa sobre PETG** (relevante para P1) |
| @hussainwake7127 | "the intake opening needs to be larger or the main shaft needs to be smaller … i don't think the steering nosil can survive" | Toma de admisión chica; tobera de dirección frágil |
| @superdupaify | "I'm waiting for you to make it able to go astern." | **No tiene marcha atrás** |
| @jonholzworth4463 | "When you inevitably discover that the 3D printed housing isn't waterproof, you can use a coat of epoxy resin" | Porosidad de la impresión FDM |
| @rickywoods3101 | "I don't think it lasted at all … the next video he is fabbing all metal assembly" | Indicio (no probado) de que se abandonó la versión plástica |
| @hemantkumar-cy6ut | "I paid the asked amount but never got the files so be aware" | Riesgo de compra; **NO VERIFICADO** |
| @andrzejw.9418 / @BigFx / @SpongeBob-xh8ir | "This is jet pump … no power source" / "another AI slop" / "Fake ai video" | Dudas sobre la credibilidad |

[VERIFICADO: https://www.youtube.com/watch?v=Z41FAXVMdKs (comentarios vía API de YouTube)]

---

## 4. V2 — "3D printed waterjet engine for my beloved boat"

### 4.1 Descripción
Texto genérico, sin ningún dato técnico: *"This is how I built a 3D printed waterjet engine for my beloved boat · This channel is the home of crazy inventions…"* [VERIFICADO: https://www.youtube.com/watch?v=CkUiNuAfPL8]. No hay links, piezas, motor ni batería.

### 4.2 Transcripción
**No existe.** El video no tiene pistas de subtítulos (ni manuales ni ASR) y no expone endpoint de transcripción. Es un video de armado con música y rótulos [VERIFICADO: https://www.youtube.com/watch?v=CkUiNuAfPL8].

### 4.3 Rótulos legibles y observación visual (storyboard, ~5 s/cuadro)

| ~t | Observación | Etiqueta |
|---|---|---|
| 00:10–00:25 | Lancha chica con un tripulante en un estanque o laguna de agua quieta. No se ve si lleva este jet | [VERIFICADO-visual: storyboard https://youtu.be/CkUiNuAfPL8, ~0:15] |
| 00:30–00:50 | CAD (interfaz tipo SolidWorks, no confirmado) con vista explotada: rampa de toma, carcasa del impulsor, estator, tobera y deflector de dirección | ídem |
| 01:00–04:00 | Armado de la rampa de toma impresa (negra) con varillas pasantes y martillo; pegamento o sellador en tubo | ídem |
| **~04:13** | Rótulo: **"M8 stainless steel threaded rod"** | [VERIFICADO-visual: ídem, ~4:13] |
| **~06:27** | Rótulo: **"S680?Z stainless steel ball bearing"** con marcas "1 2 3" (3 rodamientos; el 4.º carácter es ilegible) | [VERIFICADO-visual: ídem, ~6:27; dígito incierto] |
| ~06:35–07:50 | **Impulsor metálico de fabricación casera**: discos y álabes de chapa brillante cortados, soldados (operador con máscara) y pulidos con disco de láminas. En la miniatura: impulsor metálico de 3 álabes sobre eje roscado | [VERIFICADO-visual: https://i.ytimg.com/vi/CkUiNuAfPL8/maxresdefault.jpg y storyboard ~7:00] |
| **~10:45** | Rótulo: **"S6801z stainless steel ball bearing"** junto a un tubo blanco (buje o camisa del eje) | [VERIFICADO-visual: storyboard, ~10:45] |
| ~11:50–12:15 | Taladro inalámbrico acoplado al eje de entrada por la rampa (giro en banco) | [VERIFICADO-visual: storyboard] |
| 12:20–13:59 | Final: unidad ensamblada sobre la mesa. **No hay prueba en agua ni motor instalado** | [VERIFICADO-visual: storyboard] |

**S6801-ZZ = 12×21×5 mm, acero inoxidable AISI 440C, doble blindaje** [VERIFICADO: https://minibearings.com.au/products/12x21x5-bearings-s6801zz]. Si el rótulo ilegible fuera S6800Z, sería 10×19×5 mm [ESTIMADO: memoria técnica, no verificado; coincide con un resultado de búsqueda que no abrí]. El eje Ø10 mm que rotula V1 calzaría con un 6800 [ESTIMADO: deducción, no verificado].

### 4.4 Comentarios en V2 (55)
Ninguna respuesta del autor. Casi todos piden STL o precio. Los técnicos:
- @anthonyali968: *"putting a UP/DOWN shaft on it is unneccessary … please try it on action if the small screws you used will hold"*.
- @omarbz8681: *"Can you please post the jet in a action … will it work"*.
- @neafranklin7905: *"will it actually work with any pressure?"*.
- @Johnsmith-s3q4u: *"Does anybody have an stl of the metal impeller?"*, que confirma que los espectadores ven el impulsor como metálico.
- @luisgs500: *"Petg?"* (sin respuesta).

[VERIFICADO: https://www.youtube.com/watch?v=CkUiNuAfPL8]

---

## 5. Extracción comparada (VERIFICADO vs. NO VERIFICADO)

| Ítem | V1 | V2 | Estado |
|---|---|---|---|
| Tipo de propulsión | Bomba waterjet axial/mixta: toma por rampa, impulsor, estator, tobera y deflector de dirección | ídem; rampa con rejilla, deflector de dirección | VERIFICADO (transcripción y visual) |
| Escala | 2–3 kg; eje Ø1 cm; largo total "6? cm" (¿60–69 cm?); placa de toma ~22 cm | Similar; sin medidas | Masa VERIFICADA; medidas con dígitos inciertos |
| Motor / potencia | **Ninguno mostrado.** "works well with low-RPM motors"; "7000 RPM" como pregunta | Ninguno | NO VERIFICADO / ausente |
| Batería / tensión | Ausente | Ausente | — |
| Material / impresora | PETG (autor); impresora de cama móvil sin cerramiento, modelo desconocido; 5 días de impresión | PETG no confirmado (pregunta sin respuesta); impulsor metálico soldado | PETG en V1 VERIFICADO; V2 visual |
| Metalurgia | Eje y rodamientos "stainless" (02:07) vs. "aluminum shaft" (10:29): contradicción | Varilla M8 inox; rodamientos S680xZ y S6801Z (440C) | VERIFICADO (rótulos); calidad real del inox NO VERIFICADA |
| Sellado | Retenes en los extremos del eje + junta en el estator; grasa + inyección de aceite; toma de refrigeración | Tubo blanco (¿buje?) en el eje; sellador en tubo | VERIFICADO (V1 transcripción); V2 visual |
| Montaje | Bajo el casco, sumergido, tobera saliente; placa protectora "planned" | Rampa de toma con brida para el fondo del casco | VERIFICADO como intención; **montaje real no mostrado** |
| Rendimiento (velocidad / empuje / consumo) | **Ninguno** | **Ninguno** | Ausente |
| Fallas | No se ensaya. Riesgos señalados por terceros: empuje axial sobre PETG, cavitación por aire, toma chica, tobera frágil, porosidad | No se ensaya | Comentarios: NO VERIFICADO |
| Marcha atrás | No (un comentario lo reclama) | No se observa cuchara de reversa | VERIFICADO (ausencia) |

---

## 6. Otros videos del mismo canal y referencias cruzadas

Lista completa del canal [VERIFICADO: https://www.youtube.com/@cleanenergy6271/videos]. Los relacionados con el bote o el waterjet:

| ID | Título | Fecha | Dur. | Vistas | Dato relevante |
|---|---|---|---|---|---|
| JHcTss-dCXs | "This is my homemade mini electric turbojet boat – built for speed!" | 2025-05-03 | 18:42 | 146.799 | La descripción dice "powered entirely by an electric turbojet system". Visual: jet **metálico** torneado y casco de espuma + fibra de vidrio. Termina con "To Be Continued..." **sin prueba en agua** [VERIFICADO: https://www.youtube.com/watch?v=JHcTss-dCXs; visual por storyboard] |
| LY_aolXHy3U | "Huge 3D Printed Turbojet – It Actually Works!" | 2025-06-11 | 11:14 | 4.059 | La descripción afirma "Firing it up with real fuel … heat-resistant parts". Es el único caso de **combustión** [VERIFICADO: https://www.youtube.com/watch?v=LY_aolXHy3U (descripción); funcionamiento NO VERIFICADO] |
| esYxe6lsToA | "I Built a Mini Jet Boat with a 90mm Engine" | 2025-06-17 | 11:26 | 553 | **EDF 90 mm** (propulsión aérea) en bote RC [VERIFICADO: descripción] |
| DVsitQLd6F8 | "I built a Water Jet for my Russian friend" | 2025-09-19 | 6:38 | 3.450 | Sin datos técnicos en la descripción |
| I43TpB1Ul8A | "Built My Own Storm Proof Boat at Home!" | 2025-10-02 | 8:58 | 2.364 | Casco de composite |
| XHzgooJRuZE | "3D Printing & Assembling a Compact Waterjet for Surfboards" | 2025-11-19 | 9:39 | 3.871 | STL a 20 USD por e-mail |
| 8FAkgcQPcco | "I Built a 3D Printed Water Jet Engine for a Mini Boat" | 2026-08-02 | 23:33 | 10.481 | La descripción afirma "uses a brushless motor" y "real-world water testing". En el storyboard (~10 s/cuadro) **solo se ve material de lancha ajena al inicio y armado en banco**; rótulos "M12" y "8mm"; armado de bujes con torneado. Prueba en agua **NO VERIFICADA** [VERIFICADO: https://www.youtube.com/watch?v=8FAkgcQPcco (descripción y storyboard)] |
| fMPVdl1BVZI | "I Shrunk a 100mm Jet Down to Just 30mm" | 2026-09-09 | 17:18 | 1.750 | STL a 20 USD |

Tabla elaborada con la API `next`/yt-dlp sobre cada watch URL. Duraciones de la lista del canal.

**Credibilidad del canal.** El mismo canal publica "I Built a 100% Free Perpetual Engine – Does It Actually Exist" (wpFzkMBvykY), "Unlimited Free Energy!…" (41YV8-DeM30) y "Insane Power! Custom Tesla Battery Runs Jet Fan Without BMS" (jFDQ3uDEv28) [VERIFICADO: https://www.youtube.com/@cleanenergy6271/videos]. A eso se suman la voz IA, las tomas de agua ajenas con otra marca de agua, la ausencia de ensayos y un reclamo por STL pagados que no llegaron. **Conclusión: fuente de ideas constructivas, no de datos de rendimiento.**

### 6.1 Referencia externa de alta relevancia para P1 (apareció entre los relacionados de V1)
**DK The Welder, "DIY Electric Longtail Motor - Build & Water Test"** (zTpj2lwR2Zs; 2026-08-07; 13:29; 25.857 vistas). Es la misma familia de arquitectura que la candidata de P1.

| Dato | Valor | Etiqueta |
|---|---|---|
| Descripción | "First attempt at an electric longtail. Get parts made buy Justway" | [VERIFICADO: https://www.youtube.com/watch?v=zTpj2lwR2Zs] |
| Motor | Ficha de AliExpress en pantalla (~0:10): "Flipsky Sensorless Brushless Motor **Fully Waterproof** Motor 561?? … for Surfing Boat Underwater Thruster Hydro Efoil", **NZ$248.33**. Es un motor **sumergido en la punta del tubo**, no un motor seco arriba | [VERIFICADO-visual: storyboard, ~0:10; modelo y KV ilegibles] |
| Controlador | VESC, detección en pantalla (~3:28): I = 41,06 A · R = 41,50 mΩ · L = 36,91 µH · λ = 17,61 mWb · sensorless | [VERIFICADO-visual: storyboard ~3:28] |
| Batería | "36V" (dicho en el video, según un comentarista; el autor no lo contradice). Autor: "I have a 72v 400amp to test with, I will probably make a 60v 100amp that fits inside the cover … 21700 cells" | [VERIFICADO: comentarios] |
| Potencia | Autor: "That motor can do 6000w and I will push it to 8000w" | NO VERIFICADO (afirmación) |
| Hélices | Rótulos "standard prop" vs. "high pitch 3d printed" (~12–13 min). Autor: "I think I want more of a mud style prop and lower pitch". Terceros: "deformation due to it being too thin"; "add some Fiber + Resin". El autor responde "I know I should the problem is sanding it" | [VERIFICADO: comentarios y storyboard] |
| Pruebas | Pileta, tambor, plataforma o tabla y bote chico (dinghy) en agua de mar costera | [VERIFICADO-visual: storyboard] |
| Pivote | Comentarios: "An oarlock on the transom would make a perfect pivot"; "A dyneema loop … makes an excellent pivot" | [VERIFICADO: comentarios] |

---

## 7. Aplicabilidad a P1

### 7.1 Qué aplica y qué no

| Elemento de V1/V2 | ¿Aplica a P1? | Motivo / adaptación |
|---|---|---|
| Waterjet como propulsión principal | **NO** | (a) Rendimiento ideal ~0,30–0,44 a 6 km/h contra ~0,64–0,75 de una hélice (§7.2), con la autonomía como prioridad. (b) Va en el fondo del casco: hay que perforar el fondo de aluminio del jon boat y no admite kick-up. (c) Sin reversa: con un ESC bidireccional, una bomba axial girando al revés rinde muy mal [ESTIMADO: memoria técnica, no verificado]; hace falta una cuchara de reversa. (d) La toma aspira arena y algas en aguas bajas [ESTIMADO: memoria técnica, no verificado]. (e) Cero datos de ensayo en ambos videos |
| "Turbojet" de combustión | **NO** (además, V1 no lo es) | PETG con **HDT 68 °C a 0,45 y 1,80 MPa** [VERIFICADO: https://prusament.com/wp-content/uploads/2022/10/PETG_Prusament_TDS_2021_10_EN.pdf]: menos que los ~75–80 °C supuestos en el brief. Una microturbina tiene gases de escape de cientos de °C [ESTIMADO: memoria técnica, no verificado]. Combustible a bordo de un bote de aluminio: fuera del alcance de una propulsión eléctrica ≤48 V |
| Carcasa en **segmentos apilados con varillas roscadas pasantes** (M8 inox) | **SÍ** | Ideal para el volumen ≤210×210×260 mm de la Ender-3 S1: el tubo o soporte se parte en anillos y los tirantes metálicos toman la tracción y la flexión. En P1 conviene **A4 (316)**, no A2 [ESTIMADO: memoria técnica, no verificado] |
| **Refrentado en torno** de las caras de unión impresas (V1 04:29) | **SÍ** | P1 tiene torno: planitud para juntas y alineación de bujes |
| Toma de agua desde la zona de presión para refrigerar (V1 06:52) | **SÍ, adaptada** | En la cola larga, una toma o scoop en la zona de la hélice puede alimentar los bujes lubricados por agua del tubo |
| Grasa + aceite inyectado en el eje (V1 02:32–02:43) | **NO** | En agua salobre, mejor bujes **lubricados por agua** (diseño P1) sin aceite: no contamina y el aceite se lava igual [ESTIMADO: memoria técnica, no verificado] |
| Rodamientos de bolas "stainless" sumergidos (S6801Z = **440C**) | **Con cuidado** | El 440C es martensítico y, en agua salobre, se oxida más que el 316 [ESTIMADO: memoria técnica, no verificado]. En P1, los rodamientos de bolas van **arriba, en la zona seca** (cardán o polea); abajo, bujes poliméricos |
| Empuje axial sobre plástico (crítica a V1) | **SÍ, como lección** | En P1, el empuje de la hélice (~100–200 N a crucero [SUPUESTO]) y los golpes de basculación deben ir a un **tope metálico** (collar o arandela de empuje + seguro) contra una pieza metálica. El PETG trabaja solo a compresión distribuida |
| Álabes impresos "extra thick" y alto paso | **NO** para la hélice principal | P1 usa una hélice comercial con pasador de corte. DK The Welder confirma que las hélices impresas finas se deforman (comentario). Lo impreso, para protector y carenados |
| Impulsor metálico de chapa soldada (V2) | **NO** | Más costo y riesgo que una hélice comercial de 7,8" |
| Protección inferior ("protective plate", V1 10:47) | **SÍ, concepto** | En P1: protector de hélice impreso más patín o skeg sacrificable delante de la hélice |
| Motor sumergido en la punta del tubo (DK The Welder) | **Alternativa a evaluar** | Elimina la correa HTD y el eje largo, pero el motor queda bajo agua salobre (pod inundado) y la masa en la punta complica el kick-up. Conviene compararlo en el estudio de alternativas |

### 7.2 Cálculo: rendimiento propulsivo ideal (Froude / disco actuador) a 6 km/h
Bases: V0 = 1,667 m/s; ρ = 1010 kg/m³ (salobre) [SUPUESTO]; empuje de crucero T = 100/150/200 N [SUPUESTO]; tobera del jet Ø50–70 mm [SUPUESTO, escala V1/V2 no medida]; hélice Ø198 mm (7,8") y Ø229 mm (9") [SUPUESTO]. Jet: T = ρ·A·Vj·(Vj−V0). Hélice: T = 2ρA·v·(V0+v), con Vj = V0+2v. η_ideal = 2/(1+Vj/V0).

| T [N] | P útil [W] | Jet Ø50: η / P_ideal | Jet Ø70: η / P_ideal | Hélice 7,8": η / P_ideal | Hélice 9": η / P_ideal |
|---|---|---|---|---|---|
| 100 | 167 | 0,35 / 482 W | 0,44 / 382 W | 0,71 / 235 W | 0,75 / 221 W |
| 150 | 250 | 0,30 / 843 W | 0,38 / 658 W | 0,64 / 389 W | 0,69 / 362 W |
| 200 | 333 | 0,27 / 1258 W | 0,34 / 972 W | 0,59 / 562 W | 0,64 / 519 W |

[ESTIMADO: teoría de cantidad de movimiento, sin pérdidas de bomba, toma ni conducto]. Con las pérdidas reales del jet (rendimiento de bomba y toma), la brecha **crece**. Para la misma batería y 2 h de crucero, el jet necesitaría **~1,6–2,4×** la energía de la hélice. Para la prioridad de autonomía de P1, el waterjet queda descalificado.

---

## 8. Lo que NO se pudo verificar

| Ítem | Motivo | Para seguir |
|---|---|---|
| Modelo de motor, KV y potencia usados con V1/V2 | No se muestran ni se mencionan | buscar: "Clean Energy" cleanenergy6271 waterjet motor KV |
| Ensayo en agua del jet impreso (velocidad, empuje, consumo) | No existe en V1/V2; en 8FAkgcQPcco no se ve en el storyboard | buscar: "I Built a 3D Printed Water Jet Engine for a Mini Boat" test |
| Dígitos de los rótulos (largo "6? cm", álabes "8? cm", rodamiento "S680?Z") | Storyboard de 160×90 px; la descarga del video fue bloqueada | Ver en ≥480p: V1 ~9:00, V2 ~6:27 |
| Diámetro de tobera e impulsor | No rotulado | — |
| Origen de las tomas de lancha jet del inicio (marca de agua amarilla) | Sin atribución | buscar: jet boat canal Vietnam marca amarilla "Thánh Chế" (sin confirmar) |
| Artículos o posts que citen V1 o V2 | Búsquedas sin resultados que los mencionen (solo proyectos waterjet de otros autores) | buscar: "Will My 3D Printed Jet Engine Explode at Full Speed" · "3D printed waterjet engine for my beloved boat" |
| Modelo de impresora de V1 | Pregunta en comentarios sin respuesta | — |
| Datos completos del motor Flipsky de DK The Welder | Título de AliExpress ilegible en parte | buscar: Flipsky fully waterproof motor 56113 hydrofoil KV |

## 9. URLs abiertas en esta sesión (fuentes citadas)
- https://www.youtube.com/watch?v=Z41FAXVMdKs: página, `ytInitialData`, ASR `timedtext`, comentarios, storyboard; miniatura https://i.ytimg.com/vi/Z41FAXVMdKs/maxresdefault.jpg
- https://www.youtube.com/watch?v=CkUiNuAfPL8: página, comentarios, storyboard; miniatura https://i.ytimg.com/vi/CkUiNuAfPL8/maxresdefault.jpg
- https://www.youtube.com/@cleanenergy6271/videos
- https://www.youtube.com/watch?v=JHcTss-dCXs · https://www.youtube.com/watch?v=8FAkgcQPcco · https://www.youtube.com/watch?v=LY_aolXHy3U · https://www.youtube.com/watch?v=esYxe6lsToA · https://www.youtube.com/watch?v=XHzgooJRuZE · https://www.youtube.com/watch?v=DVsitQLd6F8 · https://www.youtube.com/watch?v=I43TpB1Ul8A · https://www.youtube.com/watch?v=fMPVdl1BVZI
- https://www.youtube.com/watch?v=zTpj2lwR2Zs: descripción, comentarios, storyboard
- https://prusament.com/wp-content/uploads/2022/10/PETG_Prusament_TDS_2021_10_EN.pdf
- https://minibearings.com.au/products/12x21x5-bearings-s6801zz

---

## Hallazgos que cambian el diseño

- **V1 no es un turbojet de combustión**: es una bomba waterjet impresa en PETG, de 2–3 kg, que el autor llama "turbo jet" [VERIFICADO: transcripción 00:53, comentario del autor]. La exclusión de la combustión se mantiene por material: **HDT del PETG = 68 °C** (no 75–80 °C) [VERIFICADO: TDS Prusament]. Para P1 vale lo mismo: **ninguna pieza de PETG cargada a más de ~55–60 °C** [ESTIMADO: HDT 68 °C menos margen]. El soporte del motor BLDC y la zona de la polea deben ser metálicos o estar ventilados.
- **Ninguno de los dos videos aporta datos de rendimiento** (0 mediciones de velocidad, empuje, consumo, motor o batería). No se pueden usar para dimensionar P1; solo como fuente de técnicas constructivas.
- **Waterjet descartado como propulsión principal de P1**: a 6 km/h su η_ideal es 0,27–0,44, contra 0,59–0,75 de una hélice de 7,8–9". Eso es **~1,6–2,4× más energía** para las mismas 2 h [ESTIMADO §7.2]. Además requiere perforar el fondo del casco, no permite kick-up y no tiene reversa sin cuchara.
- **Adoptar en P1 la arquitectura "segmentos impresos + tirantes pasantes M8 inox"** de V1/V2 (V2 ~4:13) para el tubo, el carenado o el soporte que excedan 210×210×260 mm. Usar inox **A4/316**, no el de calidad genérica.
- **Refrentar en torno** todas las caras de unión impresas (V1 04:29) antes de pegar o sellar. P1 tiene torno.
- **Empuje axial a metal**: el riesgo principal señalado en V1 es el impulsor plástico empujando contra el rodamiento. En P1, el empuje de la hélice (100–200 N de crucero [SUPUESTO], picos mayores en impactos) va a un **collar o arandela de empuje metálica con seguro**, y nunca a PETG.
- **No sumergir rodamientos 440C**: el "stainless" de V2 es S6801Z = **AISI 440C** [VERIFICADO: minibearings]. En agua salobre, los rodamientos de bolas van solo en la zona seca (cardán y polea). En el tubo, bujes poliméricos lubricados por agua.
- **Toma de agua desde la zona de presión** (V1 06:52), adaptada a P1 como scoop que alimente los bujes del tubo inclinado. Es preferible a grasa o aceite inyectado en agua salobre.
- **Nueva alternativa a comparar**: el long-tail de DK The Welder pone un **BLDC sumergido Flipsky "fully waterproof"** (NZ$248,33) en la punta del tubo, con VESC (λ = 17,61 mWb, R = 41,5 mΩ medidos) y batería de 36 V. Elimina la correa HTD-5M y el eje largo, pero cuelga masa en la punta (afecta al kick-up) y deja el motor en agua salobre. Las hélices impresas finas se deformaron (comentarios): **mantener la hélice comercial**.
- **No comprar los STL del canal** (20 USD por e-mail): no hay repositorio público, hay un reclamo por archivos pagados que no llegaron y el canal también publica contenido de "energía libre". Credibilidad baja.
