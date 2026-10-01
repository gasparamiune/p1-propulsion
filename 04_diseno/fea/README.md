# FEA de las piezas impresas críticas — P1-MNT-01, P1-MNT-05, P1-MNT-04

FEA lineal elástico 3D de las tres piezas de PETG más cargadas del montaje: abrazadera de
popa en C (MNT-01), cuna basculante (MNT-05, modelada con su tapa MNT-06 y el tubo de cola) y
mejilla de horquilla (MNT-04). La geometría, las cargas y los admisibles se leen del proyecto en
cada corrida. Por eso todas las cifras de resultados están en el bloque AUTO del final: lo
regenera `fea_run.py` y no se edita a mano.

## Archivos y uso

| Archivo | Qué hace |
|---|---|
| `fea_run.py` | CLI. Corre las 3 piezas con malla gruesa y fina, escribe `resultados_fea.json`, `img/*.png` y el bloque AUTO de este README |
| `fea_parts.py` | Modelo de cada pieza: geometría (build(p) + consultas al CAD), BCs, cargas y casos |
| `fea_model.py` | Interfaces de resortes (Winkler, cuerpo rígido, unilaterales), iteración de contacto, post-proceso |
| `fea_core.py` | Malla gmsh, espacio P2, ensamble vectorizado, cargas de superficie y solver PCG de dos niveles |
| `fea_plot.py` | Mapas de tensión sobre la superficie (matplotlib) |
| `../../tests/test_fea.py` | Viga en voladizo contra la solución analítica, verificación cruzada con scikit-fem, cuerpo rígido + Winkler, malla gruesa de MNT-04 y FS > 0 en el JSON |

```bash
python 04_diseno/fea/fea_run.py              # todo: ~2 min con 3 procesos (límite pedido: 6 min)
python 04_diseno/fea/fea_run.py --serial     # un proceso (~3,5 min)
python 04_diseno/fea/fea_run.py --quick --out /tmp/q.json   # solo malla gruesa, sin imágenes (~45 s)
python 04_diseno/fea/fea_run.py --only P1-MNT-05 --h P1-MNT-05=10,6   # otra pieza / otros tamaños de malla
pytest tests/test_fea.py                     # ~10 s
```

Dependencias: `gmsh`, `scipy`, `numpy`, `matplotlib`, `build123d`. `scikit-fem` solo se usa en el
test. Las tres ya están en `requirements.txt` como opcionales de FEA. gmsh necesita
`libglu1-mesa` del sistema.

## Método

1. **Geometría.** `params.load()` y luego el `build(p)` de cada módulo de pieza, en su marco
   natural (BOTE, UNIDAD u HORQUILLA a ψ = 0). Se exporta un STEP temporal que gmsh importa por
   OCC. Si esa importación falla, el script volumetriza `04_diseno/stl/asm/<ID>.stl`.
2. **Valores que el módulo no expone.** Los ejes de los tornillos de apriete, del buje de
   dirección, de los pernos de la tapa y del tornillo de trimado se leen de las caras cilíndricas
   del CAD (OCP `BRepAdaptor_Surface`). La huella de la base de horquilla sale del CAD de MNT-03.
   No hay posiciones copiadas a mano.
3. **Malla.**
   - Tetraedros de gmsh: Delaunay 3D con optimización.
   - Tamaño global `h`, refinamiento por curvatura (n elementos por 2π en agujeros) y, en
     MNT-05, esferas de refinamiento a h/2 en la pared pivote–tubo y en el apoyo del tope.
   - Malla gruesa ≈ 2·h de la fina.
4. **Elementos.**
   - Tetraedros cuadráticos P2 de 10 nodos con aristas rectas, integrados con 4 puntos (exacto).
   - El ensamble es vectorizado y propio. Coincide con `skfem.ElementTetP2` hasta 3·10⁻¹¹ en
     la flecha de una viga ([CALCULADO], test).
   - Por qué no se usó el ensamble de scikit-fem: tarda ~20 s en 2,6·10⁴ elementos. Con
     SuperLU directo, factorizar 1,3·10⁵ gdl llevó 92 s con orden MMD, y 189 s y ~9 GB con
     COLAMD ([CALCULADO]: medido en esta máquina).
5. **Solver.**
   - Gradiente conjugado precondicionado, tolerancia relativa 10⁻⁷.
   - El precondicionador es de dos niveles. El nivel grueso es la interpolación P1 de la misma
     malla (Galerkin, factorizado con LU dispersa); el suavizado es Chebyshev–Jacobi de grado 3.
   - Converge en 15–80 iteraciones por solución.
6. **Apoyos y contacto.**
   - **Resortes de superficie Winkler:** k en N/mm³, normales y con rigidez tangencial
     opcional.
   - **Contacto unilateral:** solo compresión, resuelto por iteración de conjunto activo. La
     malla fina arranca del estado de contacto convergido en la gruesa.
   - **Cuerpos rígidos de 6 gdl** (el tubo) acoplados por resortes normales.
   - **Perno sin fricción.** Se modela con resortes radiales exactos: la normal es radial en
     cada punto de cuadratura. Con la normal de la faceta, un agujero facetado se comporta como
     una llave Allen. En MNT-05 eso se llevaba ~1/3 del momento por el pivote y bajaba la fuerza
     en el tope ([CALCULADO]: corrida de depuración).
   - **Pernos:** resortes entre los desplazamientos promedio de dos parches.
7. **Post-proceso.**
   - **Campo de tensiones:** en P2 la tensión es lineal por elemento. Se evalúa exacta en los
     vértices y se promedia por nodo, ponderada por volumen.
   - **Criterios:** von Mises (σvm), principal máxima (σ1) y σZ = nᵀσn, donde
     n = R(META['print_rot'])ᵀ·ẑ es la dirección Z de impresión en el marco de la pieza.
   - Para cada criterio se reportan tres valores:
     - **máx. global:** incluye las singularidades donde se aplican cargas y apoyos concentrados.
     - **p99:** la tensión que se supera solo en el 1 % del volumen (percentil ponderado por
       volumen nodal). Filtra los picos puntuales sin depender de un radio elegido.
     - **máx\*:** el máximo fuera de las zonas de aplicación, es decir de los nodos a más de
       r_excl = máx(4 mm, h_fina) de una carga o apoyo concentrado: tuercas, bujes, pernos,
       tope y el empotramiento de MNT-04. Las interfaces distribuidas (espejo, asiento del tubo)
       no se excluyen. Las cargas aplicadas sobre parches tienen bordes que crecen sin límite al
       refinar. **Ese pico no es una tensión de diseño.**
   - **FS** = admisible / máx\* para cada criterio. El FS gobernante es el menor de los tres. El
     JSON también trae el FS con el máximo global y con el p99.

## Material, admisibles y anisotropía

- **Elasticidad.** E = `materials.PETG.E_mpa`. ν = 0,38 [ESTIMADO: copoliésteres amorfos
  0,37–0,40; no hay dato en inputs.yaml]. Material isotrópico equivalente y macizo.
- **Admisibles.** Se leen de `inputs.yaml` en cada corrida; los valores vigentes están en el
  bloque AUTO.
  - En XY: `S_corta = σ_XY·f_agua·f_temp·f_proceso` y `S_sost = S_corta·f_creep`.
  - En Z: `S_Z = mín(σ_Z, f_z·σ_XY)·f_agua·f_temp·f_proceso` (·f_creep si la carga es
    sostenida).
  - En Z se toma el **menor** de los dos datos y no `σ_Z·f_z`. Hoy `σ_Z ≈ f_z·σ_XY` por
    construcción en inputs.yaml, y multiplicar ambos contaría dos veces la misma debilidad
    entre capas.
- **Duración de cada caso.** El apriete de MNT-01 es una carga sostenida. Los impactos y la
  cola trabada son de corta duración. El caso de impacto incluye el apriete, pero se compara con
  S_corta, igual que en structural.py; el apriete solo ya se verifica contra S_sost en el caso (a).
- **Anisotropía.** σZ, la tensión normal a las capas, se compara con S_Z. Hay dos fuentes de
  anisotropía que no se modelan, ambas desfavorables:
  - la diferencia de rigidez entre XY y Z;
  - la anisotropía entre cordones dentro de la capa (research/R05 §A3).

## Condiciones de borde y cargas

### P1-MNT-01 — abrazadera en C (marco BOTE)

- **Espejo.** Es una cimentación Winkler unilateral con k = E_espejo/t_espejo
  (E_espejo = 500 MPa [ESTIMADO: madera o contrachapado ⟂ a la fibra, 300–800 MPa];
  t = `boat.transom.thickness_mm`). Actúa sobre dos superficies:
  - la cara x = 0 de la pata exterior;
  - el borde superior del espejo, bajo el puente (z = 0, x ∈ [−t, 0]).

  Se añade un 1 % de rigidez tangencial solo para fijar los modos rígidos; su reacción resulta
  despreciable. El momento en el puente de la C queda fijado por estática (el borde superior se
  despega), así que el valor de E_espejo solo redistribuye la presión en la pata exterior.
- **(a) Apriete sostenido.** F = T/(0,2·d) por tornillo, como en structural.py
  (T = `mount.clamp_screw_torque_nm`). Se aplica como presión uniforme en −x sobre el fondo del
  alojamiento hexagonal de cada tuerca cautiva. La tuerca empuja la pata interior hacia el
  interior del bote y la C se abre.
- **(b±) Impacto + apriete.** Se aplica H = 0,5·`loads.F_impact_peak_N` a la altura del pivote,
  hacia popa (+x) y hacia proa (−x). Se transmite como lo hace la horquilla, con tres cargas
  estáticamente equivalentes a H aplicada en z_pivote (el JSON trae `check_F`/`check_My`):
  1. H como presión de apoyo cosenoidal sobre el agujero del buje de dirección, uniforme en
     toda su altura.
  2. El momento de vuelco restante como presión lineal de la base de horquilla sobre el plato,
     en el lado comprimido de su huella.
  3. La tracción igual del perno de dirección (tuerca M16) sobre el anillo inferior del buje,
     bajo una arandela de Ø30 [ESTIMADO: ISO 7089].

  Los tornillos de apriete siguen precargados. Para el incremento se suma la rigidez axial de
  la cadena tornillo A4 + zapata + espejo, con el desplazamiento del caso (a) como referencia.
  El JSON reporta la fuerza resultante en cada tornillo.

### P1-MNT-05 — cuna basculante (marco UNIDAD), con tapa MNT-06 y tubo

El tope de marcha apoya en la **tapa**, no en la cuna, y la cuna y la tapa abrazan el tubo. Por
eso se modelan juntas: cuna + tapa (dos mallas) + tubo como cuerpo rígido.

- **Pivote.** Perno rígido fijo, unido por resortes radiales unilaterales:
  k = E_POM/t_buje (E_POM = 2,8 GPa [ESTIMADO]). Es una articulación sin fricción, más un
  resorte axial débil.
- **Tubo ↔ asiento de la cuna y de la tapa.** Contacto unilateral con penalización
  k = E_PETG/1 mm [SUPUESTO]. El tubo conserva los 4 gdl relevantes; se fijan su traslación
  axial y su giro propio, que no tienen rigidez.
- **4×M6 pasantes.** Resorte axial E·A_s/L (A_s = 20,1 mm² [ESTIMADO: ISO 898-1]) y resorte
  de corte de 10 % [SUPUESTO]. Unen la arandela Ø24 sobre la cuna con el asiento de la cabeza
  en el avellanado de la tapa. Se tratan como bilaterales (precargados).
- **Tope de marcha.** Contacto unilateral en un disco de Ø `architecture.stop_pad_d_mm` sobre
  la cara inferior de la tapa. Se centra donde el eje del tornillo de trimado (leído del CAD de
  MNT-03) corta esa cara. Sin fricción, la normal es −v.
- **Carga.** La cola trabada se representa con V = `loads.F_skeg_fuse_N` perpendicular al tubo,
  aplicada en u = u_c + M/V, de modo que el momento en el centro de la cuna sea
  `loads.M_tail_locked_Nm`, como en structural.py. Su sentido (−v) empuja la cola contra el
  tope. El sentido opuesto (basculación) lo limita el retén, que suelta a M_release ≪ M_lock;
  sin tope en ese sentido, no es un caso estructural de la cuna.

### P1-MNT-04 — mejilla de horquilla (marco HORQUILLA, mejilla de babor)

- **Pie.** Empotrado: todos los gdl fijos en z = z₀, la cara de apoyo sobre MNT-03. El
  empotramiento perfecto impide la expansión de Poisson y deja un borde singular, así que la
  banda de r_excl sobre el pie se excluye del máx\*. El momento flector a esa altura es ≥ 96 %
  del de la raíz.
- **(a±)** 0,5·H por mejilla en ±x, como apoyo cosenoidal sobre el agujero del perno Ø12.
- **(b)** Golpe lateral de 200 N completo en **una** mejilla (+y). Se aplica en el anillo
  alrededor del perno, en la cara interior, donde apoya el extremo del buje POM Ø20 de la cuna.
  Es la lectura literal y conservadora del caso.
- **(b50)** 100 N, el reparto que usa structural.py: el perno atado con anillos reparte el
  golpe entre las dos mejillas.
- **(c±)** Combinado oblicuo a± + b, por superposición lineal.

## Malla, calidad y convergencia

- **Tamaños de malla.** Están en `CFG` (`fea_run.py`). El bloque AUTO lista para cada malla el
  número de tetraedros, los gdl y la calidad γ = 3·r_in/r_circ.
- **Elementos de mala calidad.** En MNT-05 quedan unos pocos elementos con γ < 0,1. Están en la
  transición del asiento del tubo con el paso de eje y el rebaje del cartucho (u ≈ −53,
  v ≈ −70). En MNT-04 la malla gruesa tiene 3 en el arco del buje del pivote. Ninguno cae en la
  zona que gobierna.
- **Qué converge.** En las tres piezas el p99 y el desplazamiento máximo cambian unos pocos %
  entre la malla gruesa y la fina. El máx\* también converge donde no hay esquinas vivas
  (MNT-01, MNT-05).
- **Qué no converge.** En MNT-04 el máx\* está en la esquina viva de la ranura pasante de una
  tuerca M6. Es una singularidad geométrica real (en la pieza impresa el radio de esquina es de
  ~0,2 mm) y crece al refinar. Ahí el FS de diseño depende de la malla, y el JSON y la tabla
  dan también el FS con el p99.

## Comparación con structural.py y hallazgos

El bloque AUTO compara cada caso con la fila correspondiente de `resultados/estructural.json` y
da los hallazgos con las cifras vigentes. En resumen, el FEA encuentra tres diferencias de
modelo en el cálculo a mano:

1. **MNT-01.** La sección crítica de la C es el **puente** sobre el espejo (espesor =
   `shelf_top_z`), no la pata. structural.py usa `Z = b·leg_t²/6`. Con la sección del puente,
   la viga a mano coincide con el FEA dentro de ~5 % (p99 y máximo), y el FS sostenido queda muy por debajo de 3.
2. **MNT-05/06.** El tornillo de trimado es vertical y apoya en una cara inclinada θ. Sin
   fricción, el brazo de la reacción respecto del pivote es u_tope (≈ 30 mm), no
   hypot(30, v_bot) ≈ 90 mm. Eso triplica las fuerzas del tope, tanto la de marcha (sostenida)
   como la de cola trabada. La que no aguanta es la **tapa** MNT-06: queda en compresión entre
   el tope y el tubo.
3. **MNT-04.** Las ranuras pasantes de las tuercas M6, en la raíz, reducen la sección y
   concentran tensión. La fórmula `Z = L·t²/6` no las ve.

**Qué se recomienda al dueño del diseño** (este trabajo no modifica archivos fuera de
`04_diseno/fea/`):

- **MNT-01.** Engrosar el puente hasta el valor que da el bloque AUTO, o bajar el brazo
  tornillo–puente o el apriete. Corregir `Z` en structural.py.
- **MNT-05/06.**
  - Mover el tope para que actúe con un brazo grande y normal a la cara, por ejemplo un tope
    perpendicular a la tapa lejos del pivote.
  - Poner una placa metálica de reparto en la tapa.
  - Corregir `r_stop` en structural.py.
- **MNT-04.** Redondear las esquinas de las ranuras o reemplazarlas por insertos o tuercas
  cautivas más altas y fuera de la raíz.

## Limitaciones

- **Lineal, con desplazamientos pequeños.** En MNT-01 la apertura calculada de la C es de
  decenas de mm, fuera de ese supuesto. La conclusión (sección insuficiente) no cambia, pero la
  cifra exacta no es fiable.
- **Isotrópico equivalente y macizo.** No modela perímetros + relleno (`solid_frac` 0,85–0,9),
  ni la anisotropía de rigidez, ni las uniones entre cordones. σZ es una verificación
  aproximada.
- **Sin contacto real entre piezas.** Se usan resortes Winkler y de penalización, sin fricción.
  La precarga de los M6 de la tapa y del perno de dirección es desconocida; solo se precargan
  los tornillos de apriete.
- **Distribuciones de carga supuestas.** El apoyo cosenoidal en bujes, la presión lineal de la
  base de horquilla y el apoyo uniforme a lo largo del buje son supuestos. Están documentados
  arriba y en el código.
- **Impacto cuasi-estático.** Se usa la fuerza pico de sizing.json, sin dinámica. La fluencia
  lenta solo entra vía `f_creep`. No se evalúa fatiga: los admisibles `f_fatigue` están en
  structural.py. La temperatura y el agua entran solo como factores.
- **Solo tres piezas, y no la base de horquilla MNT-03.** MNT-06 entra únicamente como parte
  del modelo de MNT-05.

<!-- FEA:AUTO:INICIO (generado por fea_run.py; no editar a mano) -->

Corrida: 2026-10-01 · inputs v1.0 · 124 s · admisibles vigentes: S_corta = 23.97 MPa, S_sost = 8.39 MPa, S_Z corta/sost = 9.18/3.21 MPa [CALCULADO]

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
