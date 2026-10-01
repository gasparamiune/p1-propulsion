# R10b — Auditoría técnica del plano preliminar de waterjet de Jorge (26/09/2026)

Fecha: 2026-10-01. Objeto: `referencias/2026-09-26_plano_preliminar_waterjet_jorge.png` ("PLANO PRELIMINAR – WATERJET PARA JET BOAT 2.30 m", escala 1:10, mm, hoja 1/1, rotulado "NO USAR COMO PLANO FINAL DE MECANIZADO"). Comentario de Jorge, reenviado por Gaspar: *"La rejilla de succión que da a la altura del eje del motor en la imagen está muy atrás !"*.

**Alcance.** Este informe revisa todo el plano menos la toma, que analiza otro agente. Sobre la toma, una sola línea: **Jorge tiene razón**. En la vista lateral, la rejilla queda a ~140 mm del espejo [CALCULADO: §4.1], debajo de la tobera y a popa del impulsor. El corte A‑A no dibuja ningún ducto de admisión, y en la vista trasera la rejilla sobresale ~20 mm del fondo [CALCULADO: 5 px × 3,72 mm/px], aunque la nota dice "enrasada".

**Etiquetas:** [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO]. Los cálculos se hicieron con el script Python de la §8 (ejecutado; la salida está copiada en §4). Densidad del agua: 1013 kg/m³ [CALCULADO: `inputs.yaml` `water.density_kg_m3`].

---

## 1. Resumen ejecutivo

1. **Seguridad: estabilidad.** Con manga de 800 mm (0,71–0,77 m en la flotación, medida en la vista trasera) y el piloto sentado sobre un piso elevado por las baterías, el GM da **−40 a +90 mm** [CALCULADO: §4.3 y §9]. Aun en el mejor caso (+90 mm), correr el piloto 0,1 m hacia una banda escora el bote ~28° [CALCULADO, lineal, solo indicativo]. Puede volcar parado, al subir a bordo o al reabordar desde el agua. El agua está a < 15 °C en ≥ 90 % de los días de octubre a mayo [VERIFICADO: R07 §3.1].
2. **Seguridad: casco.**
   - El plano no tiene flotación.
   - Las baterías van sobre el fondo.
   - El sello mecánico figura en la lista (ítem 9), pero no está dibujado: su globo apunta a un rodamiento.
   - Capacidad por 33 CFR 183.33: **51–64 kg**, menos que **un** adulto [CALCULADO con fórmula VERIFICADA]. La regla de personas para motor interior (33 CFR 183.39 [VERIFICADO]) da **1 persona** como máximo. No admite una segunda persona.
3. **Seguridad: eléctrica y control.**
   - 72 V nominales son 80–84 V con la batería cargada, por encima de los 50 V CC [VERIFICADO: R06].
   - No hay kill switch ni parada de emergencia.
   - "No jet thrust, no steering" [VERIFICADO: CG Aux]. Con la reversa opcional, el bote no tiene freno.
4. **No funciona tal cual dibujado:**
   - con 150 kg el eje del jet queda **45–120 mm sobre la flotación** estática y la bomba no ceba; con 200 kg queda 0–75 mm sobre, en el límite [CALCULADO con dos modelos de sección, §4.3 y §9 + VERIFICADO: dmsonline];
   - el corte A‑A no tiene ducto de admisión;
   - la boquilla direccional está dentro de la carcasa fija;
   - después de la tobera hay una expansión brusca que pierde ~50 % de la altura dinámica [CALCULADO: §4.1].
5. **Masa.** "150 kg (embarcación + piloto + baterías)" es optimista. Lo realista son **165–242 kg** con 3 kWh LFP [ESTIMADO: §4.2].
6. **Velocidad.**
   - Con **5 kW**, ≥ 30 km/h solo se alcanza con 150 kg y una bomba buena (26–32 km/h). Con 200 kg el bote no pasa de **20–25 km/h** o no planea [CALCULADO: Savitsky + cantidad de movimiento, §4.4–4.5].
   - Con **7,2 kW sostenidos** (100 A) llega a 21–34 km/h con 200 kg; en 1 o 2 de los 6 cascos probados no pasa la transición. A esa potencia, 3 kWh útiles duran **~25 min** [CALCULADO].
7. **La bomba es coherente en orden de magnitud.** Un impulsor de Ø108 a 4500 rpm absorbe 5–7 kW [CALCULADO]:

   | Magnitud | Valor |
   |---|---|
   | Velocidad periférica U | 25,4 m/s |
   | Ω_s | 4,1–4,8 (axial) |
   | ψ | 0,10–0,13 |
   | Empuje a punto fijo | 550–760 N |
   | η batería → empuje a 30 km/h | 0,40–0,46 |
   | σ en la punta | 0,28–0,35 (margen chico) |

   El eje de Ø20 sobra: FS ≥ 5,5 [CALCULADO].
8. **Holgura de punta.** Los 0,5–0,8 mm (0,46–0,74 % de D) no se logran ni se mantienen en PETG. Una pala impresa tendría σ de raíz ≈ 7 MPa contra 2,7 MPa admisibles [CALCULADO con R05]. Hacen falta impulsor metálico y anillo de desgaste torneado.
9. **Legal y operación (Als Fjord).**
   - Los 30 km/h son **ilegales a < 300 m de la costa** (máximo 5 kn = 9,26 km/h) [VERIFICADO: reglamento policial], que es justo donde opera el proyecto.
   - A 5 kn el jet gasta **0,65–3,9 kW** [CALCULADO, con R/Δ ESTIMADO]. Como referencia, no comparable (otra velocidad, otro casco, otra carga): P1 usa 0,76–0,91 kW con 2 personas a 6 km/h.
   - No requiere licencia (< 19 kW) [VERIFICADO: R07].
   - Queda pendiente confirmar que no se lo clasifique como "vandscooter" [VERIFICADO: BEK 809/2019 §1, §3].
10. **Veredicto.** Es un croquis conceptual de **otro producto**: jet *inboard*, 1 piloto, ≥ 30 km/h, 72 V y casco propio de 2,30 × 0,80 m. Contradice los requisitos de P1: 2 personas, 6 km/h durante ≥ 2 h, ≤ 48 V, reversa obligatoria y arena (PROMPT §3–4). Las vistas tienen escalas que difieren 26 % entre sí, así que **no es fabricable**. Antes de seguir hay que confirmar con Jorge si ese casco es su bote y de dónde sale el plano (CAD, a mano o generado con una herramienta), porque varias incoherencias (globos que apuntan a otra pieza, corte A‑A imposible, "seatl") sugieren que no salió de un modelo CAD [ESTIMADO].

---

## 2. Lectura propia del plano (contra el resumen recibido)

Abrí la imagen y la medí con zooms con grilla de píxeles (PNG de 1320 × 1023, ±2 px). Lo que leo distinto o agrego al resumen:

| # | Resumen recibido | Lo que leo en la imagen |
|---|---|---|
| L1 | "eje y rodamientos/sello fuera de la cámara húmeda" | Dice literalmente **"El eje y rodamientos/seatl van fuera de la cámara húmeda"** (errata "seatl", probablemente *seal*) |
| L2 | Largo total del casco 2300 | En la vista lateral, la cota 2300 va de la proa al **pivote de la boquilla**, 166 mm a popa del espejo. En planta arranca **~200 mm a popa de la proa** y termina en el espejo [CALCULADO: §4.1]. Mide cosas distintas en cada vista |
| L3 | Cotas en popa 280 y 420 | En la vista lateral, 280 llega al **pivote/borde superior de la boquilla**. En la trasera llega al **eje del jet**. No es la misma cota |
| L4 | Cadena 850 / 750 / 700 | Suma 2300, pero está dibujada de la proa **hasta la rejilla**, no hasta el espejo. A escala mide 2010 mm [CALCULADO] |
| L5 | — | La tabla "MATERIALES SUGERIDOS" está **tapada por un ícono de "compartir"** (es una captura de pantalla). Solo se lee: "Carcasa y difusor: Alum… 316", "Impulsor: In…", "Eje: In…", "Sellos: M…", "Tornillería: In…" |
| L6 | — | El globo **9 (sello mecánico)** apunta a un **segundo rodamiento de bolas**; no hay ningún sello dibujado. Los ítems 1 (toma) y 10 (eje) no tienen globo en el detalle |
| L7 | "Ø inicial toma 120 (aprox.)", impulsor 108, tobera 72 | Las tres cotas están en el **extremo de salida** del detalle, junto a la boquilla direccional, no sobre el impulsor (ítem 2, junto a los cojinetes). El detalle "ampliado" no tiene escala propia: es ×2,37 la vista lateral [CALCULADO] |
| L8 | Vista lateral "SECCIÓN A‑A" | Las marcas A‑A de la planta están **a popa del espejo, con flechas hacia popa**. Eso define un corte transversal, no longitudinal |
| L9 | Rejilla "enrasada con el fondo" | En la vista trasera, la carcasa de la rejilla **sobresale ~20 mm** del fondo [CALCULADO] |
| L10 | — | El motor está dibujado como **motor industrial con patas, aletas y ventilador**, con baterías (3 cajas) bajo el piso del cockpit, a proa del motor |
| L11 | — | Los demás datos coinciden con el resumen: tabla de componentes 1–10, datos técnicos (7,2 / 5 kW, 72 V, 60 / 100 A, 4500 rpm, 150 kg, ≥ 30 km/h), 180 + 80 + 120 + 100 + 120 = 600, holgura 0,5–0,8 mm, rejilla de 120 × 90 mm |

---

## 3. Tabla de hallazgos

Severidad: **crítica** (afecta la seguridad o no funciona), **alta**, **media**, **baja**. Ordenada con la seguridad primero.

| N.º | Qué dice el plano | Problema | Severidad | Evidencia / cálculo | Corrección propuesta |
|---|---|---|---|---|---|
| H1 | Ancho total 800; 1 piloto en asiento con volante sobre el piso del cockpit | **Estabilidad inicial nula o negativa**: puede volcar estando quieto | **Crítica** (seguridad) | Manga en la flotación de 0,66–0,69 m; GM de −113 a +24 mm con el CG del piloto a 0,45–0,65 m del fondo [CALCULADO §4.3]. Agua < 15 °C de oct a may [VERIFICADO: R07] | Manga en la flotación ≥ 0,9 m (caja: GM +144 mm [CALCULADO]); en la práctica, manga total de 1,1–1,3 m como los jon boats de R04 [VERIFICADO: R04 A.4]. Asiento bajo y baterías en el fondo. Ensayo de escora con carga desplazada antes de navegar (buscar: ISO 12217-3 offset load test) |
| H2 | Eje del jet a 280 mm del fondo (vista trasera); eje recto horizontal | **La bomba no ceba**: el impulsor queda en el aire con el bote quieto | **Crítica** (no funciona) | Calado de 151–233 mm con 150–200 kg → eje 37–119 mm y tope del impulsor 91–173 mm **sobre** la flotación [CALCULADO §4.3]. "Position the waterjet vertically so that the centerline of the jet lies on the vessel waterline when resting. This ensures the pump of the waterjet can always prime" [VERIFICADO: dmsonline] | Bajar el eje del impulsor hasta ≤ el calado mínimo (≈ 150 mm sobre el fondo con 150 kg). Si no, prever cebado. Recalcular con el calado medido |
| H3 | Detalle A‑A: 8‑9 cojinetes → 2 impulsor → 3 estator → 4 tobera → cámara → 5 boquilla direccional | **El corte no es una bomba**: no hay ducto de admisión; tras la tobera hay una cámara de ≈Ø130–140 con un cuerpo macizo en el eje; la boquilla direccional queda dentro de la carcasa fija y no puede girar | **Crítica** (no funciona) | Expansión brusca Ø72 → Ø130–140: K = (1 − A₁/A₂)² = **0,48–0,54** de la altura dinámica del chorro [CALCULADO: Borda–Carnot] | Disposición estándar: toma enrasada → ducto ascendente → impulsor → estator → tobera Ø72 → boquilla direccional **por fuera del espejo** → bucket |
| H4 | Ítem 9 "sello mecánico externo a la cámara húmeda"; nota "eje y rodamientos/seatl fuera de la cámara húmeda" | Falta el sello y el concepto es contradictorio: un sello mecánico trabaja con una cara mojada (separa lo húmedo de lo seco), y el eje no puede estar fuera de la cámara porque lleva el impulsor. Sin sello, el agua llega a los cojinetes y a la sentina | **Crítica** (inunda / no funciona) | Globo 9 = rodamiento (L6). Velocidad periférica del eje Ø20 a 4500 rpm = **4,7 m/s** [CALCULADO] | Sello mecánico de caras en la pared de la cámara (buscar: "mechanical seal 20 mm water pump SiC"), cojinetes del lado seco, cámara de drenaje con testigo entre sello y cojinete, y bomba de achique |
| H5 | Baterías en 3 cajas sobre el fondo, bajo el piso; casco con dos pasantes (toma y eje); sin flotación | El bote se hunde si se inunda; la batería queda en la sentina | **Alta** (seguridad) | "Batteries shall be permanently installed in a dry, ventilated location above anticipated bilge water level" [VERIFICADO: R06 §5.1, ISO 13297 8.1]. LFP en agua salada: runaway posible días después [VERIFICADO: R06 §4.2]. Peso neto sumergido de máquinas + baterías + casco ≈ 60–65 kg [ESTIMADO] | Caja estanca elevada; flotación fija ≥ ~100 L de espuma de celda cerrada [ESTIMADO: 1,5 × peso neto sumergido]; bomba de achique con alarma (buscar: 33 CFR 183 subpart F flotation small boats) |
| H6 | Masa total 150 kg; 1 piloto | Capacidad de carga menor que un adulto; **no entra una segunda persona** | **Alta** (seguridad) | Desplazamiento máximo a 420 mm = 424–481 kg; 33 CFR 183.33 → W = **54–64 kg** de personas + equipo [CALCULADO con fórmula VERIFICADA]. Regla de área de R04: 34–63 kg/m² × 1,84 m² = **63–116 kg** incluyendo motor [CALCULADO con R04 A.3]. Con 2 personas (280–330 kg): francobordo en el espejo de **77–158 mm** [CALCULADO] | Rediseñar manga y puntal para la carga real. Placa: 1 persona. No llevar acompañante |
| H7 | "No usar como plano final"; casco de 2,30 × 0,80 con cubierta y cockpit | **No es el bote de diseño de P1** (jon boat de 2,44 × 1,20 m, D‑01; manga de los cascos chicos 1,10–1,30 m [VERIFICADO: R04 A.4]) | **Alta** (datos de entrada) | Vistas superior y trasera | Preguntar a Jorge si este casco es su bote o un concepto. Si es su bote, medirlo (PENDIENTES P0) |
| H8 | 72 V nominales, 60 A nominal, 100 A máximo | **Supera la tensión de seguridad**; los componentes de P1 no sirven a esta tensión | **Alta** (seguridad eléctrica) | LFP 22S, LFP 23S y NMC 20S llegan a **80,3–84,0 V** cargadas [CALCULADO]. Supera los 50 V CC de ISO 16315:2016 3.1, con reducción sugerida en ambiente húmedo [VERIFICADO: R06]. MRBF ≤ 58 V; SW80 corta bajo carga solo hasta 48 V; VESC 75100 al límite de 84 V [VERIFICADO: R06 §4.3] | LFP 13S (47,45 V máx. [VERIFICADO: R06 §4.3]) con 120–175 A. Si se mantienen 72 V: todo en clase 100 V (contactor SW80B de 96 V [VERIFICADO: R06]), fusible para ≥ 100 V CC (buscar: "class T fuse 125 VDC") y monitor de aislamiento |
| H9 | Sin kill switch ni parada de emergencia en el plano ni en la lista | El motor no se detiene si el piloto cae al agua | **Alta** (seguridad) | PWC: el cordón (ECOS) es obligatorio en EE. UU.; "If the ECOS does not shut off the engine when the lanyard is pulled, do not operate" [VERIFICADO: CG Aux] | Cordón NC en serie con la bobina de un contactor monoestable + seta (arquitectura de R06 §3.5) |
| H10 | "La reversa (bucket) es opcional" | El jet **no frena ni gobierna sin empuje**, y el proyecto exige marcha atrás (PROMPT §3) | **Alta** (seguridad) | "There are no brakes on a PWC"; "No Jet thrust, no steering… you will proceed ahead without the ability to change course"; bucket "at any speed other than idle, damage to the plate and brackets can occur" [VERIFICADO: CG Aux]. El bucket recibe hasta ≈ 550–760 N (empuje a punto fijo) [CALCULADO] | Bucket **obligatorio**, con traba en la posición de avance, límite de potencia en reversa y bisagra dimensionada para ≥ 2 × 760 N [SUPUESTO: FS 2] |
| H11 | Toma en el fondo, jet de impulsor | Choca con el requisito de **aguas someras y arena** (PROMPT §3) | **Alta** | "Never operate your PWC in water less than 24 inches" (610 mm) [VERIFICADO: CG Aux]. Hacen falta ~305 mm de luz bajo el jet en desplazamiento [VERIFICADO: R03 S12]. El desgaste de la holgura bajó un jet de 42 a 35 kn [VERIFICADO: R03 S8] | No usar en bajos de arena. Inspeccionar la holgura en cada salida. Tapa de inspección del impulsor |
| H12 | Objetivo ≥ 30 km/h | Ilegal en la zona de operación: dentro de 300 m el máximo es 5 kn | **Alta** (legal) | Reglamento local §4: "Indenfor en afstand af 300 meter fra kystlinjen … højst 5 knob" [VERIFICADO: politi.dk]. El proyecto opera a < 300 m (PROMPT §3) | Para ≥ 30 km/h hay que salir de los 300 m, fuera del alcance y de los criterios de agua fría de P1 (R07 §3.4). Si no, limitar la velocidad por firmware |
| H13 | Masa total 150 kg | Presupuesto de masas irreal | **Alta** | Sin batería: 142–219 kg; con 3 kWh LFP: **165–242 kg** [ESTIMADO §4.2]. Para cerrar 150 kg, casco + máquinas ≤ 47 kg [CALCULADO] | Diseñar para 200–230 kg |
| H14 | 5 kW de diseño, 7,2 kW máx., ≥ 30 km/h | Con 5 kW no llega con masa realista | **Alta** (no cumple objetivo) | Savitsky (openplaning) + jet con pérdidas [CALCULADO §4.5]: con 150 kg y 5 kW, **26–32 km/h**; con 200 kg y 5 kW, T < R en 20 km/h en 4 de 6 cascos y máximo 20–25 km/h en los demás; con 200 kg y 7,2 kW, **21–34 km/h**, y en 1–2 de 6 cascos no pasa los 20 km/h | Dimensionar para 7,2 kW continuos (motor, ESC y cables), o bajar el objetivo a ~20 km/h |
| H15 | Holgura de punta 0,5–0,8 mm (y el proyecto imprime en PETG) | **No es imprimible ni mantenible** en PETG | **Alta** (si se imprime) | 0,46–0,74 % de D [CALCULADO]. Tolerancia FDM ±0,15 mm por superficie [ESTIMADO: R05]. PRO‑JET tuvo que llevar la separación rotor–estator a 3 mm [VERIFICADO: R03 S4]. Pala de PETG de 40 × 5 mm: σ de raíz **7,2 MPa** contra 2,7 MPa sostenida (FS 3) y 0,5 MPa alterna [CALCULADO con R05 A7] | Impulsor metálico (la tabla dice "Impulsor: In…": confirmar). **Anillo de desgaste torneado** con el torno disponible. Holgura medida con galgas |
| H16 | Eje Ø20 "recto", motor abulonado a la caja de cojinetes, sin acople | Camino del empuje axial no definido; el motor recibe empuje y desalineación | **Media** | Empuje axial de ≈ 257 N a 30 km/h y hasta **≈ 760 N** a punto fijo con 7,2 kW [CALCULADO] | Acople flexible con juego axial. Rodamiento fijo (par de contacto angular) en la caja de la bomba. Caja abulonada al bloque de toma o al espejo. Motor en soporte propio |
| H17 | Motor de 5 kW, 4500 rpm, 72 V, dibujado como motor industrial | Tipo, refrigeración y control sin definir | **Media** | Referencia comercial: HPM5000B de 72 V, 11 kg, Ø206 × 126 mm, 91 %, 2000–6000 rpm configurable, "water resistent", 1306,48 € [VERIFICADO: Kelly]. Calor en el compartimiento ≈ 0,59 kW a 5 kW y ≈ 0,85 kW a 7,2 kW [CALCULADO: 9 % del motor + 3 % del ESC]. KV implícito de **62,5–73,5 rpm/V**. A 84 V la bomba pediría **×1,59** la potencia [CALCULADO] | ESC de clase ≥ 100 V con límites de corriente y rpm. Ventilación forzada o versión refrigerada por agua (buscar: "Golden Motor 5kW liquid cooled 72V") |
| H18 | Corriente nominal 60 A, máxima 100 A, potencia 5 / 7,2 kW | No cierra | **Baja** | 60 A × 72 V = 4,32 kW ≠ 5 kW. Pedir 7,2 kW con la batería vacía (61,6 V) son **117 A** > 100 A [CALCULADO] | Especificar la potencia a una tensión dada y limitar por corriente de batería |
| H19 | Masas dibujadas: piloto, baterías y motor | LCG muy a proa | **Media** | LCG ≈ 1,14 m del espejo = **66 %** del largo de fondo [CALCULADO §4.4]; λ = 3,0–3,7 (límite de Savitsky: 4) | Mover las baterías hacia popa. LCG objetivo ≈ 35–45 % del largo desde el espejo [ESTIMADO: memoria técnica, no verificado] |
| H20 | Impulsor Ø108 a 4500 rpm directo | Margen de cavitación chico a punto fijo y en la joroba | **Media** | U = 25,4 m/s; σ en la punta 0,28–0,35; S = 3,0–3,3 [CALCULADO]. Umbral de referencia [ESTIMADO: memoria técnica, no verificado] | Ensayo en tanque o muelle con rampa de acelerador; tope de corriente a baja velocidad |
| H21 | "Carcasa y difusor: Alum… 316" | Par galvánico Al–316 en agua salobre | **Media** | Diferencia ≈ 670 mV (límite práctico 200 mV) [VERIFICADO: R06 §0] | Aislar (bujes y arandelas no conductoras, Tef‑Gel) y ánodo de aluminio (R06) |
| H22 | Bote < 4 m con bomba de chorro | **Riesgo de clasificación como "vandscooter"** | **Media** (a confirmar) | BEK 809/2019 §1: < 4 m, bomba de chorro como propulsión principal, operado por personas que "sidder, står eller knæler på – snarere end i – skroget"; §3: prohibido a < 300 m salvo tránsito directo, perpendicular y ≤ 5 kn [VERIFICADO]. Hoy hacen falta vandscooterbevis y seguro obligatorio [VERIFICADO: Søfartsstyrelsen]. El piloto del plano va **dentro** del casco, así que probablemente no lo es. Speedbådsbevis: no, porque son < 19 kW [VERIFICADO: R07] | Consultar a Søfartsstyrelsen antes de construir. Los metadatos de BEK 809/2019 dan EndDate 2026‑06‑23: buscar la versión vigente |
| H23 | Escala 1:10; vistas lateral, superior, trasera y detalle | **Cotas incoherentes**; no es un plano a escala | **Media** | Escalas de 3,19 / 4,00 / 3,72 mm/px (dispersión del 26 %). En la lateral, 520 se dibuja más corto que 420. L/B dibujado 3,98 contra 2,88 rotulado. El "800" de la planta abarca 488 mm y el casco dibujado mide 628 mm. Tren motor‑bomba: 600 en el detalle contra 745–968 mm en lateral y planta [CALCULADO §4.1] | Rehacer en CAD con una sola referencia (fondo y espejo) y cotas encadenadas al espejo |
| H24 | Corte A‑A; diámetros en el detalle | Marcas de corte y cotas mal ubicadas | **Baja** | L7, L8 | Marcas A‑A sobre crujía; cotar Ø108 sobre el impulsor y Ø72 en la salida de la tobera |
| H25 | Tabla de materiales | Ilegible (captura de pantalla) | **Baja** | L5 | Pedir a Jorge el archivo original (PDF o CAD) |
| — | Toma / rejilla | (La analiza otro agente) | — | Una línea: coincide con Jorge (ver Alcance) | — |

---

## 4. Cálculos

Todo sale del script de la §8, ejecutado con Python 3.11, numpy, scipy y openplaning 0.4.9. Copio la salida relevante.

### 4.1 Cotas y escalas (medidas en píxeles del PNG)

```
Lateral: 2300 mm = 722 px -> 3.186 mm/px
  proa→espejo dibujado = 2134 mm; la cota 2300 termina 166 mm a popa del espejo (pivote de la boquilla)
  cadena 850/750/700: px [235, 216, 180] -> a escala [749, 688, 573] mm; total 2010 mm (rotulado 2300)
  la cadena termina en x=752 = rejilla (x (735, 760)); rejilla a 143 mm del espejo a escala
  cota 520: 99 px -> 5.25 mm/px (horizontal 3.19); a escala horizontal = 315 mm
  cota 420: 108 px -> 3.89 mm/px (horizontal 3.19); a escala horizontal = 344 mm
  cota 280: 78 px -> 3.59 mm/px (horizontal 3.19); a escala horizontal = 248 mm
  eje motor-bomba a 67 px del fondo -> 213 mm (esc. horiz.) / 241 (cal. con 280) / 352 mm (cal. con 520)
  tren motor→boquilla: 914 mm; motor→fin carcasa: 745 mm (detalle: 600)
Superior: 2300 = 575 px -> 4.00 mm/px; la cota arranca 200 mm a popa de la proa
  casco dibujado: largo 2500 mm, ancho 628 mm; cota 800 abarca 488 mm
  L/B rotulado 2.88; L/B dibujado 3.98
  tren motor→boquilla en planta: 968 mm (detalle: 600)
Trasera: 800 = 215 px -> 3.72 mm/px
  cota 520: 110 px -> a escala horizontal 409 mm
  cota 280: 57 px -> a escala horizontal 212 mm
  cota 120: 38 px -> a escala horizontal 141 mm
  escalas de las 3 vistas: lateral 3.19, superior 4.00, trasera 3.72 mm/px -> dispersión 26 %
Detalle: 600 = 446 px -> 1.345 mm/px; tramos [(180, 192), (80, 94), (120, 117), (100, 85), (120, 112)]
  escala equivalente si la hoja es A3: lateral 1:9.1 / superior 1:11.5 / trasera 1:10.7 / detalle 1:3.9
  detalle ampliado ×2.37 respecto de la vista lateral (sin escala propia rotulada)
  Expansión brusca tras la tobera Ø72 a cámara ≈Ø140 (dibujo): K Borda–Carnot = (1−A1/A2)² = 0.54
```

- "1:10" solo se cumple aproximadamente en la vista lateral, y solo si la hoja es A3 [SUPUESTO]. Las tres vistas no comparten escala.
- La altura del eje del jet sobre el fondo queda entre 213 y 352 mm según qué cota se tome como calibración [CALCULADO]. Uso **270–280 mm**, que es la cota rotulada en la vista trasera, donde 280 sí apunta al eje (57 px contra 110 px de 520 → 270 mm [CALCULADO]).
- Con Ø140, K da 0,54. Con Ø130 [ESTIMADO: lectura del detalle] da 0,48.

### 4.2 Presupuesto de masas (1 piloto)

| Partida | kg | Etiqueta |
|---|---|---|
| Casco de 2,3 × 0,8 m con cubierta, consola y asiento | 30–45 | [ESTIMADO: R04 A.3 da 8,3–14,6 kg/m² × 1,84 m² = 15–27 kg para el casco **abierto**; +50–70 % por cubierta, tapa de motor y consola] |
| Motor 5 kW, 72 V | 11–35 | 11 kg el HPM5000B [VERIFICADO: Kelly]; 35 kg si fuera el motor industrial dibujado [ESTIMADO: memoria técnica, no verificado] |
| Bomba (carcasa de Al, impulsor, estator, ducto, eje, cojinetes, boquilla) | 8–15 | [ESTIMADO] |
| Controlador 72 V / 100 A, contactor, fusible, cables | 4–7 | [ESTIMADO] |
| Dirección + bucket | 2–4 | [ESTIMADO] |
| Agua retenida en la bomba sobre la flotación | 2–5 | [ESTIMADO: ~5 L de volumen interno] |
| Equipo de seguridad | 5–8 | [ESTIMADO: R07 §1.4] |
| Piloto | 80–100 | [SUPUESTO: `inputs.yaml` usa 100] |
| **Subtotal sin batería** | **142–219** | [CALCULADO] |
| Batería LFP de 2 / 3 / 4 / 6 kWh a 128 Wh/kg | 15,6 / 23,4 / 31,2 / 46,9 | [CALCULADO con R06 §4.1 VERIFICADO] |
| **Total con 3 kWh LFP** | **165–242** | [CALCULADO] |

### 4.3 Hidrostática: calado, francobordo, cebado, capacidad y GM

**Modelo de casco** [ESTIMADO, leído del dibujo; no es a escala]:
- **Sección (vista trasera):** fondo plano de 0,42 m que se abre hasta 0,69 m en el pantoque, a 0,25 m sobre el fondo, y llega a 0,80 m en la borda a 0,52 m. Variante con fondo de 0,60 m.
- **Largo de fondo:** 1,73 m, que crece por la proa lanzada hasta 2,05 m a 0,42 m de altura.
- **Coeficientes de la flotación:** C_wp = 0,85 y C_I = 0,065 [CALCULADO: 70 % de rectángulo + 30 % de proa triangular].

```
  Δ=150 kg (fondo 0,42): calado 186 mm; francobordo espejo (420) 234 mm; eje del jet SOBRE la flotación por 84 mm
  Δ=150 kg (fondo 0,60): calado 151 mm; francobordo espejo (420) 269 mm; eje del jet SOBRE la flotación por 119 mm
  Δ=200 kg (fondo 0,42): calado 233 mm; francobordo espejo (420) 187 mm; eje del jet SOBRE la flotación por 37 mm
  Δ=200 kg (fondo 0,60): calado 196 mm; francobordo espejo (420) 224 mm; eje del jet SOBRE la flotación por 74 mm
  Δ=230 kg (fondo 0,42): calado 260 mm; francobordo espejo (420) 160 mm; eje del jet SOBRE la flotación por 10 mm
  Δ=280 kg (fondo 0,42): calado 302 mm; francobordo espejo (420) 118 mm; eje del jet BAJO la flotación por 32 mm
  Δ=330 kg (fondo 0,42): calado 343 mm; francobordo espejo (420) 77 mm
Desplazamiento máximo a 0,42 m (borde del espejo, a nivel): ∇ = 0.424 m³ -> 424 kg (agua dulce)   (fondo 0,60: 481 kg)
  USCG 183.33: Δmax 424, casco 30, máquinas+baterías 35: W1=51, W2=56 -> W = 56 kg (personas+equipo)
  USCG 183.33: Δmax 424, casco 45, máquinas+baterías 70: W1=20, W2=54 -> W = 54 kg
  USCG 183.33: Δmax 481, casco 30, máquinas+baterías 35: W1=62, W2=64 -> W = 64 kg
  USCG 183.33: Δmax 481, casco 45, máquinas+baterías 70: W1=31, W2=62 -> W = 62 kg
GM con 1 piloto sentado (alturas sobre el fondo):
  zG piloto 0.45 m, Δ 185 kg: T 220 mm, Bwl 0.66, KB 0.120, BM 0.191, KG 0.327 -> GM -16 mm | fondo 0,60: GM +5 mm
  zG piloto 0.45 m, Δ 220 kg: T 251 mm, Bwl 0.69, KB 0.138, BM 0.189, KG 0.305 -> GM +22 mm | fondo 0,60: GM +24 mm
  zG piloto 0.55 m, Δ 185 kg: ... KG 0.376 -> GM -65 mm | fondo 0,60: GM -43 mm
  zG piloto 0.65 m, Δ 185 kg: ... KG 0.424 -> GM -113 mm | fondo 0,60: GM -92 mm
Manga en la flotación (casco tipo caja) para GM ≥ +100 mm, Δ 200 kg, KG 0,36 m:
  B=0.7 m: GM=-65 mm | B=0.8 m: GM=+24 mm | B=0.9 m: GM=+144 mm | B=1.0 m: GM=+297 mm
```

**Calado y cebado.** El eje del jet (270–280 mm) queda sobre la flotación estática en todo el rango de 150–230 kg [CALCULADO]. Para que el eje quede en la flotación haría falta Δ ≈ 240–280 kg; con 2 personas (280–330 kg) el francobordo en el espejo queda en 77–158 mm [CALCULADO].

**Capacidad.** La fórmula es de 33 CFR 183.33 (botes con motor interior): W = máx[Δmax/5 − casco/5 − 4·máquinas/5 ; (Δmax − casco)/7], donde "máquinas" incluye los motores y las baterías [VERIFICADO: law.cornell.edu]. La norma no es obligatoria en Dinamarca; se usa como referencia (como en R04). La regla de personas de 183.41 es para fueraborda [VERIFICADO], así que no la uso.

**GM.** Los parámetros del cálculo:
- CG del piloto 0,20–0,25 m sobre el asiento [ESTIMADO: antropometría, memoria técnica, no verificado], con el asiento a 0,25–0,42 m del fondo [CALCULADO: según la escala que se tome en la vista lateral];
- baterías a 0,12 m;
- motor y bomba a 0,26 m;
- casco a 0,22 m [ESTIMADO].

El criterio de GM ≥ +100 mm es [SUPUESTO]. La verificación formal es un ensayo de escora (buscar: "ISO 12217-3 offset load test small boats").

### 4.4 Resistencia: joroba y planeo

| v km/h | SLR (L = 1,75 m) | Fn∇ (200 kg) | C_V (b = 0,5 m) | Régimen |
|---|---|---|---|---|
| 9,26 | 2,09 | 1,08 | 1,16 | Semidesplazamiento (límite legal) |
| 12 | 2,70 | 1,39 | 1,51 | Joroba |
| 15 | 3,38 | 1,74 | 1,88 | Joroba / preplaneo |
| 20 | 4,51 | 2,32 | 2,51 | Transición |
| 25 | 5,63 | 2,91 | 3,14 | Planeo |
| 30 | 6,76 | 3,49 | 3,76 | Planeo |

[CALCULADO]. Regímenes según Savitsky 2003: planeo con SLR > 3 [VERIFICADO: R09 §1.6].

**Joroba.** La banda es R/Δ = 0,10–0,20 [ESTIMADO]. Sale de la curva "típica" de Savitsky 2003, ≈ 0,10 a SLR 3 [VERIFICADO: R09 §1.6], multiplicada por 1–2 porque R09 mostró que los cascos rechonchos dan ~2 veces la curva típica. Da R_joroba = 147–294 N (150 kg), 196–392 N (200 kg) y 226–451 N (230 kg).

**Contraste.** Un RIB de 2,75 m con 1 persona planea a 14,8–17,6 km/h con motores de nafta de 2,5 hp [VERIFICADO: R04 C.1 #10]. Eso equivale a R/Δ ≈ 0,13–0,15 con hélice de η ≈ 0,5 [ESTIMADO], dentro de la banda.

**Planeo: Savitsky 1964 con openplaning 0.4.9.** Las ecuaciones que R09 §1.6 daba como "de memoria" coinciden con el código de openplaning [VERIFICADO: openplaning.py, `get_hydrodynamic_force`, líneas 504–519]:
- C_L0 = τ^1,1(0,012·λ^½ + 0,0055·λ^2,5/C_V²)
- C_Lβ = C_L0 − 0,0065·β·C_L0^0,6
- l_p = λb(0,75 − 1/(5,21(C_V/λ)² + 2,39))

Límites: 0,60 ≤ C_V ≤ 13, 2° ≤ τ ≤ 15° y λ ≤ 4. La fricción es ITTC‑57 con rugosidad de 150 µm.

Entradas:
- VCG 0,33 m y r_g 0,5 m;
- línea de empuje horizontal a 0,26 m (ε = 0°);
- aire: área de 1,1 × 0,5 m² con C_D 0,9;
- ν = 1,3·10⁻⁶ m²/s.

Todas son [ESTIMADO].

R total (presión + fricción + aire), en N:

| Δ kg | b m | β ° | LCG m | 20 km/h | 25 | 30 | 35 | τ a 30 km/h |
|---|---|---|---|---|---|---|---|---|
| 150 | 0,50 | 5 | 0,75 | 331 | 294 | 272 | 268 | 7,1° |
| 150 | 0,60 | 10 | 1,16 | 204 | 232 | 258 | 291 | 4,1° |
| 200 | 0,50 | 5 | 0,75 | 523 | 451 | 399 | 369 | 9,2° |
| 200 | 0,60 | 10 | 1,00 | 356 | 349 | 343 | 350 | 6,2° |
| 200 | 0,60 | 10 | 1,16 | 291 | 316 | 331 | 352 | 5,3° |
| 230 | 0,50 | 5 | 0,75 | 655 | 561 | 488 | 442 | 10,3° |
| 230 | 0,60 | 10 | 1,16 | 354 | 376 | 383 | 396 | 5,9° |

[CALCULADO: 18 casos en total. Rangos a 30 km/h: **253–272 N** con 150 kg, **331–399 N** con 200 kg y **383–488 N** con 230 kg.]

- **Desglose.** En el caso de 200 kg, b 0,6, LCG 1,0 y 30 km/h: presión 211 N, fricción 113 N y aire 19 N [CALCULADO].
- **Validez a 20 km/h.** Fn∇ = 2,3 es extrapolación: preplaneo, fuera de las hipótesis de Savitsky (R09 §1.6).
- **Por qué R/Δ ≈ 0,17–0,21 a 30 km/h.** El fondo es angosto para el peso: ∇/b³ = 1,58 con b = 0,5 m y 200 kg [CALCULADO]. Eso fuerza trimados altos.

**LCG del dibujo.** Posiciones medidas desde el espejo [CALCULADO con posiciones de la vista lateral y masas ESTIMADAS]:

| Masa | kg | Distancia al espejo |
|---|---|---|
| Piloto | 90 | 1,38 m |
| Baterías | 30 | 1,42 m |
| Motor | 20 | 0,63 m |
| Bomba | 12 | 0,25 m |
| Casco | 38 | 0,95 m |

Da **LCG = 1,14 m = 66 %** del largo de fondo.

### 4.5 Jet: empuje, rendimiento, equilibrio y autonomía

**Modelo** (cantidad de movimiento con pérdidas; mismo marco que R03 §2.3):
- T = ρQ(V_j − V₀)
- P_h = ρQ[(1 + K_n)V_j²/2 − η_in·V₀²/2]

Parámetros:
- K_n = 0,03 en la tobera [ESTIMADO];
- recuperación en la toma η_in = 0,70 ("~70 %" [VERIFICADO: R03 S9]);
- η de la bomba 0,75 [ESTIMADO: R03, impulsor chico] a 0,85 [ESTIMADO; dmsonline: "90 % or greater" para un buen diseño, VERIFICADO];
- η del motor 0,91 [VERIFICADO: Kelly HPM5000B];
- ESC 0,97 y mecánica 0,98 [ESTIMADO].

Sin estela (w = 0, conservador).

Geometría [CALCULADO]:

| Magnitud | Valor |
|---|---|
| A de la tobera | 40,7 cm² |
| A anular del impulsor (cubo 0,4) | 77,0 cm² |
| D_t/D_i | 0,667 |
| A_t/A_i | 0,444 |
| A_t/A_anular | 0,53 |

| P_el | η_bomba | T a 0 km/h | 9,26 km/h | 15 km/h | 20 km/h | 30 km/h | η_chorro a 30 km/h | η bat→empuje a 30 km/h |
|---|---|---|---|---|---|---|---|---|
| 5,0 kW | 0,75 | 547 N | 436 N | 376 N | 328 N | 241 N | 0,62 | 0,40 |
| 5,0 kW | 0,85 | 595 N | 478 N | 415 N | 365 N | 273 N | 0,62 | 0,46 |
| 7,2 kW | 0,75 | 697 N | 571 N | 502 N | 446 N | 344 N | 0,61 | 0,40 |
| 7,2 kW | 0,85 | 758 N | 626 N | 553 N | 494 N | 387 N | 0,61 | 0,45 |

[CALCULADO]. Sin pérdidas, a 30 km/h y con T = 250–400 N: V_j/V₀ = 1,56–1,78 y η_ideal = **0,72–0,78** [CALCULADO]. El chorro está bien elegido para 30 km/h.

**Velocidad máxima** (primera velocidad donde T < R entre 20 y 35 km/h) [CALCULADO]:

| Caso | 5 kW, η_bomba 0,75 | 5 kW, 0,85 | 7,2 kW, 0,75 | 7,2 kW, 0,85 |
|---|---|---|---|---|
| 150 kg (6 cascos) | 26,1–28,8 (1 caso T < R a 20) | 30,1–31,8 | > 35 | > 35 |
| 200 kg, b 0,6, LCG 1,16 | 22,6 | 25,2 | 31,0 | 34,0 |
| 200 kg, b 0,6, LCG 1,0 | T < R a 20 (−28 N) | 21,1 | 30,1 | 33,9 |
| 200 kg, b 0,5, LCG 0,75 | T < R a 20 (−195 N) | T < R a 20 (−158 N) | T < R a 20 (−77 N) | T < R a 20 (−29 N) |
| 230 kg, b 0,6, LCG 1,16 | T < R a 20 (−26 N) | 20,8 | 26,6 | 30,4 |

**Joroba (12–18 km/h).** El empuje es T(5 kW) = 347–448 N y T(7,2 kW) = 493–564 N [CALCULADO], contra R_joroba = 196–392 N (200 kg) y 226–451 N (230 kg). Con 5 kW y 230 kg el margen se anula en el borde alto de la banda.

**Autonomía** [CALCULADO]:

| Energía útil | 5 kW a 30 km/h | 7,2 kW a 30 km/h |
|---|---|---|
| 2 kWh | 24 min / 12 km | 17 min / 8 km |
| 3 kWh | 36 min / 18 km | 25 min / 12,5 km |
| 4 kWh | 48 min / 24 km | 33 min / 17 km |

**A 5 kn (zona legal de < 300 m)** [CALCULADO], con R/Δ de 0,06 a 0,16:

| Masa | P_el | η_total | Duración con 3 kWh |
|---|---|---|---|
| 150 kg | 0,65–2,2 kW | 0,27–0,35 | 1,4–4,6 h |
| 200 kg | 0,92–3,2 kW | 0,25–0,33 | 0,9–3,3 h |
| 230 kg | 1,1–3,9 kW | 0,24–0,32 | 0,8–2,7 h |

Para comparar: P1 (cola larga) usa **759–910 W de batería a 6 km/h con 2 personas** [CALCULADO: README / `resultados/sizing.json`].

### 4.6 Bomba: velocidad específica, cavitación y holgura

```
  0 km/h, 5000 W: Q 48 L/s, H 7.3 m, φ 0.24, ψ 0.110, Ω_s 4.20 (N_s US 11491), par 9.2 N·m | NPSHa 10.0 m, S 3.32, σ_punta 0.28
  12 km/h, 5000 W: Q 49 L/s, H 7.1 m, φ 0.25, ψ 0.108, Ω_s 4.30 (N_s US 11753), par 9.2 N·m | NPSHa 10.4 m, S 3.25, σ_punta 0.30
  30 km/h, 5000 W: Q 53 L/s, H 6.5 m, φ 0.27, ψ 0.099, Ω_s 4.81 (N_s US 13140), par 9.2 N·m | NPSHa 12.4 m, S 2.96, σ_punta 0.35
  30 km/h, 7200 W: Q 59 L/s, H 8.5 m, φ 0.30, ψ 0.129, Ω_s 4.14 (N_s US 11319), par 13.2 N·m | NPSHa 12.4 m, S 3.12, σ_punta 0.35
```

- **Velocidad específica.** U = π·D·n = **25,4 m/s** y Ω_s = ω√Q/(gH)^¾ = **4,1–4,8** [CALCULADO]. Eso corresponde a un impulsor axial con estator, coherente con el dibujo. El rango Ω_s ≳ 3–4 como "axial" es [ESTIMADO: memoria técnica, no verificado; buscar: "specific speed ranges axial mixed flow pump"].
- **Potencia absorbida.** ψ ≈ 0,10–0,13 y φ ≈ 0,24–0,30 [CALCULADO] son valores razonables para que un Ø108 a 4500 rpm absorba 5–7 kW. **La combinación motor + impulsor + tobera del plano es coherente.**
- **Cavitación.** σ en la punta = (p_atm − p_v + 0,7·½ρV₀²)/(½ρW²) = 0,28–0,35 con p_v = 2,34 kPa [ESTIMADO: 20 °C]. S = 3,0–3,3, equivalente a ~8 000–9 000 en unidades de EE. UU. con el factor 2733 [ESTIMADO]. El umbral de cavitación para comparar es [ESTIMADO: memoria técnica, no verificado; buscar: "waterjet suction specific speed cavitation limit"].
- **Holgura de punta.** 0,5 / 0,8 mm = 0,46 / 0,74 % de D [CALCULADO]. Ladd usó 0,5 % de D en la tobera 19A [VERIFICADO: R03 S10]. Lo que la consume [ESTIMADO, con geometría de pala SUPUESTA de 40 × 5–8 mm]:
  - tolerancia FDM de ±0,15 mm por superficie [ESTIMADO: R05], o sea ±0,3 mm en el diámetro más la ovalización;
  - dilatación del PETG: 0,057 mm por lado con ΔT 15 K y α 70 µm/m·K [ESTIMADO: memoria];
  - flecha tangencial de la pala: 0,10–0,42 mm;
  - crecimiento centrífugo: 0,015 mm.
  
  Con esa pila la holgura **no se garantiza** en PETG.
- **Pala de PETG.** F_t = 62 N por pala a 5 kW. σ de raíz: **7,2 MPa** con 5 mm y 2,8 MPa con 8 mm. Admisibles: 2,7 MPa sostenida (XY, FS 3) y 0,5 MPa alterna [VERIFICADO: R05 A7]. **Un impulsor impreso no cierra.**

### 4.7 Eje, sello, cojinetes y empuje axial

```
  diseño: par 9.4 N·m, τ nominal 6.0 MPa, con chavetero Kt 2,5 → 15 MPa; τ_y 316 ≈ 118 MPa [ESTIMADO] -> FS 7.9
  máx: par 13.5 N·m, τ nominal 8.6 MPa, con chavetero Kt 2,5 → 21 MPa -> FS 5.5
  pico motor 45 N·m [búsqueda, no verificado]: τ nominal 28.6 MPa, con chavetero → 72 MPa -> FS 1.7
  Velocidad periférica del eje Ø20 en el sello: 4.7 m/s
  Empuje axial de referencia: bollard 7,2 kW ≈ 758 N; 30 km/h 5 kW ≈ 257 N
```

- **Torsión.** El eje Ø20 sobra a torsión [CALCULADO]. Si el impulsor se traba con una piedra, el pico de par del motor deja FS ≈ 1,7. Como en P1, conviene un límite de corriente en el ESC o un fusible mecánico. σ_y de 205 MPa para 316 es [ESTIMADO: memoria técnica, no verificado].
- **"Eje recto".** Es consistente con motor y bomba coaxiales en horizontal. Pero en un jet real el eje atraviesa la pared del **ducto de admisión** hasta la cara del impulsor, y aquí no hay ducto (H3).
- **Cojinetes.** "Cojinetes fuera de la cámara húmeda" es buena práctica.
- **Sello.** "Sello externo a la cámara húmeda" no es posible: el sello es justamente el límite entre las dos zonas (H4). Un retén de labio NBR admite solo 0,03 MPa y pide un eje ≥ 45 HRC [VERIFICADO: R05 B6], así que no conviene en 316.
- **Empuje axial.** Lo toma el impulsor y debe pasar por un rodamiento fijo a la carcasa de la bomba y de ahí al casco o al espejo, no al motor (H16).

### 4.8 Eléctrico a 72 V

```
  LFP 22S: nominal 70.4 V, cargada 80.3 V, vacía 61.6 V | >50 V: SÍ
  LFP 23S: nominal 73.6 V, cargada 84.0 V, vacía 64.4 V | >50 V: SÍ
  NMC 20S: nominal 72.0 V, cargada 84.0 V, vacía 64.0 V | >50 V: SÍ
  I a 5 kW / 72 V = 69 A; 60 A × 72 V = 4320 W; 100 A × 72 V = 7200 W; 7,2 kW a 61,6 V = 117 A
  KV si 4500 rpm = vacío a 72 V: 62.5 rpm/V; si 4500 = carga (85 % de vacío): 73.5 rpm/V; a 84 V: P_bomba ×1.59
```

- **Regla del proyecto.** El proyecto fija ≤ 48 V salvo justificación (PROMPT §4). El umbral de 50 V CC viene de ISO 16315:2016 3.1, con nota para bajarlo en ambiente húmedo [VERIFICADO: R06 §5.1]. Para 5–7 kW, a 48 V hacen falta ≈ 120–175 A con LFP 13S (41,6 V nominal) [CALCULADO]. Es factible, con cable de ≥ 13,3 mm² (AWG 6: 100–120 A [VERIFICADO: R06 §5.2]) o más; recomiendo 25–35 mm² [ESTIMADO]. **72 V no está justificado por necesidad.**
- **ESC.** Necesita clase ≥ 100 V, ≥ 100 A continuos y límites de corriente de batería y de rpm. La bomba a 84 V pediría ×1,59 la potencia [CALCULADO]. El VESC 75100 de P1 no sirve. Modelo: buscar "VESC 100V 250A marine" o "Kelly KLS 72V".
- **Kill switch.** El de P1 (R06 §3.5) sirve si se cambia el contactor por uno de 96 V, el SW80B [VERIFICADO: R06].

### 4.9 Legal y operación en Als Fjord

| Tema | Resultado | Etiqueta |
|---|---|---|
| Velocidad a < 300 m de la costa | Máximo 5 kn (9,26 km/h) para toda motorbåd. Excepción: solo la velocidad mínima para maniobrar con corriente o viento | [VERIFICADO: politi.dk, Sejladsreglement Syd- og Sønderjylland §4] |
| ¿Sirve ≥ 30 km/h? | No dentro de 300 m, que es la zona de operación del proyecto. Afuera, el agua está a < 15 °C el ≥ 90 % de los días de oct–may y la supervivencia es de 1–6 h a 10–16 °C | [VERIFICADO: R07 §3] |
| Licencia (speedbådsbevis) | No hace falta: casco < 4 m planeante con < 19 kW (7,2 kW). El fondo plano en el tercio de popa es "planende" por definición | [VERIFICADO: R07; BEK 554/2020 §1 stk. 4, abierto] |
| ¿Vandscooter? | La definición pide operar "på – snarere end i – skroget"; el piloto del plano va dentro, así que **probablemente no**. Si lo fuera: prohibido a < 300 m salvo tránsito directo y perpendicular a ≤ 5 kn, más vandscooterbevis y seguro obligatorio | [VERIFICADO: BEK 809/2019 §1, §3; Søfartsstyrelsen]. **Consultar** a Søfartsstyrelsen |
| Playas | Prohibido salir o llegar a playas comunales con "vandscootere, jetski og lignende fartøjer" | [VERIFICADO: reglamento §3] |
| Chaleco | Llevar uno por persona; usarlo puesto no es obligatorio por ley, pero el proyecto lo exige | [VERIFICADO: R07 §1.2] |
| Ropa en jet | "Wet suit bottom or … equivalent protection. Severe internal injuries can occur if water is forced into body cavities … near the jet thrust nozzle" | [VERIFICADO: CG Aux] |

### 4.10 Reversa, gobierno, poca profundidad y bañistas

**Gobierno y freno.**
- Sin empuje no hay gobierno, y un PWC "no tiene frenos" [VERIFICADO: CG Aux].
- Con viento en el fiordo y a ralentí, el jet deriva sin gobierno [ESTIMADO].
- La reversa por bucket es la única forma de frenar o retroceder.
- No encontré fuente abierta sobre qué fracción del empuje de avance da en reversa (buscar: "jet boat reverse bucket thrust percentage").
- Invertir el giro de un impulsor axial con estator rinde muy poco [ESTIMADO: memoria técnica, no verificado].

**Poca profundidad y arena.**
- Profundidad mínima de 610 mm [VERIFICADO: CG Aux] y 305 mm de luz bajo el jet [VERIFICADO: R03 S12].
- La arena aspirada desgasta la holgura de 0,5–0,8 mm y la del anillo.
- Es lo contrario de lo que pide P1 (basculación, protección y fusible mecánico en arena).

**Bañistas.**
- No hay hélice expuesta. Es una ventaja real frente a una hélice abierta sin protector [ESTIMADO].
- La rejilla aspira pelo, ropa y correas de chaleco: "has resulted in drowning or other injury" [VERIFICADO: CG Aux].
- El chorro lesiona y despide arena y piedras a alta velocidad [VERIFICADO: CG Aux].
- La cola larga de P1 tiene protector perfilado, patín y pasador de corte. A 6 km/h y con el motor detenido por el cordón, su riesgo para bañistas es de otro orden, menor por energía [ESTIMADO].

---

## 5. Correcciones mínimas para que el concepto sea viable (si Jorge lo quiere seguir)

1. **Casco:**
   - manga en la flotación ≥ 0,9–1,0 m (manga total ~1,1–1,3 m);
   - asiento bajo;
   - flotación fija de ~100 L;
   - baterías elevadas y estancas;
   - bomba de achique [CALCULADO / ESTIMADO, §4.3].
2. **Bomba:**
   - disposición estándar toma → ducto → impulsor → estator → tobera Ø72 → boquilla externa → bucket;
   - eje del impulsor a ≤ ~150 mm del fondo, para que quede bajo la flotación con 150 kg;
   - sello mecánico en la pared de la cámara;
   - rodamiento axial fijo a la carcasa;
   - acople flexible;
   - impulsor metálico y anillo de desgaste torneado.
3. **Eléctrico:**
   - ≤ 48 V (LFP 13S) o clase 100 V completa;
   - contactor + cordón + seta;
   - límites de corriente y rpm en el ESC;
   - ventilación o refrigeración del motor.
4. **Masa y potencia:** diseñar para 200–230 kg y 7,2 kW continuos, o bajar el objetivo a ~20 km/h.
5. **Legal:** consultar la clasificación con Søfartsstyrelsen; limitar la velocidad a 5 kn por firmware dentro de los 300 m.
6. **Plano:** rehacerlo en CAD a escala, con cotas referidas al espejo y al fondo, y escala propia en el detalle.

---

## 6. No verificado o pendiente

- **Geometría real del casco.** Manga en la flotación, astilla muerta, altura del asiento y LCG salen de un dibujo que no está a escala [ESTIMADO]. **Pedir a Jorge las medidas, o el archivo CAD o PDF original.**
- **Masas del casco y de la bomba** [ESTIMADO]. HPM5000B: 11 kg [VERIFICADO]. Las 3700 rpm nominales, 13 N·m nominal, 45 N·m de pico, 85 A e IP65 salen **solo del resumen del buscador**, no de una página abierta.
- **η de la bomba 0,75–0,85, K_n, banda de joroba R/Δ 0,10–0,20 y umbrales de cavitación (σ, S)** [ESTIMADO]. Savitsky está extrapolado en casco angosto y con LCG a proa.
- **CG de una persona sentada y criterio de GM**: buscar "ISO 12217-3".
- **Flotación mínima**: buscar "33 CFR 183.101 flotation".
- **Fracción de empuje en reversa con bucket**: buscar "jet boat reverse bucket thrust percentage".
- **Versión vigente de la vandscooterbekendtgørelse.** BEK 809/2019 figura con EndDate 2026‑06‑23 en sus metadatos: buscar "vandscooterbekendtgørelse 2026".
- **σ_y del 316 (205 MPa) y CTE del PETG (70 µm/m·K)**: memoria técnica.
- **Fusible y ESC de 100 V CC**: buscar "class T fuse 125 VDC" y "VESC 100V 250A".

---

## 7. Fuentes

**Abiertas en esta sesión (2026-10-01):**

| Id | URL | Qué se leyó |
|---|---|---|
| W1 | https://dmsonline.us/how-to-design-a-waterjet-key-elements-of-waterjets/ | "position the waterjet vertically so that the centerline of the jet lies on the vessel waterline when resting. This ensures the pump of the waterjet can always prime"; "pumps with efficiencies of 90% or greater"; "A bad nozzle may reduce waterjet efficiency to 30% or less" |
| W2 | https://edept.cgaux.org/pdf/PWC%20Safety%20Seminar.pdf | CG Auxiliary, "PWC Safety" (2023): "No Jet thrust, no steering"; "There are no brakes on a PWC"; bucket solo a ralentí; "Never operate your PWC in water less than 24 inches"; succión por la rejilla ("drowning"); "Wet suit bottom…"; ECOS |
| W3 | https://www.law.cornell.edu/cfr/text/33/183.33 | Fórmula de capacidad para motor interior; definición de "boat weight" y "machinery weight" (incluye baterías) |
| W4 | https://www.law.cornell.edu/cfr/text/33/183.41 | La regla de personas aplica a "boats designed to use one or more outboard motors" |
| W5 | https://politi.dk/politikredse/syd-og-soenderjyllands-politi/sejladsreglement | Texto completo §1–§8: 5 kn a < 300 m (§4); playas (§3); speedbåde solo en tránsito perpendicular (§4 stk. 3) |
| W6 | https://www.retsinformation.dk/eli/lta/2019/809/pdf (y `/xml` para los metadatos) | BEK 809/2019 §1 (definición de vandscooter) y §3 (300 m); EndDate 2026‑06‑23 en los metadatos |
| W7 | https://www.soefartsstyrelsen.dk/fritidssejlads/fritidsfartoejer/vandscooter-og-jetski | Vandscooterbevis (16 años), seguro obligatorio y regla de 300 m vigentes |
| W8 | https://www.retsinformation.dk/api/pdf/208169 | BEK 554/2020 §1 stk. 4 y 5 (definición de "planende"; Søfartsstyrelsen decide los casos dudosos) |
| W9 | https://www.kellycontrollers.eu/hpm5000b-5kw-72v-leghuteses | HPM5000B de 72 V: 5000 W, 2000–6000 rpm configurable, 12 mΩ, 154 µH, 91 %, 11 kg, Ø206 × 126 mm, 1306,48 € |
| W10 | https://pypi.org/project/openplaning | openplaning 0.4.9 (licencia MIT), instalado con pip; leí el código de `get_hydrodynamic_force` (Savitsky 1964) y `sum_forces` |
| W11 | https://lex.dk/vandscooter | Definición enciclopédica (contexto; no es norma) |

**Del repositorio:**
- R03: §2.2–2.4, J2/S4, J6/S8, S9, S10, S12.
- R04: A.3, A.4, C.1.
- R05: A1, A6, A7, B6.
- R06: §0, §3.5, §4.1–4.3, §5.1–5.2.
- R07: §0, §1.2, §3.
- R09: §1.6.
- README / `resultados/sizing.json` para la referencia de P1.

**No abiertos (buscar):**
- "ISO 12217-3 offset load test";
- "33 CFR 183.101 flotation";
- "specific speed ranges axial mixed flow pump";
- "waterjet suction specific speed cavitation limit";
- "jet boat reverse bucket thrust percentage";
- "Golden Motor 5kW liquid cooled 72V";
- "VESC 100V 250A";
- "class T fuse 125 VDC";
- "mechanical seal 20 mm water pump SiC";
- "vandscooterbekendtgørelse 2026".

---

## 8. Script ejecutado

Se ejecutó con `python calc_r10b.py` en un entorno virtual con `pip install openplaning numpy scipy`, fuera del repositorio. No se escribió nada en `resultados/`. Las posiciones en píxeles son mediciones propias sobre el PNG.

<details><summary>calc_r10b.py (327 líneas)</summary>

```python
"""R10b — Auditoría técnica del plano preliminar de waterjet de Jorge (2026-09-26).
Todos los cálculos que cita research/R10b_auditoria_plano_jorge.md.
Ejecutar con el venv del scratchpad (openplaning 0.4.9 instalado allí):
    ./venv/bin/python calc_r10b.py
"""
import math
import numpy as np
_trap = getattr(np, "trapezoid", None) or np.trapz

g = 9.81
RHO = 1013.0      # agua salobre Als Fjord [CALCULADO: inputs.yaml water.density_kg_m3]
RHO_F = 1000.0    # agua dulce (USCG 33 CFR 183.33 usa desplazamiento en calma; tomo agua dulce, conservador)
P_ATM = 101325.0
P_V = 2340.0      # presión de vapor a 20 °C [ESTIMADO: memoria técnica, no verificado]

def hdr(t):
    print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)

# ---------------------------------------------------------------------------
hdr("A. COTAS: píxeles medidos en el PNG 1320x1023 (±2 px) y escalas implícitas")
# Vista lateral
lat = dict(L2300=(127, 849), transom_x=797, bow_x=127,
           chain=(121, 356, 572, 752),          # 850 | 750 | 700
           h520=(119, 218), h420=(110, 218), h280=(140, 218),
           axis_y=151, bottom_y=218, grille_x=(735, 760),
           motor_x=(563, 640), pump_x=(680, 797), nozzle_end_x=850)
s_lat = 2300 / (lat['L2300'][1] - lat['L2300'][0])
print(f"Lateral: 2300 mm = {lat['L2300'][1]-lat['L2300'][0]} px -> {s_lat:.3f} mm/px")
hull_drawn = (lat['transom_x'] - lat['bow_x']) * s_lat
print(f"  proa→espejo dibujado = {hull_drawn:.0f} mm; la cota 2300 termina {(lat['L2300'][1]-lat['transom_x'])*s_lat:.0f} mm a popa del espejo (pivote de la boquilla)")
c = lat['chain']
segs = np.diff(c)
print(f"  cadena 850/750/700: px {segs.tolist()} -> a escala {[round(s*s_lat) for s in segs]} mm; total {sum(segs)*s_lat:.0f} mm (rotulado 2300)")
print(f"  la cadena termina en x={c[-1]} = rejilla (x {lat['grille_x']}); rejilla a {(lat['transom_x']-c[-1])*s_lat:.0f} mm del espejo a escala")
for k, lab in (('h520', 520), ('h420', 420), ('h280', 280)):
    px = lat[k][1] - lat[k][0]
    print(f"  cota {lab}: {px} px -> {lab/px:.2f} mm/px (horizontal {s_lat:.2f}); a escala horizontal = {px*s_lat:.0f} mm")
ax_px = lat['bottom_y'] - lat['axis_y']
print(f"  eje motor-bomba a {ax_px} px del fondo -> {ax_px*s_lat:.0f} mm (esc. horiz.) / {ax_px*280/78:.0f} (cal. con 280) / {ax_px*520/99:.0f} mm (cal. con 520)")
print(f"  tren motor→boquilla: {(lat['nozzle_end_x']-lat['motor_x'][0])*s_lat:.0f} mm; motor→fin carcasa: {(lat['pump_x'][1]-lat['motor_x'][0])*s_lat:.0f} mm (detalle: 600)")
# Vista superior
top = dict(L2300=(214, 789), bow_x=164, stern_x=789, w800=(330, 452), hull_w=(311, 468), motor_x=(543, 785))
s_top = 2300 / (top['L2300'][1] - top['L2300'][0])
print(f"Superior: 2300 = {top['L2300'][1]-top['L2300'][0]} px -> {s_top:.2f} mm/px; la cota arranca {(top['L2300'][0]-top['bow_x'])*s_top:.0f} mm a popa de la proa")
print(f"  casco dibujado: largo {(top['stern_x']-top['bow_x'])*s_top:.0f} mm, ancho {(top['hull_w'][1]-top['hull_w'][0])*s_top:.0f} mm; cota 800 abarca {(top['w800'][1]-top['w800'][0])*s_top:.0f} mm")
print(f"  L/B rotulado {2300/800:.2f}; L/B dibujado {(top['stern_x']-top['bow_x'])/(top['hull_w'][1]-top['hull_w'][0]):.2f}")
print(f"  tren motor→boquilla en planta: {(top['motor_x'][1]-top['motor_x'][0])*s_top:.0f} mm (detalle: 600)")
# Vista trasera
rear = dict(w800=(999, 1214), h520=(131, 241), h280=(189, 246), w120=(1088, 1126))
s_rear = 800 / (rear['w800'][1] - rear['w800'][0])
print(f"Trasera: 800 = {rear['w800'][1]-rear['w800'][0]} px -> {s_rear:.2f} mm/px")
for k, lab in (('h520', 520), ('h280', 280), ('w120', 120)):
    px = rear[k][1] - rear[k][0]
    print(f"  cota {lab}: {px} px -> a escala horizontal {px*s_rear:.0f} mm")
print(f"  escalas de las 3 vistas: lateral {s_lat:.2f}, superior {s_top:.2f}, trasera {s_rear:.2f} mm/px -> dispersión {(max(s_lat,s_top,s_rear)/min(s_lat,s_top,s_rear)-1)*100:.0f} %")
# Detalle
det = dict(L600=(87, 533), parts=(87, 230, 300, 387, 450, 533), d120=(568, 669), d108=(584, 647))
s_det = 600 / (det['L600'][1] - det['L600'][0])
p = np.diff(det['parts']); lab = [180, 80, 120, 100, 120]
print(f"Detalle: 600 = {det['L600'][1]-det['L600'][0]} px -> {s_det:.3f} mm/px; tramos {list(zip(lab, [round(x*s_det) for x in p]))}")
print(f"  'Ø inicial toma 120' {det['d120'][1]-det['d120'][0]} px -> {(det['d120'][1]-det['d120'][0])*s_det:.0f} mm; '108' {det['d108'][1]-det['d108'][0]} px -> {(det['d108'][1]-det['d108'][0])*s_det:.0f} mm")
px_per_mm_paper = 1205 / 420   # [SUPUESTO: hoja A3 apaisada, marco ≈ 1205 px]
for nm, sc in (("lateral", s_lat), ("superior", s_top), ("trasera", s_rear), ("detalle", s_det)):
    print(f"  escala equivalente si la hoja es A3: {nm} 1:{sc*px_per_mm_paper:.1f}")
print(f"  detalle ampliado ×{s_lat/s_det:.2f} respecto de la vista lateral (sin escala propia rotulada)")
K_bc = (1 - (72/140)**2)**2
print(f"  Expansión brusca tras la tobera Ø72 a cámara ≈Ø140 (dibujo): K Borda–Carnot = (1−A1/A2)² = {K_bc:.2f} de la altura dinámica del chorro")
print(f"  ¿1:10 sobre A3 (420 mm)? marco ≈ 1205 px -> 2300 mm lateral = {722/1205*420:.0f} mm de papel -> escala 1:{2300/(722/1205*420):.1f} [solo si la hoja es A3: SUPUESTO]")

# ---------------------------------------------------------------------------
hdr("B. Presupuesto de masas (1 piloto) contra los 150 kg del plano")
masses = {  # (min, max) kg
    'casco 2,3x0,8 con cubierta, consola, asiento': (30, 45),   # ver abajo
    'motor 5 kW 72 V': (11, 35),        # 11 kg HPM5000B [VERIFICADO Kelly]; motor industrial dibujado [ESTIMADO]
    'bomba (carcasa Al, impulsor, estator, toma, eje, cojinetes, boquilla)': (8, 15),
    'controlador 72 V 100 A + contactor + fusible + cables': (4, 7),
    'dirección + bucket': (2, 4),
    'agua atrapada en bomba/ducto sobre la flotación': (2, 5),
    'equipo de seguridad (remo, ancla, achicador, chaleco puesto)': (5, 8),
    'piloto': (80, 100),
}
area = 2.3 * 0.8
print(f"Casco: R04 A.3 8,3–14,6 kg/m² × {area:.2f} m² = {8.3*area:.0f}–{14.6*area:.0f} kg (jon boats abiertos, sin cubierta)")
lo = sum(v[0] for v in masses.values()); hi = sum(v[1] for v in masses.values())
for k, v in masses.items():
    print(f"  {k:70s} {v[0]:>4}–{v[1]:<4} kg")
print(f"  SUBTOTAL sin batería: {lo}–{hi} kg")
for wh_kg, chem in ((128, 'LFP (R06: LiTime 128 Wh/kg)'), (160, 'NMC pack [ESTIMADO 150–180]')):
    for E in (2.0, 3.0, 4.0, 6.0):
        mb = E * 1000 / wh_kg
        print(f"  batería {chem} {E:.0f} kWh = {mb:.1f} kg -> total {lo+mb:.0f}–{hi+mb:.0f} kg")
print(f"  Para cerrar 150 kg con piloto 80 kg y batería LFP 3 kWh ({3000/128:.0f} kg): casco+máquina ≤ {150-80-3000/128:.0f} kg")

# ---------------------------------------------------------------------------
hdr("C. Hidrostática: calado, francobordo, capacidad USCG, GM")
# Sección según vista trasera: fondo plano 0,42 m; quiebre a z_k con 0,69 m; borda 0,80 m a 0,52 m
def B_of_z(z, b0=0.42, bk=0.69, zk=0.25, bs=0.80, zs=0.52):
    if z <= zk:
        return b0 + (bk - b0) * z / zk
    return bk + (bs - bk) * (z - zk) / (zs - zk)
def L_of_z(z):  # largo de flotación: fondo plano 1,73 m, crece por la proa lanzada (vista lateral)
    return (542 + 0.2405 * z * 1000) * s_lat / 1000
CWP = 0.85     # [ESTIMADO: rectángulo 70 % + proa triangular 30 % del largo]
CI = 0.065     # I_T = CI·L·B³ con la misma planta [CALCULADO: 0,7/12 + 0,3/48]
def vol(T, n=400, **kw):
    zz = np.linspace(0, T, n)
    a = np.array([CWP * L_of_z(z) * B_of_z(z, **kw) for z in zz])
    V = _trap(a, zz); zb = _trap(a * zz, zz) / V if V > 0 else 0
    return V, zb
def draft(m, rho=RHO, **kw):
    lo_, hi_ = 1e-4, 0.52
    for _ in range(60):
        mid = 0.5 * (lo_ + hi_)
        if vol(mid, **kw)[0] * rho < m: lo_ = mid
        else: hi_ = mid
    return mid
print(f"L(z=0) = {L_of_z(0):.2f} m, L(0,2) = {L_of_z(0.2):.2f} m, L(0,42) = {L_of_z(0.42):.2f} m")
for m in (150, 180, 200, 230, 280, 330):
    for kw, nm in (({}, 'fondo 0,42'), ({'b0': 0.60, 'bk': 0.75}, 'fondo 0,60')):
        T = draft(m, **kw)
        print(f"  Δ={m} kg ({nm}): calado {T*1000:.0f} mm; francobordo espejo (420) {420-T*1000:.0f} mm; eje del jet (260–280) {'BAJO' if T*1000>=260 else 'SOBRE'} la flotación por {abs(270-T*1000):.0f} mm")
Vmax, _ = vol(0.42)
Dmax = Vmax * RHO_F
print(f"Desplazamiento máximo a 0,42 m (borde del espejo, a nivel): ∇ = {Vmax:.3f} m³ -> {Dmax:.0f} kg (agua dulce)")
Vmax2, _ = vol(0.42, b0=0.60, bk=0.75)
print(f"   (fondo 0,60: {Vmax2*RHO_F:.0f} kg)")
for Dm in (Dmax, Vmax2 * RHO_F):
    for BW, MW in ((30, 35), (45, 70)):
        W1 = Dm / 5 - BW / 5 - 4 * MW / 5
        W2 = (Dm - BW) / 7
        W = max(W1, W2)
        npers = round((W / 0.4536 + 32) / 141)
        print(f"  USCG 183.33: Δmax {Dm:.0f}, casco {BW}, máquinas+baterías {MW}: W1={W1:.0f}, W2={W2:.0f} -> W = {W:.0f} kg (personas+equipo); personas ≈ {npers} (regla 183.41, 141 lb/p)")
# GM
def GM(m_tot, items, **kw):
    T = draft(m_tot, **kw)
    V, KB = vol(T, **kw)
    Bwl = B_of_z(T, **kw); Lwl = L_of_z(T)
    BM = CI * Lwl * Bwl ** 3 / V
    KG = sum(mi * zi for mi, zi in items) / sum(mi for mi, zi in items)
    return T, KB, BM, KG, KB + BM - KG, Bwl
print("GM con 1 piloto sentado (alturas sobre el fondo):")
for pil_z in (0.45, 0.55, 0.65):
    for (mh, mm_, mb) in ((35, 30, 25), (45, 40, 40)):
        items = [(90, pil_z), (mb, 0.12), (mm_, 0.26), (mh, 0.22), (5, 0.30)]
        mt = sum(x[0] for x in items)
        T, KB, BM, KG, gm, Bwl = GM(mt, items)
        T2, KB2, BM2, KG2, gm2, Bwl2 = GM(mt, items, b0=0.60, bk=0.75)
        print(f"  zG piloto {pil_z:.2f} m, Δ {mt} kg: T {T*1000:.0f} mm, Bwl {Bwl:.2f}, KB {KB:.3f}, BM {BM:.3f}, KG {KG:.3f} -> GM {gm*1000:+.0f} mm | fondo 0,60: GM {gm2*1000:+.0f} mm")
# manga necesaria para GM >= +100 mm (criterio SUPUESTO) con fondo plano ancho b y costado vertical
print("Manga en la flotación (casco tipo caja, fondo plano = manga) para GM ≥ +100 mm [SUPUESTO criterio], Δ 200 kg, KG 0,36 m:")
for B in (0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3):
    L = 1.8; V = 200 / RHO; T = V / (CWP * L * B); KB = T / 2; BM = CI * L * B ** 3 / V
    print(f"  B={B:.1f} m: T={T*1000:.0f} mm, KB+BM={KB+BM:.3f}, GM={(KB+BM-0.36)*1000:+.0f} mm")

# ---------------------------------------------------------------------------
hdr("D. Resistencia: joroba (banda) y planeo (Savitsky 1964 vía openplaning 0.4.9)")
L_ft = 1.75 / 0.3048
for v in (9.26, 12, 15, 18, 20, 25, 30):
    V = v / 3.6
    print(f"  {v:5.1f} km/h: SLR {V/0.5144/math.sqrt(L_ft):.2f}; Fn_L {V/math.sqrt(g*1.75):.2f}; Fn∇(200 kg) {V/math.sqrt(g*(200/RHO)**(1/3)):.2f}; C_V(b 0,5) {V/math.sqrt(g*0.5):.2f}")
print("Banda de joroba R/Δ = 0,10–0,20 [ESTIMADO: Savitsky 2003 típica ≈0,10 a SLR 3 (R09 §1.6) ×1–2 por casco rechoncho (R09)]:")
for m in (150, 200, 230):
    print(f"  Δ {m} kg: R_joroba {0.10*m*g:.0f}–{0.20*m*g:.0f} N")
try:
    from openplaning import PlaningBoat
    import warnings; warnings.filterwarnings('ignore')
    res = {}
    for m in (150, 200, 230):
        for b, beta, lcg in ((0.50, 5, 0.75), (0.50, 5, 1.00), (0.60, 10, 0.75), (0.60, 10, 1.00), (0.45, 4, 0.90), (0.60, 10, 1.16)):
            row = []
            for v in (20, 25, 30, 35):
                V = v / 3.6
                boat = PlaningBoat(V, m * g, b, lcg, 0.33, 0.5, beta, 0, 0.26, 0.0, rho=RHO, nu=1.3e-6,
                                   l_air=0.9, h_air=1.1, b_air=0.5, C_shape=1, C_D=0.9)
                try:
                    boat.get_steady_trim()
                    boat.get_forces()
                    Rx = abs(boat.hydrodynamic_force[0] + boat.skin_friction[0] + boat.air_resistance[0] + boat.lift_change[0])
                    row.append((v, Rx, boat.tau, boat.lambda_W))
                except Exception as e:
                    row.append((v, float('nan'), float('nan'), float('nan')))
            res[(m, b, beta, lcg)] = row
            print(f"  Δ {m} kg, b {b}, β {beta}°, LCG {lcg} m: " + "; ".join(f"{v} km/h R={R:.0f} N τ={t:.1f}° λ={l:.2f}" for v, R, t, l in row))
except ImportError as e:
    print("openplaning no disponible:", e)
    res = {}

# ---------------------------------------------------------------------------
hdr("E. Jet: cantidad de movimiento con pérdidas (impulsor Ø108, tobera Ø72, 4500 rpm)")
Dj, Di, hub = 0.072, 0.108, 0.40
Aj = math.pi / 4 * Dj ** 2
Aan = math.pi / 4 * (Di ** 2 - (hub * Di) ** 2)
n = 4500; w = 2 * math.pi * n / 60; U = math.pi * Di * n / 60
print(f"A_tobera {Aj*1e4:.1f} cm²; A_anular impulsor (cubo {hub}) {Aan*1e4:.1f} cm²; Dt/Di {Dj/Di:.3f}; At/Ai {Dj**2/Di**2:.3f}; At/Aanular {Aj/Aan:.2f}")
print(f"Velocidad periférica {U:.1f} m/s; ω {w:.0f} rad/s")
ETA_MOT, ETA_ESC, ETA_MEC = 0.91, 0.97, 0.98   # 0,91 [VERIFICADO Kelly HPM5000B]; resto [ESTIMADO]
def jet_state(V0, Pel, eta_p, Kn=0.03, eta_in=0.70, h_j=0.0):
    """Resuelve V_j con P_h = ρQ[(1+Kn)Vj²/2 − η_in V0²/2 + g h_j]. Devuelve dict."""
    Ph = Pel * ETA_ESC * ETA_MOT * ETA_MEC * eta_p
    f = lambda Vj: RHO * Aj * Vj * ((1 + Kn) * Vj ** 2 / 2 - eta_in * V0 ** 2 / 2 + g * h_j) - Ph
    lo_, hi_ = max(V0, 0.1), 80
    for _ in range(100):
        mid = 0.5 * (lo_ + hi_)
        if f(mid) < 0: lo_ = mid
        else: hi_ = mid
    Vj = mid; Q = Aj * Vj
    T = RHO * Q * (Vj - V0)
    H = ((1 + Kn) * Vj ** 2 - eta_in * V0 ** 2) / (2 * g) + h_j
    return dict(Vj=Vj, Q=Q, T=T, H=H, Ph=Ph, Pshaft=Pel * ETA_ESC * ETA_MOT * ETA_MEC,
                eta_jet=T * V0 / Ph if Ph else 0, eta_tot=T * V0 / Pel)
for Pel in (5000, 7200):
    for eta_p in (0.75, 0.85):
        print(f"P_el {Pel} W, η_bomba {eta_p}:")
        for v in (0, 5, 9.26, 12, 15, 20, 25, 30, 35):
            s = jet_state(v / 3.6, Pel, eta_p)
            print(f"   {v:5.1f} km/h: Vj {s['Vj']:.1f} m/s, Q {s['Q']*1000:.0f} L/s, T {s['T']:.0f} N, H {s['H']:.1f} m, η_jet(chorro) {s['eta_jet']:.2f}, η_total(bat→empuje) {s['eta_tot']:.2f}")
# Punto de diseño 30 km/h: empuje necesario vs disponible
print("Equilibrio T(V) = R(V) (R de Savitsky/openplaning, 20–35 km/h):")
def R_interp(row, v):
    vs = [r[0] for r in row]; Rs = [r[1] for r in row]
    return float(np.interp(v, vs, Rs))
if res:
    for key in sorted(res):
        row = res[key]
        out = []
        for Pel in (5000, 7200):
            for eta_p in (0.75, 0.85):
                vv = np.linspace(20, 35, 301)
                margin = np.array([jet_state(v / 3.6, Pel, eta_p)['T'] - R_interp(row, v) for v in vv])
                if margin[0] < 0:
                    txt = f"T<R ya a 20 km/h (déficit {-margin[0]:.0f} N)"
                elif (margin >= 0).all():
                    txt = ">35"
                else:
                    txt = f"{vv[np.argmax(margin < 0)]:.1f}"
                out.append(f"{Pel/1000:.1f}kW/η{eta_p}: {txt}")
        print(f"   Δ{key[0]} b{key[1]} β{key[2]} LCG{key[3]}: " + " | ".join(out))
print("Joroba: empuje disponible vs banda R/Δ 0,10–0,20:")
for m in (150, 200, 230):
    for v in (12, 15, 18):
        T5 = jet_state(v/3.6, 5000, 0.75)['T']; T5b = jet_state(v/3.6, 5000, 0.85)['T']; T7 = jet_state(v/3.6, 7200, 0.80)['T']
        print(f"   Δ{m} @ {v} km/h: R {0.10*m*g:.0f}–{0.20*m*g:.0f} N; T(5 kW) {T5:.0f}–{T5b:.0f} N; T(7,2 kW) {T7:.0f} N")
# LCG del dibujo
items = [('piloto', 90, 1.38), ('baterías', 30, 1.42), ('motor', 20, 0.63), ('bomba', 12, 0.25), ('casco', 38, 0.95), ('controlador+varios', 10, 1.0)]
M = sum(i[1] for i in items); LCG = sum(i[1]*i[2] for i in items)/M
print(f"LCG desde el espejo (posiciones medidas en la vista lateral): {LCG:.2f} m = {LCG/1.73*100:.0f} % del largo de fondo (1,73 m); Δ {M} kg")
# ideal sin pérdidas a 30 km/h y comparación con hélice
V0 = 30 / 3.6
for T_need in (250, 300, 350, 400):
    Vj = (V0 + math.sqrt(V0 ** 2 + 4 * T_need / (RHO * Aj))) / 2
    print(f"  T requerido {T_need} N a 30 km/h -> Vj {Vj:.1f} m/s, Vj/V0 {Vj/V0:.2f}, η_ideal chorro {2/(1+Vj/V0):.2f}, P_h ideal {RHO*Aj*Vj*(Vj**2-V0**2)/2:.0f} W")

# ---------------------------------------------------------------------------
hdr("F. Bomba: coeficientes, velocidad específica, cavitación")
for v, Pel in ((0, 5000), (12, 5000), (30, 5000), (30, 7200)):
    s = jet_state(v / 3.6, Pel, 0.80)
    Q, H = s['Q'], s['H']
    psi = g * H / U ** 2; phi = (Q / Aan) / U
    Om_s = w * math.sqrt(Q) / (g * H) ** 0.75
    Ns_us = n * math.sqrt(Q * 15850.3) / (H / 0.3048) ** 0.75
    torque = s['Pshaft'] / w
    # cavitación: NPSHa con impulsor h_i sobre la flotación (0,05–0,15 m) y recuperación 70 % de V0²/2g
    for h_i in (0.0, 0.10):
        NPSHa = (P_ATM - P_V) / (RHO * g) - h_i + 0.70 * (v / 3.6) ** 2 / (2 * g)
        S = w * math.sqrt(Q) / (g * NPSHa) ** 0.75
        Wtip = math.sqrt(U ** 2 + (Q / Aan) ** 2)
        sig_tip = (P_ATM - P_V - RHO * g * h_i + 0.70 * 0.5 * RHO * (v / 3.6) ** 2) / (0.5 * RHO * Wtip ** 2)
        print(f"  {v} km/h, {Pel} W: Q {Q*1000:.0f} L/s, H {H:.1f} m, φ {phi:.2f}, ψ {psi:.3f}, Ω_s {Om_s:.2f} (N_s US {Ns_us:.0f}), par {torque:.1f} N·m | h_imp {h_i} m: NPSHa {NPSHa:.1f} m, S {S:.2f}, σ_punta {sig_tip:.2f}")

# ---------------------------------------------------------------------------
hdr("G. Eje Ø20, cojinetes, empuje axial")
d = 0.020
for Pel, lab in ((5000, 'diseño'), (7200, 'máx'), (None, 'pico motor 45 N·m [búsqueda, no verificado]')):
    Tq = (Pel * ETA_ESC * ETA_MOT / w) if Pel else 45.0
    tau = 16 * Tq / (math.pi * d ** 3) / 1e6
    print(f"  {lab}: par {Tq:.1f} N·m, τ nominal {tau:.1f} MPa, con chavetero Kt 2,5 → {2.5*tau:.0f} MPa; τ_y 316 ≈ 0,577·205 = {0.577*205:.0f} MPa [ESTIMADO] -> FS {0.577*205/(2.5*tau):.1f}")
print(f"  Velocidad periférica del eje Ø20 en el sello: {math.pi*0.020*n/60:.1f} m/s")
s0 = jet_state(0.01, 7200, 0.85); s30 = jet_state(30/3.6, 5000, 0.80)
print(f"  Empuje axial de referencia: bollard 7,2 kW ≈ {s0['T']:.0f} N; 30 km/h 5 kW ≈ {s30['T']:.0f} N (el impulsor tira hacia proa; debe ir a un rodamiento fijo y de ahí al casco)")

# ---------------------------------------------------------------------------
hdr("H. Eléctrico 72 V")
for nm, ns, vn, vmax_c, vmin_c in (("LFP 22S", 22, 3.2, 3.65, 2.8), ("LFP 23S", 23, 3.2, 3.65, 2.8), ("NMC 20S", 20, 3.6, 4.2, 3.2)):
    print(f"  {nm}: nominal {ns*vn:.1f} V, cargada {ns*vmax_c:.1f} V, vacía {ns*vmin_c:.1f} V | >50 V (ISO 16315:2016 3.1): {'SÍ' if ns*vmax_c>50 else 'no'}")
print(f"  I a 5 kW / 72 V = {5000/72:.0f} A; 60 A × 72 V = {60*72} W; 60 A × 84 V = {60*84} W; 100 A × 72 V = {100*72} W; 7,2 kW a 61,6 V (LFP 22S vacía) = {7200/61.6:.0f} A")
for nload_frac in (1.0, 0.85):
    Kv = 4500 / (72 * nload_frac)
    print(f"  KV si 4500 rpm = {'vacío' if nload_frac==1 else 'carga (85 % de vacío)'} a 72 V: {Kv:.1f} rpm/V; a 84 V: n0 = {84*Kv:.0f} rpm -> P_bomba ∝ n³: ×{(84*Kv*nload_frac/4500)**3:.2f}")

# ---------------------------------------------------------------------------
hdr("I. Autonomía y operación legal (5 kn = 9,26 km/h a < 300 m)")
for E in (2.0, 3.0, 4.0):
    for Pel, v in ((5000, 30), (7200, 30)):
        print(f"  E útil {E} kWh @ {Pel} W: {E*1000/Pel*60:.0f} min, {E*1000/Pel*v:.1f} km a {v} km/h")
# potencia para sostener 5 kn con el jet
for m in (150, 200, 230):
    for RD in (0.06, 0.10, 0.16):
        R = RD * m * g; V0 = 9.26 / 3.6
        # buscar P_el tal que T = R
        lo_, hi_ = 10, 8000
        for _ in range(60):
            mid = 0.5 * (lo_ + hi_)
            if jet_state(V0, mid, 0.75)['T'] < R: lo_ = mid
            else: hi_ = mid
        print(f"  Δ {m} kg, R/Δ {RD} -> R {R:.0f} N a 5 kn: P_el jet ≈ {mid:.0f} W (η_total {R*V0/mid:.2f}); 3 kWh -> {3000/mid:.1f} h, {3000/mid*9.26:.0f} km")
print("  Referencia P1 cola larga: 759–910 W a 6 km/h con 2 personas (README / sizing)")

# ---------------------------------------------------------------------------
hdr("J. Holgura de punta y PETG")
for c in (0.5, 0.8):
    print(f"  holgura {c} mm = {c/108*100:.2f} % de D (Ladd 19A: 0,5 % de D; R03)")
Tq = 5000 * ETA_ESC * ETA_MOT / w
Ft = Tq / 4 / (0.7 * Di / 2)
span = (Di - hub * Di) / 2
M = Ft * 0.6 * span
for (ch, t) in ((0.040, 0.005), (0.040, 0.008)):
    Z = ch * t ** 2 / 6; I = ch * t ** 3 / 12
    sig = M / Z / 1e6
    delta = Ft * span ** 3 / (8 * 1.5e9 * I) * 1000
    print(f"  pala PETG cuerda {ch*1000:.0f} × e {t*1000:.0f} mm: F_t {Ft:.0f} N/pala, M_raíz {M:.2f} N·m, σ {sig:.1f} MPa (adm. R05: 2,7 MPa sostenida XY FS3; 0,5 MPa alterna) ; flecha tangencial ≈ {delta:.2f} mm (E 1,5 GPa)")
cte = 70e-6  # [ESTIMADO: memoria técnica, PETG 60–80 µm/m·K]
print(f"  dilatación radial PETG Ø108, ΔT 15 K, α 70 µm/m·K: {cte*54*15:.3f} mm por lado")
rho_p = 1270
sig_c = rho_p * w ** 2 * (Di / 2) ** 2 / 2
print(f"  crecimiento centrífugo de pala PETG a 4500 rpm: σ≈{sig_c/1e6:.2f} MPa -> {sig_c/1.5e9*54:.3f} mm")
print("  tolerancia FDM por superficie ±0,15 mm [ESTIMADO: R05] -> Ø impreso ±0,3 mm + ovalización; apilado > holgura")
```
</details>
