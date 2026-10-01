# PROGRESS — P1 propulsión eléctrica

Leyenda: [x] hecho · [~] en curso · [ ] pendiente

## Pasada 1 — Funcional de punta a punta ✅ (2026-10-01)
- [x] PROMPT.md guardado
- [x] Investigación en paralelo (subagentes → `research/`): R01–R09 completos (R08 en dos partes: eléctrica y mecánica)
- [x] inputs.yaml (única fuente de entradas, cada número etiquetado)
- [x] sizing.py + p1calc/ + 02_calculos.md (optimizador hélice × batería × poleas)
- [x] 04_diseno/params.py + 34 piezas + build_all.py (STEP + STL)
- [x] verify_parts.py (envolvente, manifold, cotas, interferencias con barrido ψ × φ) — OK
- [x] structural.py (44 FS por pieza/caso) — OK
- [x] planos.py (10 SVG de torneado/mecanizado)
- [x] bom.csv + curvas costo–autonomía
- [x] arquitectura.py (matriz ponderada + sensibilidad Monte Carlo)
- [x] run_all.py (exit 0 desde cero en ~4 min) + requirements.txt + 24 tests pytest (OK)
- [x] Renders Blender headless (bpy 5.0.1) + vistas matplotlib
- [x] Documentos mínimos: README, decisiones, PENDIENTES_GASPAR, 01..07, checklist_salida, auditoria

## Pasada 2 — Profundidad
- [~] 01_investigacion.md completo (workflow de documentos en curso)
- [x] Cálculos refinados: B-series verificada, Burrill tabulado, R en caliente, térmico del ESC, límite legal, fatiga del pasador, poleas/correas existentes, asiento de hélice
- [~] 03_arquitectura.md actualizado con R08 (workflow de documentos en curso)
- [x] CAD detallado (38 piezas) + 12 planos; corrección del montaje del eje (A-08)
- [~] FEA 2–3 piezas críticas (workflow de electrónica/FEA/fabricación en curso)
- [~] Electrónica + firmware + tests de lógica (firmware y tests listos; README en curso)
- [~] 05_fabricacion.md + perfiles PrusaSlicer + probetas CAD (en curso)
- [~] 06_ensamblaje_y_pruebas.md + FMEA + checklist_salida.md (workflow de documentos en curso)
- [x] Blender (scripts + renders) — re-render al final
- [~] 07_roadmap_P2.md (workflow de documentos en curso)
- [x] Integración R07 (normativa DK), R08a/R08b (BOM verificada: 72 % del subtotal), R09 (métodos)

## Pasada 3 — Auditoría adversarial
- [ ] Ronda 1
- [ ] Ronda 2 (hasta no encontrar problemas relevantes)
- [ ] Prueba de regeneración desde inputs.yaml documentada

## Definición de terminado (sección 9)
- [ ] `pip install -r requirements.txt && python run_all.py` exit 0
- [ ] `pytest` pasa
- [ ] Toda pieza impresa: STEP + STL, manifold, ≤ 210×210×260, sin interferencias (incl. basculación)
- [ ] Cambio en inputs.yaml regenera todo (probado y documentado)
- [ ] FS por caso de carga; los < 3 resueltos o justificados
- [ ] Números etiquetados; links abiertos en esta sesión
- [ ] Coherencia .md ↔ código
- [ ] auditoria.md sin críticos abiertos
- [ ] README completo
- [ ] Todo commiteado y pusheado

## Bitácora
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
