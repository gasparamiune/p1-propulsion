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

Corrida: 2026-10-02 · inputs v2.0 · 4788 s [CALCULADO]

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
| P1-REV-01 | gruesa | 6 | 46480 | 252975 | 0.003 | 0.408 | 56 |
| P1-REV-01 | fina | 3.5 | 153447 | 773826 | 0.001 | 0.530 | 60 |
| P1-STE-01 | gruesa | 8 | 29629 | 159123 | 0.000 | 0.020 | 373 |
| P1-STE-01 | fina | 4.5 | 95764 | 486504 | 0.000 | 0.197 | 496 |
| P1-INT-02 | gruesa | 14 | 47904 | 268719 | 0.000 | 0.228 | 112 |
| P1-INT-02 | fina | 8 | 93218 | 507585 | 0.000 | 0.307 | 168 |
| P1-CTL-02 | gruesa | 6 | 11240 | 65856 | 0.082 | 0.393 | 0 |
| P1-CTL-02 | fina | 3 | 46480 | 259596 | 0.208 | 0.454 | 0 |

### Resultados (malla fina) — tensiones en MPa; FS = admisible / σ de diseño

σ de diseño = σvm máx* (máximo fuera de r_excl de cargas y apoyos) si cambia ≤ 20 % de la malla gruesa a la fina; si no converge, máx(máx* fino, extrapolación tipo Richardson) (la falta de convergencia nunca baja la σ: re-auditoría FEA-R5-01); el promedio en una esfera de radio 3 mm («prom.») solo vale en una arista viva del CAD nombrada en `aristas_vivas` del JSON. Lo mismo para el |σθ| de los bordes. En PETG el FS es el menor de σvm, σ1 y σZ (el criterio va entre paréntesis). El FS del caso es el menor entre el del cuerpo y el del borde de los agujeros cargados (tabla de bordes; criterio «borde»). Casos de fatiga (reversa de sizing) contra el admisible de fatiga del material; si el caso lleva una tensión media (precarga de los émbolos en STE-01 f/f2), la σ es la equivalente de Goodman σ_cíclica/(1 − σ_m⁺/S_u). Casos «informativo» fuera del FS mínimo. «Cumple» exige además que ninguna extrapolación tipo Richardson de un caso de diseño quede bajo el objetivo.

| Pieza | Caso | σvm máx | σvm p99 | σvm máx* | σvm prom. | σ diseño | u máx [mm] | **FS** | FS (p99) | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|
| P1-DRV-03 | a: Empuje Fa = 765 N hacia proa (tapa → 4 × M5) + radial 3 g + Fr = 143 N | 32.59 | 20.37 | 26.30 | 22.98 | 26.30 (máx*) | 0.286 | **4.37** | 5.65 | cumple |
| P1-DRV-03 | b: Empuje Fa = 765 N hacia popa (resalte trasero, reversa) + radial 143 N | 39.42 | 20.92 | 29.59 | 25.96 | 29.59 (máx*) | 0.296 | **3.89** | 5.50 | cumple |
| P1-REV-01 | a: Reversa: chorro F_b = 1408 N (J = 720 N, M_h = 135 N·m); R12: las dos trabas apoyan a la vez, sin desfase (informativo) | 32.75 | 10.88 | 26.05 | 17.77 | 26.05 (máx*) | 0.095 | **4.80** | 11.49 | informativo |
| P1-REV-01 | b: Reversa: chorro F_b = 1408 N (J = 720 N, M_h = 135 N·m); R12: la traba −Y apoya 0.1 mm después que la +Y (desfase; informativo, sin requisito) | 65.59 | 17.42 | 55.13 | 36.96 | 55.13 (máx*) | 0.475 | **2.27** | 7.18 | informativo |
| P1-REV-01 | d: Reversa: chorro F_b = 1408 N (J = 720 N, M_h = 135 N·m); R12 con SOLO la traba +Y (la −Y no está): M_h completo por el brazo +Y (DISEÑO) | 74.98 | 18.92 | 60.12 | 40.35 | 60.12 (máx*) | 0.548 | **2.08** | 6.61 | cumple |
| P1-REV-01 | e: Reversa: chorro F_b = 1408 N (J = 720 N, M_h = 135 N·m); R12 con SOLO la traba −Y (la +Y no está): M_h completo por el brazo −Y (DISEÑO) | 84.13 | 19.74 | 55.34 | 33.73 | 55.34 (máx*) | 0.544 | **2.26** | 6.33 | cumple |
| P1-REV-01 | f: Reversa: chorro F_b = 698 N (J = 357 N, M_h = 67 N·m); Reversa de sizing con SOLO la traba +Y (fatiga de soldadura) | 37.19 | 9.39 | 29.82 | 20.02 | 29.82 (máx*) | 0.272 | **2.28** | 7.24 | cumple |
| P1-REV-01 | g: Reversa: chorro F_b = 698 N (J = 357 N, M_h = 67 N·m); Reversa de sizing con SOLO la traba −Y (fatiga de soldadura) | 41.73 | 9.79 | 27.45 | 16.73 | 27.45 (máx*) | 0.270 | **2.48** | 6.94 | cumple |
| P1-STE-01 | a: Desvío del chorro F_s = máx(sizing 323, R12 364) = 364 N repartido en el paso (centro de presión e = 66 mm, = structural) | 16.19 | 5.92 | 15.95 | 7.96 | 17.67 (Richardson (máx* no convergido)) | 0.068 | **13.58** | 40.54 | cumple |
| P1-STE-01 | b: F_s = 364 N en la boca de salida (últimos 20 mm; brazo ≈ L = 132 mm, conservador) | 33.69 | 11.00 | 33.69 | 14.59 | 33.69 (máx*) | 0.131 | **7.12** | 21.82 | cumple |
| P1-STE-01 | c: Reversa R12 (F_b = 1408 N, M_h = 135 N·m) con M_h COMPLETO en la traba +Y: pivote +Y (chorro/2 + traba), pivote −Y (chorro/2) y rosca M24 +Y + precarga de los émbolos (DISEÑO) | 194.04 | 83.45 | 97.07 | 80.36 | borde rosca_mas_y: σθ 134.89 | 0.183 | **1.78** (borde rosca_mas_y) | 2.88 | **NO CUMPLE** |
| P1-STE-01 | c2: Reversa R12 con M_h COMPLETO en la traba −Y: pivote −Y (chorro/2 + traba), pivote +Y y rosca M24 −Y + precarga de los émbolos (DISEÑO) | 192.88 | 82.26 | 93.29 | 86.03 | borde rosca_menos_y: σθ 138.11 | 0.223 | **1.74** (borde rosca_menos_y) | 2.92 | **NO CUMPLE** |
| P1-STE-01 | d: Combinado: reversa (c) + desvío F_s en el paso (a) (maniobra en reversa) + precarga de los émbolos | 194.17 | 83.47 | 97.16 | 80.41 | borde rosca_mas_y: σθ 134.98 | 0.193 | **1.78** (borde rosca_mas_y) | 2.88 | **NO CUMPLE** |
| P1-STE-01 | d2: Combinado: reversa (c2) + desvío F_s en el paso (a) + precarga de los émbolos | 192.79 | 82.23 | 93.26 | 86.00 | borde rosca_menos_y: σθ 138.02 | 0.205 | **1.74** (borde rosca_menos_y) | 2.92 | **NO CUMPLE** |
| P1-STE-01 | f: Reversa de sizing (F_b = 698 N, M_h = 67.1 N·m) con M_h completo en la traba +Y (fatiga; precarga = media, Goodman) | 96.33 | 20.77 | 47.58 | 39.39 | borde pivote_mas_y: σθ 51.61 | 0.091 | **1.74** (borde pivote_mas_y) | 4.33 | **NO CUMPLE** |
| P1-STE-01 | f2: Reversa de sizing con M_h completo en la traba −Y (fatiga; precarga = media, Goodman) | 87.58 | 20.10 | 45.70 | 41.89 | borde pivote_menos_y: σθ 46.91 | 0.119 | **1.92** (borde pivote_menos_y) | 4.48 | **NO CUMPLE** |
| P1-STE-01 | p: Precarga máxima de los dos cuerpos de émbolo sola (F = 30.6 kN por oreja, p radial 16.7 MPa; informativo: es la tensión media de f/f2) | 140.68 | 72.98 | 64.84 | 57.67 | borde rosca_mas_y: σθ 94.82 | 0.037 | **2.53** (borde rosca_mas_y) | 3.29 | informativo |
| P1-INT-02 | a: Espárragos del pórtico: precarga 6944 N (10 N·m, K 0.18) ± vuelco Fa·h/Δx/2 = 422 N (Φ = 0.25) + corte Fa/4 | 63.39 | 14.67 | 9.55 | 9.55 | 9.55 (máx*) | 0.023 | **13.09** | 8.52 | cumple |
| P1-INT-02 | b: Golpe de fondo 50 kPa + presión de cierre 67 kPa en la abertura + tiro de la brida del conducto 4049 N (placa sola, sin la rigidez del conducto: conservador) | 51.42 | 30.02 | 51.11 | 51.11 | 51.11 (máx*) | 0.216 | **2.45** | 4.16 | cumple |
| P1-INT-02 | b2: Ídem (b) con el conducto P1-INT-01 como rigidizador rígido abulonado (cota rígida; = modelo de structural_toma) | 20.86 | 10.66 | 18.26 | 17.44 | 18.26 (máx*) | 0.048 | **6.85** | 11.73 | cumple |
| P1-CTL-02 | a: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-10, 0) mm (nervio entre ranuras); A cargada 847 mm² | 7.03 | 2.88 | 7.03 | 6.85 | 7.03 (máx*) | 0.813 | **3.41** | 8.34 | cumple |
| P1-CTL-02 | b: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-62, -12) mm (tapa ancha junto a la ranura del bucket); A cargada 1472 mm² | 4.35 | 2.22 | 4.35 | 3.66 | σZ 2.63 (máx*) | 0.419 | **3.49** (Z) | 10.81 | cumple |

\* máximo fuera de las zonas de aplicación de cargas/apoyos concentrados (r_excl en la tabla de convergencia); el máximo global incluye singularidades de aplicación y se reporta para transparencia.

### Borde de los agujeros cargados por perno (sección neta, a ±90° de la carga)

Nodos de la superficie del agujero con |cos θ| ≤ 0,5 respecto de la dirección de la carga (θ = 60…120°), zona que la exclusión r_excl del máx* no mira (auditoría ronda 4, F3). Se verifica la tensión circunferencial |σθ| (sección neta del «lug»): FS = admisible del caso / |σθ| máx. (malla fina). σvm de la ventana: informativo (en el arco de contacto incluye el aplastamiento y el borde del contacto, que verifican las filas de aplastamiento). Si |σθ| cambia > 10 % de la gruesa a la fina se extrapola (tipo Richardson, p = 2, tamaños locales); si cambia > 20 % el FS usa máx(fina, extrapolada). En los casos de fatiga con precarga, |σθ| es el equivalente de Goodman |σθ_cíclico|/(1 − σθ_media⁺/S_u).

| Pieza | Caso | Agujero | σθ (valor abs.) gruesa → fina [MPa] | θ [°] | σvm ventana [MPa] (FS) | **FS** | Richardson σ_ext (FS) |
|---|---|---|---|---|---|---|---|
| P1-REV-01 | a | traba | 13.15 → 13.32 (+1 %) | 64 | 18.48 (6.77) | **9.39** | — |
| P1-REV-01 | a | traba_menos_y | 17.52 → 17.20 (-2 %) | 65 | 21.47 (5.82) | **7.27** | — |
| P1-REV-01 | a | pivote_mas_y | 23.85 → 24.56 (+3 %) | 87 | 25.93 (4.82) | **5.09** | — |
| P1-REV-01 | a | pivote_menos_y | 18.15 → 18.32 (+1 %) | 100 | 20.92 (5.97) | **6.82** | — |
| P1-REV-01 | b | traba | 25.65 → 27.66 (+7 %) | 98 | 65.59 (1.91) | **4.52** | — |
| P1-REV-01 | b | traba_menos_y | 8.11 → 10.98 (+26 %) | 61 | 8.54 (14.65) | **10.03** (Richardson (no convergido)) | 12.46 (10.03) |
| P1-REV-01 | b | pivote_mas_y | 33.26 → 34.38 (+3 %) | 94 | 37.04 (3.37) | **3.64** | — |
| P1-REV-01 | b | pivote_menos_y | 12.16 → 12.34 (+1 %) | 117 | 15.28 (8.18) | **10.13** | — |
| P1-REV-01 | d | traba | 28.25 → 30.77 (+8 %) | 98 | 74.98 (1.67) | **4.06** | — |
| P1-REV-01 | d | pivote_mas_y | 34.65 → 35.90 (+3 %) | 95 | 38.82 (3.22) | **3.48** | — |
| P1-REV-01 | d | pivote_menos_y | 11.05 → 11.42 (+3 %) | 113 | 17.10 (7.31) | **10.95** | — |
| P1-REV-01 | e | traba_menos_y | 26.17 → 27.14 (+4 %) | 79 | 51.15 (2.44) | **4.61** | — |
| P1-REV-01 | e | pivote_mas_y | 11.44 → 11.54 (+1 %) | 116 | 16.95 (7.37) | **10.83** | — |
| P1-REV-01 | e | pivote_menos_y | 27.79 → 29.25 (+5 %) | 73 | 31.11 (4.02) | **4.27** | — |
| P1-REV-01 | f | traba | 14.01 → 15.26 (+8 %) | 98 | 37.19 (1.83) | **4.45** | — |
| P1-REV-01 | f | pivote_mas_y | 17.19 → 17.81 (+3 %) | 95 | 19.26 (3.53) | **3.82** | — |
| P1-REV-01 | f | pivote_menos_y | 5.48 → 5.66 (+3 %) | 113 | 8.48 (8.02) | **12.01** | — |
| P1-REV-01 | g | traba_menos_y | 12.98 → 13.46 (+4 %) | 79 | 25.37 (2.68) | **5.05** | — |
| P1-REV-01 | g | pivote_mas_y | 5.67 → 5.73 (+1 %) | 116 | 8.41 (8.09) | **11.87** | — |
| P1-REV-01 | g | pivote_menos_y | 13.78 → 14.51 (+5 %) | 73 | 15.43 (4.41) | **4.69** | — |
| P1-STE-01 | c | pivote_mas_y | 103.19 → 104.97 (+2 %) | 107 | 144.93 (1.66) | **2.29** | — |
| P1-STE-01 | c | rosca_mas_y | 118.70 → 134.89 (+12 %) | 68 | 177.32 (1.35) | **1.78** | 142.39 (1.69) |
| P1-STE-01 | c | pivote_menos_y | 21.39 → 18.57 (-15 %) | 116 | 25.01 (9.60) | **12.92** | 17.27 (13.90) |
| P1-STE-01 | c2 | pivote_mas_y | 19.88 → 22.69 (+12 %) | 116 | 27.90 (8.60) | **10.58** | 23.99 (10.01) |
| P1-STE-01 | c2 | pivote_menos_y | 92.27 → 96.21 (+4 %) | 114 | 123.63 (1.94) | **2.49** | — |
| P1-STE-01 | c2 | rosca_menos_y | 126.06 → 138.11 (+9 %) | 65 | 180.88 (1.33) | **1.74** | — |
| P1-STE-01 | d | pivote_mas_y | 103.22 → 104.99 (+2 %) | 107 | 144.95 (1.66) | **2.29** | — |
| P1-STE-01 | d | rosca_mas_y | 118.79 → 134.98 (+12 %) | 68 | 177.41 (1.35) | **1.78** | 142.48 (1.68) |
| P1-STE-01 | d | pivote_menos_y | 21.39 → 18.59 (-15 %) | 116 | 24.95 (9.62) | **12.91** | 17.30 (13.87) |
| P1-STE-01 | d2 | pivote_mas_y | 19.88 → 22.69 (+12 %) | 116 | 27.90 (8.60) | **10.58** | 23.99 (10.00) |
| P1-STE-01 | d2 | pivote_menos_y | 92.28 → 96.22 (+4 %) | 114 | 123.64 (1.94) | **2.49** | — |
| P1-STE-01 | d2 | rosca_menos_y | 125.96 → 138.02 (+9 %) | 65 | 180.79 (1.33) | **1.74** | — |
| P1-STE-01 | f | pivote_mas_y | 50.62 → 51.61 (+2 %) | 120 | 71.61 (1.26) | **1.74** | — |
| P1-STE-01 | f | rosca_mas_y | 33.65 → 34.50 (+2 %) | 111 | 43.11 (2.09) | **2.61** | — |
| P1-STE-01 | f | pivote_menos_y | 8.88 → 9.35 (+5 %) | 92 | 12.37 (7.27) | **9.63** | — |
| P1-STE-01 | f2 | pivote_mas_y | 8.98 → 9.38 (+4 %) | 107 | 12.16 (7.40) | **9.60** | — |
| P1-STE-01 | f2 | pivote_menos_y | 42.92 → 46.91 (+9 %) | 114 | 60.71 (1.48) | **1.92** | — |
| P1-STE-01 | f2 | rosca_menos_y | 35.02 → 35.26 (+1 %) | 65 | 48.38 (1.86) | **2.55** | — |
| P1-STE-01 | p | rosca_mas_y | 97.95 → 94.82 (-3 %) | 68 | 138.95 (1.73) | **2.53** | — |
| P1-STE-01 | p | rosca_menos_y | 104.17 → 92.25 (-13 %) | 65 | 137.29 (1.75) | **2.60** | 86.73 (2.77) |

### Convergencia (gruesa → fina)

Columna «Richardson»: si el máx* cambia > 10 %, σ_ext = σ_f + (σ_f − σ_g)/(r^p − 1) con r = h_g/h_f locales (esferas de refinamiento) y p = 2 [SUPUESTO: tensión con P2 en campo suave]; entre paréntesis el FS con σ_ext. Entre 10 y 20 % es informativo (pero «cumple» es falso si ese FS queda bajo el objetivo); > 20 % entra en la σ de diseño.

| Pieza | Caso | r_excl [mm] | σvm p99 | σvm máx* | σvm máx global | u máx [mm] | Richardson máx* |
|---|---|---|---|---|---|---|---|
| P1-DRV-03 | a | 5 | 21.41 → 20.37 (-5 %) | 25.55 → 26.30 (+3 %) | 28.08 → 32.59 (+14 %) | 0.2825 → 0.2862 (+1 %) | — |
| P1-DRV-03 | b | 5 | 21.99 → 20.92 (-5 %) | 29.60 → 29.59 (-0 %) | 33.03 → 39.42 (+16 %) | 0.2921 → 0.2963 (+1 %) | — |
| P1-REV-01 | a | 4 | 11.07 → 10.88 (-2 %) | 25.13 → 26.05 (+4 %) | 32.37 → 32.75 (+1 %) | 0.0949 → 0.0952 (+0 %) | — |
| P1-REV-01 | b | 4 | 17.84 → 17.42 (-2 %) | 52.05 → 55.13 (+6 %) | 59.74 → 65.59 (+9 %) | 0.4749 → 0.4751 (+0 %) | — |
| P1-REV-01 | d | 4 | 19.36 → 18.92 (-2 %) | 56.43 → 60.12 (+6 %) | 67.62 → 74.98 (+10 %) | 0.5444 → 0.5478 (+1 %) | — |
| P1-REV-01 | e | 4 | 20.59 → 19.74 (-4 %) | 52.34 → 55.34 (+5 %) | 82.18 → 84.13 (+2 %) | 0.5406 → 0.5443 (+1 %) | — |
| P1-REV-01 | f | 4 | 9.60 → 9.39 (-2 %) | 27.99 → 29.82 (+6 %) | 33.54 → 37.19 (+10 %) | 0.2701 → 0.2717 (+1 %) | — |
| P1-REV-01 | g | 4 | 10.21 → 9.79 (-4 %) | 25.96 → 27.45 (+5 %) | 40.77 → 41.73 (+2 %) | 0.2682 → 0.2700 (+1 %) | — |
| P1-STE-01 | a | 4 | 6.32 → 5.92 (-7 %) | 12.22 → 15.95 (+23 %) | 13.39 → 16.19 (+17 %) | 0.0665 → 0.0684 (+3 %) | 17.67 (13.58) |
| P1-STE-01 | b | 4 | 11.77 → 11.00 (-7 %) | 28.41 → 33.69 (+16 %) | 28.41 → 33.69 (+16 %) | 0.1282 → 0.1305 (+2 %) | 36.14 (6.64) |
| P1-STE-01 | c | 4 | 85.61 → 83.45 (-3 %) | 94.99 → 97.07 (+2 %) | 185.44 → 194.04 (+4 %) | 0.2148 → 0.1830 (-17 %) | — |
| P1-STE-01 | c2 | 4 | 85.65 → 82.26 (-4 %) | 85.40 → 93.29 (+8 %) | 176.45 → 192.88 (+9 %) | 0.2307 → 0.2227 (-4 %) | — |
| P1-STE-01 | d | 4 | 85.60 → 83.47 (-3 %) | 95.01 → 97.16 (+2 %) | 185.55 → 194.17 (+4 %) | 0.2241 → 0.1929 (-16 %) | — |
| P1-STE-01 | d2 | 4 | 85.67 → 82.23 (-4 %) | 85.38 → 93.26 (+8 %) | 176.37 → 192.79 (+9 %) | 0.2132 → 0.2049 (-4 %) | — |
| P1-STE-01 | f | 4 | 22.15 → 20.77 (-7 %) | 42.50 → 47.58 (+11 %) | 93.98 → 96.33 (+2 %) | 0.1479 → 0.0914 (-62 %) | 49.93 (1.80) |
| P1-STE-01 | f2 | 4 | 21.88 → 20.10 (-9 %) | 42.21 → 45.70 (+8 %) | 85.89 → 87.58 (+2 %) | 0.1310 → 0.1195 (-10 %) | — |
| P1-STE-01 | p | 4 | 79.67 → 72.98 (-9 %) | 73.98 → 64.84 (-14 %) | 163.55 → 140.68 (-16 %) | 0.1366 → 0.0374 (-265 %) | 60.61 (3.96) |
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
| P1-REV-01 | Brazo trabado: flexión en su plano con M_h completo (R12, corta) | d · brazos (máx*) | 1.00 | 28.18 | 60.12 (21.68) | 4.44 | 2.08 | -53 % ⚠ |
| P1-REV-01 | Brazo trabado: flexión en su plano con M_h completo (reversa sizing, fatiga de soldadura) | f · brazos (máx*) | 1.00 | 13.98 | 29.82 (10.76) | 4.86 | 2.28 | -53 % ⚠ |
| P1-REV-01 | Cuchara como viga entre brazos (bucket R12, corta) | a · cuchara (máx*) | 1.00 | 1.82 | 5.24 (4.20) | 68.61 | 23.87 | -65 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta) | a · cuchara (máx*) | 1.02 | 2.53 | 5.36 (4.29) | 49.49 | 23.34 | -53 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja (fatiga de soldadura, 1e5) | a · cuchara (máx*) | 1.02 | 2.53 | 5.36 (4.29) | 26.92 | 12.70 | -53 % ⚠ |
| P1-REV-01 | Cuchara abierta a torsión con un solo brazo trabado (R12, corta) | d · cuchara (Richardson) | 1.00 | 57.73 | 39.52 (10.78) | 2.17 | 3.16 | +46 % ⚠ |
| P1-REV-01 | Cuchara abierta a torsión con un solo brazo trabado (reversa sizing, fatiga de soldadura) | f · cuchara (Richardson) | 1.00 | 28.64 | 19.60 (5.35) | 2.37 | 3.47 | +46 % ⚠ |
| P1-REV-01 | Pivote: aplastamiento del brazo + aro (buje Ø24 × 18), R12 | d · pivotes (promedio) | 1.00 | 7.64 | 9.16 (28.62) | 16.35 | 13.65 | -17 % |
| P1-REV-01 | Agujero de traba: aplastamiento del brazo (perno Ø16, M_h completo, R12) | d · traba (promedio) | 1.00 | 23.49 | 16.20 (52.49) | 5.32 | 7.72 | +45 % ⚠ |
| P1-STE-01 | Flexión del tubo por el desvío del chorro (fatiga, sizing) | a · tubo (máx*) | 0.89 | 0.62 | 6.74 (3.43) | 145.87 | 13.36 | -91 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión en su plano (R12, corta; pivote + traba con M_h completo) | c · orejas_bucket (máx*) | 1.00 | 32.88 | 97.07 (95.80) | 7.30 | 2.47 | -66 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión (reversa sizing, fatiga; M_h completo en su traba) | f · orejas_bucket (máx*) | 1.00 | 16.31 | 47.58 (25.13) | 5.52 | 1.89 | -66 % ⚠ |
| P1-STE-01 | Oreja del bucket: ligamento de la rosca M24 del émbolo (R12, M_h completo) | c · lobulo_rosca (máx*) | 1.00 | 23.25 | 80.61 (129.07) | 10.32 | 2.98 | -71 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión fuera del plano por el pivote en voladizo (R12, M_h completo) | c · orejas_bucket (máx*) | 1.00 | 40.71 | 97.07 (95.80) | 5.90 | 2.47 | -58 % ⚠ |
| P1-STE-01 | Oreja: aplastamiento del piloto Ø20 con corte y momento del pivote (R12, unión deslizada) | c · anillo_piloto (promedio) | 1.00 | 91.04 | 27.49 (130.32) | 2.64 | 8.73 | +231 % ⚠ |
| P1-STE-01 | Oreja de pivote (dentro de la de la bomba): flexión de la raíz | d · orejas_pivote (máx*) | 1.00 | 2.33 | 32.70 (15.15) | 103.14 | 7.34 | -93 % ⚠ |
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
- **P1-REV-01: FS = 2.08** (objetivo 2, cumple); caso d, criterio vm: σ de diseño 60.1 MPa (máx*, máx* gruesa→fina +6 %) en (358.0, 64.5, 37.7) mm; σvm p99 18.9 MPa (FS p99 6.61). Criterio de traba única (ronda 4): con una traba sola (d/e a R12, f/g con la reversa de sizing contra el admisible de fatiga de soldadura) todo M_h pasa por un brazo y la cuchara abierta gira hasta él; el máximo queda en la cara exterior del brazo trabado, sobre su borde, bajo el pivote (el punto caliente de la ronda 3, ahora dentro de una esfera de refinamiento en las dos mallas). Con las dos trabas sin desfase (a, informativo) cada una toma la mitad de M_h. El borde de los agujeros de traba y de pivote (|σθ| de sección neta a ±90°) queda por debajo del cuerpo; el σvm de la ventana de la traba incluye el borde del contacto del perno rígido (aplastamiento). Carga = balance de cantidad de movimiento del chorro, con resultante y momento verificados contra bucket_reactions.
  - ⚠ «Brazo trabado: flexión en su plano con M_h completo (R12, corta)»: FS mano 4.44 vs FS FEA 2.08 (-53 %). La fila es la flexión del brazo EN SU PLANO con M_h completo (sección t × 60). Con una traba sola (d, f) el FEA suma la flexión FUERA del plano y la torsión que mete la cuchara abierta al girar hasta el brazo trabado, con el pico en la cara exterior del brazo, sobre su borde bajo el pivote: mecanismo que la fila no ve; el FS de diseño es el del FEA.
  - ⚠ «Brazo trabado: flexión en su plano con M_h completo (reversa sizing, fatiga de soldadura)»: FS mano 4.86 vs FS FEA 2.28 (-53 %). La fila es la flexión del brazo EN SU PLANO con M_h completo (sección t × 60). Con una traba sola (d, f) el FEA suma la flexión FUERA del plano y la torsión que mete la cuchara abierta al girar hasta el brazo trabado, con el pico en la cara exterior del brazo, sobre su borde bajo el pivote: mecanismo que la fila no ve; el FS de diseño es el del FEA.
  - ⚠ «Cuchara como viga entre brazos (bucket R12, corta)»: FS mano 68.61 vs FS FEA 23.87 (-65 %). La fila trata la cuchara como viga entre brazos; con las dos trabas (a) la cuchara casi no trabaja (σ de pocos MPa en los dos modelos): diferencia relativa grande sobre valores chicos.
  - ⚠ «Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta)»: FS mano 49.49 vs FS FEA 23.34 (-53 %). La franja empotrada (p_dinámica) no incluye la flexión global de la cuchara; el FEA (caso a escalado a p_dinámica/q_entrada) mide la tensión total de la chapa. Ambos muy por debajo del admisible.
  - ⚠ «Chapa de la cuchara: franja (fatiga de soldadura, 1e5)»: FS mano 26.92 vs FS FEA 12.70 (-53 %). La franja empotrada (p_dinámica) no incluye la flexión global de la cuchara; el FEA (caso a escalado a p_dinámica/q_entrada) mide la tensión total de la chapa. Ambos muy por debajo del admisible.
  - ⚠ «Cuchara abierta a torsión con un solo brazo trabado (R12, corta)»: FS mano 2.17 vs FS FEA 3.16 (+46 %). La fila es torsión de Saint-Venant de la sección abierta con T = M_h en la unión con el brazo trabado, sin restricción de alabeo (cota). En el FEA (una traba sola) los brazos y el aro restringen el alabeo y parte del momento entra al brazo como flexión fuera del plano: la cuchara trabaja menos. Fila conservadora para la cuchara.
  - ⚠ «Cuchara abierta a torsión con un solo brazo trabado (reversa sizing, fatiga de soldadura)»: FS mano 2.37 vs FS FEA 3.47 (+46 %). La fila es torsión de Saint-Venant de la sección abierta con T = M_h en la unión con el brazo trabado, sin restricción de alabeo (cota). En el FEA (una traba sola) los brazos y el aro restringen el alabeo y parte del momento entra al brazo como flexión fuera del plano: la cuchara trabaja menos. Fila conservadora para la cuchara.
  - ⚠ «Agujero de traba: aplastamiento del brazo (perno Ø16, M_h completo, R12)»: FS mano 5.32 vs FS FEA 7.72 (+45 %). La fila es la presión media F/(d·t) con M_h completo en una traba; el FEA promedia σvm en un anillo de 3 mm alrededor del agujero de la traba cargada (caso d): por definición menor que el pico. Mismo orden de magnitud.
- **P1-STE-01: FS = 1.74** (objetivo 2, **NO CUMPLE**); caso c2, criterio borde: borde del agujero «rosca_menos_y» a ±90° de la carga: |σθ| 138.1 MPa, gruesa→fina +9 % en (394.7, -38.0, 62.8) mm (cuerpo: FS 2.57); σvm p99 82.3 MPa (FS p99 2.92). Cargas del bucket autoequilibradas por oreja (F1; pivote rediseñado en la ronda 5): el pivote apoya con el piloto Ø20 h6 en el Ø20 H7 de la oreja con presión lineal a lo largo del agujero (par de aplastamiento, resultante en la mitad del buje; sin par en la brida: MEC-02), así que el piloto apoya en la pared cargada junto a la cara exterior y en la opuesta junto a la interior; la traba, fuerza en la rosca M24 de la misma oreja y par del perno en voladizo bajo el collar del cuerpo del émbolo; resultante y vector momento verificados contra la estática. La precarga máxima de los cuerpos de émbolo se superpone en c/c2/d/d2 y es la media (Goodman) de f/f2 (FEA-R5-02). Con M_h completo en una traba gobierna la oreja de esa traba, en su CARA INTERIOR: a R12, el borde de la rosca M24 a ±90° de la carga del perno, donde la tensión tangencial de la precarga (caso p, bastante mayor que la fila de cilindro grueso: el lóbulo no es un cilindro y la corona del collar llega al borde) se suma a la del perno, también lejos de la esquina (|σθ| interior en el JSON); en fatiga, el borde del agujero del piloto junto a la cara interior (apoyo del piloto contra la pared opuesta por el par de aplastamiento), y el máx* del cuerpo en la cara exterior junto al agujero del piloto. Los dos mecanismos son nuevos de la ronda 5 (precarga superpuesta y momento del pivote por el par de aplastamiento en vez de la brida).
  - ⚠ Extrapolación tipo Richardson bajo el objetivo (caso c, borde rosca_mas_y): σ_ext 142.4 MPa, FS 1.69 → no cumple hasta un 3.er nivel de malla o un rediseño.
  - ⚠ Extrapolación tipo Richardson bajo el objetivo (caso d, borde rosca_mas_y): σ_ext 142.5 MPa, FS 1.68 → no cumple hasta un 3.er nivel de malla o un rediseño.
  - ⚠ Extrapolación tipo Richardson bajo el objetivo (caso f, cuerpo): σ_ext 49.9 MPa, FS 1.80 → no cumple hasta un 3.er nivel de malla o un rediseño.
  - Precarga máxima de los cuerpos de émbolo sola (caso p, informativo; F = 30.6 kN, p radial 16.7 MPa): |σθ| en el borde de la rosca M24 a ±90° de la carga del perno 94.8 MPa; a ≥ 2 mm de las caras 77.6 MPa (fila a mano de cilindro grueso: 35.5 MPa). Se superpone en c/c2/d/d2 y es la tensión media (Goodman) de f/f2.
  - ⚠ «Flexión del tubo por el desvío del chorro (fatiga, sizing)»: FS mano 145.87 vs FS FEA 13.36 (-91 %). La fila trata el tubo Ø101 como viga (σ nominal < 1 MPa). En el FEA el máximo de la región del tubo está donde se le unen la torre y la oreja de pivote superior (entra el par del yugo y la reacción de los pernos): concentración local que la viga no ve. Nivel bajo (FS > 10).
  - ⚠ «Oreja del bucket: flexión en su plano (R12, corta; pivote + traba con M_h completo)»: FS mano 7.30 vs FS FEA 2.47 (-66 %). Las filas usan una sección de raíz STE_ear_t × 36 bajo el pivote (en su plano: pivote + traba con M_h completo; fuera del plano: momento del pivote en voladizo). El FEA pone el máximo de la oreja en el lóbulo de la rosca M24 y en el borde de los agujeros, donde la fuerza del perno, el par bajo el collar del émbolo, el par de aplastamiento del piloto Ø20 y la precarga del cuerpo del émbolo concentran: mecanismo local que la viga no ve; el FS de diseño es el del FEA.
  - ⚠ «Oreja del bucket: flexión (reversa sizing, fatiga; M_h completo en su traba)»: FS mano 5.52 vs FS FEA 1.89 (-66 %). Las filas usan una sección de raíz STE_ear_t × 36 bajo el pivote (en su plano: pivote + traba con M_h completo; fuera del plano: momento del pivote en voladizo). El FEA pone el máximo de la oreja en el lóbulo de la rosca M24 y en el borde de los agujeros, donde la fuerza del perno, el par bajo el collar del émbolo, el par de aplastamiento del piloto Ø20 y la precarga del cuerpo del émbolo concentran: mecanismo local que la viga no ve; el FS de diseño es el del FEA.
  - ⚠ «Oreja del bucket: ligamento de la rosca M24 del émbolo (R12, M_h completo)»: FS mano 10.32 vs FS FEA 2.98 (-71 %). La fila es el desgarro de los dos ligamentos de la rosca M24 (τ media). El FEA da el máx* del lóbulo de la rosca fuera de r_excl (flexión del lóbulo por la fuerza del perno, el par bajo el collar y la precarga del cuerpo del émbolo) y el borde del agujero aparte (tabla de bordes): mecanismos distintos.
  - ⚠ «Oreja del bucket: flexión fuera del plano por el pivote en voladizo (R12, M_h completo)»: FS mano 5.90 vs FS FEA 2.47 (-58 %). Las filas usan una sección de raíz STE_ear_t × 36 bajo el pivote (en su plano: pivote + traba con M_h completo; fuera del plano: momento del pivote en voladizo). El FEA pone el máximo de la oreja en el lóbulo de la rosca M24 y en el borde de los agujeros, donde la fuerza del perno, el par bajo el collar del émbolo, el par de aplastamiento del piloto Ø20 y la precarga del cuerpo del émbolo concentran: mecanismo local que la viga no ve; el FS de diseño es el del FEA.
  - ⚠ «Oreja: aplastamiento del piloto Ø20 con corte y momento del pivote (R12, unión deslizada)»: FS mano 2.64 vs FS FEA 8.73 (+231 %). La fila es el par de aplastamiento del piloto Ø20 en la oreja (p = R/(d·L) + 6·M/(d·L²): presión de borde de una distribución lineal). El FEA aplica esa distribución lineal (apoyo cosenoidal) y promedia σvm en el anillo de 3 mm alrededor del piloto, que además incluye la flexión de la oreja y la precarga del émbolo vecino: métricas distintas.
  - ⚠ «Oreja de pivote (dentro de la de la bomba): flexión de la raíz»: FS mano 103.14 vs FS FEA 7.34 (-93 %). La fila toma F/2 a 12 mm en 25 × 30. En el FEA los pernos de pivote reciben un par (reacciones opuestas en la mejilla Ø8 y en la rosca M6) porque el bucket empuja muy por encima del eje; el máximo está donde la oreja cilíndrica se une al frente esférico.
- **P1-INT-02: FS = 2.45** (objetivo 2, cumple); caso b, criterio vm: σ de diseño 51.1 MPa (máx*, máx* gruesa→fina +7 %) en (525.6, 149.4, 10.0) mm; σvm p99 30.0 MPa (FS p99 4.16). Gobierna el golpe de fondo con la placa sola (b): máximo en la cara superior sobre el borde del apoyo del ala (unión cuerpo–ala), convergido. Con el conducto como rigidizador (b2) baja a ≈ 18 MPa. Los avellanados M8 del pórtico: σvm promedio bajo el cono ≈ presión de la fila a mano.
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 6.85 (-94 %). La fila apoya el paño en la línea de bulones del conducto (luz 68 mm a lo ancho). Placa sola (b): sin el conducto, la franja entre la abertura y el ala trabaja a lo largo y el máximo sale en la unión cuerpo–ala; es la cota conservadora. Con el conducto rígido (b2) se recupera el modelo de la fila; la realidad está entre ambos.
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 2.45 (-98 %). La fila apoya el paño en la línea de bulones del conducto (luz 68 mm a lo ancho). Placa sola (b): sin el conducto, la franja entre la abertura y el ala trabaja a lo largo y el máximo sale en la unión cuerpo–ala; es la cota conservadora. Con el conducto rígido (b2) se recupera el modelo de la fila; la realidad está entre ambos.
  - ⚠ «Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono)»: FS mano 2.94 vs FS FEA 5.54 (+89 %). La fila usa τ media en el cilindro Ø dk × (t − h_cono) suponiendo que todo el tiro pasa por corte puro. En el FEA la compresión de la zapata sobre la cara superior equilibra la precarga en el mismo lugar y el cilindro no está en corte puro: el promedio de σvm en ese volumen es menor. Fila conservadora.
- **P1-CTL-02: FS = 3.41** (objetivo 3, cumple); caso a, criterio vm: σ de diseño 7.0 MPa (máx*, máx* gruesa→fina +2 %) en (1820.6, -108.8, 674.0) mm; σvm p99 2.9 MPa (FS p99 8.34). Paredes de 5 mm engrosadas hacia afuera (ronda 3, F-02; el entrehierro del sensor hall no cambia): gobierna la tapa (von Mises) y la tracción entre capas de las paredes ya no manda; la variante V1 (paredes de 4 mm) muestra la sensibilidad. La pieza real es 5 perímetros + 30 % giroide (solid_frac 0,55): el FEA macizo es optimista.
  - ⚠ «Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta)»: FS mano 3.84 vs FS FEA 5.51 (+44 %). La fila es una franja 50 × 6 apoyada con luz 50; la tapa real está casi toda ranurada (ranuras de las palancas), y la palma carga el nervio de 6 mm entre las dos ranuras o la tapa angosta junto a la del bucket.

<!-- FEA:AUTO:FIN -->
