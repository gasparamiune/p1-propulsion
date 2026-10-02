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
python 04_diseno/fea/fea_run.py              # todo (gruesa + fina + variantes), 3 procesos: ~12 min
python 04_diseno/fea/fea_run.py --quick      # solo malla gruesa, sin imágenes ni README (~2,5 min) → resultados_fea_quick.json
python 04_diseno/fea/fea_run.py --only P1-STE-01 --h P1-STE-01=10,6 --out /tmp/ste.json   # una pieza / otros tamaños
python 04_diseno/fea/fea_run.py --readme-only   # rehace hallazgos y bloque AUTO desde resultados_fea.json
python -m pytest -q tests/test_fea.py        # ~20 s
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

- **Geometría.** Alma central de ±0,35·Ø del alojamiento con empalmes cóncavos r 3 alma–tablero y
  alma–alojamiento (auditoría ronda 3, F-03: con el alma de ±Ø/4 el alojamiento entraba al tablero en una
  cuña de ~30° y el pico no convergía).
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
  vertical que da M_h = 1,10·F_b·Z_pivote, igual que structural_direccion (la estática es una sola
  función: `structural_direccion.bucket_reactions`).
- **Apoyos.** Pivotes (bujes POM P1-REV-03 de Ø `REV_bush_od`, k = E_POM/espesor del buje, unilaterales,
  sin fricción, resorte axial débil), con la reacción de cada lado por separado. **Trabas: una por brazo**
  (auditoría ronda 3). Cada émbolo Ø12 es un cuerpo rígido que **solo reacciona en la dirección
  tangencial** al círculo alrededor del pivote (el momento), como el cálculo a mano, y apoya solo en la
  **mitad de su agujero** que avanza hacia el perno bajo la carga (la otra mitad tiene la holgura del
  Ø12,5). Rigidez del émbolo 10⁶ N/mm (~100 × la del brazo) y resorte débil en las otras traslaciones.
- **Casos.** (a) R12, las dos trabas apoyan a la vez. (b)/(c) R12 con la traba −Y o +Y apoyando
  `REV_lock_mismatch` mm después (el émbolo tardío se corre ese desfase en el sentido de avance del brazo):
  da el **reparto máximo** entre trabas, que el cálculo a mano del pivote usa como `REV_lock_share_max` y
  `tests/test_fea.py` controla. (d)/(e) FALLA: el émbolo −Y o +Y no entró (su contacto se quita del modelo),
  con la reversa de sizing (límite del controlador): criterio FS ≥ 2.
- **Variantes** (V1, V2): FALLA DOBLE, un émbolo no entró y además reversa R12 sin límite del controlador:
  criterio de la fila a mano, sin fluencia (FS ≥ 1).

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
  **(c)/(c2)** Reversa R12 con el **reparto máximo admitido entre trabas** (`REV_lock_share_max`, del FEA
  del bucket con el desfase admitido) del lado de la traba +Y / −Y: reacción de cada pivote como apoyo
  cosenoidal en el agujero Ø(M12 + 0,4) del tornillo del pivote **más el momento del espaciador en voladizo**
  (P1-REV-02) como par lineal sobre su anillo de apoyo en la cara exterior de la oreja; fuerza de cada traba
  en la rosca M20 de su oreja. **(d)/(d2)** c/c2 + a con contacto resuelto. **Variante V1:** M_h completo en
  una traba (falla doble: un émbolo no entró y reversa sin límite del controlador), criterio sin fluencia.

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

- **Geometría.** Paredes de `W_OUT` = 5 mm engrosadas hacia afuera (auditoría ronda 3: con 3,5 mm la
  tracción entre capas daba FS 2,74); las caras interiores, el entrehierro del sensor hall y las luces de la
  manivela no cambian. Variante V1: sensibilidad con paredes de 4 mm.
- **Apoyos.** Cara inferior del ala y de las paredes sobre la tapa de contrachapado de la consola
  (Winkler unilateral, k = E_⟂/t_tapa, E_⟂ = 500 MPa [ESTIMADO]); 4 × M5 con arandela Ø10 empotrados, en
  las posiciones del módulo de la pieza (`bolt_xy()`).
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

Corrida: 2026-10-02 · inputs v2.0 · 3156 s [CALCULADO]

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
| P1-DRV-03 | gruesa | 10 | 13612 | 74541 | 0.004 | 0.189 | 27 |
| P1-DRV-03 | fina | 5 | 44732 | 235371 | 0.014 | 0.392 | 27 |
| P1-REV-01 | gruesa | 6 | 34799 | 197334 | 0.000 | 0.348 | 75 |
| P1-REV-01 | fina | 3.5 | 110120 | 577602 | 0.000 | 0.504 | 68 |
| P1-STE-01 | gruesa | 8 | 24881 | 136005 | 0.000 | 0.017 | 383 |
| P1-STE-01 | fina | 4.5 | 74578 | 389337 | 0.000 | 0.153 | 495 |
| P1-INT-02 | gruesa | 14 | 47904 | 268719 | 0.000 | 0.228 | 112 |
| P1-INT-02 | fina | 8 | 93218 | 507585 | 0.000 | 0.307 | 168 |
| P1-CTL-02 | gruesa | 6 | 11240 | 65856 | 0.082 | 0.393 | 0 |
| P1-CTL-02 | fina | 3 | 46480 | 259596 | 0.208 | 0.454 | 0 |

### Resultados (malla fina) — tensiones en MPa; FS = admisible / σ de diseño

σ de diseño = σvm máx* (máximo fuera de r_excl de cargas y apoyos) si cambia ≤ 20 % de la malla gruesa a la fina; si no converge (arista viva del CAD o astilla de malla), el máximo del promedio en una esfera de radio 3 mm («prom.»). En PETG el FS es el menor de σvm, σ1 y σZ (el criterio va entre paréntesis).

| Pieza | Caso | σvm máx | σvm p99 | σvm máx* | σvm prom. | σ diseño | u máx [mm] | **FS** | FS (p99) | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|
| P1-DRV-03 | a: Empuje Fa = 764 N hacia proa (tapa → 4 × M5) + radial 3 g + Fr = 143 N | 32.58 | 20.36 | 26.29 | 22.97 | 26.29 (máx*) | 0.286 | **4.37** | 5.65 | cumple |
| P1-DRV-03 | b: Empuje Fa = 764 N hacia popa (resalte trasero, reversa) + radial 143 N | 39.41 | 20.91 | 29.59 | 25.96 | 29.59 (máx*) | 0.296 | **3.89** | 5.50 | cumple |
| P1-REV-01 | a: Reversa: chorro F_b = 1408 N en la cuchara; M_h = 127 N·m; R12: las dos trabas apoyan a la vez (reparto nominal) | 49.74 | 14.08 | 27.37 | 19.49 | 27.37 (máx*) | 0.114 | **4.57** | 8.88 | cumple |
| P1-REV-01 | b: Reversa: chorro F_b = 1408 N en la cuchara; M_h = 127 N·m; R12: la traba −Y apoya 0.1 mm después que la +Y (desfase de fabricación admitido) | 87.53 | 18.79 | 45.08 | 31.62 | 45.08 (máx*) | 0.521 | **2.77** | 6.65 | cumple |
| P1-REV-01 | c: Reversa: chorro F_b = 1408 N en la cuchara; M_h = 127 N·m; R12: la traba +Y apoya 0.1 mm después que la −Y (desfase de fabricación admitido) | 81.84 | 18.74 | 49.83 | 34.01 | 49.83 (máx*) | 0.544 | **2.51** | 6.67 | cumple |
| P1-REV-01 | d: Reversa: chorro F_b = 698 N en la cuchara; M_h = 63 N·m; FALLA, reversa de sizing: el émbolo −Y no entró (M_h por el brazo +Y) | 63.41 | 13.58 | 33.69 | 23.08 | 33.69 (máx*) | 0.504 | **3.71** | 9.20 | cumple |
| P1-REV-01 | e: Reversa: chorro F_b = 698 N en la cuchara; M_h = 63 N·m; FALLA, reversa de sizing: el émbolo +Y no entró (M_h por el brazo −Y) | 76.66 | 14.46 | 36.30 | 25.36 | 36.30 (máx*) | 0.504 | **3.44** | 8.64 | cumple |
| P1-STE-01 | a: Desvío del chorro F_s = máx(sizing 323, R12 364) = 364 N repartido en el paso (centro de presión e = 66 mm, = structural) | 20.53 | 6.31 | 15.25 | 8.18 | 15.25 (máx*) | 0.072 | **15.74** | 38.03 | cumple |
| P1-STE-01 | b: F_s = 364 N en la boca de salida (últimos 20 mm; brazo ≈ L = 132 mm, conservador) | 37.90 | 11.67 | 37.50 | 15.09 | 37.50 (máx*) | 0.138 | **6.40** | 20.57 | cumple |
| P1-STE-01 | c: Reversa R12 (F_b = 1408 N, M_h = 127 N·m) con M_h completo en la traba +Y: pivotes (+ par del espaciador) y rosca M20 | 172.05 | 64.08 | 124.61 | 94.32 | 124.61 (máx*) | 0.769 | **1.93** | 3.75 | **NO CUMPLE** |
| P1-STE-01 | c2: Reversa R12 con M_h completo en la traba −Y: pivotes (+ par del espaciador) y rosca M20 de la oreja −Y | 179.66 | 80.92 | 133.07 | 101.84 | 133.07 (máx*) | 1.134 | **1.80** | 2.97 | **NO CUMPLE** |
| P1-STE-01 | d: Combinado: reversa (c) + desvío F_s en el paso (a) (maniobra en reversa) | 172.02 | 63.98 | 124.59 | 94.35 | 124.59 (máx*) | 0.780 | **1.93** | 3.75 | **NO CUMPLE** |
| P1-STE-01 | d2: Combinado: reversa (c2) + desvío F_s en el paso (a) | 179.67 | 80.94 | 133.07 | 102.15 | 133.07 (máx*) | 1.116 | **1.80** | 2.97 | **NO CUMPLE** |
| P1-INT-02 | a: Espárragos del pórtico: precarga 6944 N (10 N·m, K 0.18) ± vuelco Fa·h/Δx/2 = 422 N (Φ = 0.25) + corte Fa/4 | 63.39 | 14.67 | 9.55 | 9.55 | 9.55 (máx*) | 0.023 | **13.09** | 8.52 | cumple |
| P1-INT-02 | b: Golpe de fondo 50 kPa + presión de cierre 67 kPa en la abertura + tiro de la brida del conducto 4047 N (placa sola, sin la rigidez del conducto: conservador) | 51.41 | 30.02 | 51.10 | 51.10 | 51.10 (máx*) | 0.216 | **2.45** | 4.16 | cumple |
| P1-INT-02 | b2: Ídem (b) con el conducto P1-INT-01 como rigidizador rígido abulonado (cota rígida; = modelo de structural_toma) | 20.86 | 10.65 | 18.26 | 17.44 | 18.26 (máx*) | 0.048 | **6.85** | 11.73 | cumple |
| P1-CTL-02 | a: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-10, 0) mm (nervio entre ranuras); A cargada 847 mm² | 7.03 | 2.88 | 7.03 | 6.85 | 7.03 (máx*) | 0.813 | **3.41** | 8.34 | cumple |
| P1-CTL-02 | b: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-62, -12) mm (tapa ancha junto a la ranura del bucket); A cargada 1472 mm² | 4.35 | 2.22 | 4.35 | 3.66 | σZ 2.63 (máx*) | 0.419 | **3.49** (Z) | 10.81 | cumple |

\* máximo fuera de las zonas de aplicación de cargas/apoyos concentrados (r_excl en la tabla de convergencia); el máximo global incluye singularidades de aplicación y se reporta para transparencia.

### Convergencia (gruesa → fina)

| Pieza | Caso | r_excl [mm] | σvm p99 | σvm máx* | σvm máx global | u máx [mm] |
|---|---|---|---|---|---|---|
| P1-DRV-03 | a | 5 | 21.40 → 20.36 (-5 %) | 25.54 → 26.29 (+3 %) | 28.07 → 32.58 (+14 %) | 0.2824 → 0.2861 (+1 %) |
| P1-DRV-03 | b | 5 | 21.98 → 20.91 (-5 %) | 29.60 → 29.59 (-0 %) | 33.02 → 39.41 (+16 %) | 0.2920 → 0.2962 (+1 %) |
| P1-REV-01 | a | 4 | 14.40 → 14.08 (-2 %) | 22.93 → 27.37 (+16 %) | 48.78 → 49.74 (+2 %) | 0.1133 → 0.1137 (+0 %) |
| P1-REV-01 | b | 4 | 20.16 → 18.79 (-7 %) | 40.35 → 45.08 (+10 %) | 77.84 → 87.53 (+11 %) | 0.5212 → 0.5215 (+0 %) |
| P1-REV-01 | c | 4 | 20.48 → 18.74 (-9 %) | 40.67 → 49.83 (+18 %) | 81.09 → 81.84 (+1 %) | 0.5440 → 0.5445 (+0 %) |
| P1-REV-01 | d | 4 | 14.45 → 13.58 (-6 %) | 29.11 → 33.69 (+14 %) | 54.91 → 63.41 (+13 %) | 0.5003 → 0.5045 (+1 %) |
| P1-REV-01 | e | 4 | 15.63 → 14.46 (-8 %) | 29.95 → 36.30 (+17 %) | 73.75 → 76.66 (+4 %) | 0.5001 → 0.5043 (+1 %) |
| P1-STE-01 | a | 4 | 6.68 → 6.31 (-6 %) | 12.39 → 15.25 (+19 %) | 13.91 → 20.53 (+32 %) | 0.0701 → 0.0720 (+3 %) |
| P1-STE-01 | b | 4 | 12.58 → 11.67 (-8 %) | 31.06 → 37.50 (+17 %) | 31.06 → 37.90 (+18 %) | 0.1351 → 0.1381 (+2 %) |
| P1-STE-01 | c | 4 | 57.77 → 64.08 (+10 %) | 114.83 → 124.61 (+8 %) | 151.83 → 172.05 (+12 %) | 0.4968 → 0.7688 (+35 %) |
| P1-STE-01 | c2 | 4 | 60.22 → 80.92 (+26 %) | 117.81 → 133.07 (+11 %) | 150.75 → 179.66 (+16 %) | 0.5967 → 1.1344 (+47 %) |
| P1-STE-01 | d | 4 | 57.73 → 63.98 (+10 %) | 114.81 → 124.59 (+8 %) | 151.79 → 172.02 (+12 %) | 0.5050 → 0.7795 (+35 %) |
| P1-STE-01 | d2 | 4 | 60.03 → 80.94 (+26 %) | 117.81 → 133.07 (+11 %) | 150.76 → 179.67 (+16 %) | 0.5793 → 1.1164 (+48 %) |
| P1-INT-02 | a | 8 | 14.07 → 14.67 (+4 %) | 9.00 → 9.55 (+6 %) | 63.94 → 63.39 (-1 %) | 0.0194 → 0.0226 (+14 %) |
| P1-INT-02 | b | 8 | 27.79 → 30.02 (+7 %) | 47.52 → 51.10 (+7 %) | 47.80 → 51.41 (+7 %) | 0.2047 → 0.2162 (+5 %) |
| P1-INT-02 | b2 | 8 | 10.29 → 10.65 (+3 %) | 17.57 → 18.26 (+4 %) | 17.71 → 20.86 (+15 %) | 0.0458 → 0.0485 (+5 %) |
| P1-CTL-02 | a | 4 | 3.20 → 2.88 (-11 %) | 6.89 → 7.03 (+2 %) | 6.89 → 7.03 (+2 %) | 0.7892 → 0.8127 (+3 %) |
| P1-CTL-02 | b | 4 | 2.26 → 2.22 (-2 %) | 4.05 → 4.35 (+7 %) | 4.05 → 4.35 (+7 %) | 0.4020 → 0.4195 (+4 %) |

### Comparación con el cálculo a mano (resultados/estructural.json)

σ FEA = σvm de la región de la pieza que modela la fila (máx* salvo que se indique promedio en volumen), escalada a la carga de la fila (columna «×»). FS con el admisible de la fila. Dif = (FS_FEA − FS_mano)/FS_mano.

| Pieza | Fila structural_*.py | Caso FEA · región | × | σ mano [MPa] | σ FEA [MPa] (p99) | FS mano | FS FEA | Dif |
|---|---|---|---|---|---|---|---|---|
| P1-DRV-03 | Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa) | a · mejillas (prom. esfera) | 1.00 | 1.02 | 17.97 (7.79) | 112.30 | 6.40 | -94 % ⚠ |
| P1-DRV-03 | Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico | a · tablero_y_alma (máx*) | 1.00 | 16.59 | 26.29 (22.80) | 6.93 | 4.37 | -37 % ⚠ |
| P1-DRV-03 | Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo | b · alojamiento (prom. esfera) | 1.00 | 2.99 | 9.47 (9.47) | 80.29 | 25.34 | -68 % ⚠ |
| P1-REV-01 | Brazo trabado: flexión en su plano con M_h completo (bucket R12, corta) | b · brazos (máx*) | 1.00 | 35.21 | 45.08 (21.94) | 3.55 | 2.77 | -22 % |
| P1-REV-01 | Brazo trabado: flexión en su plano con M_h completo (reversa sizing, fatiga de soldadura) | b · brazos (máx*) | 0.50 | 17.46 | 22.36 (10.88) | 3.89 | 3.04 | -22 % |
| P1-REV-01 | Cuchara como viga entre brazos (bucket R12, corta) | a · cuchara (máx*) | 1.00 | 2.30 | 4.90 (4.13) | 54.32 | 25.49 | -53 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta) | a · cuchara (máx*) | 0.52 | 3.89 | 2.57 (2.16) | 32.15 | 48.73 | +52 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja (fatiga de soldadura, 1e5) | a · cuchara (máx*) | 0.52 | 3.89 | 2.57 (2.16) | 17.49 | 26.51 | +52 % ⚠ |
| P1-REV-01 | Cuchara abierta a torsión con un solo brazo trabado (FALLA: un émbolo no entró; reversa sizing) | d · cuchara (máx*) | 1.00 | 48.53 | 22.87 (7.89) | 2.58 | 5.46 | +112 % ⚠ |
| P1-REV-01 | Pivote: aplastamiento del brazo + aro (buje Ø22 × 14), R12 con reparto máx. | b · pivotes (promedio) | 1.00 | 7.74 | 10.02 (32.65) | 16.15 | 12.48 | -23 % |
| P1-REV-01 | Agujero de traba: aplastamiento del brazo con M_h completo (émbolo Ø12, R12) | b · traba (promedio) | 1.00 | 39.12 | 12.64 (53.16) | 3.20 | 9.89 | +209 % ⚠ |
| P1-STE-01 | Flexión del tubo por el desvío del chorro (fatiga, sizing) | a · tubo (máx*) | 0.89 | 0.62 | 6.68 (3.52) | 145.87 | 13.47 | -91 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión en su plano (bucket R12, corta; pivote + traba, M_h completo en una traba) | c · orejas_bucket (máx*) | 1.00 | 52.37 | 124.61 (77.52) | 4.58 | 1.93 | -58 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión (reversa sizing, fatiga; reparto máx. entre trabas) | c · orejas_bucket (máx*) | 0.50 | 17.97 | 61.80 (38.44) | 5.01 | 1.46 | -71 % ⚠ |
| P1-STE-01 | Oreja del bucket: ligamento de la rosca M20 de la traba (M_h completo en una traba, R12) | c · orejas_bucket (máx*) | 1.00 | 60.98 | 124.61 (77.52) | 3.94 | 1.93 | -51 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión fuera del plano por el pivote en voladizo (R12, reparto máx.) | c · orejas_bucket (máx*) | 1.00 | 52.79 | 124.61 (77.52) | 4.55 | 1.93 | -58 % ⚠ |
| P1-STE-01 | Oreja de pivote (dentro de la de la bomba): flexión de la raíz | d · orejas_pivote (prom. esfera) | 1.00 | 2.33 | 23.66 (19.53) | 103.14 | 10.15 | -90 % ⚠ |
| P1-INT-02 | Paño lateral entre bulones del conducto y del ala: golpe de fondo | b2 · pano_lateral (máx*) | 1.00 | 1.17 | 18.26 (12.28) | 106.56 | 6.85 | -94 % ⚠ |
| P1-INT-02 | Paño lateral entre bulones del conducto y del ala: golpe de fondo | b · pano_lateral (máx*) | 1.00 | 1.17 | 51.10 (36.45) | 106.56 | 2.45 | -98 % ⚠ |
| P1-INT-02 | Asiento cónico de la cabeza M8 en el 5083 (aplastamiento) | a · asiento_cono (promedio) | 1.01 | 50.82 | 47.52 (59.77) | 2.46 | 2.63 | +7 % |
| P1-INT-02 | Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono) | a · tapon_dk (promedio) | 1.01 | 42.51 | 22.54 (29.53) | 2.94 | 5.54 | +89 % ⚠ |
| P1-CTL-02 | Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta) | a · tapa (máx*) | 1.00 | 6.25 | 7.03 (5.14) | 3.84 | 3.41 | -11 % |
| P1-CTL-02 | Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta) | b · tapa (máx*) | 1.00 | 6.25 | 4.35 (2.61) | 3.84 | 5.51 | +44 % ⚠ |

### Variantes propuestas (evaluadas en el modelo FEA; la pieza NO se modificó)

| Pieza | Variante | Caso | σvm máx* | σvm p99 | u máx [mm] | FS (máx*) | FS (p99) | Veredicto |
|---|---|---|---|---|---|---|---|---|
| P1-REV-01 | V1: FALLA DOBLE: el émbolo −Y no entró + reversa R12 sin límite del controlador (criterio: sin fluencia, FS ≥ 1) | a | 67.71 | 27.29 | 1.017 | **1.85** | 4.58 | **NO CUMPLE** |
| P1-REV-01 | V2: FALLA DOBLE: el émbolo +Y no entró + reversa R12 (criterio: sin fluencia, FS ≥ 1) | a | 73.19 | 29.10 | 1.017 | **1.71** | 4.30 | **NO CUMPLE** |
| P1-CTL-02 | V1: sensibilidad: paredes de 4 mm (hoy W_OUT = 5) | a | 7.09 | 3.21 | 0.873 | **3.27** | 7.47 | cumple |
| P1-CTL-02 | V1: sensibilidad: paredes de 4 mm (hoy W_OUT = 5) | b | 6.06 | 2.72 | 0.515 | **2.89** | 8.80 | **NO CUMPLE** |

⚠ diferencia > 30 %: explicada en «Hallazgos».

### Hallazgos cuantitativos

- **P1-DRV-03: FS = 3.89** (objetivo 2, cumple); caso b, criterio vm: σ de diseño 29.6 MPa (máx*, máx* gruesa→fina -0 %) en (590.7, -23.0, 169.5) mm; σvm p99 20.9 MPa (FS p99 5.50). Máximo en la unión del alma central con el alojamiento Ø65 y el tablero (esquina viva, mecanizada o soldada): el empuje excéntrico y el radial entran al tablero por el alma. Cumple; conviene un radio ≥ 3 mm (o cordón de filete) en esa unión.
  - ⚠ «Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa)»: FS mano 112.30 vs FS FEA 6.40 (-94 %). La fila solo mira la flexión de la mejilla en su plano por Fa/2 (sección 12 × 150, muy rígida). El FEA pone el máximo de la mejilla en su unión con el tablero: el tablero cargado por el alojamiento flexiona y arrastra el borde superior de la mejilla fuera de su plano (marco tablero + mejillas). Mecanismo que la fila no ve; nivel bajo.
  - ⚠ «Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico»: FS mano 6.93 vs FS FEA 4.37 (-37 %). El máximo está en la unión del alma central (columna tablero–alojamiento) con el tablero: el momento de Fa excéntrico y el radial entran al tablero por el alma, con concentración en la esquina viva de esa unión; la viga biapoyada de la fila no la ve. Fila a mano no conservadora, pero el FS sigue sobre 2.
  - ⚠ «Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo»: FS mano 80.29 vs FS FEA 25.34 (-68 %). La fila es el corte medio del resalte (τ = Fa/(π·D·t)), un valor nominal; el FEA mide la flexión del resalte como placa anular (el aro apoya solo entre Da_max y D) y la del alojamiento en su unión con el alma. Ambos lejos del admisible.
- **P1-REV-01: FS = 2.51** (objetivo 2, cumple); caso c, criterio vm: σ de diseño 49.8 MPa (máx*, máx* gruesa→fina +18 %) en (353.9, -59.5, 36.7) mm; σvm p99 18.7 MPa (FS p99 6.67). Máximo en el brazo +Y junto al agujero de traba (flexión fuera del plano de la chapa de 4 mm) y ≈ 120 MPa en el borde inferior de la cuchara junto al brazo (soldadura). Causa: la traba está en un solo brazo, así que todo M_h pasa por la cuchara (sección abierta) a torsión hasta el brazo +Y (giro de 3,6 mm). **Propuesta al dueño de P1-REV-01/04**: (1) traba en los dos brazos (segundo émbolo en −Y o perno pasante) — V1 baja la cuchara a < 10 MPa y el giro a 0,2 mm, pero el lóbulo de traba de 4 mm queda en FS 1,3; (2) además brazos (o al menos los lóbulos de pivote y traba) de 6 mm, p. ej. con una arandela de refuerzo soldada — V2 da FS 2,3. Corregir structural_direccion: el brazo con la traba lleva todo M_h, no F_b/2.
  - ⚠ «Cuchara como viga entre brazos (bucket R12, corta)»: FS mano 54.32 vs FS FEA 25.49 (-53 %). Misma causa: la fila trata la cuchara como viga entre brazos con los dos extremos apoyados; con la traba de un solo lado la cuchara trabaja a torsión (sección abierta) y su borde inferior junto al brazo (soldadura) concentra.
  - ⚠ «Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta)»: FS mano 32.15 vs FS FEA 48.73 (+52 %). La franja empotrada (p_dinámica) no incluye la torsión de la cuchara; el FEA (escalado a p_dinámica/q) mide la tensión total de la chapa, dominada por esa torsión. Con traba en los dos brazos (V1) la cuchara baja a < 10 MPa.
  - ⚠ «Chapa de la cuchara: franja (fatiga de soldadura, 1e5)»: FS mano 17.49 vs FS FEA 26.51 (+52 %). La franja empotrada (p_dinámica) no incluye la torsión de la cuchara; el FEA (escalado a p_dinámica/q) mide la tensión total de la chapa, dominada por esa torsión. Con traba en los dos brazos (V1) la cuchara baja a < 10 MPa.
  - ⚠ «Cuchara abierta a torsión con un solo brazo trabado (FALLA: un émbolo no entró; reversa sizing)»: FS mano 2.58 vs FS FEA 5.46 (+112 %). 
  - ⚠ «Agujero de traba: aplastamiento del brazo con M_h completo (émbolo Ø12, R12)»: FS mano 3.20 vs FS FEA 9.89 (+209 %). La fila es la presión media de aplastamiento F/(d·t); el FEA promedia σvm en un anillo de 3 mm: por definición menor que el pico. Coinciden en el orden de magnitud; el pico local (fuera de r_excl) es el que no cumple.
- **P1-STE-01: FS = 1.80** (objetivo 2, **NO CUMPLE**); caso d2, criterio vm: σ de diseño 133.1 MPa (máx*, máx* gruesa→fina +11 %) en (329.5, -44.0, 77.6) mm; σvm p99 80.9 MPa (FS p99 2.97). El pico global (≈ 200 MPa) está en la arista viva donde la oreja de pivote corta el labio de entrada (x = X_pivote, sin radio en el CAD, con astillas de malla) y no converge: se usa el promedio en volumen y el máx* convergido de cada región. Gobierna la oreja del bucket +Y sobre la rosca M20 de la traba (ligamento de ~5 mm hasta el contorno de la oreja), con la reversa. Cumple; un radio de 1–2 mm en la arista oreja/labio quitaría la singularidad.
  - ⚠ «Flexión del tubo por el desvío del chorro (fatiga, sizing)»: FS mano 145.87 vs FS FEA 13.47 (-91 %). La fila trata el tubo Ø101 como viga (σ nominal < 1 MPa). En el FEA el máximo de la región del tubo está donde se le unen la torre y la oreja de pivote superior (entra el par del yugo y la reacción de los pernos): concentración local que la viga no ve. Nivel bajo (FS > 10).
  - ⚠ «Oreja del bucket: flexión en su plano (bucket R12, corta; pivote + traba, M_h completo en una traba)»: FS mano 4.58 vs FS FEA 1.93 (-58 %). La fila carga cada oreja con F_b/2 a 52 mm. Con la traba la oreja +Y recibe además la fuerza del émbolo (≈ 2,8 kN en la rosca M20, a 45 mm del pivote) y el pivote +Y toma más que el −Y; el máximo está en el lóbulo de la traba.
  - ⚠ «Oreja del bucket: flexión (reversa sizing, fatiga; reparto máx. entre trabas)»: FS mano 5.01 vs FS FEA 1.46 (-71 %). La fila carga cada oreja con F_b/2 a 52 mm. Con la traba la oreja +Y recibe además la fuerza del émbolo (≈ 2,8 kN en la rosca M20, a 45 mm del pivote) y el pivote +Y toma más que el −Y; el máximo está en el lóbulo de la traba.
  - ⚠ «Oreja del bucket: ligamento de la rosca M20 de la traba (M_h completo en una traba, R12)»: FS mano 3.94 vs FS FEA 1.93 (-51 %). 
  - ⚠ «Oreja del bucket: flexión fuera del plano por el pivote en voladizo (R12, reparto máx.)»: FS mano 4.55 vs FS FEA 1.93 (-58 %). La fila carga cada oreja con F_b/2 a 52 mm. Con la traba la oreja +Y recibe además la fuerza del émbolo (≈ 2,8 kN en la rosca M20, a 45 mm del pivote) y el pivote +Y toma más que el −Y; el máximo está en el lóbulo de la traba.
  - ⚠ «Oreja de pivote (dentro de la de la bomba): flexión de la raíz»: FS mano 103.14 vs FS FEA 10.15 (-90 %). La fila toma F/2 a 12 mm en 25 × 30. En el FEA los pernos de pivote reciben un par (reacciones opuestas en la mejilla Ø8 y en la rosca M6) porque el bucket empuja muy por encima del eje, y el máximo está en la arista viva donde la oreja cilíndrica corta el frente esférico (sin radio en el CAD; zona con astillas de malla).
- **P1-INT-02: FS = 2.45** (objetivo 2, cumple); caso b, criterio vm: σ de diseño 51.1 MPa (máx*, máx* gruesa→fina +7 %) en (525.6, 149.4, 10.0) mm; σvm p99 30.0 MPa (FS p99 4.16). Gobierna el golpe de fondo con la placa sola (b): máximo en la cara superior sobre el borde del apoyo del ala (unión cuerpo–ala), convergido. Con el conducto como rigidizador (b2) baja a ≈ 18 MPa. Los avellanados M8 del pórtico: σvm promedio bajo el cono ≈ presión de la fila a mano.
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 6.85 (-94 %). La fila apoya el paño en la línea de bulones del conducto (luz 68 mm a lo ancho). Placa sola (b): sin el conducto, la franja entre la abertura y el ala trabaja a lo largo y el máximo sale en la unión cuerpo–ala; es la cota conservadora. Con el conducto rígido (b2) se recupera el modelo de la fila; la realidad está entre ambos.
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 2.45 (-98 %). La fila apoya el paño en la línea de bulones del conducto (luz 68 mm a lo ancho). Placa sola (b): sin el conducto, la franja entre la abertura y el ala trabaja a lo largo y el máximo sale en la unión cuerpo–ala; es la cota conservadora. Con el conducto rígido (b2) se recupera el modelo de la fila; la realidad está entre ambos.
  - ⚠ «Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono)»: FS mano 2.94 vs FS FEA 5.54 (+89 %). La fila usa τ media en el cilindro Ø dk × (t − h_cono) suponiendo que todo el tiro pasa por corte puro. En el FEA la compresión de la zapata sobre la cara superior equilibra la precarga en el mismo lugar y el cilindro no está en corte puro: el promedio de σvm en ese volumen es menor. Fila conservadora.
- **P1-CTL-02: FS = 3.41** (objetivo 3, cumple); caso a, criterio vm: σ de diseño 7.0 MPa (máx*, máx* gruesa→fina +2 %) en (1820.6, -108.8, 674.0) mm; σvm p99 2.9 MPa (FS p99 8.34). Gobierna σZ (tracción entre capas, Z de impresión = z): la tapa cargada gira en sus bordes y flexiona las paredes de 3,5 mm, con la cara exterior a tracción vertical justo bajo la tapa. La fila a mano (franja de tapa) no lo ve; la tapa en sí da FS ≈ 3,3. **Propuesta al dueño de P1-CTL-02**: paredes de 5 mm (V1: FS 3,5) engrosadas hacia afuera para no mover el entrehierro del sensor hall; una tapa de 8 mm (V2) exige subir ZT para conservar la luz sobre el cubo. Además la pieza real es 5 perímetros + 30 % giroide (solid_frac 0,55): el FEA macizo es optimista.
  - ⚠ «Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta)»: FS mano 3.84 vs FS FEA 5.51 (+44 %). La fila es una franja 50 × 6 apoyada con luz 50; la tapa real está casi toda ranurada (ranuras de las palancas), y la palma carga el nervio de 6 mm entre las dos ranuras o la tapa angosta junto a la del bucket. Ver σZ: la flexión de las paredes cruza capas.

<!-- FEA:AUTO:FIN -->
