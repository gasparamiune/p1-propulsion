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
| `../../tests/test_fea.py` | Viga en voladizo contra la solución analítica, verificación cruzada con scikit-fem, cuerpo rígido + Winkler, malla gruesa de CTL-02, estática del bucket contra structural_direccion, carga aplicada = estática en REV-01/STE-01 (setup con malla muy gruesa: resultante, M_y y vector momento; piloto y cuerpo ajustado del émbolo como apoyos lineales en sus agujeros H7, sin precarga), regla de la σ de diseño sin convergencia (FEA-R5-01, unitario y sobre el JSON), traba única con M_h completo (casos d/e/f/g), STE-01 sin caso p ni media de Goodman (cuerpo ajustado, ronda 5), bordes de agujeros cargados (también f/f2 de STE-01), aristas vivas declaradas solo en los pies de los lóbulos de STE-01, mismo r_excl en `--quick` que en la corrida completa, sin caras astilla en las orejas del bucket (re-auditoría del cierre de la ronda 5: FEA-1/2/3, TEST-1) y cumplimiento en el JSON |

```bash
python 04_diseno/fea/fea_run.py              # todo (gruesa + fina + variantes), 3 procesos: ~12 min
python 04_diseno/fea/fea_run.py --quick      # solo malla gruesa (mismo r_excl que la corrida completa), sin imágenes ni README (~2,5 min) → resultados_fea_quick.json
python 04_diseno/fea/fea_run.py --only P1-STE-01 --h P1-STE-01=10,6 --out /tmp/ste.json   # una pieza / otros tamaños
python 04_diseno/fea/fea_run.py --only P1-REV-01 P1-STE-01 --merge   # rehace esas piezas dentro de resultados_fea.json + README
python 04_diseno/fea/fea_run.py --readme-only   # rehace hallazgos y bloque AUTO desde resultados_fea.json
python -m pytest -q tests/test_fea.py        # ~1 min [ESTIMADO] (incluye dos setups de malla muy gruesa)
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
   en los apoyos críticos (pivotes y trabas del bucket y el punto caliente de la ronda 3 en la cara exterior
   de cada brazo, a ~47 mm [CALCULADO: FEA ronda 3] bajo el pivote; pivotes, agujeros de los cuerpos de émbolo y orejas de
   pivote de STE-01; espárragos de INT-02). Las esferas quedan en `mallas.<nivel>.refine` del JSON. Malla
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
   cargas y apoyos concentrados (pernos, roscas, avellanados, arandelas); h_fina es el de la configuración también en
   `--quick`, que no corre la malla fina (re-auditoría del cierre de la ronda 5, FEA-1: con el h de la gruesa la prueba
   rápida excluía 8 mm en lugar de 4,5 y dejaba afuera los máximos junto a los agujeros [CALCULADO: re-auditoría]).
   **FS = admisible / σvm máx\***
   (metales dúctiles: von Mises). En PETG también σ1 y σZ (normal a las capas) contra S_Z; el FS es el
   menor de los tres. Además se resume cada **región** de la pieza (máx\*, p99 y **promedio en
   volumen**): las filas del cálculo a mano de aplastamiento/corte se comparan con el promedio en el
   volumen que la fila representa (anillo alrededor del agujero, cilindro del tapón, capa bajo el cono).
   - **Borde de agujeros cargados por perno («lug», auditoría ronda 4, F3).** La exclusión r_excl alrededor
     de un agujero cargado tapa el pico de sección neta del borde a ±90° de la carga (y parte del ligamento
     del agujero del émbolo de STE-01). Se eligió reportarlo como **verificación aparte**: en cada caso, para cada
     agujero cargado (trabas y pivotes de REV-01; agujeros H7 de los pivotes y de los cuerpos de émbolo de STE-01, `pivote_*` y `embolo_*`) se toman los nodos
     de la superficie del agujero con |cos θ| ≤ 0,5 [SUPUESTO: ventana θ = 60…120° desde la dirección de la
     carga, proyectada ⟂ al eje] y se reporta el máximo de la tensión **circunferencial |σθ|** (la de sección
     neta del «lug») y el σvm máx. de la ventana. La dirección de la carga es la reacción de la interfaz
     (REV-01) o la fuerza aplicada (STE-01). **FS = admisible del caso / |σθ| del borde**, con el mismo objetivo
     (≥ 2); el FS del caso es el menor entre el del cuerpo (máx\*) y el de los bordes (criterio «borde»). El
     σvm de la ventana es informativo: en el arco de contacto (p. ej. la mitad de apoyo de las trabas de REV-01,
     que termina en θ = 90°, con el perno rígido que no acompaña el giro del brazo) incluye el aplastamiento y el
     borde del contacto, que verifican las filas de aplastamiento. Se compara gruesa → fina; el agujero de una
     traba deshabilitada no se evalúa como cargado y sale de las zonas excluidas (su entorno sí se evalúa). Se informa además el |σθ| **interior** (nodos a ≥ 2 mm de los dos extremos del agujero [SUPUESTO], `sigma_theta_interior_MPa`): separa el pico de la esquina agujero–cara (donde llega el borde de un apoyo lineal) del de sección neta; es informativo, el FS usa la ventana completa.
   - **Convergencia (F4 y re-auditoría FEA-R5-01).** Si el máx\* o el |σθ| de un borde cambia > 10 % de la malla
     gruesa a la fina se calcula una extrapolación tipo Richardson σ_ext = σ_f + (σ_f − σ_g)/(r^p − 1), con
     r = h_g/h_f locales (esfera de refinamiento que contiene el punto) y p = 2 [SUPUESTO: tensión con P2 en campo
     suave]. **La falta de convergencia nunca baja la σ de diseño**: si el cambio pasa el 20 %, la σ de diseño es
     máx(σ fina, σ_ext) (`fea_run.design_sigma`, `edge_block`). El promedio en volumen en una esfera de 3 mm solo se
     admite en una **arista viva del CAD nombrada** por el setup de la pieza (`aristas_vivas` en el JSON; hoy solo
     P1-STE-01, en los pies de los lóbulos engrosados: re-auditoría del cierre de la ronda 5, FEA-3). Entre 10 y 20 % la extrapolación es informativa, pero si su FS queda bajo el objetivo en un
     caso de diseño la pieza **no cumple** (`richardson_bajo_objetivo` en el JSON).
   - **Casos de diseño e informativos.** El FS mínimo de la pieza se toma solo de los casos de diseño
     (`casos_diseno` en el JSON); los informativos (p. ej. REV-01 a/b, con las dos trabas) se reportan igual.
     Los casos de **fatiga** (reversa de sizing) se comparan con el admisible de fatiga del material
     (`S_fat`) con el mismo objetivo: el pico del ciclo 0 → máx. contra el límite R = −1 (convención conservadora del
     proyecto). Si un caso lleva además una **tensión media constante** (una precarga; hoy ningún caso la lleva: desde el
     cierre de la ronda 5 el cuerpo del émbolo de STE-01 va ajustado, sin precarga, y f/f2 son ciclos 0 → máx.), el caso
     guarda la precarga sola resuelta con el mismo conjunto activo (`u_media`; el sistema es
     lineal, así que la parte cíclica total − media es exacta) y se usa la corrección de **Goodman** sobre ese admisible:
     σ_eq = σ_cíclica/(1 − σ_m⁺/S_u) contra `S_fat`, o sea FS = S_fat·(1 − σ_m⁺/S_u)/σ_cíclica (FS sobre la carga de
     servicio con la precarga fija). σ_m⁺ es, nodo a nodo, máx(0, σ1, σvm con el signo de la traza) de la precarga
     (una media de compresión no se aprovecha); en los bordes, máx(σθ de la precarga, 0) con |σθ| cíclica
     (`fea_model.goodman_fields`, `hole_edge`). S_u de 6061-T6 = 260 MPa [ESTIMADO: EN 755-2, Rm mín.].
6. **Comparación con el cálculo a mano.** Cada fila de `resultados/estructural.json` se compara con la
   región que modela y el admisible de la propia fila. Las filas de fatiga de la reversa se comparan con los
   casos de sizing **corridos** (no se escala un caso con contacto; auditoría ronda 4, F2). Solo se escala un
   caso cuando el problema es homogéneo de grado 1 (contacto sin juego inicial: si u resuelve f, k·u resuelve
   k·f), p. ej. la chapa de la cuchara a p_dinámica o el tubo de STE-01 a F_s de sizing; los casos con
   desfase entre trabas nunca se escalan. Diferencias de FS > 30 % se explican en «Hallazgos».

## Materiales y admisibles

- **Aluminios.** E = 70 GPa, ν = 0,33 [ESTIMADO: EN 1999-1-1]. Admisibles tomados de las constantes de
  los `structural_<grupo>.py` (fuente única): DRV-03 `SY_6082_HAZ` = 115 MPa (zona soldada, en toda la
  pieza); REV-01 `AL5083` = 125 MPa; STE-01 `AL6061` = 240 MPa; INT-02 `pmp_mat['Al 5083'].Sy` = 125 MPa.
  Casos de fatiga (reversa de sizing): REV-01 `AL5083_WLCF` = 68 MPa [CALCULADO: detalle soldado FAT 25,
  m = 3, 1e5 ciclos] en toda la pieza (conservador lejos de las soldaduras); STE-01 `AL6061_FAT` = 90 MPa
  [ESTIMADO]. FS objetivo `fs_target_metal` = 2 en todos.
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
- **Apoyos.** Zapatas sobre la placa base: resortes **bilaterales** en toda la cara inferior de las
  zapatas, normales k = E/t_placa y **tangenciales k/2** (unión precargada a T/(K·d) por espárrago ≫ el tiro
  de servicio, que no se abre; el corte lo transmiten la fricción de la unión y los 2 pasadores Ø6 por
  zapata que se escarian en montaje y no están en el CAD). Los agujeros Ø9 de los espárragos **no** son
  apoyo en el modelo (las ranuras abiertas a popa no toman corte en x): solo son zona excluida (arandelas
  y espárragos). Así está en `fea_parts.setup_drv03` (auditoría ronda 4, F6).
- **(a)** Empuje `sizing.mech.Fa_max_N` hacia proa (eje del jet inclinado α): la tapa P1-DRV-06 tira de
  las 4 roscas M5 de la cara delantera (tracción uniforme en sus paredes). Radial 3 g × m_rotor + Fr
  (de structural_tren) como apoyo cosenoidal en el Ø47, perpendicular al eje.
- **(b)** El mismo Fa hacia popa sobre el resalte trasero, solo en el anillo de apoyo del aro exterior
  (Da_max ≤ Ø ≤ D) + el mismo radial.

### P1-REV-01 — bucket abajo (marco BOQUILLA)

- **Geometría.** `build_down(p)`: chapa Al 5083 de `REV_t` = 8 mm, aro de refuerzo `REV_ring_t` = 10 mm en el
  pivote (buje de brazo + aro), dos agujeros de traba Ø `REV_lock_hole_d` = 16,5 mm por brazo; en reversa
  trabaja el de ABAJO de cada brazo (+Y a `REV_lock_ang`, −Y a `REV_lock_ang_m`, los dos a `REV_lock_r` del
  pivote) [CALCULADO: params_direccion].
- **Carga (auditoría ronda 4).** Balance de cantidad de movimiento del chorro, `structural_direccion.jet_momentum`
  (la misma función que usa la fila a mano): entra J = F_b/(1 − t_x) por el eje en +x y sale por el labio
  inferior con el mismo módulo en la dirección t_out (tangente de la elipse interior en `REV_cup_t1`). En el
  FEA: **entrada** = tracción uniforme en +x por área proyectada del chorro (Ø del chorro + cono a la altura
  del fondo de la cuchara) sobre la cara interior de la cuchara, con resultante J; **salida** = tracción
  uniforme −J·t_out en una franja de 10 mm [SUPUESTO] medida sobre la cuchara junto al labio inferior, de ancho
  |y| ≤ R_chorro. El setup **verifica** que la resultante y el momento alrededor del pivote coinciden con
  `bucket_reactions` (± 2 %; si no, se detiene) y los guarda en `extra.resultante` y en
  `verificacion_mano.resultante_R12`.
- **Apoyos.** Pivotes: muñón de P1-REV-02 en el buje POM P1-REV-03 (Ø `REV_bush_od`,
  k = E_POM/espesor del buje, unilaterales, sin fricción, resorte axial débil), con la reacción de cada lado.
  **Trabas: una por brazo.** Cada émbolo (perno Ø `REV_lock_pin_d`) es un cuerpo rígido que **solo
  reacciona en la dirección tangencial** al círculo alrededor del pivote (el momento), como el cálculo a mano,
  y apoya solo en la **mitad de su agujero** que avanza hacia el perno (la otra mitad tiene la holgura).
  Rigidez del émbolo 10⁶ N/mm [SUPUESTO] y resorte débil en las otras traslaciones.
- **Casos (criterio de traba única, ronda 4).** (a) R12 con las dos trabas apoyando a la vez, sin desfase
  (**informativo**). (b) R12 con la traba −Y apoyando 0,10 mm [SUPUESTO] después de la +Y (**informativo**, sin
  requisito: el desfase no está controlado y ya no es criterio). (d)/(e) **DISEÑO**: R12 con **solo** la traba
  +Y / **solo** la −Y (la interfaz de la otra no existe en el caso y su agujero sale de las zonas excluidas):
  FS ≥ 2 contra fluencia. (f)/(g) **DISEÑO, fatiga**: lo mismo con la reversa de sizing, corrida (no
  escalada), contra `AL5083_WLCF`. Ya no hay casos de «falla» ni variantes de falla doble: son estos casos.
- **Borde de los agujeros** (trabas y pivotes): verificación de sección neta a ±90° de la reacción (Método, 5).

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
- **Reversa (auditoría ronda 4, F1; pivote y traba rediseñados en la ronda 5).** Fuerzas del bucket sobre cada oreja de
  `bucket_statics` (= `structural_direccion.bucket_reactions`, cantidad de movimiento del chorro) con **M_h completo
  en una traba**: esa oreja recibe su pivote (chorro/2 + traba) y su traba; la otra, solo chorro/2 en su pivote. Carga
  **autoequilibrada** por oreja. Desde el cierre de la ronda 5 (R5-N5) la oreja (placa de `STE_ear_t` = <!--V:manifest.params.STE_ear_t:g-->14<!--/V--> mm) tiene
  **lóbulos engrosados** alrededor de los dos agujeros: el del pivote, `STE_piv_t` = <!--V:manifest.params.STE_piv_t:g-->20<!--/V--> mm, solo hacia adentro, y el de la
  traba, `STE_lock_t` = <!--V:manifest.params.STE_lock_t:g-->23.5<!--/V--> mm, desde su cara exterior en |y| = `STE_lock_y1` = <!--V:manifest.params.STE_lock_y1:g-->55<!--/V--> mm (3 mm por fuera de la placa;
  apoyo del collar del émbolo) hacia adentro, con radio `STE_lock_in_r` = <!--V:manifest.params.STE_lock_in_r:g-->18<!--/V--> mm en la parte que entra más allá de la
  placa. Las selecciones de los agujeros, los planos medios de los apoyos lineales y los bordes usan el largo de cada lóbulo
  (`largo_agujero_piloto_malla_mm` y `largo_agujero_embolo_malla_mm` en el JSON):
  - pivote (P1-REV-02, re-auditoría MEC-01/02/05/06; en dos piezas desde la re-auditoría del cierre de la ronda 5,
    MECH-1): el piloto h6 del **casquillo** de dúplex (`REV_sp_pilot_d` = <!--V:manifest.params.REV_sp_pilot_d:g-->24<!--/V--> mm, más grueso que el muñón desde el
    cierre de la ronda 5) entra ajustado en el **H7** que atraviesa el lóbulo del pivote, con Loctite 641, que llena el juego
    (FEA-4: con Tef-Gel quedaba un juego de hasta 34 µm que el apoyo sin juego no modela [CALCULADO: ISO 286]); el muñón,
    que va dentro del casquillo, no se modela (solo la reacción sobre el agujero de la oreja). El camino **diseñado** del corte y del momento es el **apoyo del piloto en el agujero** (par de
    aplastamiento): presión cosenoidal con **variación lineal a lo largo del agujero**, ℓ(η) = 1 + κ·η, con ℓ⁺ en la pared
    que empuja la carga y ℓ⁻ en la opuesta (solo compresión; `fea_parts.linear_bearing`). κ se ajusta para que la
    resultante pase por la **mitad del buje**, a (`REV_y_in` − `STE_ear_y1`) + `REV_bush_L`/2 de la cara exterior
    (`brazo_pivote_desde_cara_exterior_mm`), o sea M = R × ese brazo en la cara exterior; ℓ cambia de signo dentro del
    agujero (`apoyo_lineal` en el JSON: el piloto apoya en la pared cargada junto a la cara exterior y en la opuesta junto
    a la interior). **No hay par en la cara de la brida**: con Tef-Gel la unión apretada desliza y no se cuenta con ella
    (la precarga del M12 es baja, 12 N·m, y solo retiene). La selección se limita al agujero de cada lóbulo (el JSON guarda
    `facetas_agujero_pivote_fuera_de_las_orejas`, que debe ser 0);
  - traba (P1-REV-04, cuerpo **ajustado** desde el cierre de la ronda 5, R5-N1): el cuerpo h6 del émbolo (`REV_lock_bore_d`
    = <!--V:manifest.params.REV_lock_bore_d:g-->24<!--/V--> mm) va en el H7 liso del lóbulo de la traba de la **misma oreja** con Loctite 641, sin rosca ni precarga, y
    apoya igual que el piloto: `linear_bearing` con la resultante en la **mitad del brazo del bucket** (línea de acción del
    perno), a (`REV_y_in` − `STE_lock_y1`) + `REV_t`/2 de la cara exterior del lóbulo (`excentricidad_traba_desde_plano_medio_mm`
    la mide desde el plano medio del agujero). El collar exterior y el anillo DIN 471 solo ubican el cuerpo en su eje
    (Limitaciones).
  El setup **verifica** que la resultante aplicada, su momento alrededor del eje del pivote (M_y) y el **vector
  momento completo** alrededor del pivote coinciden con la estática (± 1 %; `verificacion_mano.resultante_bucket`).
- **Geometría de las orejas (re-auditoría del cierre de la ronda 5).** Los lóbulos se construyen con los mismos polígonos
  que el contorno de la oreja y apoyados cara con cara (FEA-2: con cilindros verdaderos solapados 0,01 mm sobre una placa
  de 24 lados quedaban escalones de 0,17–0,19 mm y caras astilla justo donde caen los máximos [CALCULADO: re-auditoría];
  `test_ste01_no_sliver_faces_on_bucket_ears`). Los pies de los lóbulos (uniones reentrantes con la placa, en sus dos
  caras) son aristas vivas en el CAD (R1,5 en la pieza, 05 §3) y el setup las declara en `aristas_vivas` (FEA-3):
  esferas de r 4 mm cada ≈ 4 mm a lo largo del contorno del lóbulo donde la placa sigue más allá
  (`fea_parts.ste01_sharp_edges`); si el máx.* fino cae en una de ellas y no converge, vale el promedio en volumen
  (Método, 5). El tubo lleva la garganta bajo el émbolo −Y (MECH-3; `_release.saddle`), que es parte de `build(p)`.
- **Sin precarga en la oreja (cierre de la ronda 5).** Con el cuerpo del émbolo ajustado desaparecen la precarga
  superpuesta en c/c2/d/d2 (FEA-R5-02, obsoleto por diseño), la tensión media de Goodman en f/f2 y el caso informativo p.
  Con el cuerpo roscado M24×1,5 a 110 N·m de la primera versión de la ronda 5, la tensión tangencial de esa precarga se
  sumaba a la de la carga de la traba y el FEA daba FS 1,74 en el borde de la rosca, cara interior (R5-N1) [CALCULADO:
  corrida fina de esa versión; ya no está en el CAD]. La precarga del M12 del pivote (3,6–6,7 kN, compresión de la oreja
  ≈ 10 MPa entre brida y arandela ancha) no se modela; la cubren las filas a mano de presión de la brida y de la arandela.
- **Casos.** (c)/(c2) **DISEÑO**: reversa R12 con M_h completo en la traba +Y / −Y (FS ≥ 2 contra fluencia).
  (d)/(d2) c/c2 + (a) (maniobra en reversa). (f)/(f2) **DISEÑO, fatiga**: reversa de sizing con M_h completo en la
  traba +Y / −Y, corrida, ciclo 0 → máx. contra `AL6061_FAT`. El FS de diseño de la pieza es `FS_min` del JSON (bloque
  AUTO).
- **Borde de los agujeros** (`pivote_mas_y`/`pivote_menos_y` y `embolo_mas_y`/`embolo_menos_y`, antes `rosca_*`; región del
  lóbulo de la traba `lobulo_embolo`, antes `lobulo_rosca`): verificación de sección neta a ±90° de la carga aplicada
  (Método, 5).

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
  ZAT se aplica a toda la pieza soldada (DRV-03, REV-01). La fatiga de soldadura de REV-01 se verifica con los casos
  f/g del FEA (reversa de sizing corrida, una traba sola) contra `AL5083_WLCF` (detalle soldado FAT 25) en toda la
  pieza: conservador lejos de los cordones, pero sin el factor de entalla real del pie del cordón.
- **Sin contacto real entre piezas** (resortes de penalización, sin fricción) y piezas vecinas rígidas
  (orejas de la bomba, pernos, émbolo). En INT-02 el conducto se acota entre «ausente» y «rígido».
- **Cargas cuasi-estáticas** (sizing / R12) sin dinámica; los impactos solo entran por los factores de
  los casos a mano.
- **PETG** macizo equivalente (ver arriba).
- **Trabas del bucket (REV-01).** El perno es rígido y no gira: cuando el brazo trabado se tuerce (traba
  sola) el contacto se concentra en el borde del agujero; ese pico es aplastamiento local (filas de
  aplastamiento), no sección neta. La holgura del agujero (Ø16,5 / Ø16) no se modela (contacto sin juego
  en la mitad de apoyo).
- **Apoyos de la oreja de STE-01.** El piloto del pivote y el cuerpo ajustado del émbolo son presiones impuestas en sus
  agujeros (rígidos y sin juego: los dos van con Loctite 641, que llena el juego del H7/h6; re-auditoría del cierre de la
  ronda 5, FEA-4): si el retenedor faltara, el apoyo se concentraría aún más en los bordes del agujero (×1,23–1,42 en la
  presión de borde con el juego medio a máximo [CALCULADO: re-auditoría, modelo Winkler]). Las fuerzas axiales del resorte y del cable, que el collar exterior lleva a la cara exterior
  del lóbulo de la traba (hacia adentro; tiro por cable ≤ <!--V:manifest.parts.14.checks.5.value:.0f-->106<!--/V--> N contra
  <!--V:est.loads.structural_direccion.F_lock_pin_N:.0f-->3006<!--/V--> N del perno [CALCULADO: check de P1-CTL-14 y
  `structural_direccion`]), y la retención del anillo DIN 471 no se modelan. Hasta el cierre de la ronda 5 el cuerpo iba
  roscado y apretado contra un collar interior: su precarga se modelaba como cargas equivalentes (corona, tiro axial y
  presión radial de los flancos, FEA-R5-02); con el cuerpo ajustado ya no hay unión roscada en la oreja.
- **Ventana del borde de los agujeros (re-auditoría del cierre de la ronda 5, FEA-5).** El |σθ| del borde se evalúa en
  θ = 60–120° de la carga (Método, 5) y el resto del contorno queda dentro de r_excl: un pico a θ < 60° no lo evalúa
  ningún criterio. En la corrida gruesa de la re-auditoría el máximo del agujero de la traba +Y cayó en θ = 61°, al límite
  de la ventana [CALCULADO: re-auditoría del cierre]; queda como limitación documentada (sin cambio en el código).

<!-- FEA:AUTO:INICIO (generado por fea_run.py; no editar a mano) -->

Corrida: 2026-10-02 · inputs v2.0 · 2890 s [CALCULADO]

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
| P1-REV-01 | gruesa | 6 | 48672 | 262551 | 0.003 | 0.428 | 59 |
| P1-REV-01 | fina | 3.5 | 152997 | 772020 | 0.001 | 0.530 | 60 |
| P1-STE-01 | gruesa | 8 | 37569 | 200220 | 0.000 | 0.035 | 402 |
| P1-STE-01 | fina | 4.5 | 115466 | 582480 | 0.000 | 0.214 | 525 |
| P1-INT-02 | gruesa | 14 | 47904 | 268719 | 0.000 | 0.228 | 112 |
| P1-INT-02 | fina | 8 | 93218 | 507585 | 0.000 | 0.307 | 168 |
| P1-CTL-02 | gruesa | 6 | 11240 | 65856 | 0.082 | 0.393 | 0 |
| P1-CTL-02 | fina | 3 | 46480 | 259596 | 0.208 | 0.454 | 0 |

### Resultados (malla fina) — tensiones en MPa; FS = admisible / σ de diseño

σ de diseño = σvm máx* (máximo fuera de r_excl de cargas y apoyos) si cambia ≤ 20 % de la malla gruesa a la fina; si no converge, máx(máx* fino, extrapolación tipo Richardson) (la falta de convergencia nunca baja la σ: re-auditoría FEA-R5-01); el promedio en una esfera de radio 3 mm («prom.») solo vale en una arista viva del CAD nombrada en `aristas_vivas` del JSON. Lo mismo para el |σθ| de los bordes. En PETG el FS es el menor de σvm, σ1 y σZ (el criterio va entre paréntesis). El FS del caso es el menor entre el del cuerpo y el del borde de los agujeros cargados (tabla de bordes; criterio «borde»). Casos de fatiga (reversa de sizing) contra el admisible de fatiga del material; si un caso lleva una tensión media (precarga), la σ es la equivalente de Goodman σ_cíclica/(1 − σ_m⁺/S_u) (hoy ningún caso la lleva: el cuerpo del émbolo de STE-01 va ajustado, sin precarga). Casos «informativo» fuera del FS mínimo. «Cumple» exige además que ninguna extrapolación tipo Richardson de un caso de diseño quede bajo el objetivo.

| Pieza | Caso | σvm máx | σvm p99 | σvm máx* | σvm prom. | σ diseño | u máx [mm] | **FS** | FS (p99) | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|
| P1-DRV-03 | a: Empuje Fa = 765 N hacia proa (tapa → 4 × M5) + radial 3 g + Fr = 143 N | 32.59 | 20.37 | 26.30 | 22.98 | 26.30 (máx*) | 0.286 | **4.37** | 5.65 | cumple |
| P1-DRV-03 | b: Empuje Fa = 765 N hacia popa (resalte trasero, reversa) + radial 143 N | 39.43 | 20.92 | 29.60 | 25.96 | 29.60 (máx*) | 0.296 | **3.89** | 5.50 | cumple |
| P1-REV-01 | a: Reversa: chorro F_b = 1408 N (J = 720 N, M_h = 135 N·m); R12: las dos trabas apoyan a la vez, sin desfase (informativo) | 32.73 | 10.84 | 26.04 | 17.76 | 26.04 (máx*) | 0.095 | **4.80** | 11.53 | informativo |
| P1-REV-01 | b: Reversa: chorro F_b = 1408 N (J = 720 N, M_h = 135 N·m); R12: la traba −Y apoya 0.1 mm después que la +Y (desfase; informativo, sin requisito) | 65.13 | 17.26 | 54.71 | 36.67 | 54.71 (máx*) | 0.476 | **2.28** | 7.24 | informativo |
| P1-REV-01 | d: Reversa: chorro F_b = 1408 N (J = 720 N, M_h = 135 N·m); R12 con SOLO la traba +Y (la −Y no está): M_h completo por el brazo +Y (DISEÑO) | 75.69 | 18.96 | 60.28 | 40.47 | 60.28 (máx*) | 0.558 | **2.07** | 6.59 | cumple |
| P1-REV-01 | e: Reversa: chorro F_b = 1408 N (J = 720 N, M_h = 135 N·m); R12 con SOLO la traba −Y (la +Y no está): M_h completo por el brazo −Y (DISEÑO) | 85.12 | 19.78 | 55.54 | 33.82 | 55.54 (máx*) | 0.555 | **2.25** | 6.32 | cumple |
| P1-REV-01 | f: Reversa: chorro F_b = 698 N (J = 357 N, M_h = 67 N·m); Reversa de sizing con SOLO la traba +Y (fatiga de soldadura) | 37.55 | 9.41 | 29.90 | 20.08 | 29.90 (máx*) | 0.277 | **2.27** | 7.23 | cumple |
| P1-REV-01 | g: Reversa: chorro F_b = 698 N (J = 357 N, M_h = 67 N·m); Reversa de sizing con SOLO la traba −Y (fatiga de soldadura) | 42.22 | 9.81 | 27.55 | 16.77 | 27.55 (máx*) | 0.275 | **2.47** | 6.93 | cumple |
| P1-STE-01 | a: Desvío del chorro F_s = máx(sizing 323, R12 364) = 364 N repartido en el paso (centro de presión e = 66 mm, = structural) | 16.38 | 5.81 | 14.48 | 7.93 | 14.48 (máx*) | 0.068 | **16.57** | 41.33 | cumple |
| P1-STE-01 | b: F_s = 364 N en la boca de salida (últimos 20 mm; brazo ≈ L = 132 mm, conservador) | 33.56 | 10.86 | 33.56 | 14.70 | 33.56 (máx*) | 0.130 | **7.15** | 22.09 | cumple |
| P1-STE-01 | c: Reversa R12 (F_b = 1408 N, M_h = 135 N·m) con M_h COMPLETO en la traba +Y: pivote +Y (chorro/2 + traba), pivote −Y (chorro/2) y cuerpo del émbolo +Y (DISEÑO) | 96.15 | 33.74 | 55.69 | 47.81 | borde pivote_mas_y: σθ 71.74 | 0.163 | **3.35** (borde pivote_mas_y) | 7.11 | cumple |
| P1-STE-01 | c2: Reversa R12 con M_h COMPLETO en la traba −Y: pivote −Y (chorro/2 + traba), pivote +Y y cuerpo del émbolo −Y (DISEÑO) | 89.68 | 31.31 | 54.79 | 47.42 | borde embolo_menos_y: σθ 71.90 | 0.161 | **3.34** (borde embolo_menos_y) | 7.66 | cumple |
| P1-STE-01 | d: Combinado: reversa (c) + desvío F_s en el paso (a) (maniobra en reversa) | 96.27 | 33.76 | 55.74 | 47.88 | borde pivote_mas_y: σθ 71.79 | 0.173 | **3.34** (borde pivote_mas_y) | 7.11 | cumple |
| P1-STE-01 | d2: Combinado: reversa (c2) + desvío F_s en el paso (a) | 89.64 | 31.48 | 64.16 | 47.40 | borde embolo_menos_y: σθ 71.89 | 0.193 | **3.34** (borde embolo_menos_y) | 7.62 | cumple |
| P1-STE-01 | f: Reversa de sizing (F_b = 698 N, M_h = 67.1 N·m) con M_h completo en la traba +Y (fatiga, 0 → máx.) | 47.70 | 16.74 | 27.63 | 23.72 | borde pivote_mas_y: σθ 35.59 | 0.081 | **2.53** (borde pivote_mas_y) | 5.38 | cumple |
| P1-STE-01 | f2: Reversa de sizing con M_h completo en la traba −Y (fatiga, 0 → máx.) | 44.49 | 15.53 | 27.18 | 23.52 | borde embolo_menos_y: σθ 35.67 | 0.080 | **2.52** (borde embolo_menos_y) | 5.79 | cumple |
| P1-INT-02 | a: Espárragos del pórtico: precarga 6944 N (10 N·m, K 0.18) ± vuelco Fa·h/Δx/2 = 422 N (Φ = 0.25) + corte Fa/4 | 63.39 | 14.67 | 9.55 | 9.55 | 9.55 (máx*) | 0.023 | **13.09** | 8.52 | cumple |
| P1-INT-02 | b: Golpe de fondo 50 kPa + presión de cierre 67 kPa en la abertura + tiro de la brida del conducto 4049 N (placa sola, sin la rigidez del conducto: conservador) | 51.42 | 30.02 | 51.11 | 51.11 | 51.11 (máx*) | 0.216 | **2.45** | 4.16 | cumple |
| P1-INT-02 | b2: Ídem (b) con el conducto P1-INT-01 como rigidizador rígido abulonado (cota rígida; = modelo de structural_toma) | 20.86 | 10.66 | 18.26 | 17.44 | 18.26 (máx*) | 0.048 | **6.85** | 11.73 | cumple |
| P1-CTL-02 | a: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-10, 0) mm (nervio entre ranuras); A cargada 847 mm² | 7.03 | 2.88 | 7.03 | 6.85 | 7.03 (máx*) | 0.813 | **3.41** | 8.34 | cumple |
| P1-CTL-02 | b: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-62, -12) mm (tapa ancha junto a la ranura del bucket); A cargada 1472 mm² | 4.35 | 2.22 | 4.35 | 3.66 | σZ 2.63 (máx*) | 0.419 | **3.49** (Z) | 10.81 | cumple |

\* máximo fuera de las zonas de aplicación de cargas/apoyos concentrados (r_excl en la tabla de convergencia); el máximo global incluye singularidades de aplicación y se reporta para transparencia.

### Borde de los agujeros cargados por perno (sección neta, a ±90° de la carga)

Nodos de la superficie del agujero con |cos θ| ≤ 0,5 respecto de la dirección de la carga (θ = 60…120°), zona que la exclusión r_excl del máx* no mira (auditoría ronda 4, F3). Se verifica la tensión circunferencial |σθ| (sección neta del «lug»): FS = admisible del caso / |σθ| máx. (malla fina). σvm de la ventana: informativo (en el arco de contacto incluye el aplastamiento y el borde del contacto, que verifican las filas de aplastamiento). Si |σθ| cambia > 10 % de la gruesa a la fina se extrapola (tipo Richardson, p = 2, tamaños locales); si cambia > 20 % el FS usa máx(fina, extrapolada). En un caso de fatiga con precarga, |σθ| sería el equivalente de Goodman |σθ_cíclico|/(1 − σθ_media⁺/S_u).

| Pieza | Caso | Agujero | σθ (valor abs.) gruesa → fina [MPa] | θ [°] | σvm ventana [MPa] (FS) | **FS** | Richardson σ_ext (FS) |
|---|---|---|---|---|---|---|---|
| P1-REV-01 | a | traba | 13.15 → 13.31 (+1 %) | 64 | 18.46 (6.77) | **9.39** | — |
| P1-REV-01 | a | traba_menos_y | 17.52 → 17.19 (-2 %) | 65 | 21.47 (5.82) | **7.27** | — |
| P1-REV-01 | a | pivote_mas_y | 23.87 → 24.55 (+3 %) | 87 | 25.92 (4.82) | **5.09** | — |
| P1-REV-01 | a | pivote_menos_y | 18.15 → 18.30 (+1 %) | 100 | 20.91 (5.98) | **6.83** | — |
| P1-REV-01 | b | traba | 25.43 → 27.44 (+7 %) | 98 | 65.13 (1.92) | **4.55** | — |
| P1-REV-01 | b | traba_menos_y | 8.01 → 11.16 (+28 %) | 61 | 9.08 (13.76) | **9.78** (Richardson (no convergido)) | 12.78 (9.78) |
| P1-REV-01 | b | pivote_mas_y | 33.02 → 34.09 (+3 %) | 94 | 36.75 (3.40) | **3.67** | — |
| P1-REV-01 | b | pivote_menos_y | 12.36 → 12.84 (+4 %) | 61 | 15.45 (8.09) | **9.73** | — |
| P1-REV-01 | d | traba | 28.36 → 30.93 (+8 %) | 98 | 75.69 (1.65) | **4.04** | — |
| P1-REV-01 | d | pivote_mas_y | 34.57 → 35.78 (+3 %) | 95 | 38.73 (3.23) | **3.49** | — |
| P1-REV-01 | d | pivote_menos_y | 12.09 → 11.56 (-5 %) | 113 | 17.32 (7.22) | **10.81** | — |
| P1-REV-01 | e | traba_menos_y | 26.13 → 27.39 (+5 %) | 79 | 51.66 (2.42) | **4.56** | — |
| P1-REV-01 | e | pivote_mas_y | 11.53 → 11.64 (+1 %) | 116 | 17.16 (7.28) | **10.74** | — |
| P1-REV-01 | e | pivote_menos_y | 27.76 → 29.24 (+5 %) | 73 | 30.95 (4.04) | **4.27** | — |
| P1-REV-01 | f | traba | 14.07 → 15.34 (+8 %) | 98 | 37.55 (1.81) | **4.43** | — |
| P1-REV-01 | f | pivote_mas_y | 17.15 → 17.75 (+3 %) | 95 | 19.21 (3.54) | **3.83** | — |
| P1-REV-01 | f | pivote_menos_y | 6.00 → 5.73 (-5 %) | 113 | 8.59 (7.92) | **11.86** | — |
| P1-REV-01 | g | traba_menos_y | 12.96 → 13.59 (+5 %) | 79 | 25.62 (2.65) | **5.00** | — |
| P1-REV-01 | g | pivote_mas_y | 5.72 → 5.77 (+1 %) | 116 | 8.51 (7.99) | **11.78** | — |
| P1-REV-01 | g | pivote_menos_y | 13.77 → 14.51 (+5 %) | 73 | 15.35 (4.43) | **4.69** | — |
| P1-STE-01 | c | pivote_mas_y | 65.85 → 71.74 (+8 %) | 116 | 85.21 (2.82) | **3.35** | — |
| P1-STE-01 | c | embolo_mas_y | 65.82 → 66.83 (+2 %) | 100 | 72.52 (3.31) | **3.59** | — |
| P1-STE-01 | c | pivote_menos_y | 12.39 → 12.86 (+4 %) | 119 | 16.47 (14.57) | **18.67** | — |
| P1-STE-01 | c2 | pivote_mas_y | 13.01 → 13.25 (+2 %) | 119 | 16.84 (14.25) | **18.11** | — |
| P1-STE-01 | c2 | pivote_menos_y | 56.54 → 64.41 (+12 %) | 112 | 74.39 (3.23) | **3.73** | 68.05 (3.53) |
| P1-STE-01 | c2 | embolo_menos_y | 63.27 → 71.90 (+12 %) | 91 | 78.02 (3.08) | **3.34** | 75.89 (3.16) |
| P1-STE-01 | d | pivote_mas_y | 65.90 → 71.79 (+8 %) | 116 | 85.25 (2.82) | **3.34** | — |
| P1-STE-01 | d | embolo_mas_y | 65.79 → 66.79 (+1 %) | 100 | 72.53 (3.31) | **3.59** | — |
| P1-STE-01 | d | pivote_menos_y | 12.39 → 12.87 (+4 %) | 119 | 16.48 (14.56) | **18.65** | — |
| P1-STE-01 | d2 | pivote_mas_y | 13.06 → 13.29 (+2 %) | 119 | 16.88 (14.22) | **18.06** | — |
| P1-STE-01 | d2 | pivote_menos_y | 56.56 → 64.42 (+12 %) | 112 | 74.41 (3.23) | **3.73** | 68.06 (3.53) |
| P1-STE-01 | d2 | embolo_menos_y | 63.26 → 71.89 (+12 %) | 91 | 78.03 (3.08) | **3.34** | 75.89 (3.16) |
| P1-STE-01 | f | pivote_mas_y | 32.66 → 35.59 (+8 %) | 116 | 42.27 (2.13) | **2.53** | — |
| P1-STE-01 | f | embolo_mas_y | 32.65 → 33.15 (+2 %) | 100 | 35.98 (2.50) | **2.71** | — |
| P1-STE-01 | f | pivote_menos_y | 6.15 → 6.38 (+4 %) | 119 | 8.17 (11.01) | **14.11** | — |
| P1-STE-01 | f2 | pivote_mas_y | 6.45 → 6.57 (+2 %) | 119 | 8.36 (10.77) | **13.69** | — |
| P1-STE-01 | f2 | pivote_menos_y | 28.05 → 31.95 (+12 %) | 112 | 36.90 (2.44) | **2.82** | 33.76 (2.67) |
| P1-STE-01 | f2 | embolo_menos_y | 31.39 → 35.67 (+12 %) | 91 | 38.70 (2.33) | **2.52** | 37.65 (2.39) |

### Convergencia (gruesa → fina)

Columna «Richardson»: si el máx* cambia > 10 %, σ_ext = σ_f + (σ_f − σ_g)/(r^p − 1) con r = h_g/h_f locales (esferas de refinamiento) y p = 2 [SUPUESTO: tensión con P2 en campo suave]; entre paréntesis el FS con σ_ext. Entre 10 y 20 % es informativo (pero «cumple» es falso si ese FS queda bajo el objetivo); > 20 % entra en la σ de diseño.

| Pieza | Caso | r_excl [mm] | σvm p99 | σvm máx* | σvm máx global | u máx [mm] | Richardson máx* |
|---|---|---|---|---|---|---|---|
| P1-DRV-03 | a | 5 | 21.41 → 20.37 (-5 %) | 25.55 → 26.30 (+3 %) | 28.08 → 32.59 (+14 %) | 0.2825 → 0.2862 (+1 %) | — |
| P1-DRV-03 | b | 5 | 21.99 → 20.92 (-5 %) | 29.61 → 29.60 (-0 %) | 33.03 → 39.43 (+16 %) | 0.2921 → 0.2963 (+1 %) | — |
| P1-REV-01 | a | 4 | 11.06 → 10.84 (-2 %) | 25.13 → 26.04 (+4 %) | 32.37 → 32.73 (+1 %) | 0.0950 → 0.0953 (+0 %) | — |
| P1-REV-01 | b | 4 | 17.60 → 17.26 (-2 %) | 51.66 → 54.71 (+6 %) | 59.29 → 65.13 (+9 %) | 0.4756 → 0.4758 (+0 %) | — |
| P1-REV-01 | d | 4 | 19.30 → 18.96 (-2 %) | 56.59 → 60.28 (+6 %) | 68.20 → 75.69 (+10 %) | 0.5550 → 0.5583 (+1 %) | — |
| P1-REV-01 | e | 4 | 20.62 → 19.78 (-4 %) | 52.63 → 55.54 (+5 %) | 83.15 → 85.12 (+2 %) | 0.5511 → 0.5547 (+1 %) | — |
| P1-REV-01 | f | 4 | 9.57 → 9.41 (-2 %) | 28.07 → 29.90 (+6 %) | 33.83 → 37.55 (+10 %) | 0.2753 → 0.2770 (+1 %) | — |
| P1-REV-01 | g | 4 | 10.23 → 9.81 (-4 %) | 26.11 → 27.55 (+5 %) | 41.25 → 42.22 (+2 %) | 0.2734 → 0.2751 (+1 %) | — |
| P1-STE-01 | a | 4 | 6.21 → 5.81 (-7 %) | 12.18 → 14.48 (+16 %) | 13.52 → 16.38 (+17 %) | 0.0662 → 0.0681 (+3 %) | 15.55 (15.44) |
| P1-STE-01 | b | 4 | 11.73 → 10.86 (-8 %) | 30.50 → 33.56 (+9 %) | 30.50 → 33.56 (+9 %) | 0.1275 → 0.1300 (+2 %) | — |
| P1-STE-01 | c | 4 | 34.59 → 33.74 (-3 %) | 52.02 → 55.69 (+7 %) | 94.64 → 96.15 (+2 %) | 0.1603 → 0.1633 (+2 %) | — |
| P1-STE-01 | c2 | 4 | 32.81 → 31.31 (-5 %) | 51.41 → 54.79 (+6 %) | 87.25 → 89.68 (+3 %) | 0.1586 → 0.1613 (+2 %) | — |
| P1-STE-01 | d | 4 | 34.58 → 33.76 (-2 %) | 52.04 → 55.74 (+7 %) | 94.75 → 96.27 (+2 %) | 0.1695 → 0.1727 (+2 %) | — |
| P1-STE-01 | d2 | 4 | 32.80 → 31.48 (-4 %) | 62.36 → 64.16 (+3 %) | 87.22 → 89.64 (+3 %) | 0.1888 → 0.1929 (+2 %) | — |
| P1-STE-01 | f | 4 | 17.16 → 16.74 (-3 %) | 25.81 → 27.63 (+7 %) | 46.95 → 47.70 (+2 %) | 0.0795 → 0.0810 (+2 %) | — |
| P1-STE-01 | f2 | 4 | 16.28 → 15.53 (-5 %) | 25.50 → 27.18 (+6 %) | 43.28 → 44.49 (+3 %) | 0.0787 → 0.0800 (+2 %) | — |
| P1-INT-02 | a | 8 | 14.07 → 14.67 (+4 %) | 9.00 → 9.55 (+6 %) | 63.94 → 63.39 (-1 %) | 0.0194 → 0.0226 (+14 %) | — |
| P1-INT-02 | b | 8 | 27.79 → 30.02 (+7 %) | 47.53 → 51.11 (+7 %) | 47.81 → 51.42 (+7 %) | 0.2047 → 0.2162 (+5 %) | — |
| P1-INT-02 | b2 | 8 | 10.29 → 10.66 (+3 %) | 17.57 → 18.26 (+4 %) | 17.71 → 20.86 (+15 %) | 0.0458 → 0.0485 (+5 %) | — |
| P1-CTL-02 | a | 4 | 3.20 → 2.88 (-11 %) | 6.89 → 7.03 (+2 %) | 6.89 → 7.03 (+2 %) | 0.7892 → 0.8127 (+3 %) | — |
| P1-CTL-02 | b | 4 | 2.26 → 2.22 (-2 %) | 4.05 → 4.35 (+7 %) | 4.05 → 4.35 (+7 %) | 0.4020 → 0.4195 (+4 %) | — |

### Comparación con el cálculo a mano (resultados/estructural.json)

σ FEA = σvm de la región de la pieza que modela la fila (máx* salvo que se indique promedio en volumen), escalada a la carga de la fila (columna «×»). FS con el admisible de la fila. Dif = (FS_FEA − FS_mano)/FS_mano.

| Pieza | Fila structural_*.py | Caso FEA · región | × | σ mano [MPa] | σ FEA [MPa] (p99) | FS mano | FS FEA | Dif |
|---|---|---|---|---|---|---|---|---|
| P1-DRV-03 | Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa) | a · mejillas (Richardson) | 1.00 | 1.02 | 19.52 (7.79) | 112.30 | 5.89 | -95 % ⚠ |
| P1-DRV-03 | Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico | a · tablero_y_alma (máx*) | 1.00 | 16.60 | 26.30 (22.81) | 6.93 | 4.37 | -37 % ⚠ |
| P1-DRV-03 | Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo | b · alojamiento (Richardson) | 1.00 | 2.99 | 17.60 (9.48) | 80.27 | 13.63 | -83 % ⚠ |
| P1-REV-01 | Brazo trabado: flexión en su plano con M_h completo (R12, corta) | d · brazos (máx*) | 1.00 | 28.18 | 60.28 (21.82) | 4.44 | 2.07 | -53 % ⚠ |
| P1-REV-01 | Brazo trabado: flexión en su plano con M_h completo (reversa sizing, fatiga de soldadura) | f · brazos (máx*) | 1.00 | 13.98 | 29.90 (10.82) | 4.86 | 2.27 | -53 % ⚠ |
| P1-REV-01 | Cuchara como viga entre brazos (bucket R12, corta) | a · cuchara (máx*) | 1.00 | 1.82 | 5.31 (4.24) | 68.61 | 23.56 | -66 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta) | a · cuchara (máx*) | 1.02 | 2.53 | 5.43 (4.34) | 49.49 | 23.02 | -53 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja (fatiga de soldadura, 1e5) | a · cuchara (máx*) | 1.02 | 2.53 | 5.43 (4.34) | 26.92 | 12.52 | -53 % ⚠ |
| P1-REV-01 | Cuchara abierta a torsión con un solo brazo trabado (R12, corta) | d · cuchara (Richardson) | 1.00 | 57.73 | 48.65 (10.87) | 2.17 | 2.57 | +19 % |
| P1-REV-01 | Cuchara abierta a torsión con un solo brazo trabado (reversa sizing, fatiga de soldadura) | f · cuchara (Richardson) | 1.00 | 28.64 | 24.14 (5.39) | 2.37 | 2.82 | +19 % |
| P1-REV-01 | Pivote: aplastamiento del brazo + aro (buje Ø24 × 18), R12 | d · pivotes (promedio) | 1.00 | 7.64 | 9.19 (28.61) | 16.35 | 13.60 | -17 % |
| P1-REV-01 | Agujero de traba: aplastamiento del brazo (perno Ø16, M_h completo, R12) | d · traba (promedio) | 1.00 | 23.49 | 16.25 (53.21) | 5.32 | 7.69 | +45 % ⚠ |
| P1-STE-01 | Flexión del tubo por el desvío del chorro (fatiga, sizing) | a · tubo (máx*) | 0.89 | 0.62 | 7.01 (3.38) | 145.87 | 12.84 | -91 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión en su plano (R12, corta; pivote + traba con M_h completo) | c · orejas_bucket (máx*) | 1.00 | 32.88 | 55.69 (37.96) | 7.30 | 4.31 | -41 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión (reversa sizing, fatiga; M_h completo en su traba) | f · orejas_bucket (máx*) | 1.00 | 16.31 | 27.63 (18.83) | 5.52 | 3.26 | -41 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión fuera del plano por el pivote en voladizo (R12, M_h completo) | c · orejas_bucket (máx*) | 1.00 | 40.71 | 55.69 (37.96) | 5.90 | 4.31 | -27 % |
| P1-STE-01 | Oreja: aplastamiento del piloto Ø24 con corte y momento del pivote (R12, unión deslizada) | c · anillo_piloto (promedio) | 1.00 | 57.44 | 15.15 (68.25) | 4.18 | 15.84 | +279 % ⚠ |
| P1-STE-01 | Oreja: aplastamiento del cuerpo ajustado Ø24 del émbolo con fuerza y momento del perno (R12) | c · lobulo_embolo (promedio) | 1.00 | 30.17 | 10.07 (50.38) | 7.96 | 23.84 | +200 % ⚠ |
| P1-STE-01 | Oreja de pivote (dentro de la de la bomba): flexión de la raíz | d · orejas_pivote (máx*) | 1.00 | 2.33 | 32.65 (16.38) | 103.14 | 7.35 | -93 % ⚠ |
| P1-INT-02 | Paño lateral entre bulones del conducto y del ala: golpe de fondo | b2 · pano_lateral (máx*) | 1.00 | 1.17 | 18.26 (12.28) | 106.56 | 6.85 | -94 % ⚠ |
| P1-INT-02 | Paño lateral entre bulones del conducto y del ala: golpe de fondo | b · pano_lateral (máx*) | 1.00 | 1.17 | 51.11 (36.46) | 106.56 | 2.45 | -98 % ⚠ |
| P1-INT-02 | Asiento cónico de la cabeza M8 en el 5083 (aplastamiento) | a · asiento_cono (promedio) | 1.01 | 50.83 | 47.52 (59.77) | 2.46 | 2.63 | +7 % |
| P1-INT-02 | Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono) | a · tapon_dk (promedio) | 1.01 | 42.51 | 22.54 (29.53) | 2.94 | 5.54 | +89 % ⚠ |
| P1-CTL-02 | Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta) | a · tapa (máx*) | 1.00 | 6.25 | 7.03 (5.14) | 3.84 | 3.41 | -11 % |
| P1-CTL-02 | Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta) | b · tapa (máx*) | 1.00 | 6.25 | 4.35 (2.61) | 3.84 | 5.51 | +44 % ⚠ |

### Variantes propuestas (evaluadas en el modelo FEA; la pieza NO se modificó)

| Pieza | Variante | Caso | σvm máx* | σvm p99 | u máx [mm] | FS (máx*) | FS (p99) | Veredicto |
|---|---|---|---|---|---|---|---|---|
| P1-CTL-02 | V1: sensibilidad: paredes de 4 mm (hoy W_OUT = 5) | a | 7.09 | 3.21 | 0.873 | **3.27** | 7.47 | cumple |
| P1-CTL-02 | V1: sensibilidad: paredes de 4 mm (hoy W_OUT = 5) | b | 6.06 | 2.72 | 0.515 | **2.89** | 8.80 | **NO CUMPLE** |

⚠ diferencia > 30 %: explicada en «Hallazgos».

### Hallazgos cuantitativos

- **P1-DRV-03: FS = 3.89** (objetivo 2, cumple); caso b, criterio vm: σ de diseño 29.6 MPa (máx*, máx* gruesa→fina -0 %) en (590.7, -23.0, 169.5) mm; σvm p99 20.9 MPa (FS p99 5.50). Alma de ±0,35·Ø del alojamiento con empalmes r 3 alma–tablero y alma–alojamiento (auditoría ronda 3, F-03): el máximo queda sobre el empalme alma–tablero y converge (antes era una arista viva, en una cuña de ~30° entre el alojamiento y el tablero, que no convergía). Cumple con margen.
  - ⚠ «Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa)»: FS mano 112.30 vs FS FEA 5.89 (-95 %). La fila solo mira la flexión de la mejilla en su plano por Fa/2 (sección 12 × 150, muy rígida). El FEA pone el máximo de la mejilla en su unión con el tablero: el tablero cargado por el alojamiento flexiona y arrastra el borde superior de la mejilla fuera de su plano (marco tablero + mejillas). Mecanismo que la fila no ve; nivel bajo.
  - ⚠ «Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico»: FS mano 6.93 vs FS FEA 4.37 (-37 %). El máximo está en la unión del alma central con el tablero (ahora con empalme r 3): el momento de Fa excéntrico y el radial entran al tablero por el alma; la viga biapoyada de la fila no ve esa concentración. FS sobre 2.
  - ⚠ «Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo»: FS mano 80.27 vs FS FEA 13.63 (-83 %). La fila es el corte medio del resalte (τ = Fa/(π·D·t)), un valor nominal; el FEA mide la flexión del resalte como placa anular (el aro apoya solo entre Da_max y D) y la del alojamiento en su unión con el alma. Ambos lejos del admisible.
- **P1-REV-01: FS = 2.07** (objetivo 2, cumple); caso d, criterio vm: σ de diseño 60.3 MPa (máx*, máx* gruesa→fina +6 %) en (358.0, 65.5, 37.7) mm; σvm p99 19.0 MPa (FS p99 6.59). Criterio de traba única (ronda 4): con una traba sola (d/e a R12, f/g con la reversa de sizing contra el admisible de fatiga de soldadura) todo M_h pasa por un brazo y la cuchara abierta gira hasta él; el máximo queda en la cara exterior del brazo trabado, sobre su borde, bajo el pivote (el punto caliente de la ronda 3, ahora dentro de una esfera de refinamiento en las dos mallas). Con las dos trabas sin desfase (a, informativo) cada una toma la mitad de M_h. El borde de los agujeros de traba y de pivote (|σθ| de sección neta a ±90°) queda por debajo del cuerpo; el σvm de la ventana de la traba incluye el borde del contacto del perno rígido (aplastamiento). Carga = balance de cantidad de movimiento del chorro, con resultante y momento verificados contra bucket_reactions.
  - ⚠ «Brazo trabado: flexión en su plano con M_h completo (R12, corta)»: FS mano 4.44 vs FS FEA 2.07 (-53 %). La fila es la flexión del brazo EN SU PLANO con M_h completo (sección t × 60). Con una traba sola (d, f) el FEA suma la flexión FUERA del plano y la torsión que mete la cuchara abierta al girar hasta el brazo trabado, con el pico en la cara exterior del brazo, sobre su borde bajo el pivote: mecanismo que la fila no ve; el FS de diseño es el del FEA.
  - ⚠ «Brazo trabado: flexión en su plano con M_h completo (reversa sizing, fatiga de soldadura)»: FS mano 4.86 vs FS FEA 2.27 (-53 %). La fila es la flexión del brazo EN SU PLANO con M_h completo (sección t × 60). Con una traba sola (d, f) el FEA suma la flexión FUERA del plano y la torsión que mete la cuchara abierta al girar hasta el brazo trabado, con el pico en la cara exterior del brazo, sobre su borde bajo el pivote: mecanismo que la fila no ve; el FS de diseño es el del FEA.
  - ⚠ «Cuchara como viga entre brazos (bucket R12, corta)»: FS mano 68.61 vs FS FEA 23.56 (-66 %). La fila trata la cuchara como viga entre brazos; con las dos trabas (a) la cuchara casi no trabaja (σ de pocos MPa en los dos modelos): diferencia relativa grande sobre valores chicos.
  - ⚠ «Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta)»: FS mano 49.49 vs FS FEA 23.02 (-53 %). La franja empotrada (p_dinámica) no incluye la flexión global de la cuchara; el FEA (caso a escalado a p_dinámica/q_entrada) mide la tensión total de la chapa. Ambos muy por debajo del admisible.
  - ⚠ «Chapa de la cuchara: franja (fatiga de soldadura, 1e5)»: FS mano 26.92 vs FS FEA 12.52 (-53 %). La franja empotrada (p_dinámica) no incluye la flexión global de la cuchara; el FEA (caso a escalado a p_dinámica/q_entrada) mide la tensión total de la chapa. Ambos muy por debajo del admisible.
  - ⚠ «Agujero de traba: aplastamiento del brazo (perno Ø16, M_h completo, R12)»: FS mano 5.32 vs FS FEA 7.69 (+45 %). La fila es la presión media F/(d·t) con M_h completo en una traba; el FEA promedia σvm en un anillo de 3 mm alrededor del agujero de la traba cargada (caso d): por definición menor que el pico. Mismo orden de magnitud.
- **P1-STE-01: FS = 2.52** (objetivo 2, cumple); caso f2, criterio borde: borde del agujero «embolo_menos_y» a ±90° de la carga: |σθ| 35.7 MPa, gruesa→fina +12 % en (393.4, -52.8, 57.5) mm (cuerpo: FS 3.31); σvm p99 15.5 MPa (FS p99 5.79). Cargas del bucket autoequilibradas por oreja (F1; ronda 5): el pivote apoya con el piloto h6 del espaciador en su H7 de la oreja y la traba con el cuerpo AJUSTADO del émbolo (Ø24 h6 en H7, sin rosca ni precarga) en el suyo, los dos con presión lineal a lo largo del agujero (par de aplastamiento; resultante en la mitad del buje y en la mitad del brazo; sin par en la brida: MEC-02), así que cada uno apoya en la pared cargada junto a la cara exterior y en la opuesta junto a la interior; resultante y vector momento verificados contra la estática. Con M_h completo en una traba gobierna la oreja de esa traba (ver caso y ubicación en la tabla). La versión anterior (cuerpo roscado M24 apretado a 110 N·m) daba FS 1,74 en el borde de la rosca por la tensión tangencial de la precarga: R5-N1.
  - ⚠ «Flexión del tubo por el desvío del chorro (fatiga, sizing)»: FS mano 145.87 vs FS FEA 12.84 (-91 %). La fila trata el tubo Ø101 como viga (σ nominal < 1 MPa). En el FEA el máximo de la región del tubo está donde se le unen la torre y la oreja de pivote superior (entra el par del yugo y la reacción de los pernos): concentración local que la viga no ve. Nivel bajo (FS > 10).
  - ⚠ «Oreja del bucket: flexión en su plano (R12, corta; pivote + traba con M_h completo)»: FS mano 7.30 vs FS FEA 4.31 (-41 %). Las filas usan una sección de raíz STE_ear_t × 36 bajo el pivote (en su plano: pivote + traba con M_h completo; fuera del plano: momento del pivote en voladizo). El FEA pone el máximo de la oreja en los lóbulos y en el borde de los agujeros, donde los pares de aplastamiento del piloto y del cuerpo del émbolo concentran: mecanismo local que la viga no ve; el FS de diseño es el del FEA.
  - ⚠ «Oreja del bucket: flexión (reversa sizing, fatiga; M_h completo en su traba)»: FS mano 5.52 vs FS FEA 3.26 (-41 %). Las filas usan una sección de raíz STE_ear_t × 36 bajo el pivote (en su plano: pivote + traba con M_h completo; fuera del plano: momento del pivote en voladizo). El FEA pone el máximo de la oreja en los lóbulos y en el borde de los agujeros, donde los pares de aplastamiento del piloto y del cuerpo del émbolo concentran: mecanismo local que la viga no ve; el FS de diseño es el del FEA.
  - ⚠ «Oreja: aplastamiento del piloto Ø24 con corte y momento del pivote (R12, unión deslizada)»: FS mano 4.18 vs FS FEA 15.84 (+279 %). La fila es el par de aplastamiento (p = F/(d·L)·(1 + 6·a/L): presión de borde de una distribución lineal). El FEA aplica esa distribución lineal (apoyo cosenoidal) y promedia σvm en el anillo o el lóbulo alrededor del agujero, que además incluye la flexión de la oreja: métricas distintas.
  - ⚠ «Oreja: aplastamiento del cuerpo ajustado Ø24 del émbolo con fuerza y momento del perno (R12)»: FS mano 7.96 vs FS FEA 23.84 (+200 %). La fila es el par de aplastamiento (p = F/(d·L)·(1 + 6·a/L): presión de borde de una distribución lineal). El FEA aplica esa distribución lineal (apoyo cosenoidal) y promedia σvm en el anillo o el lóbulo alrededor del agujero, que además incluye la flexión de la oreja: métricas distintas.
  - ⚠ «Oreja de pivote (dentro de la de la bomba): flexión de la raíz»: FS mano 103.14 vs FS FEA 7.35 (-93 %). La fila toma F/2 a 12 mm en 25 × 30. En el FEA los pernos de pivote reciben un par (reacciones opuestas en la mejilla Ø8 y en la rosca M6) porque el bucket empuja muy por encima del eje; el máximo está donde la oreja cilíndrica se une al frente esférico.
- **P1-INT-02: FS = 2.45** (objetivo 2, cumple); caso b, criterio vm: σ de diseño 51.1 MPa (máx*, máx* gruesa→fina +7 %) en (525.6, 149.4, 10.0) mm; σvm p99 30.0 MPa (FS p99 4.16). Gobierna el golpe de fondo con la placa sola (b): máximo en la cara superior sobre el borde del apoyo del ala (unión cuerpo–ala), convergido. Con el conducto como rigidizador (b2) baja a ≈ 18 MPa. Los avellanados M8 del pórtico: σvm promedio bajo el cono ≈ presión de la fila a mano.
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 6.85 (-94 %). La fila apoya el paño en la línea de bulones del conducto (luz 68 mm a lo ancho). Placa sola (b): sin el conducto, la franja entre la abertura y el ala trabaja a lo largo y el máximo sale en la unión cuerpo–ala; es la cota conservadora. Con el conducto rígido (b2) se recupera el modelo de la fila; la realidad está entre ambos.
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 2.45 (-98 %). La fila apoya el paño en la línea de bulones del conducto (luz 68 mm a lo ancho). Placa sola (b): sin el conducto, la franja entre la abertura y el ala trabaja a lo largo y el máximo sale en la unión cuerpo–ala; es la cota conservadora. Con el conducto rígido (b2) se recupera el modelo de la fila; la realidad está entre ambos.
  - ⚠ «Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono)»: FS mano 2.94 vs FS FEA 5.54 (+89 %). La fila usa τ media en el cilindro Ø dk × (t − h_cono) suponiendo que todo el tiro pasa por corte puro. En el FEA la compresión de la zapata sobre la cara superior equilibra la precarga en el mismo lugar y el cilindro no está en corte puro: el promedio de σvm en ese volumen es menor. Fila conservadora.
- **P1-CTL-02: FS = 3.41** (objetivo 3, cumple); caso a, criterio vm: σ de diseño 7.0 MPa (máx*, máx* gruesa→fina +2 %) en (1820.6, -108.8, 674.0) mm; σvm p99 2.9 MPa (FS p99 8.34). Paredes de 5 mm engrosadas hacia afuera (ronda 3, F-02; el entrehierro del sensor hall no cambia): gobierna la tapa (von Mises) y la tracción entre capas de las paredes ya no manda; la variante V1 (paredes de 4 mm) muestra la sensibilidad. La pieza real es 5 perímetros + 30 % giroide (solid_frac 0,55): el FEA macizo es optimista.
  - ⚠ «Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta)»: FS mano 3.84 vs FS FEA 5.51 (+44 %). La fila es una franja 50 × 6 apoyada con luz 50; la tapa real está casi toda ranurada (ranuras de las palancas), y la palma carga el nervio de 6 mm entre las dos ranuras o la tapa angosta junto a la del bucket.

<!-- FEA:AUTO:FIN -->
