# PROGRESS — P1 propulsión eléctrica

Leyenda: [x] hecho · [~] en curso · [ ] pendiente

## Pasada 1 — Funcional de punta a punta
- [x] PROMPT.md guardado
- [~] Investigación lanzada en paralelo (subagentes → `research/`)
- [ ] inputs.yaml (única fuente de entradas)
- [ ] sizing.py + 02_calculos.md mínimo
- [ ] 04_diseno/params.py + piezas/ + build_all.py (STEP + STL)
- [ ] verify_parts.py (envolvente, manifold, interferencias, kick-up)
- [ ] bom.csv generado
- [ ] run_all.py + requirements.txt + tests/
- [ ] Documentos mínimos: README, decisiones, PENDIENTES_GASPAR, 01..07, checklist_salida

## Pasada 2 — Profundidad
- [ ] 01_investigacion.md completo (videos, ≥8 proyectos, jon boats, materiales, sellado, BLDC, normativa)
- [ ] Cálculos refinados (R(v) por régimen, hélice, cavitación, motor, batería, cables, térmico, mecánico, sensibilidad)
- [ ] 03_arquitectura.md (matriz ponderada + sensibilidad de pesos)
- [ ] CAD detallado + planos de torneado
- [ ] FEA 2–3 piezas críticas
- [ ] Electrónica + firmware + tests de lógica
- [ ] 05_fabricacion.md + perfiles PrusaSlicer + probetas CAD
- [ ] 06_ensamblaje_y_pruebas.md + FMEA + checklist_salida.md
- [ ] Blender (scripts + renders)
- [ ] 07_roadmap_P2.md

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
