# PROYECTO: Propulsión eléctrica con piezas impresas en 3D para mini lancha de aluminio — Prototipo P1

## 0. Modo de ejecución: AUTÓNOMO DE PUNTA A PUNTA
Trabajás sin supervisión durante una sesión larga (~10 h). Nadie va a responder preguntas ni aprobar pasos. Reglas no negociables:

1. **Nunca te detengas a preguntar ni a pedir confirmación.** No termines el turno hasta cumplir la Definición de terminado (sección 9).
2. **Datos faltantes:** primero investigá (web, catálogos, datasheets); si no hay fuente, inferí con criterio de ingeniería y elegí el valor **conservador** (el que da más seguridad). Registrá cada decisión en `decisiones.md`: decisión, alternativas, justificación, etiqueta y qué cambia si el dato real difiere.
3. **Diseñá para un rango, no para un punto.** Si un dato de la lancha es incierto, cubrí un rango razonable (p. ej. abrazadera de popa ajustable a varios espesores) y dejá todo parametrizado.
4. **Tres pasadas, en este orden:**
   - **Pasada 1 — Funcional de punta a punta.** Todos los entregables existen en versión mínima y todos los scripts corren sin error (sizing → CAD → STEP/STL → verificación → BOM). Si la sesión se corta, queda algo completo y usable.
   - **Pasada 2 — Profundidad.** Investigación completa, cálculos refinados, FEA, electrónica y firmware, fabricación, pruebas, FMEA, renders.
   - **Pasada 3 — Auditoría adversarial.** Revisá todo como un revisor que busca romperlo: errores de cálculo, unidades, incoherencias entre documentos y código, FS insuficientes, piezas no imprimibles o no ensamblables, riesgos de seguridad. Corregí y documentá en `auditoria.md`. Repetí hasta no encontrar problemas relevantes.
5. **Persistencia:**
   - Mantené `PROGRESS.md` con la checklist de hitos y su estado.
   - Tras cada hito: actualizá `PROGRESS.md`, hacé `git commit` y `git push` a tu rama de trabajo. Nunca acumules horas sin commitear.
   - Si tu contexto se compacta o se reinicia, antes de seguir releé `PROMPT.md` (guardá este prompt ahí al empezar), `PROGRESS.md`, `decisiones.md` e `inputs.yaml`.
6. **Bloqueos:** si falta una herramienta, instalala (`pip install ...`); si no se puede, usá una alternativa; si no hay, documentalo y seguí con otra cosa. Nunca esperes, nunca hagas polling ni `sleep`.
7. **Paralelismo:** si tu entorno permite subagentes, usalos para la investigación (videos, proyectos comparables, materiales, sellado, normativa) mientras avanzás con los cálculos.
8. **Acciones físicas** (imprimir probetas, medir el bote, probar en el agua) no bloquean: van a `PENDIENTES_GASPAR.md`, ordenadas y con criterio pasa/no-pasa.
9. **Si dos opciones son viables,** desarrollá la recomendada completa y la alternativa como concepto documentado (plan B).

## 1. Rol y reglas de rigor
Actuá como ingeniero senior en propulsión marina eléctrica de baja potencia (< 5 kW), diseño para fabricación aditiva FDM y seguridad eléctrica y de baterías en embarcaciones pequeñas. El destinatario es estudiante de último año de Ingeniería Mecatrónica: sin fundamentos; ecuaciones, entradas, resultados, supuestos y fuentes.

- El sistema se usa en el mar con personas a bordo: la seguridad manda sobre el alcance. Si un requisito es inviable o inseguro, decilo con números y adoptá la alternativa segura.
- Todo número que influya en el diseño lleva etiqueta: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO].
- Prohibido inventar contenido de videos no vistos, números de pieza, links, precios o propiedades de materiales. Sin fuente → [ESTIMADO] con base explícita. Links solo si los abriste en esta sesión; si no, "buscar: <términos>".
- Contrastá cada resultado clave con un orden de magnitud o una referencia real (p. ej. empuje y consumo de trolling motors comerciales).
- Unidades SI; geometría en mm.
- Ejecutá y verificá todo script. Lo que no pudiste ejecutar se marca [NO EJECUTADO] con el motivo.
- Densidad antes que volumen: sin texto genérico. Tablas para datos estructurados; prosa y viñetas para el razonamiento.

## 2. Objetivo
Diseñar y dejar listo para fabricar y validar el prototipo P1 del sistema de propulsión de la mini lancha de Jorge, para uso real en el mar.
- Se imprime en PETG todo lo que sea razonable imprimir.
- Se compra lo que no: motor, ESC, batería, eje, rodamientos, herrajes y, si el cálculo lo exige, la hélice o el impulsor.
- P1 es un prototipo funcional y seguro, a validar con pruebas escalonadas; no un modelo de exhibición.

Comparación de referencia: un motor eléctrico comercial (trolling motor apto para agua salada) resuelve el problema comprándolo. P1 se justifica solo si aporta algo concreto (costo, adaptación, reparabilidad, aprendizaje) sin perder seguridad. Compará contra esa referencia y decí honestamente si conviene.

## 3. Datos de entrada (confirmados por el usuario)
Todos los valores finales, firmes o inferidos, van a `inputs.yaml`: es la **única fuente de entradas** y todo el proyecto se regenera desde ahí.

Embarcación
- Bote de **aluminio de fondo plano** (tipo jon boat), **eslora < 2,5 m**. Manga, peso en vacío, geometría y espejo de popa: investigá jon boats de aluminio de ese tamaño y diseñá para el rango (altura del espejo para elegir el largo de pata, espesor del espejo para la abrazadera; típicamente aluminio con refuerzo de madera, a verificar).
- **2 personas a bordo** (usá una masa conservadora por persona + equipo de seguridad + batería).

Operación
- Zona: **Dinamarca, Sønderborg (Als Fjord / Mar Báltico)**. Investigá la salinidad (agua salobre del Báltico occidental), la temperatura del agua por estación y la normativa danesa aplicable (registro, límites de potencia o velocidad, chaleco, kill cord): todo "a confirmar con la autoridad local".
- **Distancia máxima a la costa < 300 m.**
- Velocidad y autonomía. Prioridad del usuario: **autonomía + costo**.
  - Crucero ≈ velocidad de casco (~6 km/h, verificalo) durante **≥ 2 h**.
  - **8–12 km/h solo como velocidad máxima por ratos**; cuantificá cuánto tiempo se sostiene.
  - Entregá la curva de compromiso velocidad–autonomía–costo y justificá el punto elegido.
- **Marcha atrás obligatoria** (ESC bidireccional).
- **Aguas poco profundas y arena:** basculación (kick-up) obligatoria, protección de hélice y pasador de corte.

Recursos
- Presupuesto: **sin cifra; minimizá el costo** sin comprometer la seguridad y reportá el total.
- Componentes existentes: **ninguno**, todo se compra.
- Herramientas: **taladro + machos de roscar, soldador + multímetro, torno, dinamómetro.** El torno permite mecanizar eje, bujes o acoples: aprovechalo donde mejore la seguridad o la durabilidad.

Videos de referencia (sin notas del usuario)
- V1: https://youtu.be/Z41FAXVMdKs — su título indica un turbojet impreso en 3D para un bote pequeño.
- V2: https://youtu.be/CkUiNuAfPL8 — su título indica un waterjet impreso en 3D para un bote.
Intentá acceder (título, descripción, transcripción, comentarios, artículos que los citen). Lo que no puedas verificar va como "no verificado".

Fabricación (fijo)
- Impresora Creality Ender-3 S1: volumen útil por pieza ≤ 210 × 210 × 260 mm; hotend máx. 260 °C; cama máx. 100 °C; boquilla de latón de 0,4 mm; cama PC; sin cerramiento.
- Slicer: PrusaSlicer. Material base: PETG. Se aceptan alternativas compatibles con 260 °C y sin cerramiento; los materiales con fibra exigen boquilla endurecida (en la BOM).

Software
- Python. Blender 5.1, solo visual: intentá `pip install bpy` para render sin interfaz gráfica; si no se puede, entregá scripts `bpy` [NO EJECUTADO] listos para correr localmente.

## 4. Restricciones de diseño

Generales
- Solo propulsión eléctrica. Combustión (turbojet incluido) excluida en P1: riesgo de incendio y el PETG ablanda a ~75–80 °C.
- Piezas impresas cerca del motor o el ESC: temperatura de servicio con margen claro respecto de la Tg del PETG; definí el límite.
- La unidad no se pierde si se suelta del espejo: cabo de seguridad o flotabilidad.
- Desmontable con herramienta común; protocolo de enjuague con agua dulce.

Estructura
- FS ≥ 3 en piezas impresas estructurales, con propiedades degradadas por anisotropía en Z, absorción de agua, creep y fatiga. Rutas de carga en el plano XY de impresión.
- Casos de carga mínimos: empuje máximo sostenido (avance y marcha atrás); torque de rotor trabado; golpe de la hélice contra un objeto; varada o impacto del pie en arena; ola y vibración (fatiga a la frecuencia de paso de pala); manipulación.
- Fusible mecánico: pasador de corte (shear pin) en la hélice y montaje basculante (kick-up) con retención en marcha atrás, para que un impacto rompa una pieza barata y prevista, no el espejo ni la carcasa.
- Ninguna unión estructural depende solo de adhesivo; las piezas divididas se unen con pasadores o encastres + tornillería.

Corrosión
- Casco de **aluminio en agua salobre**: los herrajes de inoxidable A4 (316) en contacto con el aluminio generan **corrosión galvánica**. Aislá (arandelas o bujes no conductivos, compuesto aislante tipo Tef-Gel o equivalente), evitá el cobre y el latón cerca del casco y evaluá ánodos de sacrificio (zinc o aluminio, según la salinidad).
- Descincificación de insertos de latón: alternativas (pasantes A4 + autoblocante, insertos inoxidables).

Eléctrico
- Tensión nominal ≤ 48 V salvo justificación. Guía: ISO 13297 / ABYC E-11 (citar solo lo verificado).
- Batería con BMS; comparar LiFePO4, Li-ion y LiPo por seguridad a bordo. Montaje fijo en caja estanca; analizar qué pasa si la lancha se inunda o vuelca. Considerá el peso de la batería en el trimado de un bote tan chico.
- Fusible principal junto al borne, desconexión principal y precarga si se usa contactor.
- Kill switch con cordón, fail-safe: cable cortado, conector suelto o pérdida de señal = motor detenido. Sin arranque si el acelerador no está en cero.

Propulsor
- Si una hélice o impulsor impreso no tiene margen a la potencia requerida, se compra comercial y se documenta.
- Protección de hélice obligatoria por el uso en aguas poco profundas (tobera o protector), con su efecto en el empuje cuantificado.

## 5. Contenido a producir (orden sugerido; sin pausas entre bloques)

5.1 Investigación → `01_investigacion.md`
- Videos V1 y V2: tipo de propulsión y escala, motor y potencia, materiales, sellado, montaje, rendimiento y fallas.
- ≥ 8 proyectos comparables (prioridad: escala tripulada y agua salada) de Printables, MakerWorld, Thingiverse, Cults3D, GitHub, foil.zone, Endless Sphere, RCGroups y papers. Cubrir: outboards impresos para kayak o dinghy, conversiones de trolling motor, waterjets impresos, hélices entubadas y rim-driven, eFoil. Por proyecto: link, escala, potencia, qué funcionó, qué falló, qué aplica a P1.
- Jon boats de aluminio < 2,5 m: dimensiones, pesos, altura y espesor de espejo típicos, potencia recomendada por fabricantes.
- PETG en agua salobre (absorción, UV, creep, fatiga) vs ASA, PC, nylon-CF y epoxi.
- Sellado: O-rings según Parker O-Ring Handbook (ORD 5700) o ISO 3601, considerando el acabado alcanzable en FDM; retenes, prensaestopas; motor inundado vs seco sellado vs acople magnético.
- BLDC en agua salada: inrunner vs outrunner, recubrimientos, rodamientos; ESC bidireccionales y refrigerados por agua.
- Normativa danesa (ver sección 3).
- Cierre: "hallazgos que cambian el diseño".

5.2 Dimensionamiento → `02_calculos.md` + `sizing.py` (lee `inputs.yaml`; tabla de resultados; gráficos R(v), P(v), autonomía(v), costo vs autonomía)
- R(v) para casco plano chico con método justificado por régimen y Froude (incluí la zona de transición por encima de la velocidad de casco). Procedimiento de calibración: remolque con dinamómetro a velocidad conocida (a `PENDIENTES_GASPAR.md`).
- Empuje con margen por viento, olas y corriente. Bollard pull objetivo. Potencia al eje y eficiencia propulsiva por arquitectura.
- Hélice: diámetro, paso, rpm, cavitación (Burrill o Keller), efecto de la protección.
- Motor (KV, tensión, corriente continua y pico); ESC bidireccional con margen ≥ 30 %; batería (Wh para 2 h de crucero + 20 % de reserva, tasa C, masa, costo); cables por caída < 3 % y ampacidad; fusible.
- Térmico: disipación de motor y ESC, método de refrigeración.
- Mecánico: eje (torsión y flexión), rodamientos (axial = empuje en ambos sentidos), momento en el soporte de popa, tornillos e insertos, FS por cada caso de carga.
- Sensibilidad: las 3 entradas inciertas que más mueven el resultado.
- Criterios de éxito de P1 con números: bollard pull, velocidad de crucero y máxima con 2 personas, autonomía, estanqueidad tras inmersión, límites térmicos, corte de emergencia < 1 s.

5.3 Arquitectura → `03_arquitectura.md`
Matriz ponderada (pesos justificados + sensibilidad de pesos) entre: A outboard con hélice (motor seco sellado o inundado); B conversión de trolling motor; C waterjet; D hélice entubada o rim-driven; E propulsión aérea eléctrica (solo comparación); F motor comercial completo (referencia). Criterios: empuje y eficiencia en el rango objetivo, seguridad, viabilidad en PETG, sellado, corrosión, costo, tiempo, reparabilidad, aptitud para poca profundidad, consecuencia de falla en el mar. Salida: recomendada + plan B + "se imprime / se compra / se tornea" + 5 riesgos principales con mitigación.

5.4 Diseño detallado → `04_diseno/`
- Nomenclatura `P1-<SUB>-<NN>_<nombre>`, SUB ∈ {MNT, HSG, DRV, PRP, STR, ELE, SAF}, igual en archivos, objetos y colecciones de Blender.
- Lista de piezas: ID, función, envolvente, material, impresa, comprada o torneada, cantidad, caso de carga dominante, orientación de impresión, gramos y horas.
- Ajustes: holguras iniciales 0,2–0,3 mm (a confirmar con probeta), alojamientos de O-ring, asientos de rodamientos, uniones roscadas.
- CAD paramétrico con build123d (o CadQuery si lo justificás): `params.py` (deriva de `inputs.yaml` y del dimensionamiento), un script por pieza, `build_all.py`, export STEP + STL en mm. Planos acotados (PDF o SVG) de las piezas torneadas.
- `verify_parts.py`: envolvente ≤ 210 × 210 × 260 mm, malla manifold, volumen y masa, cotas críticas, sin interferencias en el ensamblaje (incluida la basculación completa del kick-up). Termina con exit code ≠ 0 si algo falla.
- Cálculo estructural a mano de todas las piezas. FEA de las 2–3 más críticas (FreeCAD FEM / CalculiX, o alternativa pip como gmsh + scikit-fem), con factores de reducción FDM explícitos.
- Blender, solo visual: ensamblaje, materiales, explosionada, renders ortográficos y en perspectiva, animación de montaje → `blender/`.

5.5 Electrónica y control → `04_diseno/electronica/`
- Diagrama de cableado y tabla de verdad del kill switch y la cadena de habilitación.
- Acelerador con marcha atrás (p. ej. sensor hall en la caña con zona muerta central, o MCU con rampa, límite de corriente, watchdog, failsafe y retardo en la inversión de sentido). Si hay firmware, entregalo con tests de su lógica en simulación.
- Estanqueidad de conectores y prensaestopas.

5.6 Fabricación → `05_fabricacion.md` + perfiles PrusaSlicer (`.ini`) por familia de pieza
- Probetas con criterio pasa/no-pasa, también diseñadas en CAD: tolerancias, pull-out de insertos y pasantes, caja estanca con O-ring (24 h), absorción en agua salada (7 días).
- Perfiles: temperaturas, velocidades, ventilador, perímetros, capas superiores e inferiores, relleno, costura, soportes, brim, adhesión en PC, secado del filamento.
- Orientación por pieza justificada por la carga. Post-procesado: insertos, epoxi, compatibilidad química de adhesivos, selladores y fijadores de rosca con PETG.

5.7 Ensamblaje y pruebas → `06_ensamblaje_y_pruebas.md` + `checklist_salida.md` (una página, imprimible)
- Secuencia de ensamblaje con torques para plástico [ESTIMADO, validar con probeta]; mapa de sellado y de aislamiento galvánico; conectores IP68; grasa dieléctrica; ánodos.
- Pruebas escalonadas pasa/no-pasa: T0 banco en seco · T1 estanqueidad · T2 tanque (bollard pull con el dinamómetro, consumo, temperaturas) · T3 agua dulce o puerto calmo, poco profundo, con remos y acompañante · T4 Als Fjord en calma a < 300 m de la costa con chaleco, remo, acompañante y temperatura del agua considerada · post-uso.
- FMEA de 10 modos de falla (S, O, D, RPN, mitigación).

5.8 Roadmap P2 → `07_roadmap_P2.md`: materiales (ASA, nylon-CF), mecanizado de piezas críticas, refrigeración, telemetría (V, I, T, rpm), potencia.

## 6. Estructura de archivos
```
README.md                 # resumen, arquitectura elegida, estado, cómo correr, qué está verificado y qué no
PROMPT.md                 # este prompt
PROGRESS.md               # checklist de hitos
decisiones.md             # registro de decisiones y supuestos
auditoria.md              # hallazgos de la pasada 3 y su resolución
PENDIENTES_GASPAR.md      # acciones físicas y datos a medir del bote real, en orden
inputs.yaml               # única fuente de entradas
run_all.py                # pipeline: sizing → CAD → export → verify → BOM → renders
requirements.txt
tests/                    # pytest
01_investigacion.md
02_calculos.md  sizing.py
03_arquitectura.md
04_diseno/                # params.py, piezas/, build_all.py, verify_parts.py, step/, stl/, planos/, electronica/
blender/                  # scripts bpy, renders
05_fabricacion.md  prusaslicer/
06_ensamblaje_y_pruebas.md  checklist_salida.md
bom.csv
07_roadmap_P2.md
```
BOM: ID, descripción, especificación técnica mínima (no solo marca), cantidad, proveedor con envío a Dinamarca y link verificado o "buscar: <términos>", precio [ESTIMADO] en EUR o DKK con fecha, y total.

## 7. Idioma y formato
Español. Markdown con encabezados y viñetas; tablas para datos estructurados. Código comentado donde aporte.

## 8. Honestidad sobre el alcance
"100 % funcional" se refiere al paquete de ingeniería: todo corre, todo es coherente y todo está verificado en software. La validación física (medidas reales del bote, probetas, estanqueidad, pruebas en agua) queda pendiente y debe decirse explícitamente. No declares nada como probado si no lo está.

## 9. Definición de terminado (verificar antes de cerrar)
- [ ] `pip install -r requirements.txt && python run_all.py` corre desde cero sin errores (exit code 0).
- [ ] `pytest` pasa (sanidad de sizing, consistencia de params, envolventes, que verify detecte fallas).
- [ ] Toda pieza impresa: STEP + STL, manifold, dentro de 210 × 210 × 260 mm, sin interferencias (incluida la basculación).
- [ ] Cambiar un valor en `inputs.yaml` (p. ej. espesor del espejo) y correr `run_all.py` regenera cálculos, geometría y BOM (probalo y documentalo).
- [ ] Cada caso de carga de la sección 4 tiene FS calculado; los < 3 están resueltos o justificados.
- [ ] Cada número de diseño está etiquetado; cada link fue abierto en esta sesión.
- [ ] Coherencia: los valores en los .md coinciden con los que produce el código.
- [ ] Pasada 3 completada; `auditoria.md` sin hallazgos críticos abiertos.
- [ ] README con: resumen ejecutivo (≤ 15 líneas), arquitectura elegida, comparación con el motor comercial, costo total, velocidad y autonomía esperadas, estado verificado / no verificado, próximos pasos físicos.
- [ ] Todo commiteado y pusheado.

Cuando todo esté tildado, hacé una última pasada de mejora sobre los puntos más débiles y terminá con un resumen final: qué se entregó, qué decidiste por inferencia, riesgos abiertos y los 5 primeros pasos físicos para Gaspar (empezando por medir el bote real y actualizar `inputs.yaml`).

Empezá ahora: guardá este prompt en `PROMPT.md`, creá `PROGRESS.md` y arrancá la Pasada 1.
