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

Corrida: 2026-10-02 · inputs v2.0 · 682 s [CALCULADO]

### Materiales y admisibles

| Pieza | Material | Admisible [MPa] | Criterio | FS objetivo | Marco |
|---|---|---|---|---|---|
| P1-DRV-03 | Al 5052/6082 | 115 (Al 6082-T651 soldado (ZAT)) | von Mises | 2 | BOTE |
| P1-REV-01 | Al 5083 | 125 (Al 5083-O/H111 (= ZAT)) | von Mises | 2 | BOQUILLA (bucket abajo) |
| P1-STE-01 | Al 6061-T6 | 240 (Al 6061-T6) | von Mises | 2 | BOQUILLA (δ = 0) |
| P1-INT-02 | Al 5083 | 125 (Al 5083-H111) | von Mises | 2 | BOTE |
| P1-CTL-02 | PETG | S_corta 23.97 · S_Z corta 9.18 | σvm, σ1 y σZ (Z de impresión (0.0, 0.0, -1.0)) | 3 | BOTE |

### Mallas

| Pieza | Malla | h [mm] | Tetraedros | gdl (P2) | γ mín | γ p1 | n(γ<0,05) |
|---|---|---|---|---|---|---|---|
| P1-DRV-03 | gruesa | 10 | 9836 | 55269 | 0.004 | 0.167 | 29 |
| P1-DRV-03 | fina | 5 | 36392 | 193158 | 0.013 | 0.396 | 25 |
| P1-REV-01 | gruesa | 6 | 26878 | 156429 | 0.001 | 0.347 | 45 |
| P1-REV-01 | fina | 3.5 | 68969 | 391512 | 0.003 | 0.431 | 61 |
| P1-STE-01 | gruesa | 8 | 22357 | 122553 | 0.001 | 0.018 | 314 |
| P1-STE-01 | fina | 4.5 | 69060 | 361194 | 0.001 | 0.177 | 378 |
| P1-INT-02 | gruesa | 14 | 46135 | 259128 | 0.000 | 0.219 | 119 |
| P1-INT-02 | fina | 8 | 89021 | 485712 | 0.000 | 0.311 | 162 |
| P1-CTL-02 | gruesa | 6 | 11013 | 64527 | 0.077 | 0.383 | 0 |
| P1-CTL-02 | fina | 3 | 41364 | 236448 | 0.157 | 0.465 | 0 |

### Resultados (malla fina) — tensiones en MPa, FS = admisible / σvm máx* (máx. fuera de zonas de carga)

| Pieza | Caso | σvm máx | σvm p99 | σvm máx* | u máx [mm] | FS (máx*) | FS (p99) | Veredicto |
|---|---|---|---|---|---|---|---|---|
| P1-DRV-03 | a: Empuje Fa = 764 N hacia proa (tapa → 4 × M5) + radial 3 g + Fr = 143 N | 31.36 | 21.06 | 31.36 | 0.313 | **3.67** | 5.46 | cumple |
| P1-DRV-03 | b: Empuje Fa = 764 N hacia popa (resalte trasero, reversa) + radial 143 N | 29.69 | 21.56 | 29.69 | 0.326 | **3.87** | 5.33 | cumple |
| P1-REV-01 | a: Reversa: chorro F_b = máx(sizing 698 N, R12 1408 N) = 1408 N en la cuchara; M_h = 127 N·m (traba + pivotes) | 300.91 | 69.69 | 285.50 | 3.641 | **0.44** | 1.79 | **NO CUMPLE** |
| P1-STE-01 | a: Desvío del chorro F_s = máx(sizing 323, R12 364) = 364 N repartido en el paso (centro de presión e = 66 mm, = structural) | 81.24 | 6.53 | 81.24 | 0.071 | **2.95** | 36.78 | cumple |
| P1-STE-01 | b: F_s = 364 N en la boca de salida (últimos 20 mm; brazo ≈ L = 132 mm, conservador) | 213.56 | 12.05 | 213.56 | 0.136 | **1.12** | 19.92 | **NO CUMPLE** |
| P1-STE-01 | c: Reversa: reacciones del bucket (F_b = 1408 N, M_h = 127 N·m) en orejas Ø8,4 y rosca M20 de la traba | 172.32 | 24.33 | 172.32 | 0.119 | **1.39** | 9.86 | **NO CUMPLE** |
| P1-STE-01 | d: Combinado: reversa (c) + desvío F_s en el paso (a) (maniobra en reversa) | 209.69 | 24.13 | 209.69 | 0.134 | **1.14** | 9.95 | **NO CUMPLE** |
| P1-INT-02 | a: Espárragos del pórtico: precarga 6944 N (10 N·m, K 0.18) ± vuelco Fa·h/Δx/2 = 422 N (Φ = 0.25) + corte Fa/4 | 62.94 | 15.31 | 9.86 | 0.023 | **12.67** | 8.17 | cumple |
| P1-INT-02 | b: Golpe de fondo 50 kPa + presión de cierre 67 kPa en la abertura + tiro de la brida del conducto 4059 N (placa sola, sin la rigidez del conducto: conservador) | 52.99 | 30.93 | 50.49 | 0.216 | **2.48** | 4.04 | cumple |
| P1-INT-02 | b2: Ídem (b) con el conducto P1-INT-01 como rigidizador rígido abulonado (cota rígida; = modelo de structural_toma) | 21.47 | 10.76 | 18.54 | 0.048 | **6.74** | 11.61 | cumple |
| P1-CTL-02 | a: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-10, 0) mm (nervio entre ranuras); A cargada 829 mm² | 7.25 | 3.46 | 7.25 | 0.934 | **3.00** (Z) | 6.92 | cumple |
| P1-CTL-02 | b: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-62, -12) mm (tapa ancha junto a la ranura del bucket); A cargada 1407 mm² | 6.01 | 3.09 | 6.01 | 0.586 | **2.74** (Z) | 7.75 | **NO CUMPLE** |

\* máximo fuera de las zonas de aplicación de cargas/apoyos concentrados (r_excl en la tabla de convergencia); el máximo global incluye singularidades de aplicación y se reporta para transparencia.

### Convergencia (gruesa → fina)

| Pieza | Caso | r_excl [mm] | σvm p99 | σvm máx* | σvm máx global | u máx [mm] |
|---|---|---|---|---|---|---|
| P1-DRV-03 | a | 5 | 22.05 → 21.06 (-5 %) | 27.04 → 31.36 (+14 %) | 27.04 → 31.36 (+14 %) | 0.3074 → 0.3130 (+2 %) |
| P1-DRV-03 | b | 5 | 22.68 → 21.56 (-5 %) | 27.93 → 29.69 (+6 %) | 27.93 → 29.69 (+6 %) | 0.3194 → 0.3256 (+2 %) |
| P1-REV-01 | a | 4 | 72.58 → 69.69 (-4 %) | 247.50 → 285.50 (+13 %) | 273.36 → 300.91 (+9 %) | 3.6100 → 3.6411 (+1 %) |
| P1-STE-01 | a | 4 | 6.76 → 6.53 (-4 %) | 10.94 → 81.24 (+87 %) | 13.28 → 81.24 (+84 %) | 0.0689 → 0.0707 (+3 %) |
| P1-STE-01 | b | 4 | 12.57 → 12.05 (-4 %) | 26.11 → 213.56 (+88 %) | 26.11 → 213.56 (+88 %) | 0.1327 → 0.1357 (+2 %) |
| P1-STE-01 | c | 4 | 24.89 → 24.33 (-2 %) | 72.65 → 172.32 (+58 %) | 92.60 → 172.32 (+46 %) | 0.1181 → 0.1190 (+1 %) |
| P1-STE-01 | d | 4 | 24.88 → 24.13 (-3 %) | 72.65 → 209.69 (+65 %) | 92.58 → 209.69 (+56 %) | 0.1321 → 0.1336 (+1 %) |
| P1-INT-02 | a | 8 | 14.85 → 15.31 (+3 %) | 9.43 → 9.86 (+4 %) | 65.23 → 62.94 (-4 %) | 0.0211 → 0.0233 (+9 %) |
| P1-INT-02 | b | 8 | 27.92 → 30.93 (+10 %) | 50.80 → 50.49 (-1 %) | 50.80 → 52.99 (+4 %) | 0.2055 → 0.2156 (+5 %) |
| P1-INT-02 | b2 | 8 | 10.53 → 10.76 (+2 %) | 17.49 → 18.54 (+6 %) | 18.01 → 21.47 (+16 %) | 0.0460 → 0.0485 (+5 %) |
| P1-CTL-02 | a | 4 | 3.91 → 3.46 (-13 %) | 7.32 → 7.25 (-1 %) | 7.32 → 7.25 (-1 %) | 0.9315 → 0.9339 (+0 %) |
| P1-CTL-02 | b | 4 | 3.13 → 3.09 (-1 %) | 5.10 → 6.01 (+15 %) | 5.10 → 6.01 (+15 %) | 0.5758 → 0.5858 (+2 %) |

### Comparación con el cálculo a mano (resultados/estructural.json)

σ FEA = σvm de la región de la pieza que modela la fila (máx* salvo que se indique promedio en volumen), escalada a la carga de la fila (columna «×»). FS con el admisible de la fila. Dif = (FS_FEA − FS_mano)/FS_mano.

| Pieza | Fila structural_*.py | Caso FEA · región | × | σ mano [MPa] | σ FEA [MPa] (p99) | FS mano | FS FEA | Dif |
|---|---|---|---|---|---|---|---|---|
| P1-DRV-03 | Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa) | a · mejillas (máx*) | 1.00 | 1.02 | 18.01 (7.95) | 112.30 | 6.38 | -94 % ⚠ |
| P1-DRV-03 | Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico | a · tablero_y_alma (máx*) | 1.00 | 16.60 | 28.28 (22.93) | 6.93 | 4.07 | -41 % ⚠ |
| P1-DRV-03 | Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo | b · alojamiento (máx*) | 1.00 | 2.99 | 27.14 (13.48) | 80.29 | 8.84 | -89 % ⚠ |
| P1-REV-01 | Brazo lateral: flexión (bucket R12, corta) | a · brazos (máx*) | 1.00 | 37.41 | 285.50 (76.80) | 3.34 | 0.44 | -87 % ⚠ |
| P1-REV-01 | Brazo lateral: flexión (reversa sizing, fatiga de soldadura) | a · brazos (máx*) | 0.50 | 18.55 | 141.60 (38.09) | 3.67 | 0.48 | -87 % ⚠ |
| P1-REV-01 | Cuchara como viga entre brazos (bucket R12, corta) | a · cuchara (máx*) | 1.00 | 3.51 | 119.07 (45.99) | 35.60 | 1.05 | -97 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta) | a · cuchara (máx*) | 0.52 | 8.73 | 62.18 (24.02) | 14.31 | 2.01 | -86 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja (fatiga de soldadura, 1e5) | a · cuchara (máx*) | 0.52 | 8.73 | 62.18 (24.02) | 7.79 | 1.09 | -86 % ⚠ |
| P1-REV-01 | Pivote: aplastamiento del brazo + refuerzo (buje Ø14 × 8) | a · pivotes (promedio) | 1.00 | 6.29 | 33.34 (93.56) | 19.89 | 3.75 | -81 % ⚠ |
| P1-REV-01 | Agujero de traba: aplastamiento del brazo (émbolo Ø12) | a · traba (promedio) | 1.00 | 58.68 | 41.46 (200.95) | 2.13 | 3.02 | +42 % ⚠ |
| P1-STE-01 | Flexión del tubo por el desvío del chorro (fatiga, sizing) | a · tubo (máx*) | 0.89 | 0.62 | 6.76 (3.55) | 145.87 | 13.31 | -91 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión en su plano (bucket R12, corta) | c · orejas_bucket (máx*) | 1.00 | 21.12 | 76.36 (38.06) | 11.36 | 3.14 | -72 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión (reversa sizing, fatiga) | c · orejas_bucket (máx*) | 0.50 | 10.47 | 37.87 (18.88) | 8.59 | 2.38 | -72 % ⚠ |
| P1-STE-01 | Oreja de pivote (dentro de la de la bomba): flexión de la raíz | d · orejas_pivote (máx*) | 1.00 | 2.33 | 209.69 (12.41) | 103.14 | 1.14 | -99 % ⚠ |
| P1-INT-02 | Paño lateral entre bulones del conducto y del ala: golpe de fondo | b2 · pano_lateral (máx*) | 1.00 | 1.17 | 18.54 (12.68) | 106.56 | 6.74 | -94 % ⚠ |
| P1-INT-02 | Paño lateral entre bulones del conducto y del ala: golpe de fondo | b · pano_lateral (máx*) | 1.00 | 1.17 | 50.49 (36.88) | 106.56 | 2.48 | -98 % ⚠ |
| P1-INT-02 | Asiento cónico de la cabeza M8 en el 5083 (aplastamiento) | a · asiento_cono (promedio) | 1.01 | 50.82 | 47.36 (60.01) | 2.46 | 2.64 | +7 % |
| P1-INT-02 | Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono) | a · tapon_dk (promedio) | 1.01 | 42.51 | 22.78 (32.77) | 2.94 | 5.49 | +87 % ⚠ |
| P1-CTL-02 | Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta) | a · tapa (máx*) | 1.00 | 6.25 | 7.25 (5.49) | 3.84 | 3.30 | -14 % |
| P1-CTL-02 | Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta) | b · tapa (máx*) | 1.00 | 6.25 | 6.01 (3.43) | 3.84 | 3.99 | +4 % |

### Variantes propuestas (evaluadas en el modelo FEA; la pieza NO se modificó)

| Pieza | Variante | Caso | σvm máx* | σvm p99 | u máx [mm] | FS (máx*) | FS (p99) | Veredicto |
|---|---|---|---|---|---|---|---|---|
| P1-REV-01 | V1: traba en ambos brazos (2.º émbolo en −Y), chapa 4 mm | a | 95.01 | 27.03 | 0.231 | **1.32** | 4.62 | **NO CUMPLE** |
| P1-REV-01 | V2: traba en ambos brazos + brazos y cuchara de 6 mm | a | 53.32 | 17.22 | 0.152 | **2.34** | 7.26 | cumple |

⚠ diferencia > 30 %: explicada en «Hallazgos».

### Hallazgos cuantitativos

- **P1-DRV-03: FS = 3.67** (objetivo 2, cumple); caso a, σvm máx* = 31.4 MPa en (593.3, 17.0, 171.2) mm, p99 21.1 MPa (FS p99 5.46).
  - ⚠ «Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa)»: FS mano 112.30 vs FS FEA 6.38 (-94 %). 
  - ⚠ «Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico»: FS mano 6.93 vs FS FEA 4.07 (-41 %). 
  - ⚠ «Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo»: FS mano 80.29 vs FS FEA 8.84 (-89 %). 
- **P1-REV-01: FS = 0.44** (objetivo 2, NO CUMPLE); caso a, σvm máx* = 285.5 MPa en (391.1, 53.5, 78.8) mm, p99 69.7 MPa (FS p99 1.79).
  - ⚠ «Brazo lateral: flexión (bucket R12, corta)»: FS mano 3.34 vs FS FEA 0.44 (-87 %). 
  - ⚠ «Brazo lateral: flexión (reversa sizing, fatiga de soldadura)»: FS mano 3.67 vs FS FEA 0.48 (-87 %). 
  - ⚠ «Cuchara como viga entre brazos (bucket R12, corta)»: FS mano 35.60 vs FS FEA 1.05 (-97 %). 
  - ⚠ «Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta)»: FS mano 14.31 vs FS FEA 2.01 (-86 %). 
  - ⚠ «Chapa de la cuchara: franja (fatiga de soldadura, 1e5)»: FS mano 7.79 vs FS FEA 1.09 (-86 %). 
  - ⚠ «Pivote: aplastamiento del brazo + refuerzo (buje Ø14 × 8)»: FS mano 19.89 vs FS FEA 3.75 (-81 %). 
  - ⚠ «Agujero de traba: aplastamiento del brazo (émbolo Ø12)»: FS mano 2.13 vs FS FEA 3.02 (+42 %). 
- **P1-STE-01: FS = 1.12** (objetivo 2, NO CUMPLE); caso b, σvm máx* = 213.6 MPa en (295.7, 12.5, 46.4) mm, p99 12.1 MPa (FS p99 19.92).
  - ⚠ «Flexión del tubo por el desvío del chorro (fatiga, sizing)»: FS mano 145.87 vs FS FEA 13.31 (-91 %). 
  - ⚠ «Oreja del bucket: flexión en su plano (bucket R12, corta)»: FS mano 11.36 vs FS FEA 3.14 (-72 %). 
  - ⚠ «Oreja del bucket: flexión (reversa sizing, fatiga)»: FS mano 8.59 vs FS FEA 2.38 (-72 %). 
  - ⚠ «Oreja de pivote (dentro de la de la bomba): flexión de la raíz»: FS mano 103.14 vs FS FEA 1.14 (-99 %). 
- **P1-INT-02: FS = 2.48** (objetivo 2, cumple); caso b, σvm máx* = 50.5 MPa en (533.1, -151.9, 10.0) mm, p99 30.9 MPa (FS p99 4.04).
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 6.74 (-94 %). 
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 2.48 (-98 %). 
  - ⚠ «Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono)»: FS mano 2.94 vs FS FEA 5.49 (+87 %). 
- **P1-CTL-02: FS = 2.74** (objetivo 3, NO CUMPLE); caso b, σvm máx* = 6.0 MPa en (1742.7, -107.0, 677.0) mm, p99 3.1 MPa (FS p99 7.75).

<!-- FEA:AUTO:FIN -->
