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
- [~] FEA de piezas críticas del jet (agente en curso)
- [~] 05_fabricacion.md + probetas + PrusaSlicer (agente en curso)
- [~] 06_ensamblaje_y_pruebas.md + FMEA + checklist_salida.md + PENDIENTES_GASPAR.md (agente en curso)
- [x] 01, 02, 03, 07, decisiones.md, README reescritos

## Pasada 3 — Auditoría adversarial
- [ ] Ronda 1
- [ ] Ronda 2 (hasta no encontrar problemas relevantes)
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
