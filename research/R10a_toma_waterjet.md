# R10a: la toma (succión) del waterjet de Jorge. ¿Está muy atrás?

**Fecha:** 2026-10-01.

**Objeto:** `referencias/2026-09-26_plano_preliminar_waterjet_jorge.png`, rotulado "PLANO PRELIMINAR – WATERJET PARA JET BOAT 2.30 m". Datos del rótulo: escala 1:10, mm, 26/09/2026, "NO USAR COMO PLANO FINAL DE MECANIZADO".

**Comentario de Jorge**, reenviado por Gaspar (literal): *"La rejilla de succión que da a la altura del del eje del motor en la imagen está muy atrás !"*

**Alcance:**
- Este informe cubre solo la toma: posición, rampa, labio, rejilla, altura del eje, cebado, IVR y cavitación en la entrada del impulsor.
- El resto del plano (estabilidad, masa, 72 V, bomba, legalidad) lo audita otro agente en `research/R10b_auditoria_plano_jorge.md`.

**Archivos:**
- Croquis: `referencias/croquis_toma_waterjet.svg`.
- Script: `referencias/croquis_toma_waterjet.py`. Calcula todos los números de este documento e imprime la tabla de la §6.

**Etiquetas:**
- [VERIFICADO: Sx] = leído en la fuente Sx de la §9, abierta en esta sesión.
- [CALCULADO] = salida del script, ejecutado.
- [ESTIMADO: base] y [SUPUESTO] = lo que dicen.

---

## 0. Seguridad primero

1. **La toma de un jet atrapa.** La guía de seguridad de motos de agua dice: *"Keep away from intake grate while engine is on. Items such as long hair, loose clothing or PFD straps can become entangled in moving parts resulting in severe injury or drowning."* [VERIFICADO: S11].
   - Con 5 kW pasan ~45 L/s por la toma [CALCULADO].
   - En la rejilla de 120 × 90 del plano, el agua va a **5,2 m/s** (punto fijo); en la toma corregida, a 1,5 m/s [CALCULADO].
   - Una luz de 12 mm entre barras no deja afuera los dedos [ESTIMADO: memoria técnica, no verificado].
   - **Reglas:**
     - kill cord en el piloto;
     - motor desarmado si hay alguien en el agua cerca de la popa;
     - nunca limpiar la rejilla con el sistema armado.
2. **Tal como está dibujado, el jet no bombea, y sin chorro no hay dirección.**
   - El impulsor queda por encima de la flotación estática, así que no ceba (§3.2). Además, nada une la rejilla con la bomba (§2).
   - En un jet, la dirección y la reversa salen del chorro. R10b documenta "no jet thrust, no steering".
   - Si se lo pone en el agua así, el bote queda sin propulsión y sin gobierno.
   - El sello mecánico giraría en seco. Eso es una fuga potencial hacia el casco [ESTIMADO: memoria técnica, no verificado].
3. **La toma corregida es un agujero de 311 × 130 mm en el fondo** [CALCULADO].
   - El bloque de toma y la carcasa de la bomba pasan a ser parte del límite estanco del casco: una fisura inunda el bote.
   - HamiltonJet advierte: *"Extreme care is required whenever inspection covers are removed, as water may enter the vessel through these openings"* [VERIFICADO: S6 p.162].
   - Cualquier tapa de inspección tiene que quedar **sobre** la flotación.
   - El bote necesita flotación propia (ver R10b).
4. **Aire en la toma = pérdida momentánea de control.** *"The Impeller may unload suddenly causing the engine RPM to fluctuate wildly… The operator must be prepared to lose control temporarily"* [VERIFICADO: S4 p.29].
5. **Velocidad legal.** Dentro de 300 m de la costa el máximo es 5 kn = 9,26 km/h [VERIFICADO: research/R07]. El objetivo "≥ 30 km/h" del plano solo es legal más afuera. Todo lo que sigue se dimensiona también para 9–10 km/h, que es donde el jet va a pasar la mayor parte del tiempo.

---

## 1. Veredicto (párrafo para reenviarle a Jorge)

> **Sí, Jorge tiene razón: la rejilla está muy atrás.**
>
> - En el dibujo está a unos 8–23 cm del espejo, debajo de la tobera. Eso queda **detrás** del impulsor (22–25 cm a popa de su cara).
> - En un waterjet el agua tiene que entrar **delante** del impulsor y subir por una rampa hasta su cara. Detrás del impulsor la bomba ya está empujando el agua hacia afuera, así que ahí no puede aspirar nada.
> - Además, el plano no dibuja ningún conducto entre la rejilla y la bomba.
> - El eje está a ~20–22 cm del fondo, o sea **por encima del agua** con el bote parado (calado ≈ 14 cm). Así la bomba no se ceba sola al arrancar.
>
> **Corrección**, con el mismo impulsor de 108 mm:
> - Abertura enrasada con el fondo de unos **31 × 13 cm** (no 12 × 9). Empieza ~10 cm delante de la cara del impulsor y llega hasta ~41 cm delante de ella, es decir a ~32–63 cm del espejo.
> - Rampa de ~27° con curvas suaves y labio redondeado.
> - Eje a **~115 mm** del fondo en el impulsor (debajo del agua en reposo), subiendo 5° hacia proa hasta el motor. El eje del motor queda a ~15 cm del fondo y unos 55–74 cm del espejo.
> - El sello va donde el eje atraviesa el techo de la rampa; los cojinetes quedan en seco por encima.
> - Rejilla de barras longitudinales, finas y perfiladas, enrasada con el fondo.
>
> **Antes de seguir:** medir el calado real en popa con piloto y baterías. El eje del impulsor tiene que quedar al menos 2 cm por debajo de esa línea de agua.

---

## 2. Qué está dibujado y dónde (lectura propia de la imagen)

**Método.**
- Recortes ampliados ×4 y ×8 con grilla de píxeles, más barrido de columnas y filas oscuras con Python (PNG de 1320 × 1023 px).
- Las posiciones se convierten a mm con las escalas que implican las **propias cotas** del plano.
- Esas escalas no coinciden entre sí [CALCULADO]:

| Cota | Escala |
|---|---|
| Horizontal: 2300 | 3,183 mm/px |
| Horizontal: cadena 850 + 750 + 700 | 3,645 mm/px (tramos de 3,44 a 3,91) |
| Vertical: 280 | 3,478 mm/px |
| Vertical: 420 | 3,836 mm/px |

Por eso cada posición se da como rango, y el dibujo **no es a escala**: la "1:10" no se cumple ni internamente.

**Posiciones medidas** (vista lateral "sección A–A"; mm, rango según la escala) [CALCULADO: script §2]:

| Elemento | Posición |
|---|---|
| Rejilla, extremo de popa | 80–91 mm del espejo |
| Rejilla, extremo de proa | 201–230 mm del espejo |
| Centro de la rejilla respecto de la cara del impulsor | **220–252 mm a popa** |
| Cara de entrada del impulsor (extremo de proa del cilindro de la bomba) | 360–412 mm del espejo |
| Extremo de popa del cilindro de la bomba (impulsor + estator) | 220–252 mm del espejo |
| Eje de la bomba sobre el fondo | **202–222 mm** |
| Eje del motor sobre el fondo | 235–259 mm. **No es coaxial con la bomba** en el dibujo |
| Rejilla respecto de la línea exterior del fondo | dibujada 12–48 mm **por encima**, dentro de un rebaje |
| Piso interior | 71–79 mm sobre el fondo |

**Dónde está la rejilla respecto de cada referencia:**
- **Impulsor:** a popa, debajo del tramo tobera/boquilla.
- **Eje:** directamente debajo de la línea del eje, aguas abajo del rotor.
- **Espejo:** pegada a él (8–23 cm).
- **Flotación:** con 150 kg el calado nominal es ≈ 137 mm (§5.1). La rejilla está bajo el agua, pero el eje (202–222 mm) y el impulsor entero (148–276 mm) quedan **por encima** de la flotación.

**¿El plano conecta la rejilla con la "Ø inicial toma 120"? No.**
- En el corte lateral, entre la rejilla y la bomba solo están el piso interior y el soporte. No hay conducto, rampa ni codo.
- En el detalle ampliado, la carcasa de la bomba es un cilindro cerrado aguas arriba por la caja de cojinetes (8) y el sello (9). No tiene ninguna abertura de entrada.
- Las tres cotas de diámetro ("Ø INICIAL TOMA 120 mm (aprox.)", "108 (impulsor)" y "Ø72 (tobera)") están dibujadas en el **extremo de salida** (derecha) del detalle, no en una entrada.
- Tal como está dibujada, la bomba no tiene por dónde recibir agua.

**Lo que leo distinto o agrego al resumen recibido:**
1. La "Ø inicial toma 120" está acotada en la salida del detalle, sobre el diámetro exterior de la carcasa. No es una entrada.
2. La cadena 850/750/700 suma 2300 [CALCULADO], pero termina **en la rejilla** (752 px), no en el espejo. La cota total 2300 llega hasta la boquilla/cuchara (849 px).
3. Vista trasera: la caja de la rejilla **asoma por debajo** de la quilla ~5 px (≈ 18–20 mm a 3,7 mm/px). En la lateral está **por encima** del fondo. Las dos vistas se contradicen, y en ninguna está "enrasada", como dice la nota.
4. Vista trasera: la cota 280 va del fondo de la caja de la rejilla hasta la línea que pasa ~8 px por encima del centro de la tobera. Con esa cota, el eje queda a ≈ 240 mm del fondo de la caja. Coherente con la lateral: eje ≈ 200–240 mm.
5. La rejilla mide 121–139 mm de largo en la lateral, contra "120 × 90 (aprox.)" en la planta y "ancho 120" en la trasera.
6. Erratas del rótulo: "AMPILIADO", "rodamientos/seatl". El título de la vista lateral está cortado ("…TA LATERAL SECCIÓN A–A").
7. Las flechas A–A de la planta marcan un corte transversal junto al espejo, pero se usan para un corte longitudinal. La tabla de materiales está tapada en parte por un ícono de "compartir" (es una captura de pantalla).
8. El motor de la lateral mide ~320–360 mm de largo, contra "180" en el detalle.

Las inconsistencias de escala, las erratas y las vistas contradictorias indican un dibujo compuesto sin CAD [ESTIMADO: lectura de la imagen]. **No hay que medir sobre él para fabricar.**

**Sobre la frase de Jorge** ("que da a la altura del eje del motor"): admite dos lecturas.
- "La rejilla que alimenta la altura del eje".
- "La rejilla que en la imagen queda debajo de la línea del eje".

Con cualquiera de las dos la conclusión es la misma: la abertura tiene que ir a proa del impulsor, y lo bastante adelante para que la rampa suba desde el fondo hasta la garganta.

---

## 3. Por qué está mal (mecanismo)

### 3.1 Dirección del flujo
- La bomba aspira por la cara de proa del impulsor; aguas abajo (estator, tobera) el agua está a presión y sale.
- Una abertura debajo de la tobera queda del lado de **descarga**. Con un conducto, haría recircular agua o descargaría por el fondo. Sin conducto, no hace nada.
- En una toma enrasada, la abertura entera está a proa de la cara del impulsor. La pared de proa (techo o "rampa") sube desde el fondo con una tangencia suave hasta la parte superior de la garganta. El labio, aguas abajo de la abertura, separa la toma del fondo del casco.
  - Esquema estándar: ITTC 23rd, toma de referencia *"flush-type lip geometry and S-shaped internal ducting"* [VERIFICADO: S3].
  - Huella elíptica *"that passes through the upstream tangency point of the inlet centerline roof curve"* [VERIFICADO: S3].

### 3.2 Cebado
- HamiltonJet: *"The Jet must be immersed with the water line at least up to the underside of the Mainshaft (at the Impeller) in order to prime (pump water) when the engine is started."* [VERIFICADO: S4 p.38].
- En el folleto: *"Water level must be at least up to the waterjet mainshaft when the craft is at rest."* [VERIFICADO: S5].
- Bulten (2006) desprecia la elevación de la bomba sobre la flotación justamente *"due to self-priming constraints"* [VERIFICADO: S1 ec. 2.64].
- En el plano, el eje queda **65–85 mm sobre la flotación nominal** [CALCULADO: 202–222 − 137].
  - Rango completo de calado (101–184 mm): de 18 a 121 mm por encima.
  - Con 200 kg en vez de 150 (R10b estima 165–242 kg), el calado nominal sube a ~183 mm [CALCULADO: 137 × 200/150] y el eje **todavía** queda 20–40 mm por encima.
- **No ceba.**

### 3.3 Tamaño de la abertura
- Un conducto de Ø120 que cruza el plano del fondo a un ángulo θ deja una huella de largo D/sin θ. A θ = 27° eso da **264 mm** [CALCULADO].
- Una abertura de 90 mm de largo no admite un conducto de 120 a ningún ángulo menor que 90°.
- Áreas:
  - 120 × 90 = 10 800 mm² = 1,18 × A_impulsor.
  - Con 6 barras de 4 mm, el área efectiva es 0,94 × A_impulsor [CALCULADO].
  - Referencia comercial, HJ212 (Ø210): abertura 525 × 260 mm → ~3,5 × A_impulsor [CALCULADO con el dato de S9].
- En punto fijo, el agua cruza la rejilla del plano a 5,2 m/s. Pierde 0,27–0,81 m de altura (K = 0,2 perfilada a 0,6 rectangular) [CALCULADO; K ESTIMADO], y eso se descuenta directamente del NPSH (§6). En la corregida pierde 0,02–0,07 m.
- La relación de ~3,5 del HJ212 se calculó con la misma forma de huella que la toma corregida (rectángulo + extremo semielíptico).

### 3.4 Rejilla no enrasada
- HamiltonJet: *"Check that the intake block is faired to the hull bottom. Contours should be smooth with no steps or protrusions greater than 2mm. There are no flow obstructions forward of the intake block."* [VERIFICADO: S6 p.43].
- El plano dibuja un rebaje y una caja que sobresale, según la vista que se mire.

---

## 4. Cómo se diseña la toma de un waterjet chico (criterios con fuente)

| Tema | Criterio | Fuente | Aplicado a Ø108 |
|---|---|---|---|
| Posición longitudinal | Abertura entera a proa del impulsor. Techo tangente al fondo en proa y alineado con el eje en la garganta. Labio aguas abajo de la abertura | [VERIFICADO: S3, S1 fig. 1.1/2.1] | Labio 96 mm y tangencia 407 mm delante de la cara del impulsor [CALCULADO] |
| Ángulo de rampa | Tomas convencionales: *"ramp-angles (duct inclination angles) that are less than about 30°"*. Con rampa baja, *"at low ship speeds, flow separation at the inlet may occur due to pump suction induced flow angles that are high relative to the shallow-ramp-angle"* y conductos largos con más pérdida viscosa | [VERIFICADO: S7] | — |
| Ángulo de rampa (caso típico) | Toma enrasada "típica" con *"a 25° ramp angle"* (D = 180 mm) | [VERIFICADO: S8] | **θ = 27°** [ESTIMADO: entre S8 y S7] |
| Forma del techo | Curva sin saltos de curvatura (polinomio de 5.º grado). "Effective inlet ramp angle taken at the inflection point" | [VERIFICADO: S3] | Arco R120 – recta – arco R120 [ESTIMADO]. Para fabricar, conviene suavizarlo a curvatura continua |
| Inclinación del eje | Bloque de toma estándar de 5° (opcional 0°): *"facilitates close direct drive coupling of the engine"* | [VERIFICADO: S5] | **α = 5°**, sube hacia proa [SUPUESTO] |
| Largo × ancho de abertura | HJ212 (Ø210): *"Inlet hole of 525mm x 260mm"* → 2,5 D × 1,24 D | [VERIFICADO: S9, dato de un usuario de foro] | 311 × 130 mm = 2,9 D × 1,2 D [CALCULADO] |
| Largo × ancho (V1) | Abertura de toma de **22 cm** en una unidad de 61 cm (0,36 del largo) | [VERIFICADO: research/R01] | Corregida: 311/746 = 0,42 del largo tangencia → boquilla. Plano de Jorge: 90/600 = 0,15 [CALCULADO] |
| Ancho del tubo de captación | Elíptico, **1,5–1,9 ×** el ancho geométrico de la toma (rectangular equivalente: 1,3 ×) | [VERIFICADO: S2]; caja de 1,3 D en [VERIFICADO: S1] | Fondo liso y sin apéndices en ≥ 200–250 mm de ancho delante de la toma [CALCULADO: 1,5–1,9 × 130] |
| Fondo delante de la toma | *"Avoid appendages such as keels, rudders, planing strakes, etc for at least 2 metres in front of the waterjet intake"* (jets de 200–400 mm). Sin escalones > 2 mm. La toma de agua de refrigeración, *"well to the side"* | [VERIFICADO: S5, S6 p.43, S6 p.39] | Escalado a este jet: ≥ 0,5–1,0 m limpios delante [ESTIMADO: 5–10 D, proporción de S5] |
| IVR: definición | ITTC: IVR = V_entrada/V_barco, medida por defecto *"in the throat of the intake"*; la recíproca se llama IVRR | [VERIFICADO: S3] | Bulten usa la recíproca (V_barco/V_bomba ≈ 1,3–1,8 en servicio) [VERIFICADO: S1] |
| IVR baja (alta velocidad) | Separación en el techo de la toma *"below IVR values of approximately 0.65"*. Riesgo de cavitación del lado casco del labio | [VERIFICADO: S3 citando a Bulten; S1 §2.1.2] | A 30 km/h: IVR = 0,54–0,59 → **zona de separación en el techo** |
| IVR alta (baja velocidad) | El punto de estancamiento pasa al lado casco del labio → *"cavitation and/or separation in the inlet at the upper side of the lip"*. *"An inlet has to be designed to cope with the low IVR and the design IVR condition"* | [VERIFICADO: S1 §2.1.2] | A 5 kn: IVR = 1,55–1,75 → **labio redondeado y generoso** |
| Labio | Redondeado, con transición *"smooth, separation free"* | [VERIFICADO: S7] | r ≈ 12 mm ≈ 0,1 D_garganta [ESTIMADO: memoria técnica, no verificado] |
| Rejilla: función | *"Intake block, including protective screen bars… the screen protects the pump from damage due to ingested material, without adversely affecting waterflow"*, con rastrillo para algas | [VERIFICADO: S5] | — |
| Rejilla: orientación | El rastrillo se usa *"over the rear of the transom"*, o sea que las barras corren a lo largo (proa-popa) | [VERIFICADO: S6 p.162]; orientación [ESTIMADO: deducida] | 7 barras longitudinales |
| Rejilla: forma | *"Rather than the circular and rectangular intake grid, the streamlined intake grid can improve the hydraulic performance"*. La rejilla reduce el empuje | [VERIFICADO: S10, solo resumen] | Perfil con borde de ataque redondo y fuga afinada |
| Rejilla tapada | *"Running at speed with a partially blocked Inlet Grill or debris on the Impeller will result in cavitation damage"* | [VERIFICADO: S4 p.28] | — |
| Rejilla: luz y espesor | Más chica que el pasaje más estrecho de la bomba y no tan chica que se tape con algas | — | **12 mm de luz, barras de 4 mm** → 78 % abierta [ESTIMADO, no verificado]. Pérdida K = 0,2 (perfilada) a 0,6 (rectangular) [ESTIMADO: fórmula de Kirschmer, memoria técnica] |
| Altura del eje | A la altura de la flotación o por debajo, en reposo (§3.2). Referencia de proporción: HJ241, *"Centre Line Height 0.284 m"* | [VERIFICADO: S4 p.37, S5]; la serie HJ va de 200 a 400 mm de impulsor [VERIFICADO: S12] | Si el Ø del HJ241 es ~240 mm, H/D ≈ 1,2 [ESTIMADO: Ø no verificado por modelo]. Para Ø108: ≤ 130 mm. Se adopta **115 mm** por el calado (§5) |
| Aire | *"Aerated water generated by the vessel's bow wave must not pass directly aft to the Jet Unit Intake(s)"*. Proa en V y ≥ 10° de astilla muerta | [VERIFICADO: S4 p.38, S5] | Fondo plano: riesgo de aire con ola y golpes (§7) |
| Arena y poca profundidad | *"At slow displacement speed avoid using high RPM in shallow water"*. Parar el motor suelta lo que quedó en la rejilla. Anillo de desgaste inox *"when operating in silt-laden water"* | [VERIFICADO: S4 p.28, S5] | ~30 cm de luz bajo el jet en desplazamiento [VERIFICADO: research/R03 S12] |
| Potencia a baja velocidad | *"Full power cannot be used at low vessel speeds"* | [VERIFICADO: S4 p.28] | Rampa de corriente o límite en el ESC por debajo de ~10 km/h (§6) |
| Velocidad periférica | Límite práctico de 35–45 m/s para impulsores de jet | [VERIFICADO: S9, foro, usuario "baeckmo"] | U = 25,4 m/s a 4500 rpm [CALCULADO] → no es el limitante |

Allison (1993), "Marine waterjet propulsion", SNAME Trans. 101, es la referencia clásica para la toma. **No la pude abrir.** Buscar: "Allison 1993 Marine waterjet propulsion SNAME Transactions 101 inlet design".

---

## 5. Geometría corregida, parametrizada

**Convenciones del script:**
- xf = distancia hacia proa desde la cara exterior del espejo.
- y = altura sobre la cara exterior del fondo.
- La pila de la bomba es la del plano: impulsor + estator 120 mm, tobera 100 mm hasta el espejo, boquilla 120 mm afuera.

Para cambiar la geometría, se editan `P[...]` en el script y se vuelve a correr.

### 5.1 Calado estático (150 kg, casco 2,30 × 0,80 m)

T = m / (ρ·C_b·L_wl·B_wl), con ρ = 1013 kg/m³ [CALCULADO: `inputs.yaml`].

| Caso | L_wl | B_wl | C_b | **T** |
|---|---|---|---|---|
| Nominal | 2000 mm [ESTIMADO: 2300 menos ~0,3 m de proa lanzada] | 750 mm [ESTIMADO] | 0,72 [ESTIMADO: el mismo de `inputs.yaml`] | **137 mm** [CALCULADO] |
| Mínimo (casco lleno y ancho) | 2300 | 800 | 0,80 | **101 mm** [CALCULADO] |
| Máximo (casco fino) | 1900 | 650 | 0,65 | **184 mm** [CALCULADO] |

El trimado hacia popa (motor, baterías y piloto atrás) aumenta el calado en popa respecto de la media, lo que favorece el cebado [ESTIMADO: no calculado, falta la distribución de masas]. **Medirlo.**

### 5.2 Tabla de la toma corregida (salida del script, valores por defecto)

| Magnitud | Valor | Etiqueta |
|---|---|---|
| Cara del impulsor desde el espejo | 219 mm | [CALCULADO: 220 × cos 5°] |
| **Labio** (punta, extremo de popa de la abertura): desde la cara del impulsor / desde el espejo | **96 / 315 mm** | [CALCULADO] |
| **Tangencia de la rampa** (extremo de proa de la abertura): desde la cara del impulsor / desde el espejo | **407 / 626 mm** | [CALCULADO] |
| Abertura, largo × ancho | **311 × 130 mm** (2,9 D × 1,2 D) | [CALCULADO] / ancho [ESTIMADO] |
| Ángulo de rampa θ (tramo recto) | 27° | [ESTIMADO: §4] |
| Radios del techo (junto a la garganta / en la tangencia) | 120 / 120 mm | [ESTIMADO] |
| Radio de la pared inferior junto a la garganta | 60 mm | [ESTIMADO] |
| Radio de nariz del labio | 12 mm | [ESTIMADO] |
| Techo en la garganta / fondo de la garganta, sobre el fondo del casco | 175 / 55 mm | [CALCULADO] |
| Área del impulsor / de la garganta Ø120 | 9 161 / 11 310 mm² | [CALCULADO] |
| Área bruta de la abertura (rectángulo + extremo de proa semielíptico) | 36 808 mm² = **4,0 × A_imp** | [CALCULADO] |
| Rejilla | 7 barras de 4 mm, luz 12 mm, 78 % abierta | [ESTIMADO] |
| Área efectiva con rejilla | 28 880 mm² = **3,15 × A_imp** | [CALCULADO]. Plano de Jorge: 0,94 × |
| Sección del tramo inclinado / garganta | 1,15 (el conducto converge hacia la bomba) | [CALCULADO con forma rect. redondeada 0,9, ESTIMADO] |
| **Eje en la cara del impulsor**, sobre el fondo | **115 mm** | [CALCULADO: regla h ≤ T − 20 con T = 137] |
| Eje respecto de la flotación nominal / parte inferior del eje | **−22 / −32 mm** (debajo del agua) | [CALCULADO] |
| Punta superior del impulsor respecto de la flotación nominal | +32 mm | [CALCULADO]. Hamilton solo exige el eje |
| Inclinación del eje α | 5°, sube hacia proa | [SUPUESTO, práctica de S5] |
| Eje de la tobera en el espejo | 96 mm sobre el fondo (sumergida en reposo, normal en jets) | [CALCULADO] |
| El eje sale por el techo (sello, cara mojada) | 349 mm del espejo. Eje mojado dentro del conducto: 130 mm | [CALCULADO] |
| Caja de cojinetes en seco (Ø70, 80 mm) | 435–515 mm del espejo | [CALCULADO; Ø70 SUPUESTO] |
| **Motor** (Ø170 × 180) | **555–735 mm del espejo** | [CALCULADO] |
| **Eje del motor**, en el centro del motor | **≈ 152 mm** sobre el fondo (plano de Jorge: 235–259) | [CALCULADO] |
| Parte inferior del motor | 67 mm sobre el fondo | [CALCULADO]. Choca con el piso dibujado a 71–79 mm |
| Velocidad periférica a 4500 rpm | 25,4 m/s | [CALCULADO] |

**Reglas de diseño** (para cuando cambie un dato):
- **Altura del eje en el impulsor:** h ≤ T_popa,medido − 20 mm, y h ≥ D_garganta/2 + ~35 mm ≈ 95 mm, para que entren la pared inferior, el labio y el casco [SUPUESTO: margen].
  - Con T = 101 mm (caso mínimo) hay que bajar a ~95–100 mm, o lastrar la popa.
  - Con T ≥ 150 mm se puede subir hasta ~130 mm (H/D ≈ 1,2, §4).
- **Sensibilidad** [CALCULADO: script con variantes]:

  | Variante | Labio / tangencia desde el impulsor | Otros efectos |
  |---|---|---|
  | θ = 25° | 101 / 434 mm | Abertura 334 mm |
  | θ = 30° | 90 / 373 mm | Abertura 283 mm, área efectiva 2,8 × |
  | h = 100 mm | 66 / 377 mm | Eje del motor 137 mm |
  | h = 130 mm | 125 / 436 mm | Eje del motor 167 mm |
  | α = 7° | — | Eje del motor 166 mm, motor a 81 mm del fondo (libra el piso dibujado), tobera a 88 mm en el espejo |
  | α = 0° | — | Motor a 589–769 mm y a 30 mm del fondo: exige piso simple, sin doble fondo |

- **Si Jorge deja el impulsor donde lo dibujó** (cara a ~385 mm del espejo):
  - labio a 480 mm y tangencia a 791 mm del espejo;
  - motor a 721–901 mm, con el eje a 152 mm [CALCULADO].

### 5.3 Comparación directa

| | Plano de Jorge | Corregido |
|---|---|---|
| Abertura respecto de la cara del impulsor | 220–252 mm **a popa** (centro) | 96 → 407 mm **a proa** |
| Abertura desde el espejo | 80–230 mm | 315–626 mm |
| Tamaño / área efectiva | 120 × 90 / 0,94 × A_imp | 311 × 130 / 3,15 × A_imp |
| Conducto rejilla → bomba | ninguno | rampa de 27° + garganta Ø120 |
| Eje en el impulsor sobre el fondo / sobre la flotación nominal | 202–222 / **+65 a +85** (no ceba) | 115 / **−22** (ceba) |
| Eje del motor sobre el fondo | 235–259 | ≈ 152 (5° de inclinación) |
| Sello / cojinetes | en línea, sin cámara húmeda definida | sello en el techo de la rampa, cojinetes en seco encima |
| V del agua en la rejilla (punto fijo, 5 kW) | 5,2 m/s | 1,5 m/s |

---

## 6. IVR y cavitación a 4500 rpm

### Modelo [CALCULADO: script §3]

**Punto de operación.** η_p·η_m·P_el = ρ g Q H_R, con:
- H_R = (1 + φ) Vj²/2g − (1 − ε) Vin²/2g [VERIFICADO: S1 ec. 2.56, con h_j ≈ 0];
- Q = A_tobera·Vj;
- Vin = (1 − w)·V.

| Parámetro | Valor | Etiqueta |
|---|---|---|
| η_m (motor + ESC) | 0,85 | [ESTIMADO] |
| η_p (bomba chica) | 0,65 (rango 0,5–0,8) | [ESTIMADO] |
| ε | 0,20 | [VERIFICADO como rango típico 0,10–0,30: S1] |
| φ | 0,02 | [VERIFICADO: valor del ejemplo de S1] |
| w | 0,05 | [ESTIMADO] |

Se supone que el impulsor absorbe la potencia de diseño a 4500 rpm.

**IVR (ITTC)** = V_garganta/V_barco, con la garganta de Ø120 [VERIFICADO: definición S3].

**NPSH disponible:**
- NPSH_A = (p_atm − p_v)/ρg + (1 − ε) Vin²/2g − h_j [VERIFICADO: S1 ec. 2.64].
- p_v = 2984 Pa (agua a 24 °C, peor caso) [ESTIMADO: `inputs.yaml`].
- Además se restan:
  - la pérdida de la rejilla, K·V_rejilla²/2g con K = 0,6 [ESTIMADO];
  - una pérdida de conducto a punto fijo, 0,2·V_garganta²/2g [ESTIMADO].
- h_j es la altura de la **punta superior** del impulsor sobre la superficie libre en popa: el calado a ≤ 10 km/h y el fondo planeando [ESTIMADO].

**NPSH requerido**, por velocidad específica de succión: n_ωs = Ω√Q/(g·NPSH_R)^¾.
- *"Values of about 4.0 are common in commercial pumps… a design value of 3.5 for a waterjet impeller is adopted"* [VERIFICADO: S1 ec. 2.29, §2.2.3].
- **Margen** = NPSH_A/NPSH_R. Un margen < 1 significa cavitación con pérdida de prestaciones.

### Resultados

| Caso | V km/h | Q L/s | V garganta m/s | **IVR** | Empuje N | NPSH_A corr. (m) | NPSH_R n_ωs 3,5 / 4,0 (m) | **Margen corregida** | Margen plano Jorge* |
|---|---|---|---|---|---|---|---|---|---|
| 5 kW | 0 | 44,6 | 3,94 | ∞ | 495 | 9,63 | 8,85 / 7,40 | **1,09 / 1,30** | 0,99 / 1,19 |
| 5 kW | 9,26 (5 kn) | 45,2 | 3,99 | 1,55 | 396 | 10,03 | 8,92 / 7,47 | 1,12 / 1,34 | 1,03 / 1,23 |
| 5 kW | **10** | 45,3 | 4,00 | **1,44** | 389 | 10,07 | 8,93 / 7,48 | 1,13 / 1,35 | 1,03 / 1,23 |
| 5 kW | 20 | 47,3 | 4,18 | 0,75 | 304 | 10,78 | 9,20 / 7,70 | 1,17 / 1,40 | 1,07 / 1,28 |
| 5 kW | **30** | 50,6 | 4,48 | **0,54** | 232 | 12,19 | 9,63 / 8,06 | 1,27 / 1,51 | 1,16 / 1,38 |
| 7,2 kW | 0 | 50,3 | 4,45 | ∞ | 631 | 9,57 | 9,59 / 8,03 | **1,00 / 1,19** | **0,89** / 1,06 |
| 7,2 kW | **10** | 50,9 | 4,50 | **1,62** | 510 | 10,05 | 9,67 / 8,09 | 1,04 / 1,24 | 0,93 / 1,11 |
| 7,2 kW | **30** | 55,7 | 4,93 | **0,59** | 326 | 12,17 | 10,26 / 8,59 | 1,19 / 1,42 | 1,06 / 1,27 |

\*Plano de Jorge **suponiendo** que tuviera conducto y estuviera cebado: rejilla de 120 × 90 e impulsor 129 mm sobre la flotación en reposo. En la realidad no bombea (§3).

Sensibilidad a η_p = 0,5–0,8, a 5 kW [CALCULADO]:
- IVR a 30 km/h: 0,50–0,57.
- IVR a 10 km/h: 1,32–1,54.
- Empuje a punto fijo: 415–568 N.

### Lectura
1. **IVR a 30 km/h = 0,54–0,59.** Está por debajo de ~0,65, donde empieza la separación en el techo [VERIFICADO: S3]. En la convención de Bulten equivale a 1,7–1,85, el extremo alto de su rango de servicio (1,3–1,8).
   - Mitigación: rampa no más baja de ~25° y curvatura continua. Opcional: micro-generadores de vórtices delante de la toma. En S8 mejoraron ~8 % la recuperación de presión a IVR 0,5, con ~1,5 % de arrastre extra a IVR > 0,7 [VERIFICADO: S8].
2. **IVR a 10 km/h = 1,44–1,62; a 5 kn = 1,55–1,75.** Ese es el régimen habitual dentro de los 300 m. Riesgo de separación y cavitación en la cara interna del labio [VERIFICADO: S1]. Por eso el labio va redondeado y la rampa no más baja de ~25–30° [VERIFICADO: S7].
3. **Cavitación del impulsor a 4500 rpm.** Aun con la toma corregida, el margen a punto fijo es chico:
   - 1,09–1,30 a 5 kW;
   - 1,00–1,19 a 7,2 kW, o sea **al límite**.
   - Caudal máximo sin cavitar (n_ωs = 3,5): ≈ 50 L/s, contra 44,6 L/s (5 kW) y 50,3 L/s (7,2 kW) [CALCULADO].
   - Con la rejilla chica del plano, el margen cae por debajo de 1 a 7,2 kW.
   - Implicancias: (a) limitar corriente o potencia por debajo de ~10 km/h, como dice Hamilton [VERIFICADO: S4 p.28]; (b) mantener la rejilla limpia; (c) si la bomba se rediseña, una rpm menor o un impulsor de menor requerimiento de succión dan margen [ESTIMADO: memoria técnica, no verificado].
4. **Velocidad periférica** de 25,4 m/s, contra el límite práctico de 35–45 m/s [VERIFICADO: S9]. No limita.
5. **Empuje a 30 km/h:** 232 N a 5 kW y 326 N a 7,2 kW [CALCULADO].
   - La curva típica de Savitsky da R/Δ ≈ 0,10 a SLR 3 [VERIFICADO: R09 S21]. Extrapolado a SLR ≈ 6 [ESTIMADO], 150 kg dan ~150 N.
   - R09 advierte que en cascos rechonchos esa curva subestima ×2, lo que da ~300 N [CALCULADO].
   - **≥ 30 km/h con 5 kW no está asegurado.** R10b lo analiza en detalle.

---

## 7. Aire, ola, arena y algas (aplicado a este bote)

- **Ola y cabeceo.** Con la toma a 8–23 cm del espejo, como en el plano, la abertura queda en la zona que primero se ventila cuando la popa sube en una ola o cuando el agua se separa del canto del espejo [ESTIMADO: memoria técnica, no verificado].
  - Al llevarla a 32–63 cm del espejo y enrasarla con el fondo, siempre queda bajo la parte mojada.
  - Una abertura más larga también tolera mejor un cabeceo breve.
- **Fondo plano.** Hamilton pide proa en V y ≥ 10° de astilla muerta para que el aire de la ola de proa no llegue a la toma [VERIFICADO: S5].
  - En un fondo plano que golpea en la ola entra aire [ESTIMADO: memoria técnica, no verificado].
  - Mitigación: toma en crujía, en el punto más bajo del casco, y nada que genere burbujas delante (quillas, tracas, transductores, cabezas de remache, la toma de refrigeración) [VERIFICADO: S5, S6 p.39].
- **Aire = pérdida de control.** Si el rpm se dispara, reducir hasta que el empuje se estabilice [VERIFICADO: S4 p.29]. Para pruebas: el ESC tiene que limitar las rpm en vacío [ESTIMADO].
- **Arena y piedras.**
  - Hamilton: no usar rpm altas en aguas bajas a velocidad de desplazamiento; salir a ralentí hasta aguas profundas [VERIFICADO: S4 p.28].
  - En desplazamiento hacen falta ~30 cm de agua libre **debajo** del jet [VERIFICADO: research/R03 S12].
  - Con un calado de ~14 cm, eso son ~45 cm de agua. La ventaja de un jet en poca agua aparece recién al planear [VERIFICADO: research/R03].
  - La holgura de punta del plano (0,5–0,8 mm) necesita un **anillo de desgaste** inox reemplazable [VERIFICADO como práctica: S5].
- **Algas.** La rejilla las retiene. Si queda tapada a velocidad, el impulsor cavita y se daña [VERIFICADO: S4 p.28].
  - Para limpiarla: parar el motor, que suelta lo atrapado [VERIFICADO: S4 p.28], y usar un rastrillo desde el espejo [VERIFICADO: S6 p.162].
  - Barras longitudinales y perfiladas facilitan las dos cosas.

---

## 8. Qué medir y probar (en orden, con criterio pasa / no pasa)

1. **Calado estático en popa**, con piloto, baterías y motor a bordo, en agua del fiordo. Se mide en el espejo, en crujía.
   - **Pasa:** eje del impulsor ≤ T − 20 mm. Con el diseño por defecto (115 mm), T ≥ 135 mm.
   - Si no pasa: recalcular con `P["h_shaft"]` y volver a correr el script.
2. **Geometría real del fondo** en la zona de la toma, de 0 a 1,0 m del espejo: ¿plano? ¿astilla muerta? ¿quilla o tracas? ¿espesor del fondo y del piso? Hace falta ≥ 0,5 m limpio delante de la tangencia. Debajo del motor, el piso tiene que quedar a ≤ ~60 mm del fondo, porque con α = 5° el motor baja hasta 67 mm. Si no, usar α = 7°.
3. **Banco en seco:** girar sin agua solo segundos y nunca a rpm altas, porque el sello no debe girar en seco [ESTIMADO: memoria técnica].
4. **Prueba de cebado en el muelle,** amarrado:
   - arrancar a rpm bajas;
   - **pasa** si sale un chorro continuo por la tobera en ≤ 3 s [SUPUESTO: criterio];
   - si no, cortar.
5. **Estanqueidad del bloque de toma:** 24 h a flote amarrado, sin agua en la sentina. Tapa de inspección sobre la flotación.
6. **Rejilla:**
   - una varilla de Ø13 mm no debe pasar [SUPUESTO];
   - barras sin rebabas y enrasadas con el fondo con escalón ≤ 2 mm [VERIFICADO: S6 p.43].
7. **Punto fijo con dinamómetro,** con escalones de 25 % de potencia.
   - Registrar empuje, corriente y rpm.
   - **No pasa** si el rpm sube con el empuje plano o si aparece ruido de grava: son síntomas de cavitación o bloqueo [VERIFICADO: S4 p.29, "engine unloading (RPM increases), lack of jet thrust, excessive noise"].
   - Comparar con 495 N a 5 kW [CALCULADO, ±20 % por η_p].
8. **Vacuómetro en la garganta** (toma de presión en la pared, delante del impulsor): mide el NPSH_A real. Si a punto fijo cae por debajo de ~9 m de columna, revisar la rejilla y el conducto [CALCULADO: §6].
9. **Hilos (tufts) en el techo y el labio,** filmados con una cámara sumergible a 5 kn y a la velocidad máxima. Muestran si hay separación en la rampa a IVR bajo y en el labio a IVR alto [ESTIMADO: método].
10. **Aire:** recorrido con ola corta, registrando las rpm. **No pasa** si hay picos de rpm > 10 % sin mover el acelerador [SUPUESTO].
11. **Arena:** solo a ralentí en < 0,5 m de agua. Después, revisar el impulsor y el anillo de desgaste.

---

## 9. Fuentes abiertas en esta sesión

| # | Fuente | Qué se leyó |
|---|---|---|
| S1 | Bulten, N. W. H. (2006), *Numerical analysis of a waterjet propulsion system*, tesis doctoral, TU Eindhoven. https://pure.tue.nl/ws/files/2277312/200612081.pdf | PDF completo (pdftotext): §1.1, §2.1–2.2.3 (IVR, fenómenos con IVR baja y alta, NPSH, n_ωs ≈ 4,0 / 3,5), ec. 2.56 y 2.64, ε = 0,10–0,30, φ = 0,02, w = 0,12, caja de 1,3 D |
| S2 | ITTC, *The Specialist Committee on Waterjets – Final Report and Recommendations to the 22nd ITTC*. https://ittc.info/media/1518/specialist-committee-on-waterjets.pdf | Ancho del área de captación 1,5–1,9 × el ancho geométrico (Roberts & Walker 1998; Alexander 1994) |
| S3 | ITTC, *The Specialist Committee on Validation of Waterjet Test Procedures – Final Report… 23rd ITTC*. https://ittc.info/media/1467/waterjet.pdf | Toma enrasada de referencia (labio enrasado, conducto en S, huella elíptica, techo polinómico de 5.º grado, ángulo efectivo en la inflexión), IVR en la garganta / IVRR, separación con IVR < ~0,65 |
| S4 | HamiltonJet HJ241 / HSRX, manual (ManualsLib). https://www.manualslib.com/manual/3387713/Hamilton-Jet-Hj241.html (páginas 28, 29, 37, 38, 39) | Inmersión hasta el eje para cebar; aire de la ola de proa; rejilla tapada → cavitación; aguas bajas; aire → pérdida de control; potencia a baja velocidad; tabla de dimensiones (altura de eje 0,284 m) |
| S5 | HamiltonJet, folleto *HJ Series 80 kW to 900 kW*. https://www.sewartsupply.com/images/pdfs/hj-series-brochure.pdf | Bloque de toma con barras y rastrillo; anillo de desgaste para agua con limo; bloque estándar de 5°; nivel de agua hasta el eje en reposo; 2 m sin apéndices delante de la toma; astilla muerta de 10–25° |
| S6 | HamiltonJet HJ212, *Installation and Service Manual* (ManualsLib). https://www.manualslib.com/manual/1639087/Hamilton-Jet-Hj212.html (páginas 39, 43, 162) | Escalones ≤ 2 mm; sin obstrucciones delante; toma de refrigeración al costado; rastrillo desde el espejo; cuidado con las tapas de inspección |
| S7 | US 5439402 A, *Design of an integrated inlet duct for efficient fluid transmission* (US Navy, 1994). https://patents.google.com/patent/US5439402A/en (WebFetch) | Antecedentes: rampas convencionales < ~30°; con rampa baja, separación a baja velocidad, conductos largos y labio de radio grande; labio "smooth, separation free" |
| S8 | Chen et al. (2025), "Influences of micro ramp vortex generators on the performance of flush waterjet propulsor", *Sci Rep* 15:31278. https://pmc.ncbi.nlm.nih.gov/articles/PMC12379258/ | Toma típica con rampa de 25°, D = 180 mm; separación en la rampa con IVR baja; efecto de los generadores de vórtices |
| S9 | boatdesign.net, "Max engine RPMs for jet drive". https://www.boatdesign.net/threads/max-engine-rpms-for-jet-drive.47831/ | baeckmo: velocidad periférica máx. 35–45 m/s. speedboats: HJ212 = impulsor de Ø210, abertura 525 × 260 mm (dato de foro) |
| S10 | Luo et al. (2021), "Investigation of Complex Characteristics of Waterjet Propulsion Device with Intake Grid", *Shock and Vibration*, doi:10.1155/2021/6688635, vía https://api.crossref.org/works/10.1155/2021/6688635 | **Solo el resumen**: rejilla perfilada mejor que circular o rectangular; la rejilla reduce el empuje |
| S11 | Discover Boating, "Riding Rules for Personal Watercraft". https://www.discoverboating.com/resources/riding-rules-for-personal-watercraft | Peligro de atrapamiento en la rejilla; cordón de corte |
| S12 | Palmer Johnson, "HamiltonJet HJ Series". https://www.pjpower.com/products/hamiltonjet/hj-series-water-jets | "8 models ranging from 200mm to 400mm diameter impellers" |

Del repositorio (ya verificadas allí):
- `research/R01_videos.md`: V1, abertura de toma de 22 cm en 61 cm.
- `research/R03_proyectos_jet_ducted_efoil.md`: S12 outboardjets, ~30 cm de luz bajo el jet; jets impresos.
- `research/R07_dinamarca.md`: 5 kn a < 300 m.
- `research/R09_metodos.md`: S21, R/Δ típica de Savitsky.
- `research/R10b_auditoria_plano_jorge.md`: resto del plano, en paralelo.

**No abiertos** (bloqueados, 403 o sin acceso):
- Allison 1993. Buscar: "Allison Marine waterjet propulsion SNAME 1993".
- Jiao et al. 2019. Buscar: "Optimal Design of Inlet Passage for Waterjet Propulsion System Based on Flow and Geometric Parameters" (según el buscador: rampa de 30–35° y largo ≈ 6 D; **no verificado**).
- "Influence of Inlet Duct Length on the Hydraulic Performance of the Waterjet Propulsion Device".
- Cuerpo del paper de Luo 2021.
- Hamilton *HJ Designer's Manual*. Buscar: "HamiltonJet HJ designers manual intake".
- Luz entre barras de rejillas comerciales. Buscar: "Mercury SportJet intake grate tine spacing rock grate".
- Fórmula de Kirschmer para rejillas. Buscar: "Kirschmer trash rack loss coefficient bar shape factor".

---

## 10. Qué no pude verificar

- **Diámetro de impulsor de cada modelo HamiltonJet.** Solo el rango de la serie (200–400 mm). Por eso H/D ≈ 1,2 es [ESTIMADO].
- **Dato del HJ212** (525 × 260 mm de abertura): es de un usuario de foro, no del fabricante.
- **Luz y espesor de barras de rejilla comerciales, y coeficiente de pérdida de la rejilla.** Quedan [ESTIMADO].
- **Radio de labio, radios del techo y relación de áreas óptimas para un jet de Ø108.** No hay fuente abierta para esta escala. Son [ESTIMADO] escalados de jets grandes y hay que validarlos con las pruebas 7–9 de la §8.
- **η de la bomba y punto de operación a 4500 rpm.** Sin curva de la bomba ni ensayo. El IVR y el NPSH dependen de Q (sensibilidad en §6).
- **n_ωs del impulsor de Jorge.** Se usaron 3,5–4,0, valores genéricos de S1.
- **Dimensiones reales del casco** (L_wl, B_wl, C_b, astilla muerta, piso, espesores) **y la masa real.** El calado de 101–184 mm es un rango calculado, no medido.
- **El plano en sí:** no es a escala y sus vistas se contradicen. Todas las posiciones "del plano de Jorge" tienen ±15 %.
