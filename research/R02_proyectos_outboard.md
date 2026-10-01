# R02 — Proyectos comparables: fueraborda impresos, conversiones de trolling motor, long-tail / surface drive eléctricos

Consulta: 2026-10-01. Autor: subagente de investigación P1. Alcance: proyectos reales (DIY y alguna referencia comercial) que sirvan para contrastar la arquitectura candidata de P1, que es una "cola larga" con motor BLDC seco arriba, correa HTD-5M, eje 316 inclinado, hélice comercial de ~7,8" y kick-up.

## 0. Método y convenciones

- **Etiquetas:** `[VERIFICADO: [Sx]]` quiere decir que el dato está en la fuente Sx, una página que abrí en esta sesión; la URL completa está en §7. `[CALCULADO: …]` es una cuenta mía hecha con datos verificados. `[ESTIMADO: base]` y `[SUPUESTO]` son lo que dicen.
- **Cómo se leyó cada fuente:**
  - Printables devuelve 403 al HTML, así que leí los modelos por su API pública `api.printables.com/graphql/` (consulta `print(id)`). El enlace al modelo se da igual, para que se pueda ubicar.
  - Endless Sphere bloquea WebFetch con Anubis; lo leí con `curl` (UA "curl/8.0").
  - MakerWorld lo leí por `makerworld.com/api/v1/design-service/design/<id>`.
  - De Thingiverse solo leí la `meta description` del HTML.
  - YouTube: solo verifiqué **títulos** vía oEmbed. **No vi el contenido de ningún video**, así que nada de lo que sigue sale de un video.
- **Las cifras de foros son lo que reporta el autor.** No las validó nadie más, salvo que se diga otra cosa. Las mediciones con wattímetro + GPS (MCDenny, ElectricKayak, Irie) son las de mejor calidad.
- **Unidades:** las millas, nudos y pulgadas del original se convierten a SI con 1 mph = 1,609 km/h, 1 kn = 1,852 km/h y 1" = 25,4 mm.

---

## 1. Tabla resumen

Relevancia para P1: **A** = alta, **M** = media, **B** = baja. "Agua": S = salada o salobre, D = dulce, ? = no declarada.

| # | Proyecto | Arquitectura | Bote · personas · agua | Motor · V · ESC | Transmisión | Hélice | Resultado medido | Falla principal documentada | Rel. |
|---|---|---|---|---|---|---|---|---|---|
| A1 | Olly Epsom, Johnson 2 hp → eléctrico [S1][S2] | Motor seco arriba, pata original | Dinghy inflable, 2 p., **S** (estuario del Clyde) | MAC12500-3A 1 kW 48 V con sensores; controlador de 1500 W | Eje vertical + engranajes cónicos originales (solo avance) | Original | ~3 kn (5,6 km/h) "generalmente"; canoa 2 p.: >10 km en <2 h con 1 kWh | Controlador subdimensionado se quemó; cargador se incendió; motor a 80 °C | **A** |
| A2 | "Infinity", Johnson 4W76M [S3][S4] | Motor seco arriba, pata original | Inflable pesado, 2 p. + equipo, D (lago) | C80100 130 kV (comprado a Alien Power System; el C8085 previo era Turnigy); Alien 250 A; 24 V plomo | Acople rígido al eje original | Original | **7 km/h** máx. (GPS) | C8085 (defectuoso) se recalentó "en segundos" a ~40 A | **A** |
| A3 | "alan-c", pata Evinrude 3 hp [S5] | Motor seco arriba, pata original | Skiff a remo de 14 ft, ? | Turnigy C80-100; 9S Li | Pata original | ? | 370 W → ~5 mph (8,0 km/h); 1,5 kW máx. | (sin fallas reportadas) | M |
| A4 | Dominic Peters, E-Kayak [S6] | Motor seco arriba, eje vertical propio | Kayak, 1 p., D (canal Rideau) | Turnigy 6374 168 kV; YEP 120 A; 12S (50,4 V máx.) ~500 Wh | Cónicos 2:1, aluminio 6061 + PLA | ? | Crucero ~300 W | Eje cortado en el cónico; prisioneros rotos; con la hélice en arena a fondo se dañaron los cónicos (patinan >500 W) | **A** |
| B1 | "ElectricKayak", boatdesign [S7][S8][S9] | Trolling modificado → long-tail con eje flexible y motor seco | Kayak inflable de 13', 1–2 p., D | Minn Kota 40 lb → Turnigy SK3-6374-149 kV; ESC naval de 120 A | Directa por eje flexible (extensión de taladro de 40–48") | APC 10×6 (de aeromodelo) | 5 km/h: **~150 W de serie ("from memory") → 45 W modificado → 30 W long-tail**. Medido de serie: 8,6 A a 5,1 km/h ≈ 105–110 W [CALCULADO: 8,6 A × ~12,5 V] | Eje flexible pandeó a 11 km/h (lo resolvió acortando o engrosando el eje); recinto antirruido calienta | **A** |
| B2 | Sean d'Epagnier, hackaday.io [S10] | Motor seco + 2 etapas HTD-5M con poleas **impresas** | Trimarán de 33 ft, ? | 6350 270 kV; ESC de 30 A; LiFePO₄ 12 V 40 Ah | 15:1 → 11,25:1 (poleas impresas de 60/90/120 dientes) | Hélice de carbono 32×10" (de aeromodelo) | 70 W → ~1 kn; 120 W → 2 kn | Polea patina sobre el eje; una chaveta en plástico "imposible"; la correa salta dientes | **A** |
| B3 | "Lachie", boatdesign [S11] | Long-tail con eje recto | Kayak, 1 p., ? (Tailandia y Australia, 3 años) | Taladro brushless de 18 V | Directa | 5" | ~5 km/h; batería de 4 Ah ≈ 2 km | (ninguna en 3 años; sin rodamientos, tubo plástico agrícola) | M |
| B4 | "blisspacket", Endless Sphere [S12] | Long-tail directo con outrunners de RC | Bote de 15 ft, ? | 2× motor 6374 + ESC Phoenix, 24 V | **Directa, sin reducción** | Pequeña, de bajo paso | — | **Quemó 2 motores 6374 y varios ESC** sin llegar a potencia plena | **A** (falla) |
| B5 | "Irie", surface drive [S13][S14][S15] | Eje inclinado pasante (short-tail) con trim | Aluminio semi-V de 12', 1 p., D | Motenergy ME1004 (escobillas, 10 kW cont.); Alltrax 48 V | Directa (acople Nova jaws) + rodamiento de empuje | 9,25×10 con cup; luego 10,5×12 | 16 mph a 8,9 kW; 25 mph a 13,7 kW | Ventilación: "estancado en 8 mph" con eje fijo a 15° | M |
| B6 | "Bazaki", Endless Sphere [S16] | Correa dentada que baja por la pata hasta la hélice | Inflable de fondo rígido en V, ? | 1) Crystalyte HT3525, 90 V 80 A; 2) Golden Motor 10 kW refrigerado por líquido | 1) Correa 1:5; 2) motor "on top of where the ICE was" (pata original, ~4400 rpm de motor) | 8×8 (con el motor 2) | Motor 1: ninguno (se quemó). Motor 2: 20 km/h a 7–8 kW (GPS) | Motor 1 (correa) quemado tras pocos intentos de planear | B |
| C1 | Anton, Crescent 5 hp [S17] | **Pod sumergido** (motor bajo la línea de flotación) | ?, ? (el "lake" del artículo es una introducción genérica) | BLDC rebobinado de 180 kV → 77 kV | Directa | **Impresa 3D** | — | **Entrada de agua**, el problema principal | **A** (falla) |
| C2 | Bare Naked Embedded, e-kayak [S18] | Motor sumergido (motor estanco de e-foil) | Kayak inflable Intex Explorer, **2 p.**, D probable (canal de Ballard a Lake Union, aguas arriba de las esclusas) | Flipsky 5062 160 kV (500 W nominales, 12 A); VESC 6.7 70 A; LiFePO₄ 24 V 480 Wh | Directa; deriva/soporte **impreso** | La que trae el motor | 1 p. 6,75 km/h; **2 p. 5,6 km/h con ~170–185 W** [CALCULADO: 60 % × 24–25,6 V × 12 A]; 22,5 km en 3,5 h | **Algas en la hélice detuvieron el motor**; VESC >50 °C dentro de la caja de batería | **A** |
| C3 | "Igor", Printables 1833248 [S19] | Motor sumergido (estanco) con carcasa **PETG** impresa | Bote de espejo estándar, ? | Flipsky 85135 + 75350; **20S (84 V)** | Directa; spline de Yamaha <6 hp | De aluminio, Flipsky ("desbalanceada") | (sin datos publicados) | Las 2 hélices compradas venían desbalanceadas | M |
| C4 | "_hori", Thingiverse 2947306 [S20] | Motor de RC sumergido | Kayak, ? | Aeolian C5065 320 kV ~600 W; 3S; ESC de 100 A | Directa | Impresas (`200_109_2L/3L`) | — | — | B |
| C5 | "Rain And Storm", Printables 681590 [S21] | Rim-drive (Hydromea DiskDrive 80) en carcasa PETG-CF impresa | Concepto | 18–24 V, ESC ≥500 W | Rim | Rim | (sin pruebas) | Advierte: arena y limo **atascan** el rim | M (descarte) |
| D1 | MCDenny, Minn Kota Endura 36 [S22] | Trolling + PWM + hélice de aeromodelo + carenado | Canoa de 14' LWL, 300 lb en total | Escobillas, 12 V | Directa | APC 10×6 + spinner | A 4,3 mph: **330 W de serie → 190 W modificado** | Puntas finas que se mellan | **A** |
| D2 | "Current", Minn Kota C2 30 lb [S23] | Trolling + ESC de RC con escobillas | ?, D | Hobbywing QUICRUN 1060 → WP 860 | Directa | APC 10×6 → original | — | ESC encerrado se recalentó a los 30 min; la hélice de RC enganchaba algas | M |
| E1 | Arcada UAS (Finlandia), hélice de bow-thruster PETG [S24] | Hélice impresa en servicio | Bote de los años 80, **S** (agua de mar) | (no declarado) | — | **PETG FFF**, 6 palas | **+25 % empuje**, 4 meses | **Pala fisurada** al desmontar; percebes | **A** |
| R1 | Torqeedo Ultralight 403/1103 (comercial) [S25] | Pod sumergido de referencia | Kayak de 4,3 m | 29,6 V | Directa | De fábrica | Rendimiento global máx. **45 % / 49 %** | — | ref. |
| R2 | Backwater SWOMP E-Series (long-tail eléctrico comercial) [S26] | Long-tail eléctrico | Botes de pantano y jon boats | MV7: 56 V 54 Ah; MV20: 72 V 200 A | **Directa, sin correas ni engranajes** | — | (sin datos de rendimiento) | — | ref. |

---

## 2. Fichas — grupo A: motor seco arriba + pata de fueraborda (eje vertical + engranajes cónicos)

### A1 — Olly Epsom: Johnson 2 hp de 1974 → BLDC de 1 kW, 48 V (Practical Boat Owner)
- **Links:** PBO [S1]; resumen en Hackaday [S2].
- **Escala y agua:** dinghy inflable con 2 personas ("Myself and my friend Corey were on the dinghy"), en servicio desde mayo de 2018 en el estuario del Clyde, con "fair swell" [VERIFICADO: [S1]]. También probado en una canoa canadiense con 2 personas en Loch Lomond [VERIFICADO: [S1]].
- **Motor y tensión:** MAC12500-3A, 48 V, con sensores, ~4000 rpm, 1 kW; el donante daba 1,49 kW a ~4000 rpm [VERIFICADO: [S1]].
- **ESC:** el controlador que vino con el motor "proved less than" adecuado y se quemó a potencia plena; lo reemplazó uno de 1500 W [VERIFICADO: [S1]].
- **Batería:** Li-ion de 1 kWh (~20 Ah a 48 V); dimensionada para "a minimum of 40 minutes at full power" [VERIFICADO: [S1]].
- **Transmisión:** placa de transición de aluminio de 10 mm cortada con láser; estría torneada con rosca de 8 mm y contratuerca; pata y caja de engranajes originales, **solo avance** [VERIFICADO: [S1]]. El autor advierte que un engranaje sin marcha atrás de diseño "won't be designed to operate backwards and there won't be a thrust bearing" [VERIFICADO: [S1]].
- **Hélice:** la original.
- **Sellado y refrigeración:** motor y controlador de e-bike con clasificación IP55 ("essentially splash proof"); Arduino y electrónica de control en una caja IP67. Ventilador impreso en el eje del motor + 4 ventiladores de 12 V comandados por Arduino. Temperatura del motor con pico de ~80 °C [VERIFICADO: [S1]]. *(Corregido en la verificación: antes decía "cajas IP55 y IP67" y "80 °C en la placa base"; la fuente da IP55 para motor y controlador y no ubica los 80 °C en la placa base.)*
- **Qué funcionó:**
  - 50 min a acelerador pleno en un banco hecho con un contenedor de basura lleno de agua, sin fallas [VERIFICADO: [S1]].
  - Con el dinghy, ~3 kn "generally" [VERIFICADO: [S1]].
  - En la canoa, "over 10km in under two hours on one battery charge" y "speeds of 6 knots" [VERIFICADO: [S1]].
  - Siguió funcionando después de quedar totalmente sumergido en una botadura torpe [VERIFICADO: [S1]].
- **Qué falló:**
  1. Controlador quemado en la primera prueba (canal, febrero): "I was averaging 5kph until after just over a kilometre at full power there was a sudden jolt and the motor stopped". Esa vez la hélice iba medio afuera del agua [VERIFICADO: [S1]].
  2. Cargador "matched" incendiado: "even now I'm loath to leave it charging unattended".
  3. Sensor Hall de corriente destruido por polaridad invertida.
  4. Soporte demasiado alto: la hélice quedaba medio afuera si el peso no estaba atrás, y hubo que **bajar 150 mm**.
  5. Agua dentro de la caja de batería.
  6. Un error de software que detenía el motor al tocar el interruptor de reversa.

  Todo [VERIFICADO: [S1]].
- **Aplica a P1:**
  - Con un **dinghy inflable**, ~5,6 km/h es lo que se obtiene en la práctica. La fuente da "generally around 3 knots" sin precisar la carga; el viaje inaugural fue con 2 personas, pero la cifra no está atada a ese viaje.
  - La altura de la hélice tiene que ser **ajustable en ≥150 mm**.
  - Controlador con margen; cargador certificado y supervisado.
  - En las cajas, **drenaje** y no solo sellos.
  - La **marcha atrás exige** un rodamiento de empuje bidireccional.
  - Energía: ≤100 Wh/km en la canoa [CALCULADO: 1 kWh / ≥10 km, cota superior].

### A2 — "Infinity": Johnson 4W76M + C80100 130 kV, 24 V (Endless Sphere)
- **Links:** [S3], [S4].
- **Escala:** "The inflatable is quite heavy with me, my friend and all the gear" (2 personas), en un lago [VERIFICADO: [S3]].
- **Motor y ESC:**
  - Primero un Turnigy C8085 de 180 kV, que se recalentó "in seconds, drawing only about 40A" (defectuoso, lo devolvió). Lo reemplazó un **C80100 de 130 kV**, comprado en alienpowersystem.com [VERIFICADO: [S3]].
  - ESC Alien de 250 A, 3–8S, para auto; interfaz de acelerador de 0–5 V para un puño de e-bike [VERIFICADO: [S3]].
- **Batería:** 2 de plomo de 12 V en serie (24 V) [VERIFICADO: [S3]].
- **Transmisión:** motor atornillado a la placa del motor original, con acople rígido al eje vertical [VERIFICADO: [S3]]. Le sugirieron un acople con algo de flexibilidad [VERIFICADO: [S3]].
- **Resultado:** "Max speed is 7km/h measured with gps"; "Nothing gets hot hot any more" (sic) [VERIFICADO: [S3]]. Costo ~300 € sin baterías; pata "ahogada" de 25 € [VERIFICADO: [S4]].
- **Falla o riesgo:** le quitó el resorte de retorno al acelerador para "set my speed" [VERIFICADO: [S3]]. Es un **riesgo de seguridad**: sin hombre al agua, el bote sigue andando.
- **Dato de contexto:** "Almost every outboard motor between 4 and 20 hp has a gear reduction of 2.33 : 1 … about 2500 rpm prop speed at WOT" (Bazaki, en el mismo hilo) [VERIFICADO: [S4]].
- **Aplica a P1:**
  - Inflable pesado + 2 personas: **7 km/h máx.** con un motor de RC de clase 80 mm a 24 V. No hay medición de potencia; la eslora del inflable no está declarada.
  - **Kill switch obligatorio**; nada de acelerador "con traba" sin cordón de hombre al agua.

### A3 — "alan-c": Turnigy C80-100 sobre una pata Evinrude de 3 hp (Endless Sphere)
- **Link:** [S5].
- **Datos:**
  - "steerable and mobile at 100W"; "370W (1/2hp) is my chosen cruising power which gives about 5mph (GPS)"; máximo 1,5 kW con 9S, que "just puts the bow up in the air" [VERIFICADO: [S5]].
  - Bote: skiff a remo de 14 ft [VERIFICADO: [S5]].
- **Aplica a P1:** aun en un casco largo de remo, 8 km/h cuesta ~370 W. Un jon boat de <2,5 m va a necesitar bastante más para la misma velocidad [ESTIMADO: casco más corto y romo → Froude mayor, ver §5].

### A4 — Dominic Peters: E-Kayak con motor seco, eje vertical y cónicos 2:1 (aluminio + PLA)
- **Link:** [S6].
- **Motor:** Turnigy 6374 168 kV ("rated at 2400W and 80A peak") [VERIFICADO: [S6]].
- **ESC:** YEP de 120 A (clon de YGE) [VERIFICADO: [S6]].
- **Batería:** 6 packs LiPo 4S 5,2 Ah en 3S2P → 50,4 V máx., 10,4 Ah, "around 500Wh" [VERIFICADO: [S6]].
- **Transmisión:**
  - Eje vertical + par cónico a 90° con reducción 2:1 [VERIFICADO: [S6]].
  - Rodamientos radiales y **un rodamiento de empuje en la tapa trasera** [VERIFICADO: [S6]].
  - "stuffing box filled with axle grease at the prop shaft output" [VERIFICADO: [S6]].
- **Materiales:** aluminio 6061 mecanizado; piezas negras en **PLA**, "I haven't had any issues" [VERIFICADO: [S6]].
- **Kick-up y soporte:**
  - Pivote basculante con pasador de acero en un bloque de 6061; placas de carbono [VERIFICADO: [S6]].
  - Dos cables de tensión contrarrestan el momento del empuje. Los tornillos M3 originales dejaban patinar el cable y los cambió por 8-32 [VERIFICADO: [S6]].
  - El autor reconoce que el diseño "doesn't accommodate lateral ones very well" (cargas al girar) [VERIFICADO: [S6]].
- **Electrónica:** ESC sobre placa de aluminio + disipador de CPU: "ESC temp never goes higher than 10-15 deg above ambient" [VERIFICADO: [S6]].
- **Qué falló:**
  1. En la 1.ª prueba "the driveshaft promptly sheared" justo en la unión con el engranaje cónico; lo resolvió con un eje de mayor diámetro.
  2. "Broken set screws, stripped servo gears, and leaky driveline casings".
  3. **"I brushed my hand on the throttle pot … full throttle while the propeller dug into the sand"**: los cónicos quedaron dañados y desde entonces patinan por encima de 500 W, cuando antes había visto 2500 W en telemetría.

  Todo [VERIFICADO: [S6]].
- **Resultado:** "most at home cruising around 300W", a una velocidad "similar to the row boats" del canal Rideau (agua dulce), con "1 ½ to 2 hours of run time" con ~500 Wh. No da la velocidad en números [VERIFICADO: [S6]].
- **Aplica a P1:**
  - (a) Unir eje y engranaje o polea con **pasador pasante o estría**, no con prisionero.
  - (b) **Armado con acelerador en cero + cordón**: un roce del acelerador con la hélice en arena rompe la transmisión, así que hace falta un pasador de corte que sea el eslabón débil a propósito.
  - (c) El kick-up tiene que resistir cargas **laterales** al girar.
  - (d) ESC montado en placa metálica.

---

## 3. Fichas — grupo B: long-tail, eje inclinado y surface drive con motor seco

### B1 — "ElectricKayak" (boatdesign.net): Minn Kota optimizado → long-tail con eje flexible y BLDC seco
- **Links:** [S7] (pág. 1), [S8] (pág. 2), [S9] (pág. 6).
- **Escala:** kayak inflable "13' inflatable Helios 2" (26" de manga en la flotación), en un lago, siempre medido con agua "glassy calm" [VERIFICADO: [S7]][VERIFICADO: [S8]].
- **Método de medición:** tramos de 500 m con promedio GPS; tensión y corriente antes del controlador [VERIFICADO: [S8]]. Es de los mejores métodos que encontré.
- **Etapa trolling (Minn Kota de 40 lb):**

| Configuración | Corriente @ 5,1 km/h | Fuente |
|---|---|---|
| Hélice de serie (50 % de acelerador) | 8,6 A | [VERIFICADO: [S7]] |
| APC 10×6 de empuje + spinner de 3" (37 % de acelerador) | 5,7 A | [VERIFICADO: [S7]] |
| Solo, tubo de serie (12,5 V) | 4,9 A | [VERIFICADO: [S8]] |
| Solo, tubo carenado | 4,1 A | [VERIFICADO: [S8]] |

  → Ahorro del 34 % por la hélice y del 16 % por el carenado [CALCULADO]. Que la primera prueba fuera con 2 personas lo infiero de "I was by myself so the numbers aren't comparable with earlier" [ESTIMADO: inferido del texto].
- **Su estimación de rendimiento global:** "1) controller 90–95 %, 2) MK motor 70–80 %, 3) propeller 65–75 % … 47% system efficiency" [VERIFICADO: [S8]] (es una estimación del autor, no una medición).
- **Versión 4, long-tail con BLDC seco:**
  - **Motor:** Turnigy Aerodrive SK3-6374-149 kV, "maximum current rating of 70A and peak output power of 2250 watts", eje de 8 mm [VERIFICADO: [S9]].
  - **ESC:** HobbyKing naval de 120 A; elegido "for waterproofness and reverse". Timing pasado a neutro por eficiencia [VERIFICADO: [S9]].
  - **Mecánica:**
    - Eje flexible de 3/16", de extensiones de taladro de 40–48" [VERIFICADO: [S9]].
    - Soporte mecanizado con **dos rodamientos inoxidables que toman todas las cargas**; el motor "not suited for the loads" del eje [VERIFICADO: [S9]].
    - **Brazo de torque flexible** (tapa de goma) [VERIFICADO: [S9]].
    - Pivote vertical "for clearing weeds" [VERIFICADO: [S9]].
  - **Ruido y calor:** recinto de PVC de 3"×6" contra el ruido. "At a sustained 30-100 watts it seems OK (peak measured temp 60 C or less)"; para potencias mayores saca la tapa [VERIFICADO: [S9]].
  - **Eficiencia:** "I now cruise around 30 watts at 5kph versus about 45 watts with the MK (from memory the original stock MK was upwards of 150 watts)" [VERIFICADO: [S9]] → 6 Wh/km [CALCULADO]. El autor tiene kayaks de mar y el inflable; **no dice en cuál midió los 30 W**.
  - **Límite mecánico:** "The 11 kph limit was due to shaft buckling. Shortening the shaft or going to a larger diameter solved the problem"; y "I suspect significantly higher speeds would require a supported shaft" [VERIFICADO: [S9]].
  - **Otro dato:** con un taladro DeWalt de 20 V y hélice de 12×6, su kayak ("mine"; no dice que sea de mar) "requires about 200 watts to run 6 knots" (~11 km/h, a ~1300 rpm) [VERIFICADO: [S9]].
- **Qué falló o quedó abierto:** refrigerar sin perder el silencio, y el eje flexible (vida a fatiga desconocida: "one has to exceed the limit a few times to know") [VERIFICADO: [S9]].
- **Aplica a P1:**
  - Es la **prueba más directa** de que un long-tail con motor seco baja el consumo frente a un trolling. Comparación limpia (mismo autor, misma velocidad): **−33 %** frente al Minn Kota ya optimizado [CALCULADO: 30/45]. El "−80 %" frente al de serie [CALCULADO: 30/150] usa una cifra "from memory" y posiblemente otra carga y otro casco; frente al de serie medido (8,6 A ≈ 105–110 W a 5,1 km/h, quizá con otra carga) sería ≈ −72 % [CALCULADO]. Usar −33 % como dato firme.
  - Ojo: es **transmisión directa** (sin reducción) con una hélice APC 10×6 y funciona bien a 30–100 W. La necesidad de reducción depende del tamaño de hélice y del empuje (ver B4).
  - Lecciones: (1) aislar los rodamientos del motor del empuje y de la flexión; (2) **eje rígido soportado** si se quiere pasar de ~10 km/h; (3) la carcasa antirruido necesita ventilación por encima de ~100 W.

### B2 — Sean d'Epagnier (hackaday.io 174537): fueraborda con 2 etapas HTD-5M de poleas impresas
- **Link:** [S10] (página + logs del 18/7, 14/8, 26/8, 27/8, 30/8 y 7/9/2020).
- **Escala:** trimarán de 33 ft (1973) [VERIFICADO: [S10]].
- **Motor y energía:** outrunner 6350 de 270 kV para skate; ESC de 30 A; LiFePO₄ 12 V 40 Ah [VERIFICADO: [S10]].
- **Transmisión:**
  - Correas HTD-5M de 9 mm × 1 m y 15 mm × 2 m. Poleas de aluminio de 20 y 24 dientes; **poleas impresas** de 120 dientes (9 mm) y 60 dientes (15 mm) con **12 % de relleno**, 4–5 h cada una.
  - "My printer is limited to 130 tooth size at 5mm pitch in a single piece".
  - Reducción 20:120 × 24:60 = **15:1**; después, con una polea de 90 dientes, **11,25:1**.

  Todo [VERIFICADO: [S10]].
- **Ejes y rodamientos:** eje de hélice de varilla roscada de 1/2" inoxidable endurecido; eje intermedio Nitronic de 10 mm; **rodamiento de empuje**; rodamientos cerámicos de 10 mm [VERIFICADO: [S10]].
- **Hélice:** de carbono de 32×10", de aeromodelo [VERIFICADO: [S10]].
- **Resultados:**

| Condición | Resultado | Fuente |
|---|---|---|
| Hélice girando en aire | 15 W (fricción) | [VERIFICADO: [S10]] |
| 1.ª prueba en agua, polea patinando | 0,75 kn a ~65 W | [VERIFICADO: [S10]] |
| Correas tensadas, 15:1 | 5,4 A a 13 V ≈ 70 W → ~1 kn | [VERIFICADO: [S10]] |
| 11,25:1 | 120 W → 2 kn | [VERIFICADO: [S10]] |

  El autor afirma "efficiency is currently around 50% vs 20% for a typical electric trolling motor" (no explica el método) [VERIFICADO: [S10]].
- **Qué falló:**
  1. "**It is impossible to use a keyed shaft on a plastic pulley, the plastic stretches**". Lo arregló con un tornillo inoxidable pasante por eje y polea.
  2. **"pulley slips on shaft"**.
  3. Las correas saltaban dientes y hubo que tensarlas "considerably"; tuvo que "hammer the pulley on the shaft". Él mismo propone un **tensor (idler) ajustable** en cada correa.
  4. Reimprimió varias veces los portarrodamientos, con offsets distintos, para alinear. "The shafts need slight angles (1 or 2 degrees) … to ensure the belts walk the right direction".

  Todo [VERIFICADO: [S10]].
- **Aplica a P1:**
  - Es la referencia más cercana a la **correa HTD-5M con piezas impresas**. Pero opera a **≤120 W**, y P1 va a transmitir varios cientos de W.
  - Consecuencias:
    - Polea del eje de hélice **de aluminio comercial** o impresa con **cubo metálico + pasador pasante**.
    - **Tensor ajustable** (ranuras o idler).
    - Portamotor con ajuste fino de alineación.
    - Rodamiento de empuje que no sea el del motor.
  - Precisión de la verificación: las fallas de B2 (polea que patina, correa que salta) ocurrieron a **≤70 W**. Los 120 W corresponden a la prueba posterior, ya corregida y sin fallas reportadas.

### B3 — "Lachie" (boatdesign 63757): long-tail con taladro de 18 V
- **Link:** [S11].
- **Datos:** "longtail straight shaft connected to an 18v brushless drill. Speed approx 5 km. and a 4ah battery lasts about 2km distance … 5in prop" [VERIFICADO: [S11]].
- **Uso:** "both in Thailand and Australia over three years, I had no bearings, the shaft was threaded, and the pipe the shaft went through was an agricultural plastic pipe and no problems" [VERIFICADO: [S11]].
- **Energía:** ~36 Wh/km y ~180 W [CALCULADO: 72 Wh nominales / 2 km; a 5 km/h].
- **En el mismo hilo:**
  - "You need to have thrust bearings in the shaft. Electric motors … are not designed to have a load parallel to the shaft" [VERIFICADO: [S11]].
  - Un motor 70110 de 100 kV a 42 V (4200 rpm) es "too much" para una hélice de 10×6: "would overheat the motor" [VERIFICADO: [S11]].
- **Aplica a P1:** la arquitectura long-tail funciona aun en su versión más tosca. Pero el taladro limita par y corriente: con un BLDC de aeromodelo hacen falta reducción y un rodamiento de empuje.

### B4 — "blisspacket" (Endless Sphere 19115, pág. 2): long-tail directo que quemó motores
- **Link:** [S12].
- **Cita:** "I torched two 6374 bldc motors and various Phoenix ESC's trying to push a 15 foot boat. And I did that without using full power--24 volts if memory serves. The motors weren't geared down, and used small lowpitch props. The props stretched off the stern longtail style" [VERIFICADO: [S12]].
- **En el mismo hilo:** otro forista, respondiendo a un canoero, cuenta que con motores "whisper" "Normally we go about 5kmh with a small boat" [VERIFICADO: [S12]].
- **Aplica a P1:** **evidencia directa** de que un outrunner de RC de 63 mm sin reducción, con hélice chica, se quema en un bote tripulado. La **reducción** (la HTD de P1) y un **límite de corriente en el ESC** no son opcionales.

### B5 — "Irie" (boatdesign 56617, 58032): surface / sub-surface drive con eje inclinado en un aluminio de 12'
- **Links:** [S13] (pág. 1), [S14] (pág. 2), [S15] (hilo 58032). Videos con título verificado vía oEmbed (contenido no visto): `chA0UEGbUq4` "Homemade electric sub/surface drive" y `Gz19oxlTJvQ` "DIY Electric Surface Drive", canal Irie Electrics.
- **Bote:** "ugly 12' aluminum semi-v center console", en un lago "electric only" [VERIFICADO: [S13]]. Peso "around 600+ lbs with 1 person" [VERIFICADO: [S15]].
- **Mecánica:**
  - Eje de varilla galvanizada de 3/4" × 36" dentro de un tubo de aluminio, con **bocina de cutlass en el extremo de la hélice** y **rodamiento de empuje** en la carcasa del acople; acople Nova jaws [VERIFICADO: [S13]][VERIFICADO: [S15]].
  - Trim de +2° a −22° con actuadores lineales; giro de dirección "roughly 25-28°" [VERIFICADO: [S13]][VERIFICADO: [S15]].
  - El eje sale ~4" por encima del fondo del espejo; "I've not had issues with water leaking thru the shaft" [VERIFICADO: [S15]].
- **Motor y energía:** Motenergy ME1004 (10 kW cont., 19 kW pico, de escobillas) + Alltrax SPM 48-400; batería de módulos de Chevy Volt 2 × 48 V 45 Ah (4 kWh) [VERIFICADO: [S13]][VERIFICADO: [S14]].
- **Medido:**
  - 16 mph con 215 A a 41,5 V = 8922,5 W [VERIFICADO: [S14]].
  - 25 mph con 324 A a 42,5 V = 13,7 kW (en superficie) [VERIFICADO: [S14]].
  - Antes, con un fueraborda convertido, "8.5mph" [VERIFICADO: [S14]].
- **Lección clave (ventilación):** "Initially I had the drive fixed at 15° with no cup in the prop and would ventilate anytime I tried going faster than 8 mph … trimming the uncupped prop down to 20° doubled my speed" [VERIFICADO: [S14]].
- **Aguas someras:** "I went from 18' to about 8" of water today with no problems, just hit a switch and trim the drive" [VERIFICADO: [S14]].
- **Otro dato del hilo 58032 (Jed233, en kayak):** probó un eje de 3/8" (9,5 mm) × 26" (660 mm) de inoxidable, con un buje pasacasco de **latón** ("brass") de 3" como apoyo de la hélice. Lo movía un motor de cabrestante viejo a través de una llave de vaso con una tuerca soldada. "the harmonics were horrible with the thin shaft not being exactly balanced and the thing vibrated intolerably" [VERIFICADO: [S15]]. *(Corregido: antes decía "bronce"; y el eje sí tenía un apoyo.)*
- **Otro dato de Jed233:** con un trolling de 86 lb a 24 V, "drew 28 amps constant at full power and I averaged 6 mph in calm water", en un kayak de 15' de flotación y ~350 lb [VERIFICADO: [S15]].
- **Irie, otros datos:** "11kw pushes the boat 21mph with the drive running at the surface"; con la hélice de 9,25×10, 2700 rpm y 19–21 mph [VERIFICADO: [S15]].
- **Aplica a P1:**
  - (a) El ángulo del eje y la profundidad de la hélice tienen que ser **ajustables**. Con eje inclinado poco profundo la hélice **ventila**: hace falta placa antiventilación o un ángulo mayor.
  - (b) **Bocina lubricada por agua en el extremo de la hélice + rodamiento de empuje arriba** funcionó hasta 13,7 kW.
  - (c) Un eje fino, desbalanceado y con acople improvisado vibra aunque tenga un buje en la popa: hay que dimensionar la velocidad crítica, balancear y usar un acople de calidad.
  - (d) El trim permite navegar en ~200 mm de agua.

### B6 — "Bazaki" (Endless Sphere 53697): correa dentada que baja por la pata hasta la hélice
- **Link:** [S16]. Video con título verificado (contenido no visto): `QYR_sgHDU-4` "Electric outboard motor testing again".
- **Concepto:** "a toothed belt all the way down through the shaft to the prop" [VERIFICADO: [S16]].
- **Motor y transmisión:** hub motor Crystalyte HT3525 de 5,5 rpm/V a 90 V (~495 rpm), correa 1:5 → hélice ~2500 rpm [VERIFICADO: [S16]].
- **Falla:** "this motor was smoked after a few attempts … I had a 90V 80A = 7Kw setup" [VERIFICADO: [S16]].
- **Después:** con un Golden Motor de 10 kW refrigerado por líquido, "20 kmh at GPS at 8kw" (o 7 kW, según el mismo autor), con hélice de 8×8. Con trim tabs planea desde 14 km/h, pero la máxima baja a 16 km/h [VERIFICADO: [S16]].
- **Precisión de la verificación:** ese resultado de 20 km/h **no es de la transmisión por correa**. El autor planea el Golden Motor "at the drive shaft" y "on top of where the ICE was", y reporta "motor rpm is now about 4400 rpm, stock ice was about 5800 rpm", lo que indica la pata original con engranajes [VERIFICADO: [S16]]. La correa 1:5 solo se usó con el HT3525, que se quemó.
- **Opiniones del hilo:**
  - Long-tails "operate at the same prop RPM as the motor output shaft (usually about 3600-4600 RPM's at the prop)" [VERIFICADO: [S16]].
  - "the first virtue of using an electric motor over a ICE is the ability to get a reverse" [VERIFICADO: [S16]].
- **Aplica a P1:**
  - Planear un bote chico cuesta **kW, no cientos de W**.
  - Un hub motor de baja kV a pocas rpm con alta carga se quema: hay que mirar la corriente de fase y no solo la potencia.

---

## 4. Fichas — grupos C a E: pods sumergidos, conversiones de trolling, hélices impresas

### C1 — Anton ("Anton makes stuff"): Crescent 5 hp con BLDC en la pata inferior
- **Links:** [S17]. Video `jGhhfbPiIIc` "Electric conversion of a Crescent 5 hp outboard" (título verificado vía oEmbed; contenido no visto).
- **Datos:**
  - Estator rebobinado "from a 180-kv motor … at 77 kv with much more copper and new Hall sensors"; mucha resina epoxi para impermeabilizar [VERIFICADO: [S17]].
  - Hélice **impresa 3D** + carenado; controlador en la caña [VERIFICADO: [S17]].
- **Falla:** "problems encountered, chief of which is water intrusion". Según Hackaday, el propio Anton señala que se resolvería "reusing the original driveshaft and mounting the motor above the waterline" [VERIFICADO: [S17]]. El tipo de agua no está declarado: el "lake" del artículo es la introducción genérica de Hackaday.
- **Comentarios útiles del artículo:**
  - "many epoxies are not waterproof – they absorb water, swell and turn to jelly" [VERIFICADO: [S17]].
  - Sobre usar el eje original con el motor arriba: "You can expect to lose around 3-5%" [VERIFICADO: [S17]] (opinión de un comentarista).
- **Aplica a P1:** confirma el riesgo de un **pod sumergido DIY** en el mar. Refuerza la elección de motor seco; las pérdidas de transmisión son del orden de unidades de %.

### C2 — Bare Naked Embedded: Intex Explorer con motor estanco Flipsky 5062 y deriva impresa
- **Link:** [S18].
- **Escala:** kayak inflable Intex Explorer (la fuente no da el modelo "K2"); el autor lo quería para "two people or a weight of about 400 lbs". Prueba de autonomía saliendo desde las Ballard Locks (Seattle) y recorriendo "the full channel all the way into Lake Union and back" [VERIFICADO: [S18]]. Ese canal está aguas arriba de las esclusas, del lado del lago, así que es agua dulce [ESTIMADO: memoria técnica, no verificado]. **No es evidencia de agua salada.**
- **Motor:** Flipsky 5062 "160kV, 500W" (motor de e-foil); "5 Kg (11 lbs)" de empuje [VERIFICADO: [S18]].
- **ESC:** Flipsky FSESC 6.7 PRO de 70 A, con control de rpm por PID [VERIFICADO: [S18]].
- **Batería:** LiFePO₄ 24 V 20 Ah = 480 Wh, 4,54 kg [VERIFICADO: [S18]].
- **Soporte:** deriva diseñada en Fusion 360, **impresa** y recubierta con XTC-3D; varias iteraciones por falta de espacio para la hélice [VERIFICADO: [S18]].
- **Medido:**
  - Velocidad máxima: "With one person … about 4.2 mph (6.75 kph). And with two people … about 3.5 mph (5.6 kph)" [VERIFICADO: [S18]].
  - Corriente: el motor llega a su máximo de 12 A con solo 60 % de ciclo de trabajo [VERIFICADO: [S18]] (~14 V efectivos [CALCULADO: 0,6 × 24 V]). Las velocidades máximas de arriba se obtuvieron en ese límite, o sea con **~170–185 W de batería** [CALCULADO: 0,6 × 24–25,6 V × 12 A], no con los 500 W nominales.
  - Autonomía: "about 14 miles in 3.5 hours and still had plenty of battery left", limitado a 10,5 A / 50 % de ciclo, ~126 W según el autor [VERIFICADO: [S18]] → ≤21 Wh/km a ~6,4 km/h con 1 persona [CALCULADO: 480 Wh / 22,5 km, cota superior].
- **Qué falló:**
  1. "my motor cut out and stopped spinning … I found a bunch of seaweed in the props".
  2. "The VESC mosfets got above 50C" dentro de la caja de la batería.
  3. El kayak "does not sail straight. At all".

  Todo [VERIFICADO: [S18]].
- **Aplica a P1:**
  - **2 personas en un kayak inflable → 5,6 km/h con ~170–185 W reales** [CALCULADO] (motor de 500 W nominales limitado a 12 A). *(Corregido: antes decía "con ~0,5 kW nominales", que sugería un consumo 3 veces mayor.)* Un kayak inflable es mucho más fino que un jon boat de <2,5 m, así que la cifra es una cota inferior optimista para P1.
  - Las **algas o la maleza** frenan la hélice; aquí pasó en un canal de agua dulce. El ESC va **fuera** de la caja de la batería.
  - Hace falta dirección o aleta direccional.

### C3 — "Igor" (Printables 1833248): soporte de PETG para un Flipsky 85135 sumergido
- **Link:** [S19] (publicado el 2026-09-30, sin mediciones).
- **Datos:**
  - "It has cooling channels for the water to flow along the motor" [VERIFICADO: [S19]].
  - Batería 20S13P Li-ion "@ 84v"; tubo inoxidable de 28 mm de diámetro exterior, ~120 cm; cable de 6 AWG [VERIFICADO: [S19]].
  - Impresión: "Use PETG (or, better, PC/ABS/Nylon …), not PLA … infill of 80% … the motor casing itself … was almost 2 kg and printed for 3 days … the motor weighs almost 4 kg" [VERIFICADO: [S19]].
  - Hélice: "aluminium one that Flipsky sells, but it's a bit unbalanced (both of the 2 that I bought)". El eje acepta hélices de Yamaha <6 hp desde 1992 [VERIFICADO: [S19]].
  - Seguridad: acelerador "self-stopping … but if you use some Cruise Control, then the kill-switch is a must" [VERIFICADO: [S19]].
  - Telemetría: VESC por CAN → ESP32 + GPS para medir velocidad [VERIFICADO: [S19]].
- **Aplica a P1:**
  - PETG con mucho relleno para piezas estructurales. Una pieza grande de ~2 kg y 3 días de impresión es un **riesgo de plazo**: segmentar.
  - **Balancear la hélice comprada** o verificarla antes de usarla.
  - Telemetría GPS + VESC para medir Wh/km.
  - 84 V queda **fuera** del límite de 48 V de P1.

### C4 — "_hori" (Thingiverse 2947306): motor de RC sumergido para kayak
- **Link:** [S20] (solo la meta description).
- **Datos:** "3S LiPo, ESC 100A, Aeolian C5065KV320 Outrunner Brushless Motor, 320 kv, ~600W, 50A, (max.2kW), 1 piece standard servo". Hélices impresas iteradas, "200_109_2L.stl", "200_109_3L.stl" [VERIFICADO: [S20]]. Videos con título verificado: `UIW-VlGq6ZM` "Motor teszt …" y `5N6Qsuc3aRI` "Csiga teszt 3 …" (contenido no visto).
- **Aplica a P1:** solo como dato de que un outrunner de RC sumergido en agua dulce funciona en un kayak. No hay datos de durabilidad ni de salinidad.

### C5 — "Rain And Storm" (Printables 681590): rim-drive en carcasa impresa
- **Link:** [S21].
- **Datos:**
  - Usa un Hydromea DiskDrive 80 comprado; cuerpo de PETG-CF con canales rellenos de fibra + epoxi; o-rings; ESC de 18–24 V, ≥500 W; **kill switch con imán y reed** en el cordón [VERIFICADO: [S21]].
  - Advertencias del autor: "Do not run dry" y "**Avoid hitting the ground — silt and sand can clog and seize the thruster**" [VERIFICADO: [S21]].
  - Es un concepto sin pruebas publicadas: 10 likes, 24 descargas [VERIFICADO: [S21]].
- **Matiz:** el mismo autor promociona el rim-drive como "harder to tangle or damage — can go where it's shallow" [VERIFICADO: [S21]]. Lo de la arena es una **advertencia** del autor, no una falla observada: no hay pruebas publicadas.
- **Aplica a P1:** desaconseja el rim-drive para un uso con arena y poca profundidad (por la advertencia, no por evidencia de campo). Toma la idea de kill switch magnético con reed para el cordón.

### D1 — MCDenny (boatdesign 27996, pág. 17): Minn Kota Endura 36 con PWM + APC 10×6 + carenado
- **Link:** [S22].
- **Método:** canoa de 14' de eslora de flotación, "All up weight was about 300 lbs"; GPS promediado en 30 s; wattímetro junto a la batería [VERIFICADO: [S22]].

| Configuración | Velocidad | Potencia (batería) | Wh/km [CALCULADO] |
|---|---|---|---|
| De serie, posición #5 | 4,3 mph (6,9 km/h) | 330 W | 47,7 |
| De serie, posición #4 | 2,9 mph (4,7 km/h) | 178 W | 38,1 |
| APC 10×6, #5 | 5,1 mph (8,2 km/h) | 410 W | 50,0 |
| PWM + APC 10×6 a 4,3 mph | 6,9 km/h | 260 W | 37,6 |
| PWM + APC 10×6 + carenado NACA 0025 + spinner | 6,9 km/h | **190 W** | **27,5** |

  Datos de la tabla: [VERIFICADO: [S22]].
- **Durabilidad de la hélice:** "I tried about a dozen different APC model airplane props … the 10 x 6 gave the best"; "The tips are very thin and prone to getting dinged up"; usó pasador de corte con una ranura cortada en el cubo [VERIFICADO: [S22]].
- **Aplica a P1:**
  - El **carenado del tubo + spinner + la hélice correcta** dan **−42 %** de potencia a igual velocidad [CALCULADO: 190/330]. Por partes: hélice −21 % (330→260 W) y carenado + spinner −27 % (260→190 W) [CALCULADO]. El autor aclara que hubo viento de 5–8 mph y oleaje de 3–6" y que sus supuestos sobre el promedio ida y vuelta pudieron fallar [VERIFICADO: [S22]].
  - Para P1: tubo del eje con **perfil NACA** y no redondo.
  - Las hélices finas de aeromodelo se mellan: con arena y piedras conviene **una hélice de fueraborda** (como ya prevé P1).

### D2 — "Current" y otros (Endless Sphere 70903, 90678): trolling con ESC de RC
- **Links:** [S23], [S27].
- **Datos:**
  - Minn Kota C2 de 30 lb con Hobbywing QUICRUN 1060: "started over heating after 30 min because in was all closed up". Lo resolvió con un WP 860, ventilación y un ventilador de CPU [VERIFICADO: [S23]].
  - Hélice de RC de 10×6: "plain plastic ones bend"; "they really seem to catch anything in the water. Weeds, plastic, anything. Now I am running the original prop and it is much better at untangling itself from the weeds" [VERIFICADO: [S23]].
  - Sobre agua salada: "If you're in salt water, the Minn Kota Riptide series is good … Stay away from Great White … they have parts of the controller in the actual underwater motor case" [VERIFICADO: [S27]].
  - Sobre sobretensión: un usuario corre un trolling de escobillas de 86 lb a 9S, ~1700 W. Su **controlador PWM externo** ("Mine (white plastic box)") "did hold continuous 50A at ~33V Out for ~30 min … but it was very hot" [VERIFICADO: [S27]]. *(Corregido: el que se calentaba era el controlador, no el motor.)*
- **Contexto:** Jeremy Harris (Endless Sphere 38992): con potencia proporcional al cubo de las rpm, sobrevoltar un trolling de escobillas "most have ended in tears", salvo que se limite la corriente a la del original [VERIFICADO: [S28]].
- **Aplica a P1:** convertir un trolling es barato, pero los ESC de RC necesitan **disipación**, las hélices de RC enganchan algas y, en salado, la electrónica sumergida es un punto débil. Todo eso le pesa en contra a la alternativa "conversión de trolling".

### E1 — Arcada UAS: hélice de bow-thruster impresa en PETG, 4 meses en agua de mar
- **Link:** [S24].
- **Datos:**
  - CF-PLA descartado por "multiple setbacks with printing failures"; el final se hizo en **PETG**, lijado y pintado con pintura para plástico [VERIFICADO: [S24]].
  - 6 palas en lugar de 3; "~25% increase in thrust; No cavitation issues"; 4 meses de verano [VERIFICADO: [S24]].
  - "at the end of the season, barnacles started to grow"; "When removing the propeller for inspection, one of the propeller blades cracked" [VERIFICADO: [S24]].
  - Los autores lo atribuyen a la degradación por agua salada [VERIFICADO: [S24]]. Causa alternativa probable: fatiga o tensión al desmontar en un material con capas [ESTIMADO: criterio de ingeniería FDM, no verificado].
- **Aplica a P1:**
  - Una hélice de PETG impresa **sobrevive una temporada** (~4 meses) en el mar, pero una pala **se fisuró al desmontarla** para inspección. La fuente solo dice "seawater" y "tested at sea", sin lugar. Que fuera el Báltico salobre, un agua comparable a la de Sønderborg, es un [SUPUESTO: Arcada está en Helsinki (memoria técnica, no verificado en la página)].
  - En P1 la hélice es comercial, como corresponde. Las piezas impresas sumergidas (protector, aleta) necesitan **inspección por fisuras** y eventualmente antifouling.

### Otros datos de hélices impresas, de menor peso
- **MaxGyver** (Printables 38641): "Boat Propeller I designed to electrically drive my canoe. It can be driven with a battery drill". 20 cm con paso de 314 mm, o 13 cm con 204 mm, en ABS; la de 13 cm "needs higher rpm (+-2000rpm)". 155 likes, 13 makes [VERIFICADO: [S29]].
- **Jere Kurvinen** (MakerWorld 1272995): cubo de 82 mm, eje de 10 mm, ranura para pasador de 3,5 mm; "tested with a small 32 lbs electric motor"; ABS alisado con vapor de acetona [VERIFICADO: [S30]].
- **Daniel Riley / rctestflight** (escala RC, no tripulada): la hélice FDM de 2 palas rindió mejor que la bi-pala y la toroidal; las pruebas de burbujas mostraron pérdida en estas últimas [VERIFICADO: [S31]].

### Referencias comerciales para contrastar órdenes de magnitud
- **Torqeedo Ultralight** (folleto de 2021) [VERIFICADO: [S25]]:

| Dato | 403 | 1103 |
|---|---|---|
| Potencia de entrada | 400 W | 1100 W |
| Potencia propulsiva | 180 W | 540 W |
| "Maximum overall efficiency" | 45 % | 49 % |
| Empuje estático | 33 lb | 70 lb |

  - Tensión nominal de 29,6 V.
  - "To compare Torqeedo static thrust data with conventional trolling motors, add approximately 50%".
  - Soporte con **kick-up**: "The mount allows the motor to kick up toward the stern of the kayak when it encounters an underwater obstacle".
  - **Marcha atrás:** "Pull the reverse cord and simply hold tension or secure it in the included cleat. Release the cord when moving forward to enable the automatic kick-up feature".
- **Backwater SWOMP E-Series**, long-tail eléctrico comercial [VERIFICADO: [S26]]:
  - "7 HP SWOMP MV7 Package - $5650 Includes 56V 54AH battery & charger" (≈3,0 kWh [CALCULADO]).
  - MV20: "Voltage: 72V • Current Draw: Up to 200A continuous • Motor Type: Brushless electric • Drive: Direct, no belts, no gears".
- **Afirmaciones de foro, no verificadas por medición:**
  - Minn Kota y similares tendrían "overall efficiency of less than 20%" frente a ~50 % del Torqeedo [VERIFICADO: [S32]].
  - "outboard legs have a lot of friction, which saps power"; un PWC jet "maybe 60% efficient at best", una buena hélice "as much as 85%" (Jeremy Harris) [VERIFICADO: [S34]].
  - Las hélices de trolling tienen "prop efficiency … down around 40% to 50% … (about 1200rpm)" (Jeremy Harris) [VERIFICADO: [S34]].

---

## 5. Tabla de contraste de rendimiento (órdenes de magnitud)

Los Wh/km son [CALCULADO] = P / v con los datos verificados de cada fila. Es potencia **de batería**, salvo Torqeedo, que también da la propulsiva.

| Fuente | Casco · carga | v (km/h) | P (W) | Wh/km | Nota |
|---|---|---|---|---|---|
| B1 v4 [S9] | Kayak (no dice si el inflable de 13' o uno de mar), 1 p. (?) | 5,0 | 30 | 6 | Long-tail seco, eje flexible |
| B1 trolling de serie [S9] | Ídem | 5,0 | ~150 | 30 | "from memory" |
| B1 trolling de serie, medido [S7] | Inflable Helios de 13' | 5,1 | ~105–110 [CALCULADO: 8,6 A × ~12,5 V] | ~21 | Carga posiblemente distinta |
| C2 [S18] | Intex Explorer inflable, 1 p. | ~6,4 (promedio; incluye ~1 milla a remo) | ~126 | ≤21 | |
| C2 [S18] | Intex Explorer inflable, **2 p.** | **5,6 (máx.)** | **~170–185** [CALCULADO: 0,6 × 24–25,6 V × 12 A] | ~30–33 | Límite de 12 A del motor |
| D1 de serie [S22] | Canoa de 14' LWL, 300 lb | 6,9 | 330 | 47,7 | Trolling de 12 V |
| D1 optimizado [S22] | Ídem | 6,9 | 190 | 27,5 | Hélice + carenado |
| B3 [S11] | Kayak, 1 p. | ~5 | ~180 | ~36 | Taladro de 18 V |
| A3 [S5] | Skiff a remo de 14' | 8,0 | 370 | 46 | Pata de fueraborda |
| B2 [S10] | Trimarán de 33' | 3,7 | 120 | 32 | Correas impresas |
| Jed233 [S15] | Kayak de 15', 350 lb | ~9,7 | 672 (28 A × 24 V) | ~70 | Trolling de 86 lb a fondo |
| A1 [S1] | Canoa canadiense, 2 p. | ≥5 (promedio) | ≤1000 | ≤100 | Cota superior |
| A1 [S1] | **Dinghy inflable, 2 p., mar** | **~5,6** | (n/d; motor de 1 kW) | — | "generally around 3 knots" |
| A1 [S1] | Dinghy inflable, 1.ª prueba en canal | 5 (promedio) | potencia plena (~1 kW nominal) | ~200 [ESTIMADO: 1 kW / 5 km/h] | Hélice medio afuera; personas a bordo no declaradas |
| A2 [S3] | **Inflable pesado, 2 p.** | **7 (máx.)** | (n/d) | — | C80100 a 24 V |
| B5 [S14] | Aluminio de 12', 1 p. | 25,7 | 8922 | 347 | Planeo, surface drive |
| B6 [S16] | Inflable con fondo en V | 20 | 7000–8000 | 350–400 | Planeo; Golden Motor sobre la pata original (no la correa) |
| R1 [S25] | Torqeedo 403 | — | 400 de entrada / 180 propulsiva | — | η global máx. 45 % |

**Lectura para P1.** Las cifras de este bloque, salvo que se indique otra cosa, son [CALCULADO] o [ESTIMADO].
- **Velocidad de casco:** con la fórmula citada en [S15], v_casco ≈ (1,3–1,5)·√LWL[ft] kn [VERIFICADO: [S15]], una LWL de 2,0–2,4 m da **6,2–7,8 km/h** [CALCULADO].
- **Número de Froude:** crucero de 6 km/h con LWL de 2,2 m → Fn = 0,36; 8–12 km/h → Fn = 0,48–0,72, que es la zona de la "joroba" de resistencia y del semiplaneo [CALCULADO: Fn = v/√(g·L)].
- **Lo que muestran los comparables:**
  - Los cascos largos y finos (canoa, kayak) consumen 6–50 Wh/km entre 5 y 8 km/h.
  - Los **inflables con 2 personas** llegaron a **5,6–7 km/h** (A1, A2, C2). Solo C2 tiene potencia medible: **~170–185 W para 5,6 km/h** con 2 personas, en un kayak inflable fino. A1 y A2 traen motores de ~1 kW, pero no hay potencia medida a esas velocidades. *(Corregido: antes decía "no superan 5,6–7 km/h aun con motores de ~0,5–1 kW", y eso no está respaldado: en C2 el motor estaba limitado a ~180 W.)*
  - Para planear o semiplanear hay que pasar al régimen de **kW** (B5, B6).
- **Estimación para P1 (jon boat de <2,5 m con 2 personas):**
  - A 6 km/h: **300–700 W de batería** [ESTIMADO: D1 (canoa de 14', 300 lb, 190–330 W a 6,9 km/h) y C2 (kayak inflable con 2 p., ~180 W a 5,6 km/h) son cascos más largos y finos; un jon boat corto y romo con 2 personas resiste más]. **Advertencia de la verificación:** ningún comparable medido respalda directamente el piso de 300 W. Los datos medidos (C2, D1) quedan en 180–330 W, con cascos más eficientes. El rango tiene que salir del cálculo R(v) de P1, no de esta interpolación.
  - Energía para 2 h: **0,6–1,4 kWh útiles** [ESTIMADO: 300–700 W × 2 h]. Hay que contrastarlo con el cálculo de resistencia de P1.

---

## 6. Patrones de falla que se repiten (síntesis)

| Modo de falla | Proyectos (evidencia) | Mitigación concreta para P1 |
|---|---|---|
| Unión eje–polea o eje–engranaje: patina o se corta | B2 (chaveta en plástico "impossible", polea patina); A4 (eje cortado en el cónico, prisioneros rotos) | Pasador pasante de inoxidable o estría; cubo metálico en las poleas; nada de prisioneros como único vínculo; pasador de corte como eslabón débil **a propósito** |
| Correa que salta dientes | B2 | Tensor ajustable (ranuras o idler); poleas alineadas con ajuste fino; correa ancha |
| Motor o ESC quemado por falta de reducción o sobrecarga | B4 (2×6374 + ESC a 24 V, directo); B6 (hub motor a 7 kW); A2 (C8085 a 40 A); A1 (controlador subdimensionado) | Reducción HTD; límite de corriente de motor y de batería en el VESC; ESC con margen ≥2× sobre la corriente continua [ESTIMADO: criterio]; rampa de aceleración |
| ESC recalentado en recinto cerrado | D2 (30 min); C2 (>50 °C en la caja de batería); B1 (motor a 60 °C en el recinto) | ESC sobre placa de aluminio o disipador (A4: +10–15 °C sobre ambiente); separado de la batería; sensor de temperatura |
| Agua en el motor sumergido o en las cajas | C1 (problema principal); A1 (agua en la caja de batería); A4 (carcasas que filtran) | Motor seco (la arquitectura de P1); cajas con drenaje y prensaestopas; el epoxi común absorbe agua ([S17], comentario) |
| Hélice en arena o golpe | A4 (cónicos destruidos con el acelerador a fondo en arena); C5 (advertencia del autor: el rim se puede atascar con arena; no es una falla observada) | Kick-up; pasador de corte; **armado solo con acelerador en cero**; cordón de hombre al agua |
| Algas en la hélice | C2 (el motor se detuvo); D2 (la hélice de RC engancha) | Hélice de palas inclinadas hacia atrás (tipo antiyuyo), protector que no forme peine, acceso rápido por kick-up |
| Ventilación con eje inclinado | B5 (estancado en 8 mph a 15° sin cup) | Profundidad y ángulo ajustables; placa antiventilación sobre la hélice |
| Eje largo: vibración o pandeo | Jed233 (3/8" × 26", desbalanceado, con buje de latón en popa: "vibrated intolerably"); B1 (pandeo a 11 km/h, resuelto acortando o engrosando el eje) | Eje rígido de 316 en tubo, con bocina en el extremo de la hélice + apoyo superior (B5); verificar la velocidad crítica |
| Kick-up que se levanta en marcha atrás | R1 (Torqeedo: hay que **trabar** el kick-up para ir en reversa) | Traba de kick-up para reversa (mecánica o por el propio empuje) en el diseño del cardán |
| Riesgos de batería y carga | A1 (cargador incendiado); [S33] (BMS y fusibles sobredimensionados no protegieron ni el ESC ni el motor; pico por corte del BMS en regeneración planteado como mecanismo posible) | Cargador certificado y supervisado; fusible; regeneración limitada en el VESC; precarga o antichispa |

---

## 7. Fuentes abiertas en esta sesión

| ID | Fuente | Cómo se leyó |
|---|---|---|
| S1 | PBO, "DIY electric outboard motor…" | curl / WebFetch |
| S2 | Hackaday 2019-01-10, "Electrifying a vintage outboard motor" | curl |
| S3 | Endless Sphere 52800, "Outboard to brushless conversion" | curl |
| S4 | Endless Sphere 51966, "Electric outboard motor..." | curl |
| S5 | Endless Sphere 113248, "Electric outboard build for canoe... Help" | curl |
| S6 | dominicpeters.ca, E-Kayak | curl |
| S7 | boatdesign 52833, pág. 1 | curl |
| S8 | boatdesign 52833, pág. 2 | curl |
| S9 | boatdesign 52833, pág. 6 | curl |
| S10 | hackaday.io 174537 + logs | curl |
| S11 | boatdesign 63757, "Kayak motor" | curl |
| S12 | Endless Sphere 19115, pág. 1 y 2 | curl |
| S13 | boatdesign 56617, pág. 1 | curl |
| S14 | boatdesign 56617, pág. 2 | curl |
| S15 | boatdesign 58032 | curl |
| S16 | Endless Sphere 53697 | curl |
| S17 | Hackaday 2022-11-29 (Anton) | curl |
| S18 | Bare Naked Embedded | curl |
| S19 | Printables 1833248 | API GraphQL |
| S20 | Thingiverse 2947306 | meta description |
| S21 | Printables 681590 | API GraphQL |
| S22 | boatdesign 27996, pág. 17 (MCDenny) | curl |
| S23 | Endless Sphere 70903 | curl |
| S24 | Arcada | curl |
| S25 | Folleto Torqeedo Ultralight | PDF |
| S26 | Backwater SWOMP E-Series | curl |
| S27 | Endless Sphere 90678 | curl |
| S28 | Endless Sphere 38992 | curl |
| S29 | Printables 38641 | API GraphQL |
| S30 | MakerWorld 1272995 | API |
| S31 | Hackaday 2023-07-02 (rctestflight) | curl |
| S32 | Endless Sphere 13639 | curl |
| S33 | Endless Sphere 129365, "7070 outboard project…" | curl |
| S34 | Endless Sphere 19115, pág. 1 (Jeremy Harris) | curl |

[S1]: https://www.pbo.co.uk/expert-advice/build-diy-electric-outboard-motor-engine-60467
[S2]: https://hackaday.com/2019/01/10/electrifying-a-vintage-outboard-motor/
[S3]: https://endless-sphere.com/sphere/threads/outboard-to-brushless-conversion.52800/
[S4]: https://endless-sphere.com/sphere/threads/electric-outboard-motor.51966/
[S5]: https://endless-sphere.com/sphere/threads/electric-outboard-build-for-canoe-help.113248/
[S6]: https://www.dominicpeters.ca/projects/ekayak.html
[S7]: https://www.boatdesign.net/threads/efficient-solar-powered-electric-kayak.52833/
[S8]: https://www.boatdesign.net/threads/efficient-solar-powered-electric-kayak.52833/page-2
[S9]: https://www.boatdesign.net/threads/efficient-solar-powered-electric-kayak.52833/page-6
[S10]: https://hackaday.io/project/174537-solar-powered-boat
[S11]: https://www.boatdesign.net/threads/kayak-motor.63757/
[S12]: https://endless-sphere.com/sphere/threads/electric-boat-research.19115/page-2
[S13]: https://www.boatdesign.net/threads/diy-electric-surface-drive.56617/
[S14]: https://www.boatdesign.net/threads/diy-electric-surface-drive.56617/page-2
[S15]: https://www.boatdesign.net/threads/straight-shaft-motorized-kayak.58032/
[S16]: https://endless-sphere.com/sphere/threads/my-new-electric-outboard-motor-hub-motor-silent-and-fast.53697/
[S17]: https://hackaday.com/2022/11/29/this-electric-outboard-conversion-makes-for-a-quiet-day-on-the-water/
[S18]: https://barenakedembedded.com/diy-electric-kayak/
[S19]: https://www.printables.com/model/1833248-flipsky-85135-motor-75350-esc-outboard-mount
[S20]: https://www.thingiverse.com/thing:2947306
[S21]: https://www.printables.com/model/681590-electric-outboard-motor
[S22]: https://www.boatdesign.net/threads/efficient-electric-boat.27996/page-17
[S23]: https://endless-sphere.com/sphere/threads/another-trolling-motor-project-need-controller-advice.70903/
[S24]: https://www.arcada.fi/en/article/blog/2025-12-18/designing-and-3d-printing-bow-thruster-propeller
[S25]: https://media.torqeedo.com/downloads/flyer/Onepager_Ultralight_2021_EN_RGB_210211.pdf
[S26]: https://www.backwaterinc.com/swomp-e-series.html
[S27]: https://endless-sphere.com/sphere/threads/trolling-motor-with-esc.90678/
[S28]: https://endless-sphere.com/sphere/threads/building-my-own-trolling-motor.38992/
[S29]: https://www.printables.com/model/38641-boat-propeller-20cm-13cm-and-10cm-diameter-10mm-sh
[S30]: https://makerworld.com/en/models/1272995-electric-outboard-motor-propeller
[S31]: https://hackaday.com/2023/07/02/testing-futuristic-propeller-designs-with-a-3d-printer-and-a-solar-powered-boat/
[S32]: https://endless-sphere.com/sphere/threads/boat-trolling-motor-efficiency.13639/
[S33]: https://endless-sphere.com/sphere/threads/7070-outboard-project-esc-bms-logging.129365/
[S34]: https://endless-sphere.com/sphere/threads/electric-boat-research.19115/

Notas sobre las fuentes leídas por otra vía:
- S19, S21 y S29: el HTML de Printables devuelve 403. El contenido se leyó con `POST https://api.printables.com/graphql/` y la consulta `print(id)`; el enlace queda para ubicar el modelo.
- S30: contenido leído vía `https://makerworld.com/api/v1/design-service/design/1272995`, porque el HTML devuelve 403.
- S20: solo la `meta description` del HTML.
- Los títulos de YouTube se verificaron con `https://www.youtube.com/oembed?url=…`.

**No pude abrir lo siguiente; no lo cito como fuente:**
- buscar: cults3d "Electric outboard for kayak DIY - Motor fueraborda para kayac DIY" (403)
- buscar: tinboats "Expected trolling speed with Minn Kota" (bloqueo de Cloudflare)
- buscar: thehulltruth "Trolling motor, what is your max GPS speed" (403)
- buscar: refugeforums "Ideas on making an electric mud motor for canoe" (redirección de pago)
- buscar: Minn Kota QUEST "30% longer" brushless runtime (la página volvió vacía)
- buscar: stlfinder "kayak motor diy" (403)
- El video de Printables 166288 (`Ix5F3YQOyLg`) no está disponible en oEmbed.

---

## Hallazgos que cambian el diseño

- **8–12 km/h no es un "modo por ratos" barato.**
  - Una LWL de 2,0–2,4 m da una velocidad de casco de **6,2–7,8 km/h** [CALCULADO con la fórmula de [S15]]. 8–12 km/h equivale a Fn 0,48–0,72.
  - Los DIY tripulados más parecidos, inflables con 2 personas, llegaron a **5,6 km/h** (A1, con motor de 1 kW, en el mar; C2, con solo ~180 W [CALCULADO]) y a **7 km/h máx.** (A2) [VERIFICADO: [S1]][VERIFICADO: [S3]][VERIFICADO: [S18]]. Para planear hicieron falta **7–14 kW** (B5, B6) [VERIFICADO: [S14]][VERIFICADO: [S16]].
  - → Dimensionar para un **crucero de 6 km/h** y tratar 8–12 km/h como "lo que dé" con un pico de ~1,5–2 kW limitado por el ESC [ESTIMADO]. Hay que documentar que probablemente no se llegue a 12 km/h a ≤48 V con 2 personas.
- **Energía de diseño provisoria: 300–700 W a 6 km/h → 0,6–1,4 kWh útiles para 2 h** [ESTIMADO: §5, a partir de D1 (190–330 W a 6,9 km/h en una canoa de 14') y C2 (~180 W a 5,6 km/h, kayak inflable con 2 p.), corregido hacia arriba por el casco corto y romo]. Hay que verificarlo con el cálculo de resistencia R(v) de P1. Si R(v) da menos de ~0,4 kWh para 2 h, revisar el modelo: está por debajo de todos los comparables tripulados medidos, cuyos cascos son más eficientes [ESTIMADO]. *(Corregido: antes el umbral era 0,6 kWh y se apoyaba en que los inflables "con 0,5–1 kW" no pasaban de 5,6–7 km/h; C2 lo desmiente.)*
- **La reducción es obligatoria y hay que limitar la corriente.**
  - Un outrunner 6374 en directo sobre un long-tail **quemó 2 motores y varios ESC a 24 V** [VERIFICADO: [S12]].
  - Lo que funcionó a cientos de W con hélices de fueraborda o grandes tenía reducción: 2:1 en cónicos [S6], ~2,33:1 en las patas originales [S4] y 11,25–15:1 por correa con una hélice de 32" [S10]. *(Corregido: antes se listaba también "1:5 por correa [S16]", pero ese montaje quemó su motor.)*
  - Contraejemplo: B1 v4 anduvo en **directa** con un 6374 de 149 kV y una hélice APC 10×6 a 30–100 W en un kayak [VERIFICADO: [S9]]. La reducción hace falta por el tamaño de la hélice y el empuje, que es justo el caso de P1 (hélice de fueraborda de ~7,8", 2 personas).
  - → HTD con una relación tal que la hélice de ~7,8" no pase de ~2000–2500 rpm a plena potencia [ESTIMADO: base [S4], "about 2500 rpm prop speed at WOT" en fuerabordas de combustión de 4–20 hp, que tienen mucha más potencia que P1; a 0,5–2 kW la hélice probablemente gire bastante menos, y la relación hay que cerrarla con la curva de la hélice]. Límites de corriente de motor y de batería configurados en el VESC.
- **Poleas HTD impresas: solo con cubo metálico y pasador pasante, más un tensor.**
  - La chaveta en plástico "is impossible … the plastic stretches"; la polea patinó y la correa saltó dientes a solo **≤70 W** [VERIFICADO: [S10]]. *(Corregido: antes decía 65–120 W; a 120 W ya andaba sin fallas reportadas.)*
  - → En P1, la polea del eje de la hélice (la de mayor par) **de aluminio comercial**, o impresa con inserto metálico + pasador ≥4 mm [ESTIMADO]. **Tensor ajustable** y ajuste de alineación de **1–2°** en el portamotor [VERIFICADO: [S10]].
- **El empuje y la flexión no pueden pasar por los rodamientos del motor.**
  - A4, B2 y B5 ponen un **rodamiento de empuje** propio [VERIFICADO: [S6]][VERIFICADO: [S10]][VERIFICADO: [S13]]. B1 pone dos rodamientos inoxidables que "take all the loads except the torque" (no dice que sean axiales) [VERIFICADO: [S9]].
  - *(Corregido: antes decía "todos los proyectos que funcionaron", y es falso.)* B3 anduvo 3 años "with no bearings" a baja potencia con un taladro [VERIFICADO: [S11]]. A1–A3 usan la pata original, que no está pensada para empuje en reversa [VERIFICADO: [S1]].
  - → Rodamiento axial bidireccional (P1 tiene marcha atrás) aguas arriba de la polea conducida; el motor solo da par, con soporte flexible al estilo de B1.
- **Eje rígido soportado en los dos extremos.**
  - Un eje de 9,5 mm × 660 mm, desbalanceado, con un buje de latón de 3" en popa y un acople improvisado, "vibrated intolerably" [VERIFICADO: [S15]]. Un eje flexible pandeó a 11 km/h; se resolvió acortándolo o engrosándolo, y el autor estima que más velocidad pide "a supported shaft" [VERIFICADO: [S9]].
  - B5 llegó a 13,7 kW con un eje de **19 mm × 914 mm** en tubo con **bocina de cutlass en el extremo de la hélice** [VERIFICADO: [S14]][VERIFICADO: [S15]].
  - → P1: buje lubricado por agua en el extremo inferior obligatorio, y verificar la velocidad crítica del eje de 316 a ≥1,5× las rpm máximas [ESTIMADO: criterio usual].
- **El ángulo y la profundidad de la hélice tienen que ser ajustables, con placa antiventilación.**
  - Con el eje fijo a 15°, B5 ventilaba por encima de 8 mph; a 20° duplicó la velocidad [VERIFICADO: [S14]].
  - A1 tuvo que bajar el soporte **150 mm** porque la hélice quedaba medio afuera según dónde estuviera sentada la gente [VERIFICADO: [S1]].
  - → Prever un ajuste de ≥150 mm de profundidad o ±5° de ángulo [ESTIMADO] y una placa antiventilación impresa sobre la hélice.
- **Kick-up + marcha atrás: hace falta una traba.** Para ir en reversa, Torqeedo pide tirar del "reverse cord" y mantenerlo tenso o amarrado a la cornamusa; "Release the cord when moving forward to enable the automatic kick-up feature" [VERIFICADO: [S25]]. Que el cabo sirva para mantener la pata abajo contra el empuje en reversa es una interpretación del folleto [ESTIMADO]. → El cardán de P1 necesita una **traba de reversa**, o una geometría donde el empuje en reversa no levante la pata. Si no, la marcha atrás obligatoria entra en conflicto con el kick-up.
- **Arranque con acelerador en cero, cordón de hombre al agua y pasador de corte como fusible.**
  - Un roce del acelerador con la hélice en arena destruyó los cónicos (de 2500 W a <500 W útiles) [VERIFICADO: [S6]].
  - Un usuario quitó el resorte del acelerador para tener crucero [VERIFICADO: [S3]].
  - → Lógica de armado en el firmware (acelerador = 0 durante ≥1 s para armar), cordón magnético con reed (idea de [S21]), pasador de corte dimensionado por debajo del par de falla de la polea y del eje.
- **Algas: un modo de falla real.** C2 se quedó sin propulsión por algas ("seaweed") en un canal que probablemente es de agua dulce [VERIFICADO: [S18]]; las hélices de RC "catch anything … weeds" [VERIFICADO: [S23]]. Que en el Als Fjord pase lo mismo es un [SUPUESTO], no un dato de estas fuentes. → Hélice de palas inclinadas hacia atrás, protector sin barras paralelas que hagan de peine, kick-up que deje la hélice al alcance de la mano desde el bote.
- **El tubo del eje tiene que ser un perfil y no un tubo redondo.**
  - Carenar el tubo de un trolling redujo la corriente un **16 %** (4,9→4,1 A) [VERIFICADO: [S8]].
  - Carenado + spinner + hélice correcta: **−42 %** (330→190 W a 6,9 km/h) [CALCULADO con datos de [S22]]. El carenado + spinner solo explica −27 % (260→190 W) [CALCULADO].
  - → Carenado NACA impreso alrededor del tubo inclinado.
- **El ESC va fuera de la caja de la batería, sobre metal y con margen.**
  - Un ESC encerrado se recalentó a los 30 min [VERIFICADO: [S23]]; un VESC pasó de 50 °C en la caja de la batería [VERIFICADO: [S18]].
  - Un ESC sobre placa de aluminio + disipador quedó en +10–15 °C sobre el ambiente [VERIFICADO: [S6]].
  - Un controlador subdimensionado murió a ~1 km a fondo [VERIFICADO: [S1]].
  - → Placa de aluminio como disipador, sensor de temperatura, ESC con ≥2× la corriente continua prevista [ESTIMADO].
- **Batería y BMS.**
  - Caso documentado en [S33]: con una batería de 72 V y 200 A, un BMS de 200 A sin bajar el límite y fusibles dimensionados para la batería, el forista "blew the controller fets short and melted the motor without tripping the BMS" [VERIFICADO: [S33]].
  - Que un corte del BMS durante la regeneración genere un pico de tensión que mata el ESC es un **mecanismo posible** que propone otro forista en el mismo hilo, no un caso observado [VERIFICADO: [S33]]. *(Corregido: antes figuraba como hecho.)*
  - Un cargador "matched" se incendió [VERIFICADO: [S1]].
  - → Límite de sobrecorriente del BMS y fusible dimensionados para el **sistema de propulsión**, no para la batería. Regeneración limitada a pocos A en el VESC, supresión de transitorios (TVS) cerca de los FET [ESTIMADO: criterio], precarga o antichispa, cargador certificado y carga supervisada.
- **Se descarta el pod sumergido DIY y el rim-drive para P1.**
  - En el pod DIY, la entrada de agua fue "chief" problema [VERIFICADO: [S17]], y "many epoxies … absorb water" [VERIFICADO: [S17]].
  - El rim-drive: "silt and sand can clog and seize" (advertencia del autor, sin pruebas de campo) [VERIFICADO: [S21]].
  - En salado, la electrónica sumergida de los trolling baratos es un punto débil [VERIFICADO: [S27]].
  - → La matriz de arquitectura de P1 debería penalizar esas opciones por arena y corrosión.
- **La arquitectura long-tail eléctrica está validada comercialmente.** Backwater vende un long-tail eléctrico "Direct, no belts, no gears" a 72 V / 200 A, y un paquete de 7 HP con batería de 56 V 54 Ah (~3,0 kWh) a US$5650 [VERIFICADO: [S26]]. → P1 apunta al mismo nicho a ≤48 V con reducción; sirve como argumento de costo frente a lo comercial.
- **Las piezas impresas sumergidas se fisuran: hay que inspeccionar.** Una hélice de PETG en agua de mar tenía percebes al final de la temporada (**~4 meses**), y una pala se fisuró al desmontarla [VERIFICADO: [S24]]. → Revisar fisuras en el protector y la aleta impresos cada pocas salidas (al FMEA). Enjuagar con agua dulce; no dejar el equipo en el agua.
- **El tamaño de las piezas impresas manda en el plazo.** Una carcasa de PETG al 80 % de relleno pesó ~2 kg y llevó 3 días de impresión [VERIFICADO: [S19]]. → Segmentar las piezas grandes para que cada impresión dure ≤12–16 h en la Ender-3 S1 [ESTIMADO] y usar relleno variable (alto solo en los anclajes).
- **Una hélice comprada puede venir desbalanceada.** Las dos hélices Flipsky que compró Igor lo estaban [VERIFICADO: [S19]]. → Agregar al checklist el balanceo estático de la hélice en el torno, antes de montarla.

---

## Verificación (adversarial)

Hecha el 2026-10-01 por un subagente verificador.
- **Fuentes reabiertas:** las 34. Todas abrieron (HTTP 200): con `curl` (UA "curl/8.0") para HTML y PDF, con la API GraphQL para Printables (S19, S21, S29) y con la API de diseño para MakerWorld (S30).
- **YouTube:** se volvieron a verificar los 6 títulos citados vía oEmbed (Irie Electrics ×2, Louis, Anton makes stuff, Istvan Horvath ×2). `Ix5F3YQOyLg` sigue sin abrir.
- **Contenido de videos:** el archivo no afirma nada que salga de un video; solo cita títulos.
- **Precios y números de pieza:** los citados (300 €, 25 €, US$5650; MAC12500-3A, SK3-6374-149, ME1004, SPM 48-400, HT3525, FSESC 6.7 PRO, QUICRUN 1060/WP 860, DiskDrive 80, C5065KV320, Flipsky 85135/75350/5062) están todos en sus fuentes.
- **Propiedades de materiales:** no se encontraron propiedades sin fuente. Lo que dice sobre PLA y PETG es cita de los autores; la causa alternativa de la fisura en E1 ya estaba marcada [ESTIMADO].

| # | Afirmación / URL | Estado | Nota |
|---|---|---|---|
| 1 | S1 PBO: MAC12500-3A 48 V 1 kW ~4000 rpm; donante 1,49 kW; controlador de 1500 W; 1 kWh ≈ 20 Ah; 40 min a fondo; placa de 10 mm; rosca de 8 mm; 50 min en el contenedor; ~3 kn; canoa >10 km en <2 h y 6 kn; −150 mm; ~80 °C; cargador incendiado; sensor Hall; error de software; agua en la caja | OK | Todo textual en la página |
| 2 | S1: "cajas IP55 y IP67", "80 °C en la placa base" | corregido | IP55 es la clasificación del motor y del controlador; IP67 la caja del Arduino; los 80 °C son de "motor temperature" |
| 3 | S1: "2 personas en un bote corto → ~5,6 km/h" | corregido | "generally around 3 knots" no está atado a 2 personas |
| 4 | S2 Hackaday 2019 (resumen de A1) | OK | |
| 5 | S3 ES 52800: C8085 a 40 A; 7 km/h GPS; 2 p.; lago; Alien 250 A; 24 V plomo; resorte quitado; acople flexible sugerido | OK | |
| 6 | S3: "Turnigy C80100" | corregido | El Turnigy era el C8085; el C80100 se compró en alienpowersystem.com |
| 7 | S4 ES 51966: ~300 € sin baterías; pata "drowned" de 25 €; 2,33:1 y ~2500 rpm a WOT | OK | La cita de 2,33:1 es de Bazaki |
| 8 | Hallazgo "hélice de 7,8" a 2000–2500 rpm [VERIFICADO: S4]" | corregido → [ESTIMADO] | S4 habla de fuerabordas de combustión de 4–20 hp a WOT, no de P1 |
| 9 | S5 ES 113248 (alan-c): 100 W, 370 W ≈ 5 mph, 1,5 kW a 9S, skiff de 14 ft | OK | |
| 10 | S6 dominicpeters.ca: todos los datos de A4 | OK | Se agregó que el agua es dulce (canal Rideau) y la autonomía de 1,5–2 h a ~300 W |
| 11 | S7 boatdesign 52833 p1: Helios 2 de 13'; 8,6 A y 5,7 A a 5,1 km/h | OK | |
| 12 | S8 p2: "glassy calm", tramos de 500 m, medición antes del controlador, 4,9→4,1 A a 12,5 V, η 47 % estimada | OK | La estimación de η es del propio ElectricKayak |
| 13 | S9 p6: SK3-6374-149 (70 A, 2250 W, eje de 8 mm), ESC naval de 120 A, eje de 3/16" × 40–48", 60 °C, 30/45/~150 W | OK | |
| 14 | S9: "pandeo a 11 km/h" presentado como falla abierta | corregido | La fuente dice que lo resolvió acortando o engrosando el eje |
| 15 | S9: DeWalt "kayak de mar" a 200 W y 6 kn | corregido | La fuente dice "mine" (su kayak), sin decir de qué tipo |
| 16 | B1: "−80 % a 5 km/h" | corregido | Usa una cifra "from memory" y quizá otro casco o carga. Dato firme: −33 % (45→30 W) |
| 17 | S10 hackaday.io 174537 + logs: todos los datos de B2 | OK | |
| 18 | Hallazgo "polea patina y correa salta a 65–120 W" | corregido | Las fallas fueron a ≤70 W; a 120 W no hay fallas reportadas |
| 19 | S11 boatdesign 63757: Lachie (18 V, 5 km/h, 4 Ah ≈ 2 km, 5", 3 años, "no bearings"); consejo de rodamiento de empuje; 4200 rpm "too much" | OK | "PVC agrícola" → "plastic pipe" agrícola |
| 20 | S12 ES 19115 p2: blisspacket (2× 6374 + Phoenix, 24 V, 15 ft, sin reducción) | OK | La cita de 5 km/h es de otro forista, no de "un canoero" (corregido) |
| 21 | S13 boatdesign 56617 p1: trim "up to 2° and down to 22°", eje de 3/4", cutlass, Nova jaws, empuje, ME1004, SPM 48-400, 2 × 48 V 45 Ah | OK | El trim estaba en el post n.º 1 |
| 22 | S14 p2: 16 mph con 215 A a 41,5 V = 8922,5 W; 25 mph a 13,7 kW; 8,5 mph antes; 15° → 20°; 18' → 8" de agua | OK | Los 16 mph son con la hélice "9x10" |
| 23 | S15 boatdesign 58032: 3/4" × 36", 4", 600+ lb, fórmula 1,3–1,5·√LWL, Jed233 a 28 A × 24 V y 6 mph | OK | |
| 24 | S15: Jed233 "buje de bronce", "eje sin soporte" | corregido | Era "brass" (latón) y el eje tenía un buje de 3"; la vibración se atribuye al desbalanceo |
| 25 | S16 ES 53697: correa, HT3525 a 5,5 rpm/V, 90 V, 1:5, quemado, 7 kW, 8×8, 20 km/h a 8 kW, tabs 14/16 km/h | OK | |
| 26 | S16: "20 km/h a 8 kW" atribuido a la correa 1:5 | corregido | Fue con el Golden Motor sobre la pata original (~4400 rpm de motor) |
| 27 | Hallazgo "lo que funcionó tenía reducción … 1:5 por correa [S16]" | corregido | Ese montaje quemó el motor. Se agregó el contraejemplo de B1, directo a baja potencia |
| 28 | S17 Hackaday 2022: 180→77 kV, epoxi, hélice impresa, entrada de agua, comentarios sobre el epoxi y el 3–5 % | OK | |
| 29 | S17: "D (lago)"; "Hackaday comenta que se resolvería…" | corregido | El lago es la intro genérica; la solución la señala Anton (según Hackaday) |
| 30 | S18 BNE: 5062 a 160 kV, 500 W y 5 kg; FSESC 6.7 PRO 70 A; 24 V 20 Ah 480 Wh; 10 lb; 6,75 y 5,6 km/h; 12 A a 60 %; 14 mi en 3,5 h; algas; >50 °C | OK | |
| 31 | S18: "Intex K2", "S/D", "5,6 km/h con ~0,5 kW" | corregido | "K2" no está en la fuente. El canal es probablemente de agua dulce. Con 2 p. el motor estaba limitado a 12 A → ~170–185 W [CALCULADO] |
| 32 | §5 "inflables con 2 p. no superan 5,6–7 km/h aun con 0,5–1 kW" | corregido | No está respaldado: la única potencia medible (C2) es de ~180 W |
| 33 | S19 Printables 1833248 (API): canales de refrigeración, 20S13P a 84 V, tubo de 28 mm, ~120 cm, 6 AWG, PETG al 80 %, ~2 kg / 3 días, hélices desbalanceadas, spline de Yamaha <6 hp, kill switch, CAN + GPS | OK | Publicado el 2026-09-30; 1 like |
| 34 | S20 Thingiverse 2947306 (meta description) | OK | |
| 35 | S21 Printables 681590 (API): DiskDrive 80, PETG-CF, 18–24 V ≥500 W, imán + reed, "Do not run dry", "silt and sand can clog", 10 likes / 24 descargas | OK | Se agregó el matiz de que el autor promociona el rim para aguas someras y que lo de la arena es una advertencia, no una falla observada |
| 36 | S22 boatdesign 27996 p17: 14' LWL, 300 lb, GPS de 30 s, "Watts Up", 330/178/410/260/190 W | OK | Se agregó la advertencia del autor sobre el viento; el −42 % pasa a [CALCULADO] e incluye el spinner |
| 37 | S23 ES 70903: C2 de 30 lb, QUICRUN 1060 recalentado a los 30 min, WP 860 + ventiladores, la hélice de RC engancha | OK | |
| 38 | S24 Arcada: CF-PLA → PETG, 6 palas, +25 %, sin cavitación, 4 meses, percebes, pala fisurada al desmontar, atribuido al agua salada | OK | La página no dice dónde navegó el bote; "Báltico" queda como [SUPUESTO] |
| 39 | S25 folleto Torqeedo: 400/1100 W, 180/540 W, 45/49 %, 33/70 lb, 29,6 V, +50 %, kick-up, cabo de reversa | OK | Que el cabo trabe el kick-up se marca como interpretación [ESTIMADO] |
| 40 | S26 Backwater: MV7 a US$5650 con batería de 56 V 54 Ah; MV20 a 72 V / 200 A, "Direct, no belts, no gears" | OK | El MV20 cuesta US$7450, solo el motor |
| 41 | S27 ES 90678: Riptide / Great White | OK | |
| 42 | S27: "86 lb a 9S sostuvo 50 A a ~33 V, very hot" | corregido | El que se calentaba era el controlador externo ("white plastic box"), no el motor |
| 43 | S28 ES 38992 (Jeremy Harris): ley cúbica, "ended in tears", limitar la corriente | OK | |
| 44 | S29 Printables 38641; S30 MakerWorld 1272995; S31 Hackaday 2023 | OK | En S31, las hélices bi-pala y toroidal se imprimieron en nylon por un servicio profesional |
| 45 | S32 ES 13639: "<20 %" frente a ~50 % de Torqeedo | OK | Es una afirmación de foro |
| 46 | S33 ES 129365: "corte del BMS en regeneración → pico que mata el ESC" como hecho | corregido | Es un mecanismo posible que plantea un forista. El caso documentado es otro: BMS de 200 A y fusibles sobredimensionados; FET en corto y motor derretido sin que actuara la protección |
| 47 | S34 ES 19115 p1 (Jeremy Harris): pata de fueraborda con "a lot of friction", jet ~60 %, hélice hasta 85 %, trolling 40–50 % a ~1200 rpm | OK | |
| 48 | Hallazgo "todos los que funcionaron ponen rodamiento de empuje propio" | corregido | Falso: B3 anduvo 3 años sin rodamientos; A1–A3 usan la pata original; en B1 los rodamientos no se declaran axiales |
| 49 | Hallazgo "algas, modo de falla real en agua salobre" | corregido | La evidencia (C2) es de un canal probablemente dulce; para el Als Fjord queda como [SUPUESTO] |
| 50 | Cálculos: velocidad de casco 6,2–7,8 km/h; Fn 0,36 / 0,48–0,72; Wh/km de §5 | OK | Recalculados. Se agregó la fila de C2 con 2 p. (~30–33 Wh/km) |

### Hallazgos de la verificación que cambian el diseño
- **El piso de 300 W a 6 km/h no tiene respaldo medido.**
  - El único comparable inflable con 2 personas y potencia medible (C2) hizo 5,6 km/h con ~170–185 W [CALCULADO con [S18]]. La canoa de D1 hizo 6,9 km/h con 190–330 W [S22].
  - El rango de 300–700 W y 0,6–1,4 kWh para 2 h sigue como [ESTIMADO] por el casco romo de P1, pero lo tiene que fijar el cálculo R(v).
  - Umbral de alarma: si R(v) da menos de ~0,4 kWh para 2 h, hay que revisarlo.
- **La ganancia firme del long-tail seco frente a un trolling optimizado es −33 %** (45→30 W a 5 km/h) [CALCULADO con [S9]], no −80 %. No conviene vender autonomía usando el −80 %.
- **Relación de la HTD:** el "~2500 rpm de hélice" sale de fuerabordas de combustión de 4–20 hp [S4]. A 0,5–2 kW, una hélice de fueraborda de ~7,8" va a girar menos [ESTIMADO]. Hay que fijar la relación con la curva par–rpm de la hélice elegida y no con 2000–2500 rpm.
- **Las poleas impresas fallaron a ≤70 W** [S10], 5–10 veces por debajo de lo que transmite P1. La polea conducida, del eje de la hélice, va de **aluminio comercial**. Una impresa solo como prototipo, con cubo metálico y pasador pasante.
- **Protección eléctrica.** Un BMS y fusibles dimensionados para la batería no salvaron ni el ESC ni el motor [S33].
  - Fusible principal y límite de sobrecorriente del BMS ajustados a la corriente de batería máxima configurada en el VESC, con un margen chico [ESTIMADO: criterio].
  - Supresión de transitorios cerca del ESC y regeneración limitada [ESTIMADO].
- **Vibración del eje:** un buje en popa no alcanza si el eje está desbalanceado o el acople es improvisado [S15]. Hay que exigir eje rectificado y balanceado (en el torno), un acople de calidad y verificar la velocidad crítica.
- **Algas:** la evidencia de las fuentes es de agua dulce. Para el Als Fjord, las previsiones antialgas (hélice de palas inclinadas hacia atrás, protector sin peine, kick-up que deje la hélice a mano) siguen siendo razonables, pero son un [SUPUESTO] a validar en el agua.
