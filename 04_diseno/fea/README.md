# FEA

<!-- FEA:AUTO:INICIO (generado por fea_run.py; no editar a mano) -->

Corrida: 2026-10-01 · inputs v1.0 · 99 s · admisibles vigentes: S_corta = 23.97 MPa, S_sost = 8.39 MPa, S_Z corta/sost = 9.18/3.21 MPa [CALCULADO]

### Mallas

| Pieza | Malla | h [mm] | Tetraedros | gdl (P2) | γ mín | γ p1 |
|---|---|---|---|---|---|---|
| P1-MNT-01 | gruesa | 14 | 6560 | 36258 | 0.139 | 0.362 |
| P1-MNT-01 | fina | 7 | 37255 | 182157 | 0.150 | 0.359 |
| P1-MNT-05 | gruesa | 14 | 16714 | 86748 | 0.005 | 0.301 |
| P1-MNT-05 | fina | 8 | 47313 | 229896 | 0.003 | 0.337 |
| P1-MNT-04 | gruesa | 6 | 4677 | 26343 | 0.073 | 0.345 |
| P1-MNT-04 | fina | 3 | 24785 | 122880 | 0.300 | 0.362 |

### Resultados (malla fina) — tensiones en MPa, FS = admisible / tensión (máx. fuera de zonas de carga)

| Pieza | Caso | Tipo | σvm máx | σvm p99 | σvm máx* | σ1 máx* | σZ máx* | u máx [mm] | FS vm | FS σ1 | FS Z | **FS** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1-MNT-01 | a: Apriete sostenido de 2×M12 (2.5 N·m → 1042 N c/u) | sostenida | 21.23 | 19.86 | 21.23 | 24.16 | 10.04 | 26.276 | 0.40 | 0.35 | 0.32 | **0.32** |
| P1-MNT-01 | b+: Impacto H = 0,5·F_pico = 501 N hacia popa (+x) a la altura del pivote + apriete | corta | 21.30 | 19.97 | 21.30 | 24.27 | 10.05 | 26.781 | 1.13 | 0.99 | 0.91 | **0.91** |
| P1-MNT-01 | b-: Impacto H = 0,5·F_pico = 501 N hacia proa (−x) a la altura del pivote + apriete | corta | 24.24 | 22.64 | 24.24 | 27.57 | 11.57 | 23.949 | 0.99 | 0.87 | 0.79 | **0.79** |
| P1-MNT-05 | a: Cola trabada contra el tope de marcha: M = 338 N·m (V = 300 N a 1176 mm) | corta | 10.21 | 5.44 | 6.84 | 3.34 | 1.55 | 0.891 | 3.51 | 7.17 | 5.93 | **3.51** |
| P1-MNT-06 | a: Cola trabada contra el tope de marcha: M = 338 N·m (V = 300 N a 1176 mm) | corta | 31.25 | 19.35 | 31.25 | 5.42 | 1.58 | 0.794 | 0.77 | 4.42 | 5.81 | **0.77** |
| P1-MNT-04 | a+: Perno: 0,5·H = 250 N hacia popa (+x) | corta | 6.19 | 2.91 | 3.98 | 4.37 | 1.30 | 0.437 | 6.02 | 5.49 | 7.08 | **5.49** |
| P1-MNT-04 | a-: Perno: 0,5·H = 250 N hacia proa (−x) | corta | 6.19 | 2.94 | 3.98 | 3.93 | 1.44 | 0.432 | 6.02 | 6.10 | 6.38 | **6.02** |
| P1-MNT-04 | b: Golpe lateral 200 N en una mejilla (+y, cuna contra la cara interior) | corta | 22.11 | 11.12 | 22.11 | 24.84 | 3.02 | 5.764 | 1.08 | 0.96 | 3.04 | **0.96** |
| P1-MNT-04 | b50: Golpe lateral repartido 100 N por mejilla (perno atado; = structural.py) | corta | 11.06 | 5.56 | 11.06 | 12.42 | 1.51 | 2.882 | 2.17 | 1.93 | 6.08 | **1.93** |
| P1-MNT-04 | c+: Combinado oblicuo: a+ + b (superposición lineal) | corta | 23.16 | 11.03 | 23.16 | 22.10 | 2.90 | 5.759 | 1.04 | 1.08 | 3.17 | **1.04** |
| P1-MNT-04 | c-: Combinado oblicuo: a- + b (superposición lineal) | corta | 25.16 | 10.89 | 25.16 | 27.85 | 3.39 | 5.801 | 0.95 | 0.86 | 2.71 | **0.86** |

\* máximo fuera de las zonas de aplicación de cargas/apoyos concentrados (radio de exclusión en la tabla de convergencia); el máximo global incluye singularidades de aplicación y se reporta para transparencia.

### Convergencia (gruesa → fina, pieza principal)

| Pieza | Caso | r_excl [mm] | σvm p99 | σvm máx* | σvm máx global | u máx [mm] |
|---|---|---|---|---|---|---|
| P1-MNT-01 | a | 7 | 20.06 → 19.86 (-1 %) | 21.11 → 21.23 (+1 %) | 21.11 → 21.23 (+1 %) | 25.677 → 26.276 (+2 %) |
| P1-MNT-01 | b+ | 7 | 20.14 → 19.97 (-1 %) | 21.02 → 21.30 (+1 %) | 30.75 → 21.30 (-44 %) | 26.183 → 26.781 (+2 %) |
| P1-MNT-01 | b- | 7 | 22.57 → 22.64 (+0 %) | 23.72 → 24.24 (+2 %) | 31.94 → 24.24 (-32 %) | 23.527 → 23.949 (+2 %) |
| P1-MNT-05 | a | 8 | 6.59 → 5.44 (-21 %) | 9.00 → 6.84 (-32 %) | 22.85 → 10.21 (-124 %) | 1.321 → 0.891 (-48 %) |
| P1-MNT-04 | a+ | 4 | 2.90 → 2.91 (+0 %) | 4.29 → 3.98 (-8 %) | 4.55 → 6.19 (+26 %) | 0.432 → 0.437 (+1 %) |
| P1-MNT-04 | a- | 4 | 3.01 → 2.94 (-3 %) | 4.51 → 3.98 (-13 %) | 4.81 → 6.19 (+22 %) | 0.446 → 0.432 (-3 %) |
| P1-MNT-04 | b | 4 | 11.51 → 11.12 (-4 %) | 16.26 → 22.11 (+26 %) | 16.26 → 22.11 (+26 %) | 5.695 → 5.764 (+1 %) |
| P1-MNT-04 | b50 | 4 | 5.75 → 5.56 (-4 %) | 8.13 → 11.06 (+26 %) | 8.13 → 11.06 (+26 %) | 2.847 → 2.882 (+1 %) |
| P1-MNT-04 | c+ | 4 | 11.51 → 11.03 (-4 %) | 18.48 → 23.16 (+20 %) | 18.48 → 23.16 (+20 %) | 5.691 → 5.759 (+1 %) |
| P1-MNT-04 | c- | 4 | 11.67 → 10.89 (-7 %) | 18.51 → 25.16 (+26 %) | 18.51 → 25.16 (+26 %) | 5.728 → 5.801 (+1 %) |

### Comparación con el cálculo a mano (resultados/estructural.json, structural.py)

| Pieza | Caso FEA | FS FEA | Fila structural.py | σ mano [MPa] | FS mano |
|---|---|---|---|---|---|
| P1-MNT-01 | a | 0.32 | Apriete (sostenido) | 2.60 | 3.23 |
| P1-MNT-01 | b+ | 0.91 | LC5 impacto + apriete (corta) | 5.04 | 4.76 |
| P1-MNT-01 | b- | 0.79 | LC5 impacto + apriete (corta) | 5.04 | 4.76 |
| P1-MNT-05 | a | 3.51 | LC5 cola trabada (corta) | 2.75 | 8.73 |
| P1-MNT-05 | a | 3.51 | LC5 cola trabada: apoyo extremo (corta) | 3.11 | 7.71 |
| P1-MNT-04 | a+ | 5.49 | LC5 en el plano (corta) | 2.66 | 9.01 |
| P1-MNT-04 | a- | 6.02 | LC5 en el plano (corta) | 2.66 | 9.01 |
| P1-MNT-04 | b | 0.96 | Golpe lateral 200 N (corta) | 4.86 | 4.94 |
| P1-MNT-04 | b50 | 1.93 | Golpe lateral 200 N (corta) | 4.86 | 4.94 |
| P1-MNT-04 | c+ | 1.04 | LC5 en el plano (corta) | 2.66 | 9.01 |
| P1-MNT-04 | c- | 0.86 | LC5 en el plano (corta) | 2.66 | 9.01 |

### Hallazgos cuantitativos

- **P1-MNT-01 — el puente de la C gobierna.** Apriete sostenido: σvm p99 = 19.9 MPa en el puente de 12 mm (la viga a mano con esa sección da 20.8 MPa, coincide) contra S_sost = 8.39 MPa → **FS = 0.32** (objetivo 3). structural.py informa σ = 2.595 MPa porque usa Z = b·leg_t²/6 de la pata (t = leg_t) y no la del puente. La C se abre 26.3 mm en el pie de la pata interior (análisis lineal: indica flexibilidad excesiva, no un valor exacto). Con el apriete actual el puente necesita t ≥ 38.5 mm [CALCULADO: viga, verificada por FEA] o bajar el brazo/apriete.
- **P1-MNT-05/06 — brazo del tope de marcha.** El tornillo de trimado es vertical y apoya en la cara inferior de la tapa, inclinada θ: sin fricción la reacción es normal a esa cara y su brazo respecto del pivote es u = 30 mm, no hypot(30, v_bot) = 90 mm como en structural.py. Con la cola trabada, el FEA da F_tope = ≫ N (estática: 11757 N) y F_pivote = ≫ N. La cuna (MNT-05) queda con FS = 3.51; la **tapa MNT-06** recibe el tope en un Ø25 y su FS es 0.77 (σvm máx. global 31.2 MPa en el apoyo del tope). En marcha normal el mismo brazo triplica la fuerza sostenida del tope respecto de structural.py.
- **P1-MNT-04 — ranuras de tuerca en la raíz.** Golpe lateral repartido (100 N/mejilla, como structural.py): σvm máx* = 11.1 MPa contra 4.9 MPa a mano (L = 64 mm sin descontar las ranuras pasantes de las tuercas M6 ni concentraciones). FS mínimo de la pieza 0.86 (caso c-, criterio s1).

<!-- FEA:AUTO:FIN -->
