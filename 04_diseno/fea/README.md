# FEA de las piezas críticas del waterjet — P1-DRV-03, P1-REV-01, P1-STE-01, P1-INT-02, P1-CTL-02

FEA lineal elástico 3D de las piezas más cargadas del waterjet eléctrico inboard: el pórtico de
rodamientos que baja el empuje del tren a la placa base (DRV-03), el bucket de reversa (REV-01), la
boquilla direccional (STE-01), la placa base de la toma (INT-02) y una pieza impresa, la caja de
palancas de la consola (CTL-02, PETG). La geometría, las cargas y los admisibles se leen del proyecto
en cada corrida; todas las cifras de resultados están en el bloque AUTO del final, que regenera
`fea_run.py` y no se edita a mano.

## Archivos y uso

| Archivo | Qué hace |
|---|---|
| `fea_run.py` | CLI. Corre las 5 piezas con malla gruesa y fina, evalúa las variantes propuestas, escribe `resultados_fea.json`, `img/*.png` y el bloque AUTO de este README |
| `fea_parts.py` | Modelo de cada pieza: geometría (build(p) + consultas al CAD), BCs, cargas, casos, regiones y filas del cálculo a mano que se comparan |
| `fea_model.py` | Interfaces de resortes (Winkler, cuerpo rígido, unilaterales), iteración de contacto, post-proceso (global y por región) |
| `fea_core.py` | Malla gmsh (con optimización Netgen), espacio P2, ensamble vectorizado, cargas de superficie y solver PCG de dos niveles |
| `fea_plot.py` | Mapas de tensión sobre la superficie (matplotlib) |
| `../../tests/test_fea.py` | Viga en voladizo contra la solución analítica, verificación cruzada con scikit-fem, cuerpo rígido + Winkler, malla gruesa de CTL-02, estática del bucket contra structural_direccion y FS > 0 en el JSON |

```bash
python 04_diseno/fea/fea_run.py              # todo (gruesa + fina + variantes), 3 procesos: ~15 min
python 04_diseno/fea/fea_run.py --quick      # solo malla gruesa, sin imágenes ni README (~4 min) → resultados_fea_quick.json
python 04_diseno/fea/fea_run.py --only P1-STE-01 --h P1-STE-01=10,6 --out /tmp/ste.json   # una pieza / otros tamaños
python 04_diseno/fea/fea_run.py --readme-only   # rehace hallazgos y bloque AUTO desde resultados_fea.json
python -m pytest -q tests/test_fea.py        # ~1 min
```

Dependencias: `gmsh`, `scipy`, `numpy`, `matplotlib`, `build123d`; `scikit-fem` solo en el test.
gmsh necesita `libglu1-mesa` del sistema. `--quick` escribe en `resultados_fea_quick.json` para no
pisar el entregable.

## Método

1. **Geometría.** `params.load()` y el `build(p)` de cada módulo de pieza en su marco natural (BOTE
   para DRV-03, INT-02 y CTL-02; BOQUILLA a δ = 0 para STE-01). El bucket se modela **abajo** (reversa)
   con `build_down(p)`, en el marco de la boquilla. STEP temporal → gmsh (OCC). Los ejes de las roscas M5
   de la tapa del pórtico se leen del CAD (OCP); el resto de las posiciones sale de params y de funciones
   del módulo (`lock_pt`, `hull_bolts`, `bolt_x`, …). No hay posiciones copiadas a mano.
2. **Malla.** Tetraedros de gmsh (Delaunay 3D + optimización Netgen, que reduce las astillas de las
   paredes finas del CAD), tamaño global `h`, refinamiento por curvatura y esferas de refinamiento a h/2
   en los apoyos críticos (pivotes y traba del bucket; orejas de STE-01; espárragos de INT-02). Malla
   gruesa ≈ 1,7–2·h de la fina. Quedan algunas decenas de elementos con γ < 0,05 en aristas del CAD
   (columna n(γ<0,05) del bloque AUTO); el p99 no depende de ellos.
3. **Elementos y solver.** Tetraedros P2 de 10 nodos (ensamble propio verificado contra
   `skfem.ElementTetP2`), PCG con precondicionador de dos niveles P2 → P1, tolerancia 10⁻⁷.
4. **Apoyos y contacto.** Resortes Winkler (normales + 1 % tangencial de estabilización), contacto
   unilateral por conjunto activo (la malla fina arranca del estado de la gruesa), pernos sin fricción con
   normal radial exacta y cuerpos rígidos de 6 gdl (émbolo de la traba, yugo de dirección, conducto).
5. **Post-proceso.** Tensión P2 evaluada en vértices y promediada por nodo (ponderada por volumen).
   Para cada caso: **máx. global** (incluye singularidades de aplicación), **p99** (percentil 99 en
   volumen) y **máx\*** = máximo fuera de un radio de exclusión r_excl = máx(4 mm, h_fina) alrededor de
   cargas y apoyos concentrados (pernos, roscas, avellanados, arandelas). **FS = admisible / σvm máx\***
   (metales dúctiles: von Mises). En PETG también σ1 y σZ (normal a las capas) contra S_Z; el FS es el
   menor de los tres. Además se resume cada **región** de la pieza (máx\*, p99 y **promedio en
   volumen**): las filas del cálculo a mano de aplastamiento/corte se comparan con el promedio en el
   volumen que la fila representa (anillo alrededor del agujero, cilindro del tapón, capa bajo el cono).
6. **Comparación con el cálculo a mano.** Cada fila de `resultados/estructural.json` se compara con la
   región que modela, con la σ del FEA escalada a la carga de la fila (p. ej. la fila de fatiga de la
   reversa usa F_bucket de sizing: σ_FEA × 698/1408) y el admisible de la propia fila. Diferencias de FS
   > 30 % se explican en «Hallazgos».

## Materiales y admisibles

- **Aluminios.** E = 70 GPa, ν = 0,33 [ESTIMADO: EN 1999-1-1]. Admisibles tomados de las constantes de
  los `structural_<grupo>.py` (fuente única): DRV-03 `SY_6082_HAZ` = 115 MPa (zona soldada, en toda la
  pieza); REV-01 `AL5083` = 125 MPa; STE-01 `AL6061` = 240 MPa; INT-02 `pmp_mat['Al 5083'].Sy` = 125 MPa.
  FS objetivo `fs_target_metal` = 2.
- **PETG (CTL-02).** E = `materials.PETG.E_mpa`, ν = 0,38 [ESTIMADO]. `S_corta = σ_XY·f_agua·f_temp·f_proceso`;
  `S_Z = mín(σ_Z, f_z·σ_XY)·f_agua·f_temp·f_proceso` (no se multiplica dos veces la debilidad entre
  capas). La caja se imprime con `print_rot = (180, 0, 0)`: Z de impresión = z del bote, así que la
  flexión de la tapa queda en el plano de las capas y la de las **paredes** cruza capas (σZ). FS objetivo
  `fs_target_printed` = 3. Material macizo equivalente: la pieza real es 5 perímetros + 30 % giroide
  (`solid_frac` 0,55), lo que en la tapa de 6 mm reduce la rigidez y la resistencia a flexión.

## Condiciones de borde y cargas

### P1-DRV-03 — pórtico de rodamientos (marco BOTE)

- **Apoyos.** Zapatas sobre la placa base: resortes bilaterales k = E/t_placa (unión precargada a
  T/(K·d) por espárrago ≫ el tiro de servicio; no se abre). El corte lo toman los 4 agujeros Ø9 de los
  espárragos (contacto radial unilateral; representan también los pasadores Ø6 que se escarian en
  montaje).
- **(a)** Empuje `sizing.mech.Fa_max_N` hacia proa (eje del jet inclinado α): la tapa P1-DRV-06 tira de
  las 4 roscas M5 de la cara delantera (tracción uniforme en sus paredes). Radial 3 g × m_rotor + Fr
  (de structural_tren) como apoyo cosenoidal en el Ø47, perpendicular al eje.
- **(b)** El mismo Fa hacia popa sobre el resalte trasero, solo en el anillo de apoyo del aro exterior
  (Da_max ≤ Ø ≤ D) + el mismo radial.

### P1-REV-01 — bucket abajo (marco BOQUILLA)

- **Carga.** F_b = máx(`sizing.loads.F_bucket_N`, 1408 N de R12 §7) = `REV_F_design`, como tracción
  uniforme **por área proyectada** del chorro (Ø del chorro + cono 5° a la altura del fondo de la
  cuchara) sobre la cara interior de la cuchara, en la dirección del chorro (+X), más la componente
  vertical que da M_h = 1,10·F_b·Z_pivote, igual que structural_direccion.
- **Apoyos.** Pivotes Ø14 (bujes POM P1-REV-03, k = E_POM/espesor del buje, unilaterales, sin
  fricción, resorte axial débil). Traba: émbolo Ø12 en el agujero Ø12,5 del brazo +Y como cuerpo
  rígido que **solo reacciona en la dirección tangencial** al círculo alrededor del pivote (el momento),
  como en el cálculo a mano; los pivotes toman el resto. La fuerza de traba del FEA coincide con
  `F_lock_pin_N` de estructural.json.
- **Variantes propuestas** (V1, V2): misma carga; la geometría se completa con su espejo en y (lóbulos
  y agujero de traba también en el brazo −Y, 2.º émbolo) y en V2 `REV_t` = 6 mm. Es solo una
  evaluación dentro del modelo FEA: `P1-REV-01_bucket.py` no se modificó.

### P1-STE-01 — boquilla direccional (marco BOQUILLA, δ = 0)

- **Apoyos.** Pernos de pivote fijos (orejas de la bomba rígidas): contacto radial unilateral en el Ø8 H7
  de la mejilla superior y en las roscas M6 de las orejas superior e inferior; arandelas POM de empuje
  como resortes axiales (la boquilla queda atrapada entre las orejas de la bomba). El **yugo** (brida
  P1-STE-04 sobre la torre) es un cuerpo rígido unido a las 4 roscas M8 y a la cara superior de la torre,
  con **solo el giro alrededor del eje de pivote bloqueado**: reacciona el par de dirección (la biela del
  M66) sin fuerza neta.
- **(a)** F_s = máx(`sizing.loads.F_steer_side_N`, 364 N de R12) lateral, como presión cosenoidal en el
  paso Ø2·r_b, en una banda centrada en el centro de presión e = `STE_e_frac`·L (el modelo de la fila a
  mano). **(b)** La misma F_s en los últimos 20 mm de la boca de salida (brazo ≈ L, conservador).
  **(c)** Reversa: las reacciones del bucket (estática de `bucket_statics`, la misma hipótesis de traba
  tangencial) en las orejas Ø8,4 y en la rosca M20 del émbolo. **(d)** c + a con contacto resuelto.

### P1-INT-02 — placa base de la toma (marco BOTE)

- **Apoyos.** Ala sobre el casco: resortes k = E/t_casco, bilaterales (26 × M6 precargados; la junta no
  se abre con estas cargas). Arandela + tuerca de cada M6 del ala: empotradas.
- **(a)** Espárragos del pórtico: precarga T/(K·d) con el par de montaje de params (`drv_nut_torque_Nm`,
  `drv_nut_K`) ± vuelco Fa·(h + t)/Δx/2 (popa a tracción) repartido con Φ = 0,25 (VDI 2230, como
  structural_toma): tiro F_v + Φ·ΔF normal al cono del avellanado, compresión F_v − (1 − Φ)·ΔF + 3 g/4 de
  la zapata en un anillo Ø24 (cono de compresión) y corte Fa/4 en ese anillo.
- **(b)** Golpe de fondo `toma_p_slam_Pa` en la cara inferior, presión de cierre máx(p_cierre, p_golpe)
  normal a todas las caras de la placa dentro de la abertura (cuña de la rampa y costados) y tiro de la
  brida del conducto p·A_abertura en las roscas M6. **Placa sola**: sin la rigidez del conducto (cota
  conservadora). **(b2)** Ídem con el conducto P1-INT-01 como **rigidizador rígido** unido a la huella de
  la brida y a las roscas M6, con el tiro aplicado al conducto (cota rígida; es la hipótesis del cálculo a
  mano, que apoya el paño en la línea de bulones del conducto). La realidad está entre (b) y (b2).

### P1-CTL-02 — caja de palancas PETG (marco BOTE)

- **Apoyos.** Cara inferior del ala y de las paredes sobre la tapa de contrachapado de la consola
  (Winkler unilateral, k = E_⟂/t_tapa, E_⟂ = 500 MPa [ESTIMADO]); 4 × M5 con arandela Ø10 empotrados.
- **Carga.** Mano apoyada 150 N [SUPUESTO de structural_direccion] como presión uniforme sobre el
  material dentro de una palma Ø50 [SUPUESTO]: (a) sobre el nervio de 6 mm entre las dos ranuras de las
  palancas, a mitad de su luz libre; (b) sobre el tramo de tapa más ancho, junto a la ranura del bucket.
  Corta duración (S_corta, S_Z corta).

## Limitaciones

- **Lineal, desplazamientos pequeños, isotrópico.** Sin plasticidad: picos locales por encima de la
  fluencia en zonas de apoyo (agujeros, avellanados) indican fluencia local, no rotura; por eso el FS de
  diseño usa el máx\* fuera de r_excl y se reporta también el p99.
- **Soldaduras.** No se modela la geometría del cordón ni la ZAT como material distinto; el admisible de
  ZAT se aplica a toda la pieza soldada (DRV-03, REV-01). La fatiga de soldadura solo entra por las filas
  a mano escaladas.
- **Sin contacto real entre piezas** (resortes de penalización, sin fricción) y piezas vecinas rígidas
  (orejas de la bomba, pernos, émbolo). En INT-02 el conducto se acota entre «ausente» y «rígido».
- **Cargas cuasi-estáticas** (sizing / R12) sin dinámica; los impactos solo entran por los factores de
  los casos a mano.
- **PETG** macizo equivalente (ver arriba).

<!-- FEA:AUTO:INICIO (generado por fea_run.py; no editar a mano) -->

Corrida: 2026-10-01 · inputs v1.0 · 106 s · admisibles vigentes: S_corta = 23.97 MPa, S_sost = 8.39 MPa, S_Z corta/sost = 9.18/3.21 MPa [CALCULADO]

### Orientación de impresión (anisotropía)

| Pieza | print_rot (META) | Z de impresión en el marco de la pieza | Marco |
|---|---|---|---|
| P1-MNT-01 | (90, 0, 0) | (0.0, 1.0, 0.0) | boat |
| P1-MNT-05 | (90, 0, 0) | (0.0, 1.0, 0.0) | unit |
| P1-MNT-04 | (90, 0, 0) | (0.0, 1.0, 0.0) | yoke |

### Mallas

| Pieza | Malla | h [mm] | Tetraedros | gdl (P2) | γ mín | γ p1 |
|---|---|---|---|---|---|---|
| P1-MNT-01 | gruesa | 14 | 6560 | 36258 | 0.139 | 0.362 |
| P1-MNT-01 | fina | 7 | 37255 | 182157 | 0.150 | 0.359 |
| P1-MNT-05 | gruesa | 14 | 19998 | 100983 | 0.005 | 0.305 |
| P1-MNT-05 | fina | 8 | 61601 | 290481 | 0.003 | 0.341 |
| P1-MNT-04 | gruesa | 6 | 4677 | 26343 | 0.073 | 0.345 |
| P1-MNT-04 | fina | 3 | 24785 | 122880 | 0.300 | 0.362 |

### Resultados (malla fina) — tensiones en MPa, FS = admisible / tensión (máx. fuera de zonas de carga)

| Pieza | Caso | Tipo | σvm máx | σvm p99 | σvm máx* | σ1 máx* | σZ máx* | u máx [mm] | FS vm | FS σ1 | FS Z | **FS** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1-MNT-01 | a: Apriete sostenido de 2×M12 (2.5 N·m → 1042 N c/u) | sostenida | 21.23 | 19.86 | 21.23 | 24.16 | 10.04 | 26.276 | 0.40 | 0.35 | 0.32 | **0.32** |
| P1-MNT-01 | b+: Impacto H = 0,5·F_pico = 501 N hacia popa (+x) a la altura del pivote + apriete | corta | 21.30 | 19.97 | 21.30 | 24.27 | 10.05 | 26.781 | 1.13 | 0.99 | 0.91 | **0.91** |
| P1-MNT-01 | b-: Impacto H = 0,5·F_pico = 501 N hacia proa (−x) a la altura del pivote + apriete | corta | 24.24 | 22.64 | 24.24 | 27.57 | 11.57 | 23.949 | 0.99 | 0.87 | 0.79 | **0.79** |
| P1-MNT-05 | a: Cola trabada contra el tope de marcha: M = 338 N·m (V = 300 N a 1176 mm) | corta | 10.95 | 5.46 | 7.06 | 3.44 | 1.61 | 0.935 | 3.40 | 6.97 | 5.71 | **3.40** |
| P1-MNT-06 | a: Cola trabada contra el tope de marcha: M = 338 N·m (V = 300 N a 1176 mm) | corta | 32.47 | 20.16 | 32.47 | 6.03 | 1.30 | 0.839 | 0.74 | 3.98 | 7.06 | **0.74** |
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
| P1-MNT-05 | a | 8 | 5.69 → 5.46 (-4 %) | 6.39 → 7.06 (+9 %) | 10.31 → 10.95 (+6 %) | 0.911 → 0.935 (+3 %) |
| P1-MNT-04 | a+ | 4 | 2.90 → 2.91 (+0 %) | 4.29 → 3.98 (-8 %) | 4.55 → 6.19 (+26 %) | 0.432 → 0.437 (+1 %) |
| P1-MNT-04 | a- | 4 | 3.01 → 2.94 (-3 %) | 4.51 → 3.98 (-13 %) | 4.81 → 6.19 (+22 %) | 0.446 → 0.432 (-3 %) |
| P1-MNT-04 | b | 4 | 11.51 → 11.12 (-4 %) | 16.26 → 22.11 (+26 %) | 16.26 → 22.11 (+26 %) | 5.695 → 5.764 (+1 %) |
| P1-MNT-04 | b50 | 4 | 5.75 → 5.56 (-4 %) | 8.13 → 11.06 (+26 %) | 8.13 → 11.06 (+26 %) | 2.847 → 2.882 (+1 %) |
| P1-MNT-04 | c+ | 4 | 11.51 → 11.03 (-4 %) | 18.48 → 23.16 (+20 %) | 18.48 → 23.16 (+20 %) | 5.691 → 5.759 (+1 %) |
| P1-MNT-04 | c- | 4 | 11.67 → 10.89 (-7 %) | 18.51 → 25.16 (+26 %) | 18.51 → 25.16 (+26 %) | 5.728 → 5.801 (+1 %) |

### Comparación con el cálculo a mano (resultados/estructural.json, structural.py)

| Pieza (FEA) | Caso FEA | FS FEA | Fila structural.py (pieza) | σ mano [MPa] | FS mano |
|---|---|---|---|---|---|
| P1-MNT-01 | a | 0.32 | Apriete (sostenido) (P1-MNT-01) | 2.60 | 3.23 |
| P1-MNT-01 | b+ | 0.91 | LC5 impacto + apriete (corta) (P1-MNT-01) | 5.04 | 4.76 |
| P1-MNT-01 | b- | 0.79 | LC5 impacto + apriete (corta) (P1-MNT-01) | 5.04 | 4.76 |
| P1-MNT-05 | a | 3.40 | LC5 cola trabada (corta) (P1-MNT-05) | 2.75 | 8.73 |
| P1-MNT-06 | a | 0.74 | LC5 cola trabada: apoyo extremo (corta) (P1-MNT-06) | 3.11 | 7.71 |
| P1-MNT-04 | a+ | 5.49 | LC5 en el plano (corta) (P1-MNT-04) | 2.66 | 9.01 |
| P1-MNT-04 | a- | 6.02 | LC5 en el plano (corta) (P1-MNT-04) | 2.66 | 9.01 |
| P1-MNT-04 | b | 0.96 | Golpe lateral 200 N (corta) (P1-MNT-04) | 4.86 | 4.94 |
| P1-MNT-04 | b50 | 1.93 | Golpe lateral 200 N (corta) (P1-MNT-04) | 4.86 | 4.94 |
| P1-MNT-04 | c+ | 1.04 | LC5 en el plano (corta) (P1-MNT-04) | 2.66 | 9.01 |
| P1-MNT-04 | c- | 0.86 | LC5 en el plano (corta) (P1-MNT-04) | 2.66 | 9.01 |

### Hallazgos cuantitativos

- **P1-MNT-01 — el puente de la C gobierna.** Apriete sostenido: σvm p99 = 19.9 MPa en el puente de 12 mm (la viga a mano con esa sección da 20.8 MPa, coincide) contra S_sost = 8.39 MPa → **FS = 0.32** (objetivo 3). structural.py informa σ = 2.60 MPa porque usa Z = b·leg_t²/6 de la pata (t = leg_t) y no la del puente. La C se abre 26.3 mm en el pie de la pata interior (análisis lineal: indica flexibilidad excesiva, no un valor exacto). Con el apriete actual el puente necesita t ≥ 38.5 mm [CALCULADO: viga, verificada por FEA] o bajar el brazo/apriete. Además la pieza se imprime con el ancho (y) como Z: la flexión de placa ancha genera σZ ≈ ν·σx = 10.0 MPa a través de capas contra S_Z,sost = 3.21 MPa.
- **P1-MNT-05/06 — brazo del tope de marcha.** El tornillo de trimado es vertical y apoya en la cara inferior de la tapa, inclinada θ: sin fricción la reacción es normal a esa cara y su brazo respecto del pivote es u = 30 mm, no hypot(30, v_bot) = 90 mm como en structural.py. Con la cola trabada, el FEA da F_tope = 10411 N (estática con el centro del tope: 11757 N) y F_pivote = 10111 N. La cuna (MNT-05) queda con FS = 3.40; la **tapa MNT-06** recibe el tope en un Ø25 y su FS es 0.74 (σvm máx. 32.5 MPa, compresión entre tope y tubo; presión media en el tope F/A = 21.2 MPa contra S_corta = 24.0 MPa). En marcha normal el mismo brazo multiplica por 3.0 la fuerza sostenida del tope respecto de structural.py.
- **P1-MNT-04 — ranuras pasantes de las tuercas M6 en la raíz.** FS gobernante 0.86 (caso c-: Combinado oblicuo: a- + b (superposición lineal); criterio s1) con el máximo en (71.2, 39.0, 51.5) mm: esquina viva de la ranura/raíz, singular (cambia +30 % al refinar), mientras el p99 converge; con el p99 el FS es 2.20. Con el reparto de structural.py (100 N por mejilla) σvm máx* = 11.1 MPa contra 4.86 MPa a mano (Z = L·t²/6 con L = 64 mm no descuenta las dos ranuras de 10.4 mm ni la concentración en sus esquinas).

<!-- FEA:AUTO:FIN -->
