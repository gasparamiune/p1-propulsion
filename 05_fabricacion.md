# 05 — Fabricación de P1: material, perfiles PrusaSlicer, probetas, orientación y post-proceso

**Estado:** todo lo de esta página está verificado *en software* — CAD de probetas cerrado y dentro de la envolvente (`build_probetas.py`), perfiles cargados y laminados por PrusaSlicer 2.7.2 CLI (`validar_perfiles.py`), tablas regeneradas desde los JSON (`tabla_fabricacion.py`), `tests/test_probetas.py`. **Nada está impreso ni ensayado: secado, probetas, refrentado y estanqueidad son [NO EJECUTADO] — pendiente físico** (PENDIENTES_GASPAR §P1).

Las tablas entre `<!-- FAB:… -->` se regeneran con `python 04_diseno/probetas/tabla_fabricacion.py` (leen `resultados/manifest.json`, `resultados/estructural.json`, `04_diseno/probetas/probetas_manifest.json`, `prusaslicer/slice_report.json` y el código de `04_diseno/piezas/`); no editarlas a mano.

Fuentes: research/R05 (S1 Prusament PETG TDS, S2 PolyLite PETG TDS V6.0, S3 Bambu PETG Basic TDS; los tres PDF se volvieron a abrir en esta sesión para secado, cama y ventilador), S18–S36 citadas por su número de R05.

---

## 0. Resumen

- **Material:** PETG de color claro con HDT(1,8 MPa) ≥ 70 °C [VERIFICADO: research/R05 A1, PolyLite 75 °C]. **Secar 65 °C × 6–8 h** y guardar a HR < 20 % [VERIFICADO: S2, S3].
- **4 familias de perfil** (impresora + filamento comunes): **estructural** 0,20 / 6 perímetros / 85 % gyroid (+ modificador = `solid_frac`), **sellado** 0,15 / 5 perímetros / 100 % / planchado, **fusible** 0,20 / 4 perímetros clásicos / 100 % a 45° (fija la rotura del patín), **cubiertas** 0,20 / 3 perímetros / 25 %. Boquilla 245 °C ≤ 260; cama 80/75 °C ≤ 100; cama PC + pegamento en barra.
- **Probetas P1.1–P1.8:** 16 STL / 33 impresiones; cada una **recorta o replica la pieza real** (mejilla MNT-04, reborde de ELE-01, patín PRP-02, puente HSG-02) leyendo la geometría de los módulos, y se imprime con el perfil de la pieza que representa.
- **Tiempo real ≈ 2× lo previsto:** PrusaSlicer da ~10 g/h para las piezas, no los 18 g/h de `inputs.yaml` (tabla §6). La abrazadera MNT-01 son **~1,8 kg y ~7 días** de impresión continua: dos bobinas y cambio a mitad de pieza (§3.2).
- **Hallazgos para el diseño:** §8.

---

## 1. Material, secado y almacenamiento

| Paso | Valor | Etiqueta |
|---|---|---|
| Compra | PETG 1,75 mm, **HDT(1,8 MPa) ≥ 70 °C declarada** (PolyLite 75 °C; Prusament y Bambu 68 °C no llegan) | [VERIFICADO: research/R05 A1, S1–S3] |
| Color | Blanco, gris claro o natural (piezas al sol) | [ESTIMADO: research/R05 A4] |
| Secado | **65 °C × 6 h** (PolyLite) a **8 h** (Bambu, horno de aire forzado); usar 8 h si la bobina estuvo abierta | [VERIFICADO: S2 "65°C/6H"; S3 "Blast Drying Oven: 65 °C, 8 h"] |
| Límite del carrete | Carrete de ABS de Bambu: 70 °C → **no pasar de 65 °C**; un horno doméstico oscila ±10 °C: medir con termómetro y quedarse en 55–60 °C si oscila | [VERIFICADO: S3 "Spool Material ABS (Temperature resistance 70 °C)"]; oscilación [ESTIMADO] |
| Almacenamiento e impresión | Caja estanca con desecante, **HR < 20 %**; las impresiones largas (MNT-01, MNT-05, ELE-01) **desde la caja seca** | [VERIFICADO: S3 "< 20% RH (Sealed, with desiccant)"] |
| Señales de humedad | Chasquidos en la boquilla, hilos, superficie áspera, burbujas → volver a secar | [ESTIMADO: práctica común] |
| Piezas impresas | **No** "recocer" ni secar piezas a 60–70 °C: deforman | [VERIFICADO: S3 "not recommended to anneal … may deform obviously"] |

Control: pesar la bobina antes/después del secado (pierde ~0,1–0,5 % si estaba húmeda [ESTIMADO: absorción en equilibrio 0,45–0,54 % de S2/S3]); registrar en la etiqueta fecha y horas de secado.

---

## 2. Perfiles PrusaSlicer (`prusaslicer/`)

| Archivo | Contenido |
|---|---|
| `P1_impresora_Ender3S1.ini` | Ender-3 S1, boquilla 0,4, Marlin 2, extrusor relativo, **zona útil 210×210×260** (forma de cama 5…215 dentro de 220×220: PrusaSlicer marca en rojo lo que sale), G-code de inicio con malla ABL y purga dentro de la zona útil |
| `P1_filamento_PETG.ini` | Temperaturas, cama PC con separador, ventilador, retracción, caudal máximo, secado en notas |
| `P1_impresion_{estructural_0.20, sellado_0.15, fusible_0.20, cubiertas_0.20}.ini` | Un perfil por familia |
| `completo/P1_<familia>_completo.ini` | Configuración completa **guardada por el propio PrusaSlicer** (impresora + filamento + impresión): Archivo → Importar → Importar configuración |
| `validar_perfiles.py` → `slice_report.json` | Formato, límites, claves conocidas, laminado de todas las probetas y piezas, eco de la configuración en el G-code |

**Uso CLI:** `prusa-slicer --load P1_impresora_Ender3S1.ini --load P1_filamento_PETG.ini --load P1_impresion_estructural_0.20.ini --fill-density 90% --export-gcode pieza.stl`. Los ajustes por objeto (relleno, borde, soporte) de §3 van en la GUI con clic derecho → *Agregar ajustes*.

**Validación ejecutada** (`python prusaslicer/validar_perfiles.py`, PrusaSlicer 2.7.2 instalado con apt en esta sesión): los 6 `.ini` tienen formato «clave = valor» sin duplicados; todas las claves existen en 2.7.2 (se compararon contra la configuración por defecto y `--help-fff`; PrusaSlicer **ignora en silencio** las claves desconocidas, por eso el control); PrusaSlicer rechazó la primera versión por falta de `G92 E0` en el G-code de capa con extrusor relativo (corregido); las 16 probetas y las 19 piezas laminan y el G-code repite temperatura, cama, perímetros, relleno, capa, costura, forma de cama y alto máximo.

### 2.1 Valores (generado desde los `.ini`)

<!-- FAB:perfiles -->
| Parámetro (print) | estructural (`P1_impresion_estructural_0.20.ini`) | sellado (`P1_impresion_sellado_0.15.ini`) | fusible (`P1_impresion_fusible_0.20.ini`) | cubiertas (`P1_impresion_cubiertas_0.20.ini`) |
|---|---|---|---|---|
| capa [mm] | 0.2 | 0.15 | 0.2 | 0.2 |
| 1.ª capa [mm] | 0.2 | 0.2 | 0.2 | 0.2 |
| perímetros | 6 | 5 | 4 | 3 |
| generador de perímetros | arachne | arachne | classic | arachne |
| capas sólidas arriba | 6 | 8 | 5 | 5 |
| capas sólidas abajo | 5 | 7 | 5 | 4 |
| relleno base | 85% | 100% | 100% | 25% |
| patrón | gyroid | rectilinear | rectilinear | gyroid |
| ángulo de relleno [°] | 45 | 45 | 45 | 45 |
| solape relleno–perímetro | 25% | 30% | 25% | 25% |
| costura | aligned | rear | aligned | aligned |
| costuras internas escalonadas | 1 | 1 | 0 | 0 |
| planchado | 0 | 1 | 0 | 0 |
| v perímetro externo [mm/s] | 25 | 20 | 25 | 30 |
| v perímetros [mm/s] | 40 | 30 | 40 | 45 |
| v relleno [mm/s] | 60 | 45 | 50 | 70 |
| v relleno sólido [mm/s] | 40 | 35 | 50 | 50 |
| soportes (por defecto) | 0 | 0 | 0 | 0 |
| compensación pata de elefante [mm] | 0.2 | 0.2 | 0.2 | 0.2 |

| Archivo | Clave | Valor |
|---|---|---|
| `P1_filamento_PETG.ini` | first_layer_temperature | 245 |
| `P1_filamento_PETG.ini` | temperature | 245 |
| `P1_filamento_PETG.ini` | first_layer_bed_temperature | 80 |
| `P1_filamento_PETG.ini` | bed_temperature | 75 |
| `P1_filamento_PETG.ini` | min_fan_speed | 15 |
| `P1_filamento_PETG.ini` | max_fan_speed | 35 |
| `P1_filamento_PETG.ini` | bridge_fan_speed | 60 |
| `P1_filamento_PETG.ini` | disable_fan_first_layers | 3 |
| `P1_filamento_PETG.ini` | filament_max_volumetric_speed | 8 |
| `P1_filamento_PETG.ini` | filament_retract_length | 1 |
| `P1_filamento_PETG.ini` | filament_retract_speed | 30 |
| `P1_impresora_Ender3S1.ini` | bed_shape | 5x5,215x5,215x215,5x215 |
| `P1_impresora_Ender3S1.ini` | max_print_height | 260 |
| `P1_impresora_Ender3S1.ini` | nozzle_diameter | 0.4 |
| `P1_impresora_Ender3S1.ini` | gcode_flavor | marlin2 |
| `P1_impresora_Ender3S1.ini` | machine_max_acceleration_extruding | 1000 |
<!-- /FAB:perfiles -->

### 2.2 Por qué cada valor

**Filamento y máquina (comunes).**
- Boquilla **245 °C**: rangos 230–260 °C (S2, S3) y 250 ± 10 °C (S1) [VERIFICADO]; al medio del rango para soldar capas sin hilos [ESTIMADO]. Techo de la máquina 260 °C [VERIFICADO: inputs.yaml]. Si P1.5 da σ_Z/σ_XY < f_z, subir a 250 °C.
- Cama **80 °C** la 1.ª capa y **75 °C** después: 80 ± 10 (S1), 70–80 (S2), 65–75 (S3) [VERIFICADO]; techo 100 °C [VERIFICADO: inputs.yaml].
- **Cama PC con agente separador (pegamento en barra, capa fina):** PolyLite lista "PC and Texture PEI" [VERIFICADO: S2]; Prusament exige pegamento sobre PEI liso y Bambu lo recomienda [VERIFICADO: S1, S3]. Sin separador el PETG se suelda a superficies lisas y arranca trozos al despegar [ESTIMADO]. Despegar con la cama **fría**; limpiar la cama con IPA.
- **Ventilador 15–35 %** (60 % en puentes, apagado 3 capas): PolyLite pide OFF–20 % [VERIFICADO: S2], Prusament 50 % [VERIFICADO: S1]. Se va al lado bajo porque el PETG es débil entre capas (f_z = 0,40, research/R05 A3) y la Ender-3 S1 imprime abierta.
- **Caudal ≤ 8 mm³/s** [ESTIMADO: hotend de serie con PETG]; el pico del perfil estructural es 60 mm/s × 0,45 × 0,20 = 5,4 mm³/s [CALCULADO].
- **Retracción 1 mm a 30 mm/s** (extrusor directo): rango 1–3 mm a 20–40 mm/s [VERIFICADO: S2].
- **Sin cerramiento:** imprimir lejos de corrientes de aire y ventanas; la temperatura ambiente estable importa más en las piezas de varios días [ESTIMADO].

**Estructural** (abrazadera, horquilla, cuna y tapa, carcasa inferior, puente, portabujes, abrazaderas de caña, placa antiventilación, puño, collar hall, soporte de kill switch). `structural.py` calcula FS ≥ 3 sobre la **sección llena** con σ = σt,XY·f_water·f_temp·f_process; `f_process = 0,80` cubre poros y costura, **no** un relleno ralo. Por eso: **6 perímetros** (2,7 mm; R05 A3 pide ≥ 6–8 en piezas cargadas), **6/5 capas sólidas** (≥ 1 mm de piel), **gyroid 85 %** como base (= el `solid_frac` más bajo del manifest, MNT-01) y **modificador por objeto = `solid_frac`** (90–100 %; tabla §3). Costura **alineada** (una línea que se puede "pintar" en zona no cargada) y **costuras internas escalonadas** para no apilar el punto débil a través de la pared. Velocidades moderadas (25/40/60 mm/s): mejor soldadura entre cordones (la anisotropía también existe dentro de la capa, 0,45 en S15).

**Sellado** (caja del ESC; probetas P1.4 y P1.6). Zonas de sello con ≥ 4 perímetros [VERIFICADO: S22] → 5; relleno 100 % con 30 % de solape (el PETG pierde agua "through the seams and contact points between perimeters and solid infill" [VERIFICADO: S22]); **capa 0,15**: Sa 10,9–12,8 µm contra 19,9–24,4 µm a 0,21 mm [VERIFICADO: S18]; **planchado** de las caras superiores (fondo de ranura y cara del O-ring); costura **atrás**, en una pared vertical, nunca sobre la cara del O-ring. La cara sigue sin llegar a Ra ≤ 0,8–1,6 µm [VERIFICADO: S24, S26] → refrentar o lijar (§5.4).

**Fusible / sacrificial** (patín PRP-02, segmentos del protector PRP-01; probeta P1.8). El patín debe romper en su cintura con `skeg_fuse_force` = 300 N antes que tubo, cuna y abrazadera. La carga de rotura depende de cuánto filamento corre a lo largo de la tensión en las fibras externas de la cintura: eso lo fijan **perímetros, relleno y ángulo**. Se fijan **4 perímetros con generador clásico** (ancho constante; Arachne varía el ancho según la geometría), **100 % rectilíneo a 45°** (sección llena: la rotura no depende de un % de relleno) y velocidades/temperaturas iguales a las de la probeta. **No cambiar ningún valor sin repetir P1.8**; imprimir **3 probetas P1.8 en la misma cama y con la misma bobina que cada patín** (testigo de tanda). El protector va con el mismo perfil: consumible con fatiga a ~50 Hz, paredes llenas [ESTIMADO: research/R05 A6, A8].

**Cubiertas** (cubrecorrea HSG-03, capó HSG-05): fuera de la ruta de carga, con drenaje y sin sello (research/R05 A8). 3 perímetros cubren casi todo el espesor de pared del CAD (2,4 mm), 25 % gyroid, velocidades más altas.

---

## 3. Orientación por pieza, perfil y ajustes por objeto

La orientación es la del CAD (`print_rot` de cada `META`; `build_all.py` exporta los STL ya orientados y apoyados en z = 0). Regla: **la carga dominante en el plano de capas (XY)**; lo que trabaja a través de capas solo a compresión. El FS mínimo y el caso salen de `estructural.json`; soporte y avisos, del laminado real.

<!-- FAB:orientacion -->
| ID | Pieza | Cant. | Perfil, relleno | Carga dominante (manifest) | Orientación de impresión: por qué (manifest) | Envolvente impresión [mm] | FS mín. (estructural.json) | Soporte auto / avisos PrusaSlicer | g c/u (CAD) | h c/u (18 g/h) | h c/u (PrusaSlicer) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1-CTL-02 | caja_acel | 1 | **estructural** 85 % | Pisada/golpe 300 N sobre la tapa [SUPUESTO]; sin cargas de mando (van a P1-CTL-08) | Tapa sobre la cama (ranuras planas, sin soportes); ala arriba. 0,2 mm, 5 perímetros, 30 % giroide `print_rot=(180, 0, 0)` | 181×78×68 | 3,84 (Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta)) | [NO EJECUTADO] | 103 | 5,7 | — |
| P1-CTL-03 | soporte_kill | 1 | **estructural** 85 % | Tirón del cordón 150 N [SUPUESTO] + golpe de mano sobre la seta 200 N [SUPUESTO] | Base sobre la cama; la cara inclinada a 45° no necesita soportes. 0,2 mm, 5 perímetros `print_rot=(0, 0, 0)` | 100×130×55 | 4,21 (Cara PETG 10 mm: golpe sobre la seta 200 N [SUPUESTO] (cor…) | [NO EJECUTADO] | 120 | 6,7 | — |
| P1-ELE-01 | esc_stand | 1 | **sellado** 100 % | Peso del ESC + capota a 3 g vertical y 1 g lateral; tirón de cables | Base abierta sobre la cama; tablero arriba (puentes de 3,2 mm entre nervios, sin soportes). `print_rot=(0, 0, 0)` | 208×138×60 | 16,02 (Insertos M5 de la capota: apriete de las tiras de EPDM (so…) | no · print warning: Detected print stability issues: | 263 | 14,6 | 74,2 |
| P1-ELE-02 | esc_hood | 1 | **estructural** 85 % | Apriete de la almohadilla EPDM (4 × M5) y 3 g vertical del ESC hacia arriba (golpe de ola) | Techo sobre la cama, paredes y nervios hacia arriba (sin soportes). `print_rot=(180, 0, 0)` | 208×126×55 | 6,39 (Techo de la capota: reacción de las tiras de EPDM (sosteni…) | [NO EJECUTADO] | 207 | 11,5 | — |
| P1-INT-04 | tapa_inspeccion | 1 | **estructural** 100 % | Presión interna de la toma (succión de cierre / recuperación a 30 km/h) sobre Ø de la junta | Cara de la ranura del O-ring y del hexágono de la tuerca sobre la cama (fondos lisos), resalte arriba, 100 % relleno `print_rot=(0, 0, 0)` | 160×160×19 | 3,35 (Tapa: ciclo marcha ↔ punto fijo Δp = 42 kPa (olas/maniobras)) | [NO EJECUTADO] | 327 | 18,2 | — |
<!-- /FAB:orientacion -->

### 3.1 Soportes y avisos de PrusaSlicer

- PrusaSlicer 2.7.2 genera soporte automático (desde la cama, umbral 50°) en las piezas marcadas "sí". Lo que hay que mirar en la vista previa:
  - **Agujeros horizontales grandes** (tubo Ø40,3 en MNT-05, MNT-06 y STR-01; buje Ø24,25 en MNT-01; buje igus Ø18,0 a presión en STR-01; tubo de caña Ø30,2 en HSG-04, que no recibe soporte automático pero da aviso de voladizo): el arco superior es voladizo. Con soporte interior: quitarlo y repasar con lima/rasqueta hasta que entre la pieza metálica; la holgura real se calibra con **P1.1H**, que imprime esos mismos Ø acostados.
  - **Caja del ESC ("Collapsing overhang")**: son los rebajes Ø32 de los prensaestopas y el del respiradero, que no se pueden soportar desde la cama. El arco superior cae algo; la junta del prensaestopas apoya en la **cara plana anular**, que se repasa con un avellanador/fresa de refrentar o se alisa con epoxi (§5.4–5.5).
  - **Patín ("Floating bridge anchors, Loose extrusions, Long bridging extrusions")**: viene de la montura de las orejas del protector. Con soporte; verificar que **ningún soporte toca los flancos de la cintura** (dejaría marcas = entallas).
- Borde (*brim*) solo en piezas altas respecto de su huella: 5 mm si alto/lado menor > 2 y 8 mm si > 5 [SUPUESTO: regla práctica]; la probeta P1.5B (10×10×100 de pie) lleva 8 mm. Prusament declara que en general no hace falta borde [VERIFICADO: S1 "The brim is not necessary in general"].

### 3.2 Impresiones largas

- **MNT-01 (~1,8 kg, ~7 días) y MNT-05 (~1,1 kg, ~6 días)** superan una bobina de 1 kg: empezar con bobina nueva + una segunda **secada** a mano; cambio con `M600` (pausa a una altura en la vista previa) o con el sensor de fin de filamento si la impresora lo tiene [SUPUESTO: verificar en el menú de la S1].
- Antes de lanzar: boquilla limpia, malla ABL nueva (`G29`, `M500`), tensión de correas, tornillos de la cama, filamento seco en caja. Revisar la 1.ª capa entera y luego cada 12 h.
- Un corte de luz a mitad de pieza = pieza perdida salvo recuperación de impresión (si la S1 la tiene activada [SUPUESTO]); una pieza recuperada con escalón en la capa de corte **no se usa en estructural** (plano de debilidad entre capas).

---

## 4. Probetas P1.1–P1.8 (`04_diseno/probetas/`)

`python 04_diseno/probetas/build_probetas.py` construye todas (≈ 1,5 min), exporta STEP + STL en orientación de impresión a `step/` y `stl/` y escribe `probetas_manifest.json` con envolvente, masa, malla (trimesh: estanca, bobinado consistente, **1 cuerpo**), cotas verificadas y criterios con números. Cada módulo `PRB-P1.x_*.py` lee la geometría de los módulos de `04_diseno/piezas/` (no copia cotas): si cambia el diseño, cambian las probetas y sus criterios.

<!-- FAB:probetas -->
| Ensayo | Archivo (step/ y stl/) | Perfil (ajustes por objeto) | Cant. | Envolvente [mm] | g c/u | h c/u (PrusaSlicer) | Malla cerrada | Descripción |
|---|---|---|---|---|---|---|---|---|
| P1.1 | `P1.1A_peine_agujeros_12_20` | estructural (fill_density=100%, fill_pattern=rectilinear) | 1 | 154×164×8 | 77,8 | 7,3 | sí | Agujeros Ø(d+c) de eje vertical: Ø12, Ø15, Ø16, Ø18, Ø20; holguras +.15, +.20, +.25, +.30 mm + las del CAD por Ø |
| P1.1 | `P1.1B_peine_agujeros_24_40` | estructural (fill_density=100%, fill_pattern=rectilinear) | 1 | 197×185×8 | 92,6 | 8,1 | sí | Agujeros Ø(d+c) de eje vertical: Ø24, Ø25, Ø30, Ø40; holguras +.15, +.20, +.25, +.30 mm + las del CAD por Ø |
| P1.1 | `P1.1PA_peine_pernos_12_24` | estructural (fill_density=100%, fill_pattern=rectilinear) | 1 | 134×172×12 | 109,4 | 9,6 | sí | Pernos Ø(d−c) de eje vertical: Ø12, Ø15, Ø16, Ø18, Ø20, Ø24; holguras +.15, +.20, +.25, +.30 mm |
| P1.1 | `P1.1PB_peine_pernos_25_40` | estructural (fill_density=100%, fill_pattern=rectilinear) | 1 | 198×129×12 | 115,0 | 9,2 | sí | Pernos Ø(d−c) de eje vertical: Ø25, Ø30, Ø40; holguras +.15, +.20, +.25, +.30 mm |
| P1.1 | `P1.1H_agujeros_horizontales` | estructural (fill_density=100%, fill_pattern=rectilinear) | 1 | 181×104×57 | 147,1 | 15,1 | sí | Agujeros horizontales Ø(d+c) para Ø12, Ø24, Ø30, Ø40 (diámetros que las piezas reales imprimen acostados) |
| P1.2 | `P1.2_alojamiento_rodamiento` | estructural (fill_density=100%, fill_pattern=rectilinear) | 2 | 187×53×12 | 44,8 | 3,7 | sí | Asientos Ø35-.15/-.10/-.05/+.10 para 6202-2RS (15×35×11), pared 4.45 mm (= HSG-02), labio 1.5 mm |
| P1.3 | `P1.3_tuerca_cautiva_M6` | estructural (fill_density=90%) | 3 | 38×74×15 | 41,0 | 4,8 | sí | Recorte de P1-MNT-04 en el perno x=24 (ligamento mín. 6.8 mm), bolsillo transversal a h=18 mm, 10.4×5.8 mm; agarre Ø12.5 |
| P1.4 | `P1.4_inserto_M4` | sellado | 3 | 20×19×31 | 12,5 | 1,7 | sí | Recorte del reborde de P1-ELE-01 (RIM 18 mm, inserto de esquina a 5 mm del borde, ranura de O-ring vecina); agujero Ø5.6×9.1; pasador Ø8.4 |
| P1.5 | `P1.5A_barra_flexion_XY` | estructural (fill_density=100%, fill_pattern=rectilinear) | 6 | 100×10×11 | 12,7 | 1,0 | sí | Barra 10×10×100 acostada (rótulo fuera de la luz) |
| P1.5 | `P1.5B_barra_flexion_Z` | estructural (fill_density=100%, fill_pattern=rectilinear, brim_width=8) | 3 | 10×10×101 | 12,7 | 2,3 | sí | Barra 10×10×100 de pie (σ a través de capas) |
| P1.6 | `P1.6A_caja_oring` | sellado | 1 | 106×86×48 | 330,0 | 35,6 | sí | Caja 70×50×45 interior, reborde 18, ranura 2.65×4.74 (cordón 3.53 mm), 4 insertos M4, 1 prensaestopas M20, respiradero M12 |
| P1.6 | `P1.6B_tapa_prueba_impresa` | sellado | 1 | 106×86×7 | 69,2 | 8,6 | sí | Tapa plana impresa 106×86×6 SOLO DE PRUEBA (la real es Al 4 mm, ELE-02) y plantilla de taladrado |
| P1.7 | `P1.7A_cubo_absorcion_A` | estructural | 1 | 20×20×21 | 8,6 | 0,8 | sí | Cubo 20 mm rotulado A |
| P1.7 | `P1.7B_cubo_absorcion_B` | estructural | 1 | 20×20×21 | 8,6 | 0,8 | sí | Cubo 20 mm rotulado B |
| P1.7 | `P1.7C_cubo_absorcion_C` | estructural | 1 | 20×20×21 | 8,6 | 0,8 | sí | Cubo 20 mm rotulado C |
| P1.8 | `P1.8_cuello_patin` | fusible | 6 | 39×140×13 | 59,7 | 4,2 | sí | Lengüeta + cintura 21.67×12 mm del patín real + brazo; carga a 110.4 mm de la sección de referencia (agujero Ø8.5) |
<!-- /FAB:probetas -->

### 4.1 Criterios pasa / no-pasa (generado; coherente con PENDIENTES_GASPAR §P1)

<!-- FAB:criterios -->
| Ensayo | Qué se mide | Pasa si | Predicción / referencia | Fuente del umbral |
|---|---|---|---|---|
| P1.1 | holgura deslizante sin juego | elegir entre 0,15, 0,20, 0,25, 0,30 mm (CAD hoy 0,25) | — | PENDIENTES §P1.1 |
| P1.2 | 6202-2RS (15×35×11): asiento a presión / deslizante | Ø35 -0,15, -0,10, -0,05 (presión); 0,10 (HSG-02) | pared 4,45 mm = HSG-02 | PENDIENTES §P1.2 |
| P1.3 | arranque de tuerca M6 en bolsillo transversal | ≥ 1 816 N (= 3 × 605 N); PENDIENTES pide ≥ 2 100 N → usar el mayor | apoyo bajo tuerca ≈ 2 462 N; corte ≈ 11 844 N [ESTIMADO] | estructural.json + R05 S1 |
| P1.4 | arranque de inserto M4 inox (reborde ELE-01) | ≥ 662 N (= 3 × 220 N); PENDIENTES ≥ 600 N | PEM M4 en ABS inyectado 912–1646 N [VERIFICADO: R05 S29] | estructural.json |
| P1.5 | flexión 3 puntos, luz 80 mm | σ_mojada/σ_seca ≥ f_water; σ_Z/σ_XY ≥ f_z | XY seca ≥ 392 N, mojada ≥ 294 N, Z ≥ 150 N [ESTIMADO: piso] | inputs.yaml materials |
| P1.6 | estanqueidad 24 h a 0,5 m (4,9 kPa) | papel tisú seco, 0 gotas | ranura 2,65×4,74 mm; cordón 3,53 mm × 279 mm; planitud ≤ 0,10 mm | R05 B3 (Parker) |
| P1.7 | absorción 7 días, 25 g/L | ganancia ≤ 1 % | PETG macizo ~0,3 % [VERIFICADO: R05 S11] | PENDIENTES §P1.7 |
| P1.8 | rotura del cuello 21,67×12 mm, brazo 110,4 mm | 200–400 N (mojadas) | mojada ≈ 290 N, seca ≈ 386 N [CALCULADO] | PENDIENTES §P1.8 + params |
<!-- /FAB:criterios -->

**Diferencias con PENDIENTES_GASPAR §P1 (no se edita desde aquí):** (1) P1.2 cita el 6002 Ø32; el diseño vigente es el **6202-2RS Ø35** (`inputs.yaml → bearings`, decisiones D-37) y la probeta lo sigue; (2) P1.3 cita ≥ 2,1 kN (FS 3 sobre 701 N de una versión anterior); `estructural.json` da hoy 605 N → 1,82 kN; **aprobar con el mayor**; (3) PENDIENTES dice "imprimir con el perfil estructural": cada probeta va con el perfil de **su** pieza (P1.4/P1.6 sellado, P1.8 fusible), si no el ensayo no la representa.

### 4.2 Banco de ensayo con el dinamómetro

- **Palanca 5:1** para tracción > rango del dinamómetro: listón de madera dura 45×95×800 mm con perno M10 de pivote en un extremo, probeta colgada a 100 mm del pivote, dinamómetro a 500 mm, tirando hacia arriba. F_probeta = 5 · F_dinamómetro − tara [CALCULADO: momentos respecto del pivote]; la tara se mide con la probeta desenganchada. Con un dinamómetro de 50 kg se llega a ≈ 2,4 kN.
- **Balde que se llena de agua** (flexión P1.5, cuello P1.8): carga lenta y continua; el dinamómetro en serie lee la fuerza; anotar el máximo (o pesar el balde al romper).
- Velocidad ~10 N/s; 3 probetas por condición; anotar F máx., dónde rompe y foto de la fractura.

### 4.3 Procedimiento por probeta

- **P1.1 holguras.** Agujeros de eje vertical **A/B** (Ø d + c) y horizontales **H**; pernos impresos **PA/PB** (Ø d − c). Las filas incluyen las holguras base 0,15/0,20/0,25/0,30 **y todas las que el CAD usa para ese Ø** (escaneo de las piezas, tabla §4.4: p. ej. Ø18 −0,05/0,00 de los bujes igus, Ø12 +0,10 del perno de basculación). Probar con la **pieza metálica real** o vástagos de broca como pernos patrón; medir los pernos impresos con calibre (error exterior → `xy_size_compensation` si supera ±0,10 mm [SUPUESTO]). Resultado → `inputs.yaml geometry.clearance_mm` (y las holguras horizontales, si difieren, a quien mantenga MNT-05/STR-01).
- **P1.2 alojamiento de rodamiento.** 3 asientos a presión (−0,15/−0,10/−0,05) y el deslizante de HSG-02 (+0,10, rodamiento B flotante), pared 4,45 mm = pared mínima real de HSG-02 (escaneada), labio de 1,5 mm para hacer tope y sacarlo empujando el aro exterior. Prensar con prensa de banco o tornillo + arandelas, **nunca a martillo**; revisar a las 24 h (creep) que el aro no gire y que no haya blanqueo. Resultado → `geometry.press_fit_mm`.
- **P1.3 tuerca cautiva M6.** Recorte de la mejilla MNT-04 en el perno con el **ligamento lateral más delgado (6,8 mm)**, bolsillo transversal a **h = 18 mm** (leído del sólido = h de `structural.py`), agarre Ø12,5. Varilla M6 A4 desde la cara de apoyo hasta la tuerca (rosca completa), agarre con perno M12 como pasador. El bolsillo **transversal** es la variante débil del ensayo de CNC Kitchen (86 kg contra 166 kg del bolsillo de fondo, en M3) [VERIFICADO: research/R05 S27] y la estimación de aplastamiento bajo la tuerca (~2,5 kN [ESTIMADO]) está cerca del umbral: si falla por hundimiento de la tuerca, la corrección es en MNT-04 (bolsillo más alto para una arandela inox M6, o tuerca con brida). Con el F medido sale el **torque admisible** de los M6: T = K·d·F_arranque/FS = 0,2 × 0,006 m × F/3 [CALCULADO: T = K·d·F; K ≈ 0,2 rosca seca, ESTIMADO] (≈ 0,8 N·m con 2,1 kN).
- **P1.4 inserto M4 inox.** Recorte de la **esquina** del reborde de ELE-01 (dos bordes a 5 mm: el caso más desfavorable), con la ranura del O-ring al lado; agujero `INSERT_HOLE[4]` = 5,6 mm × 9,1 mm (inserto + 1 mm, como pide S28). Instalar como §5.3; tirar con tornillo M4 + cáncamo y pasador M8 abajo. Además, torque de giro con llave o brazo + dinamómetro.
- **P1.5 flexión.** Barras XY (×6: 3 secas, 3 tras 7 días en agua con 25 g/L de sal) y Z (×3, de pie con borde 8 mm). Apoyos: 2 pernos Ø10 a 80 mm sobre una tabla; carga central con lazo de cable. σ_f = 3·F·S/(2·b·h²) [CALCULADO]. Resultado → `materials.design_factors.f_water` (pérdida) y `f_z` (σ_Z/σ_XY).
- **P1.6 caja estanca.** Caja reducida 70×50 de ELE-01 con **el mismo reborde, la misma ranura (2,65 × 4,74 mm)**, el mismo piso, la misma altura del prensaestopas M20 y el mismo respiradero, con insertos solo en las esquinas: la luz entre insertos (96 mm) es ≥ la mayor de ELE-01 (93 mm). Tapa impresa **solo de prueba** (y plantilla para taladrar la de Al 106×86×4 con 4 agujeros Ø4,4); la que cuenta es la de **Al**. Antes: ranura 2,57–2,72 × 4,50–4,75 mm [VERIFICADO: R05 B3] con calibre, planitud ≤ 0,10 mm con regla y galgas. O-ring de cordón NBR70 3,53 mm con empalme a tope (largo en §4.1) y **grasa de silicona** (nunca grasa mineral con EPDM [VERIFICADO: S24]). Prensaestopas M20 con un trozo de cable de punta sellada con termocontraíble con adhesivo. Papel tisú adentro, lastre (la caja flota). Secuencia: 30 min a 0,3 m → 24 h a 0,5 m (4,9 kPa) → 20 ciclos abrir/cerrar → 30 min a 0,3 m. Si gotea, repetir con tapones ciegos (M12 y M20) para separar O-ring, respiradero y prensaestopas. Atención a las **esquinas vivas** de la ranura (iguales a ELE-01): si el cordón se levanta ahí, el arreglo es redondear la isla de la ranura en ELE-01.
- **P1.7 absorción.** Cubos A/B/C con el perfil estructural **base** (85 % gyroid, sin modificador: poros reales). Acondicionar 48 h con desecante (no secar a 65 °C), pesar m0 (0,01 g), 7 días en agua con 25 g/L, secar la superficie y pesar en < 1 min. Seguir a 30 días si se quiere la saturación (semanas, research/R05 A2).
- **P1.8 cuello del patín.** Recorte del patín real (lengüeta con sus 2 agujeros + cintura 21,67 × 12 mm) + brazo con agujero de carga a **skeg_neck_lever = 110,4 mm** de la sección de referencia. La lengüeta entre dos pletinas de acero con 2 M6, bordes a ras de la raíz (como en la ranura de STR-01). Tirar en el plano de la probeta, perpendicular al brazo. La raíz de la cintura está 4 mm por encima de `skeg_neck_v`: el momento allí es 3,6 % mayor y rompe ahí (predicción en §4.1). Si la media mojada F̄ cae fuera de 200–400 N: L_nueva = L·√(300/F̄) [CALCULADO: σ ∝ F/L²] vía `inputs.yaml`, regenerar y repetir.

**Orden sugerido** (los ensayos de 7 días primero): cama 1 = P1.5A ×6 + P1.5B ×3 + P1.7 ×3 → a remojo; cama 2 = P1.3 ×3 + P1.4 ×3 (sellado: otra cama); cama 3 = P1.1 (A, B, PA, PB, H); cama 4 = P1.2 ×2; P1.8 ×3 junto con el patín + P1.8 ×3 a remojo; P1.6 al final (la más larga), antes de imprimir ELE-01.

### 4.4 Ajustes que usa el CAD (escaneo de las piezas impresas en orientación de impresión)

<!-- FAB:ajustes -->
| Pieza | Nominal (metal/POM) | Ø en CAD [mm] | Holgura CAD [mm] | Eje en impresión | Se calibra con |
|---|---|---|---|---|---|
| P1-ELE-04 | Ø12 | 12,40 | +0,40 | horizontal | pasante de perno (no es ajuste) |
| P1-MNT-01 | Ø12 | 12,40 | +0,40 | horizontal | pasante de perno (no es ajuste) |
| P1-MNT-04 | Ø12 | 12,10 | +0,10 | vertical | P1.1A/B (vertical) |
| P1-MNT-03 | Ø16 | 16,40 | +0,40 | vertical | pasante de perno (no es ajuste) |
| P1-DRV-02 | Ø18 | 17,95 | -0,05 | vertical | ajuste a presión: fila Ø18 de P1.1A/B |
| P1-STR-01 | Ø18 | 18,00 | +0,00 | horizontal | ajuste a presión: fila Ø18 de P1.1H |
| P1-MNT-05 | Ø20 | 20,30 | +0,30 | vertical | P1.1A/B (vertical) |
| P1-MNT-01 | Ø24 | 24,25 | +0,25 | horizontal | P1.1H (horizontal) |
| P1-ELE-03 | Ø30 | 30,40 | +0,40 | vertical | pasante de perno (no es ajuste) |
| P1-ELE-04 | Ø30 | 30,30 | +0,30 | vertical | P1.1A/B (vertical) |
| P1-HSG-04 | Ø30 | 30,20 | +0,20 | horizontal | P1.1H (horizontal) |
| P1-SAF-01 | Ø30 | 30,30 | +0,30 | vertical | P1.1A/B (vertical) |
| P1-MNT-05 | Ø40 | 40,30 | +0,30 | horizontal | P1.1H (horizontal) |
| P1-MNT-06 | Ø40 | 40,30 | +0,30 | horizontal | P1.1H (horizontal) |
| P1-STR-01 | Ø40 | 40,30 | +0,30 | horizontal | P1.1H (horizontal) |
<!-- /FAB:ajustes -->

---

## 5. Post-procesado

### 5.1 Al sacar de la cama

Esperar la cama fría; quitar soportes y borde; repasar la pata de elefante (compensada 0,2 mm en el perfil). **Rechazo:** capas separadas o fisura visible, alabeo > 0,5 mm en caras de apoyo [SUPUESTO], huecos en paredes (sub-extrusión), escalón por corte de luz en piezas estructurales.

### 5.2 Tuercas cautivas A4 (unión estándar)

La tuerca A4 en bolsillo es la unión más fuerte del ensayo de PETG de CNC Kitchen (166 kg, contra 119 kg del inserto térmico, en M3) y es del mismo metal que el tornillo [VERIFICADO: research/R05 A10, S27]. Mapa de bolsillos en el CAD:

<!-- FAB:roscas -->
| Pieza | Tipo | Rosca | Comentario en el CAD |
|---|---|---|---|
| P1-ELE-01 | inserto térmico (agujero Ø 6,4 mm) | ver comentario | nervios exteriores para la capota (insertos M5 arriba) |
| P1-INT-04 | tuerca cautiva, bolsillo hexagonal | M6 A4 (ISO 4032: 10 e/c) | purga: resalte arriba, hexágono de tuerca M6 desde abajo, agujero Ø6,4 |
| P1-INT-04 | tuerca cautiva, bolsillo transversal/lateral | M6 A4 (ISO 4032: 10 e/c) | purga: resalte arriba, hexágono de tuerca M6 desde abajo, agujero Ø6,4 |
<!-- /FAB:roscas -->

- Tuercas **ISO 4032 A4** (entrecaras de `cadlib.NUT_AF`). Bolsillos hexagonales: tirar la tuerca hacia adentro con un tornillo + arandela desde el lado opuesto (no a martillo). Bolsillos transversales: deslizarla y centrarla con el tornillo.
- **Torques de partida sobre PETG:** M3 0,5 · M4 1,0 · M5 2,0 N·m [ESTIMADO: research/R05 A10.3, ~50 % del torque de falla]; **M6 en tuerca cautiva: ≤ K·d·F_P1.3/3** (§4.3). Donde haga falta conservar precarga: casquillo limitador metálico (research/R05 A5).
- Fijación de la rosca: **tuerca autoblocante (nyloc) A4** o **Loctite 425** (cianoacrilato de baja resistencia "for locking metal and plastics fasteners" [VERIFICADO: S32]). **Nada de Loctite 243 ni anaeróbicos sobre PETG** ("not normally recommended for use on plastics … stress cracking" [VERIFICADO: S31]); el 243 solo en rosca metal-metal donde no pueda chorrear sobre el plástico.

### 5.3 Insertos térmicos de inox (solo donde el CAD los pide)

- Solo: **8 × M4 de la tapa de ELE-01** (zona seca, acceso de un lado) y el **M8 del cáncamo de MNT-05** (zona mojada → inox obligatorio). Ningún inserto de **latón** en zona mojada: descincificación con Zn > ~15 % [VERIFICADO: research/R05 A10.2, S30]; existen insertos de inox 300 pasivado [VERIFICADO: S29].
- Instalación: soldador con punta de insertos a **~250–260 °C** (el inox conduce peor que el latón; 245 °C es lo que S28 da para latón en PETG) [ESTIMADO: research/R05 A10.3]; agujero 1 mm más profundo que el inserto (el CAD ya lo trae) y hundir el 90 % con la punta y el último tramo con una herramienta plana fría [VERIFICADO: S28]; comprobar perpendicularidad con un tornillo largo y escuadra. **Pasa si:** a ras ±0,2 mm, sin inclinación visible, sin rebaba ni fisura alrededor (lupa 10×) [SUPUESTO]. Validar el proceso con P1.4 antes de tocar ELE-01.

### 5.4 Caras de sello: refrentado y lijado

- **Por qué:** sello estático pide Ra ≤ 0,8 µm (Parker) o ≤ 1,6 µm (Trelleborg) [VERIFICADO: S24, S26]; la cara impresa tiene Sa 10–24 µm [VERIFICADO: S18]. Las marcas de torno **circunferenciales** sellan aun rugosas; las transversales no [VERIFICADO: S24].
- **Torno:** refrentar con herramienta de HSS afilada, baja velocidad y pasadas de 0,05–0,1 mm, sin calentar el PETG [ESTIMADO]. La cara de ELE-01 (196 × 174 mm, diagonal ≈ 262 mm) solo entra si el volteo del torno es ≥ 270 mm en plato de 4 garras o plato liso [SUPUESTO: volteo desconocido]; la P1.6 (106 × 86, diagonal 137 mm) sirve para ensayar el proceso. Rebajes de prensaestopas Ø32: **refrentador / avellanador plano** en el taladro de columna.
- **Sin torno:** lapear sobre vidrio con lija al agua P240 → P400 → P600 en "ochos", controlando planitud con regla y galgas: **≤ 0,10 mm** (±0,15 mm de profundidad ya lleva la compresión a 21–29 %) [CALCULADO: research/R05 B3].
- Después de mecanizar: profundidad de ranura **2,57–2,72 mm** y ancho **4,50–4,75 mm** con calibre [VERIFICADO: R05 B3, Parker 4-3]. Si la profundidad quedó corta por el lijado de la cara, corregir el fondo, no la cara.

### 5.5 Epoxi (opcional, solo piezas frías)

| Producto | Datos | Uso en P1 |
|---|---|---|
| West System 105/205 | **HDT 48 °C**, Tg 54–61 °C, 54,5 MPa [VERIFICADO: S21] | Interior de ELE-01 y caras de prensaestopas; **nunca** en la cara que toca la tapa-disipador (la tapa puede llegar a 50 °C, PENDIENTES P2.3) ni cerca del motor |
| Smooth-On XTC-3D | Capa < 0,4 mm, Shore 80D, "works with … PetG" [VERIFICADO: S20] | Alisar antes de lijar |

Sustrato con ≥ 4 perímetros y ≥ 60 % de relleno (con 1–2 perímetros la capa "will most likely crack") [VERIFICADO: S22] → el perfil sellado cumple. Preparación: lijar P120–P180 y limpiar con IPA:agua 50:50 [VERIFICADO: S34]. Epoxi de laminado/recubrimiento marino, no de 5 minutos [ESTIMADO: research/R05 A9.2]. No hay dato verificado de adhesión epoxi–PETG impreso: si se usa, ensayarla en una probeta P1.6 extra.

### 5.6 Compatibilidad química con PETG (adhesivos, selladores, fijadores, limpieza)

| Producto | Veredicto | Evidencia |
|---|---|---|
| Loctite 243 y anaeróbicos | **No** sobre PETG (agrietamiento por tensión) | [VERIFICADO: S31] |
| Loctite 425 (CA de baja resistencia para fijar tornillos) | Sí, poca cantidad, quitar el exceso | [VERIFICADO: S32]; algunos CA debilitan el PETG [VERIFICADO: S35] → probar la marca en un retazo |
| Cianoacrilato (pegado) | Compatible con PET y PETG según Henkel/Eastman | [VERIFICADO: S33, S34] |
| Epoxi 2K (p. ej. 3M DP-100) | Recomendada para PETG | [VERIFICADO: S34] |
| PU 2K / Sikaflex-291i | PU: el más fuerte en el ensayo de PETG; Sikaflex resiste agua de mar, prohibido en PMMA/PC; PETG no figura → probar en retazo con tensión | [VERIFICADO: S34, S35, S36] |
| Silicona RTV | Solo como junta, no como adhesivo; preferir curado neutro | [ESTIMADO: research/R05 A11] |
| Grasa de silicona | Compatible con NBR/EPDM/FKM; PETG "oils and grease: good" | [VERIFICADO: S24, S2] |
| Grasa/aceite mineral | No sumergir PETG (−16,9 % de tracción en 7 días); **nunca** con O-rings de EPDM | [VERIFICADO: S43, S24] |
| Tef-Gel (roscas inox–Al) | Aislar pares galvánicos | [VERIFICADO: research/R06 §galvánica] |
| Acetona, MEK, THF, cloruro de metileno | **Prohibidos**: disuelven el PETG | [VERIFICADO: S34] |
| **Limpieza** | **IPA:agua 50:50** | [VERIFICADO: S34] |

### 5.7 Limpieza

IPA:agua 50:50 con paño sin pelusa para quitar grasa de manos y pegamento de la cama antes de pegar, sellar o instalar O-rings; nunca acetona (§5.6). Enjuague con agua dulce después de cada salida (research/R05 A12).

### 5.8 Inspección de fisuras

| Cuándo | Qué | Rechazo |
|---|---|---|
| Al imprimir | Todo, lupa 10× en bolsillos de tuerca, insertos, alojamientos a presión, cintura del patín | Fisura, capa abierta, blanqueo |
| Tras prensar / apretar | Alojamientos de rodamiento y bujes, insertos, bolsillos | Blanqueo o fisura = cambiar la pieza |
| Antes de cada salida | Abrazadera, horquilla, cuna, carcasa inferior, patín y protector | Cualquier fisura en la ruta de carga = no salir |
| Mensual | **Protector y patín** (fatiga a ~50 Hz, research/R05 A6: una hélice de PETG se fisuró a los 4 meses en agua de mar, R02/R03) | Fisura = reemplazar el segmento |
| Tras un golpe o varada | Patín (debe haber roto él), tubo, cuna | Patín roto = reemplazar con uno de la **misma tanda** que su testigo P1.8 |

### 5.9 Boquilla

Latón 0,4 para todo P1 (PETG). **Boquilla endurecida solo si P2 usa fibra** (PETG-CF: la de latón dura ~9 h [VERIFICADO: research/R05 A1, S4/S8–S10]); PA-CF y PC no son imprimibles en esta máquina (280–300 °C y cámara caliente) [VERIFICADO: R05 A1].

---

## 6. Tiempos y gramos totales

<!-- FAB:totales -->
| Conjunto | Impresiones | g (CAD × solid_frac) | g (PrusaSlicer) | h (18 g/h, inputs.yaml) | h (PrusaSlicer) |
|---|---|---|---|---|---|
| Piezas P1 (19 tipos) | 5 | 1 020 | 5 946 | 57 | 603 |
| Probetas P1.1–P1.8 | 33 | 1 690 | 1 712 | 94 | 161 |
| **Total** |  | **2 710** | **7 658** | **151** | **764** |

Bobinas de 1 kg a comprar: **10** [CALCULADO: máx(g) × 1.30 de purga, fallas y reimpresiones (= bom.py)]. Laminado: PrusaSlicer-2.7.2+UNKNOWN based on Slic3r (with GUI support), perfiles y ajustes por objeto de esta página, sin soportes (con soportes automáticos suma 26 g). El ritmo real de las piezas es **9,9 g/h**, no los 18 g/h de inputs.yaml (printer.print_rate_g_h): 6 perímetros y velocidades moderadas. Corregir ese valor en inputs.yaml para el plan de impresión.
<!-- /FAB:totales -->

Totales del CAD (manifest): <!--V:manifest.totals.printed_mass_g:.0f-->1020<!--/V--> g y <!--V:manifest.totals.printed_hours:.0f-->57<!--/V--> h a 18 g/h. Todas las piezas entran en la zona útil 210 × 210 × 260 (verificado en `build_all.py` y `build_probetas.py`).

---

## 7. Scripts y cómo regenerar

```bash
python 04_diseno/probetas/build_probetas.py          # probetas: STEP + STL + probetas_manifest.json (exit ≠ 0 si falla)
python prusaslicer/validar_perfiles.py               # perfiles: formato, límites, claves, laminado (≈ 5 min)
python 04_diseno/probetas/tabla_fabricacion.py       # tablas FAB de este documento
python -m pytest tests/test_probetas.py -q           # manifold, envolvente, claves críticas de los .ini
```

---

## 8. Hallazgos para el diseño (de esta pasada de fabricación)

1. **Ritmo de impresión:** `inputs.yaml printer.print_rate_g_h = 18` subestima el tiempo ~2× (PrusaSlicer: ~10 g/h con estos perfiles). Afecta el plan, no la masa.
2. **MNT-01 y MNT-05 > 1 kg cada una** (cambio de bobina a mitad de pieza; 6–7 días) — riesgo de pieza perdida; evaluar partirlas o bajar su relleno solo si `structural.py` lo permite.
3. **HSG-02:** el asiento del rodamiento B (B + 2,5 = 13,5 mm desde la cara de popa) **atraviesa** el puente de 12 mm: el "labio delantero" del comentario no existe en el sólido (el rodamiento B no tiene tope axial en el puente).
4. **ELE-01:** ranura de O-ring rectangular con **esquinas vivas** en la isla; P1.6 las reproduce para ver si el cordón se levanta.
5. **Agujeros horizontales Ø40,3 / Ø30,2 / Ø24,25 / Ø18,0 (buje igus a presión en STR-01) / Ø12,4** se imprimen acostados (voladizo arriba) y 8 piezas reciben soporte automático: P1.1H calibra esas holguras por separado de las verticales.
6. **PENDIENTES §P1.2/§P1.3** desactualizados (6002 → 6202; 701 N → 605 N): ver §4.1.
