# PROGRESS — P1-J waterjet eléctrico para el jet boat de Jorge

Leyenda: [x] hecho · [~] en curso · [ ] pendiente

> **Cambio de alcance (2026-10-01, pedido del usuario):** el proyecto pasó de una cola larga eléctrica
> para un jon boat a un **waterjet eléctrico inboard** para el jet boat de 2,30 m de Jorge (D-01).
> Las tres pasadas se rehicieron para el waterjet; la versión anterior queda en git (`5dfada0`).

## Pasada 1 — Funcional de punta a punta (waterjet) ✅
- [x] Investigación nueva: R10b (plano de Jorge auditado), R11 (componentes y precios del jet), R12 (métodos de bomba, toma y planeo), R13 (normativa DK del jet)
- [x] inputs.yaml reescrito (casco, masas, waterjet, motor/ESC/batería, comparación, BOM)
- [x] sizing.py + p1calc/{hull, planing, waterjet}: hidrostática, Savitsky + joroba, momento del chorro, curva de bomba, cavitación, energía, térmico, eje, pasador; optimizador paralelo
- [x] CAD de 65 piezas (toma, bomba, tren, motor, dirección, reversa, mandos, electrónica, batería, casco de referencia) con marcos BOTE/JET
- [x] verify_parts.py (boquilla ±25° × bucket) y structural.py — OK
- [x] BOM, arquitectura (matriz A–F), comprar vs construir (JT132)
- [x] run_all.py exit 0

## Pasada 2 — Profundidad ✅
- [x] Planos acotados de piezas mecanizadas/soldadas (`04_diseno/planos/`)
- [x] Electrónica: cables, fusibles, diagrama; firmware v2.0 (bucket, perfiles costa/abierto, limpieza de rejilla, kill) + 69 tests
- [x] Visor 3D web para Jorge (ensamblado, explosión, dirección, bucket, chorro, demo, corte lateral)
- [x] FEA de piezas críticas del jet (`04_diseno/fea`: DRV-03, REV-01, STE-01, INT-02, CTL-02)
- [x] 05_fabricacion.md + probetas + PrusaSlicer
- [x] 06_ensamblaje_y_pruebas.md + FMEA + checklist_salida.md + PENDIENTES_GASPAR.md
- [x] 01, 02, 03, 07, decisiones.md, README reescritos

## Pasada 3 — Auditoría adversarial
- [x] Ronda 1 (44 hallazgos, corregidos)
- [x] Ronda 2 (27 hallazgos, corregidos)
- [x] Ronda 3 (FEA de piezas críticas; superada por la ronda 4: auditoria.md)
- [x] Ronda 4 (rediseño de la traba del bucket, del pivote y del desbloqueo; FEA de REV-01/STE-01 rehecho; corrida fina en `c25d433`): superada por la re-auditoría de la ronda 5
- [~] Ronda 5 (re-auditoría adversarial del rediseño de la ronda 4: MEC-01…09, DES-01…08, FEA-R5-01…04): correcciones en el repositorio; R5-N1 y R5-N5 resueltos en el diseño con el cuerpo del émbolo ajustado (Ø24 H7/h6 con Loctite 641, sin rosca ni precarga), el piloto Ø24 y los lóbulos engrosados de las orejas, y R5-N2…R5-N4 corregidos; re-auditoría del cierre (MECH-1…10, CALC-1…4, FEA-1…5, TEST-1, DOC-1) corregida o documentada, con el pivote en dos piezas (MECH-1); **abierta**: falta la corrida completa final con el FEA fino de P1-STE-01 (FEA de la oreja: FS <!--V:fea.piezas.P1-STE-01.FS_min:.2f-->1.74<!--/V-->, objetivo 2) y la medición de R5-N6
- [x] Prueba de regeneración desde inputs.yaml (`tests/test_regeneration*.py`, auditoria.md §Regeneración)

## Definición de terminado (sección 9)
- [ ] `pip install -r requirements.txt && python run_all.py` exit 0 (corrido completo, no `--fast`)
- [ ] `pytest` pasa
- [x] Toda pieza impresa: STEP + STL, manifold, ≤ 210×210×260, sin interferencias en todos los estados
- [x] Cambio en inputs.yaml regenera todo (probado y documentado)
- [x] FS por caso de carga ≥ 3 PETG / ≥ 2 metal (los que no llegaban se rediseñaron: auditoria.md)
- [x] Números etiquetados; links abiertos en esta sesión (research/R10b–R13)
- [ ] Coherencia .md ↔ código (`tools_check_md.py` con 0 problemas)
- [ ] auditoria.md sin críticos abiertos *de la propulsión* (la estabilidad del casco queda como bloqueante físico declarado)
- [x] README completo
- [ ] Todo commiteado y pusheado

## Bitácora (waterjet)
- 2026-10-01 21:00: pedido de rediseño a waterjet con 4 imágenes de Jorge (foto JT132, plano 2,30 m, chapa, impulsor Ø70). Auditoría del plano: rejilla detrás del impulsor → toma rediseñada entera a proa.
- 2026-10-01 22:30: núcleo de cálculo y optimizador. Resultado honesto: 30 km/h no se alcanzan sostenidos con < 50 V y la batería que entra (26 km/h; ~29 km/h en pico). Estabilidad: GM ≈ 0,01 m → riesgo n.º 1.
- 2026-10-01 23:59: CAD completo (65 piezas) sin interferencias, FS OK, BOM 10,7 k€ (A) vs ~6,4–6,5 k€ (B, JT132). Matriz: gana B (89 % del Monte Carlo).
- 2026-10-02: visor 3D nuevo, docs 01/02/03/07, README, tests adaptados; FEA, fabricación y docs 06/checklist/PENDIENTES en curso.
- 2026-10-02: Pasada 3, ronda 3 — FEA de las piezas críticas: bucket con traba en un solo brazo FS 0,44 (F-01) → traba en los dos brazos, chapa 6 mm, pivote espaciador + M12; CTL-02 con paredes de 5 mm; radios en STE-01 y DRV-03; desempate estable del optimizador; R3-01…R3-11. No quedó cerrada: la corrida fina dio STE-01 FS 1,80 < 2 y el reparto entre trabas no se sostenía.
- 2026-10-02: Pasada 3, ronda 4 — tres auditores (mecánico, FEA, documentación): el reparto entre trabas depende de la carga, el desfase no estaba controlado, M_h subestimado y F_z con el signo cambiado, el émbolo de catálogo supuesto no existe, el FEA de STE-01 aplicaba mal la reacción del pivote, desbloqueo imposible de montar. Rediseño (D-17c): criterio de traba única, cargas por cantidad de movimiento, bucket 8 mm, pivote con brida y piloto, émbolo propio Ø16 / M24×1,5, orejas de 12 mm, balancines + vainas modeladas + gatillo con barra igualadora; FEA de REV-01/STE-01 con casos de una traba sola, verificación de borde de agujeros y estática verificada; `structural.py` sin filas bajo objetivo. En curso: corrida fina del FEA, 05/06/BOM, abiertos de auditoria.md (ronda 4).
- 2026-10-02: Pasada 3, ronda 5 — re-auditoría adversarial del rediseño de la ronda 4 (mecánica, FEA, desbloqueo; dos escépticos por hallazgo; sobrevivieron todos menos FEA-R5-04). Rediseño (D-17d): pivote con el piloto Ø20 H7/h6 como camino de carga, espaciador dúplex 1.4462, brida Ø36 × 4, orejas de 14 mm, M12 × 60 a 12 N·m con Loctite 243, tuerca ISO 4032 y arandela ISO 7093; cuerpo del émbolo a 110 N·m con K 0,15–0,28; cola del perno 44 mm; resorte re-especificado; eslabón rígido ajustable, balancines con cubos, pestaña de tope agrandada; FEA con criterio de convergencia conservador, pivote en el piloto y precarga del émbolo superpuesta. `build_all`, `verify_parts` y `structural.py` sin fallas; **el FEA fino de P1-STE-01 da FS 1,74 < 2** (borde de la rosca M24 con la precarga del émbolo): decisión de diseño pendiente. 02, 05, 06, PENDIENTES, checklist, decisiones, auditoría, HANDOFF y README al día.
- 2026-10-02: Pasada 3, ronda 5 (cierre de R5-N1…R5-N5) — el cuerpo del émbolo pasa a **ajustado**, de un solo Ø: Ø24 h6 en un agujero liso Ø24 H7 (como el piloto) con Loctite 641, collar exterior Ø32 × 1,5 y anillo DIN 471-24 por dentro, sin rosca ni precarga (la precarga de 110 N·m del cuerpo roscado M24 abría el lóbulo de la oreja: FEA 1,74); piloto del pivote Ø24; lóbulos engrosados en las orejas alrededor del pivote (20 mm, hacia adentro, con tuerca baja ISO 4035 para seguir con el M12 × 60) y de cada émbolo (23,5 mm: 3 por fuera de la placa y 6,5 por dentro), porque con el cuerpo ajustado en la oreja de 14 mm el FEA grueso no llegaba a FS 2 y una versión intermedia (cuerpo Ø26, lóbulos de 21 y 16 mm) quedaba con poco margen (R5-N5); pomo de 316 Ø23 roscado en la cola; filas a mano nuevas (aplastamiento del cuerpo y del piloto con el brazo al plano medio del agujero, carga de prueba de la tuerca baja), check del resorte con compacto + Sa, BOM corregida (B-RING24, Loctite 641, un solo escariador Ø24 H7). FEA de STE-01 sin precarga ni caso p. Docs al día; falta la corrida fina del FEA y la re-auditoría.
- 2026-10-02: Pasada 3, ronda 5 (re-auditoría del cierre: MECH-1…10, CALC-1…4, FEA-1…5, TEST-1, DOC-1; auditoria.md) — el espaciador de una pieza del pivote no se podía montar (MECH-1, Alta): pivote en **dos piezas de dúplex**, casquillo con brida y piloto Ø24 h6 enrasado con la cara interior del lóbulo, puesto antes del bucket con Loctite 641, y muñón Ø20 h7 que entra después por el buje (barras MP-DPX-D40 + MP-DPX-D22, planos de casquillo y muñón); garganta en el tubo de la boquilla bajo el émbolo −Y, que pasaba a 0,26 mm (MECH-3); cola del perno 42 mm (MECH-2), ranura del anillo con tolerancia (MECH-5), vástago M4 de 14 y rosca de 12 (MECH-6), hexágono en la punta y tapa con agujeros de llave (MECH-7), tuerca ISO 4035 m 6 (MECH-9); secuencia del anillo del émbolo −Y y control de los brazos soldados en 05/06 (MECH-4, MECH-8); ligamentos a mano con la misma presión lineal que el aplastamiento y filas nuevas del muñón en el casquillo, la guía del perno y el collar (CALC-1…4); FEA: mismo r_excl en `--quick` (FEA-1), lóbulos sin caras astilla (FEA-2), pies de los lóbulos como aristas vivas (FEA-3), piloto sin juego (FEA-4), ventana del borde como limitación (FEA-5); tests (TEST-1) y comentarios (DOC-1, MECH-10). Docs al día; falta la corrida completa final.

## Bitácora (versión anterior: cola larga, archivada)
- 2026-10-01: inicio. V1/V2: títulos verificados vía YouTube oEmbed (canal "Clean Energy").
- 2026-10-01: Pasada 1 cerrada. `run_all.py` exit 0 desde cero (4 min 15 s); pytest 24/24.
  Pendientes de Pasada 2 detectados por la investigación: factores de material R05 (fatiga 0,06,
  creep 0,35, agua 0,75, T servicio 50 °C) → placa motriz de Al; kill switch por contactor (R06);
  O-ring 3,53 mm con caras refrentadas; aro protector perfilado (R03); arrastre de apéndices;
  opción 12S/36 V; firmware + tests; FEA; perfiles PrusaSlicer + probetas; 06 completo + FMEA.
- 2026-10-01 14:10: Pasada 2 — integrados R07, R08a, R08b, R09. Cambios de diseño: tope de ERPM legal,
  caja ESC 160×110×45 con prensaestopas M20 rebajados + disipador con R_th requerida, rodamientos 6202,
  bujes igus H370, poleas/correas Dold existentes, hélice MKP-32 (comprable), pasador 316, sin ánodo,
  eje montable (A-08). Costo total sistema 2 255 € (72 % verificado). pytest 64 OK.
- 2026-10-01 19:00: Pasada 3, ronda 1 — auditoría adversarial con 87 hallazgos (resultados/auditoria_ronda1.json:
  2 críticos de CAD/FS, ~20 altos). Corrección en curso por subsistema (montaje, cabezal/cola/mando,
  electrónica, fabricación, documentos). Propulsión (agente principal): bollard neto con deducción y aro,
  térmico sostenido desde la T de crucero, pico de batería sobre todas las variantes de V máx, margen del
  ESC contra la corriente de fase, rendimiento de reversa en inputs, sensibilidad con D/P de hélice, R_th
  y aire (temperatura del motor por entrada), disipador del ESC por el caso V máx, caso legal de 2 personas
  con batería llena, y comparación con comprar un motor generada (`comparacion.py`).
