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
| `../../tests/test_fea.py` | Viga en voladizo contra la solución analítica, verificación cruzada con scikit-fem, cuerpo rígido + Winkler, malla gruesa de CTL-02, estática del bucket contra structural_direccion, carga aplicada = estática en REV-01/STE-01 (setup con malla muy gruesa: resultante, M_y y vector momento; piloto Ø20 y precarga de los émbolos), regla de la σ de diseño sin convergencia (FEA-R5-01, unitario y sobre el JSON), traba única con M_h completo (casos d/e/f/g), precarga y Goodman en STE-01, bordes de agujeros cargados y cumplimiento en el JSON |

```bash
python 04_diseno/fea/fea_run.py              # todo (gruesa + fina + variantes), 3 procesos: ~12 min
python 04_diseno/fea/fea_run.py --quick      # solo malla gruesa, sin imágenes ni README (~2,5 min) → resultados_fea_quick.json
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
   de cada brazo, a ~47 mm [CALCULADO: FEA ronda 3] bajo el pivote; pivotes, roscas M24 y orejas de pivote de
   STE-01; espárragos de INT-02). Las esferas quedan en `mallas.<nivel>.refine` del JSON. Malla
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
   - **Borde de agujeros cargados por perno («lug», auditoría ronda 4, F3).** La exclusión r_excl alrededor
     de un agujero cargado tapa el pico de sección neta del borde a ±90° de la carga (y parte del ligamento
     de la rosca M24 de STE-01). Se eligió reportarlo como **verificación aparte**: en cada caso, para cada
     agujero cargado (trabas y pivotes de REV-01; pivotes Ø20 H7 y roscas M24 de STE-01) se toman los nodos
     de la superficie del agujero con |cos θ| ≤ 0,5 [SUPUESTO: ventana θ = 60…120° desde la dirección de la
     carga, proyectada ⟂ al eje] y se reporta el máximo de la tensión **circunferencial |σθ|** (la de sección
     neta del «lug») y el σvm máx. de la ventana. La dirección de la carga es la reacción de la interfaz
     (REV-01) o la fuerza aplicada (STE-01). **FS = admisible del caso / |σθ| del borde**, con el mismo objetivo
     (≥ 2); el FS del caso es el menor entre el del cuerpo (máx\*) y el de los bordes (criterio «borde»). El
     σvm de la ventana es informativo: en el arco de contacto (p. ej. la mitad de apoyo de las trabas de REV-01,
     que termina en θ = 90°, con el perno rígido que no acompaña el giro del brazo) incluye el aplastamiento y el
     borde del contacto, que verifican las filas de aplastamiento. Se compara gruesa → fina; el agujero de una
     traba deshabilitada no se evalúa como cargado y sale de las zonas excluidas (su entorno sí se evalúa).
   - **Convergencia (F4 y re-auditoría FEA-R5-01).** Si el máx\* o el |σθ| de un borde cambia > 10 % de la malla
     gruesa a la fina se calcula una extrapolación tipo Richardson σ_ext = σ_f + (σ_f − σ_g)/(r^p − 1), con
     r = h_g/h_f locales (esfera de refinamiento que contiene el punto) y p = 2 [SUPUESTO: tensión con P2 en campo
     suave]. **La falta de convergencia nunca baja la σ de diseño**: si el cambio pasa el 20 %, la σ de diseño es
     máx(σ fina, σ_ext) (`fea_run.design_sigma`, `edge_block`). El promedio en volumen en una esfera de 3 mm solo se
     admite en una **arista viva del CAD nombrada** por el setup de la pieza (`aristas_vivas` en el JSON; hoy ninguna
     pieza declara una). Entre 10 y 20 % la extrapolación es informativa, pero si su FS queda bajo el objetivo en un
     caso de diseño la pieza **no cumple** (`richardson_bajo_objetivo` en el JSON).
   - **Casos de diseño e informativos.** El FS mínimo de la pieza se toma solo de los casos de diseño
     (`casos_diseno` en el JSON); los informativos (p. ej. REV-01 a/b, con las dos trabas) se reportan igual.
     Los casos de **fatiga** (reversa de sizing) se comparan con el admisible de fatiga del material
     (`S_fat`) con el mismo objetivo: el pico del ciclo 0 → máx. contra el límite R = −1 (convención conservadora del
     proyecto). Si el caso lleva además una **tensión media constante** (la precarga de los cuerpos de émbolo en
     STE-01 f/f2), el caso guarda la precarga sola resuelta con el mismo conjunto activo (`u_media`; el sistema es
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
- **Apoyos.** Pivotes: muñón del espaciador P1-REV-02 en el buje POM P1-REV-03 (Ø `REV_bush_od`,
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
- **Reversa (auditoría ronda 4, F1; pivote rediseñado en la ronda 5).** Fuerzas del bucket sobre cada oreja de
  `bucket_statics` (= `structural_direccion.bucket_reactions`, cantidad de movimiento del chorro) con **M_h completo
  en una traba**: esa oreja recibe su pivote (chorro/2 + traba) y su traba; la otra, solo chorro/2 en su pivote. Carga
  **autoequilibrada** por oreja:
  - pivote (P1-REV-02, re-auditoría MEC-01/02/05/06): el muñón Ø20 h6 del espaciador de dúplex es también el piloto,
    ajustado en el **Ø20 H7** (`REV_sp_pilot_d`) que atraviesa la oreja de `STE_ear_t` = 14 mm. El camino **diseñado**
    del corte y del momento es el **apoyo del piloto en el agujero** (par de aplastamiento): presión cosenoidal con
    **variación lineal a lo largo del agujero**, ℓ(η) = 1 + κ·η, con ℓ⁺ en la pared que empuja la carga y ℓ⁻ en la
    opuesta (solo compresión; `fea_parts.linear_bearing`). κ se ajusta para que la resultante pase por la **mitad del
    buje**, a (`REV_y_in` − `STE_ear_y1`) + `REV_bush_L`/2 de la cara exterior (`brazo_pivote_desde_cara_exterior_mm`),
    o sea M = R × ese brazo en la cara exterior; ℓ cambia de signo dentro del agujero (`apoyo_lineal_piloto` en el JSON:
    el piloto apoya en la pared cargada junto a la cara exterior y en la opuesta junto a la interior). **No hay par en
    la cara de la brida**: con Tef-Gel la unión apretada desliza y no se cuenta con ella (la precarga del M12 es baja,
    12 N·m, y solo retiene). La selección se limita a la oreja (|y| ≥ `STE_ear_y0` − 0,5; el JSON guarda
    `facetas_agujero_pivote_fuera_de_las_orejas`, que debe ser 0);
  - traba: la **fuerza** del perno sobre la **rosca M24×1,5 de la misma oreja** (apoyo cosenoidal con la resultante en
    el plano medio de la oreja) y su **momento** (perno en voladizo hasta la mitad del brazo, `brazo_par_perno_traba_mm`)
    como par lineal de resultante nula **bajo el collar integral del cuerpo del émbolo** P1-REV-04 en la cara interior
    (corona equivalente Ø34/Ø24,5 de la fila a mano: collar Ø36 con 2 planos e/c 32; `r_collar_mm`).
  El setup **verifica** que la resultante aplicada, su momento alrededor del eje del pivote (M_y) y el **vector
  momento completo** alrededor del pivote coinciden con la estática (± 1 %; `verificacion_mano.resultante_bucket`).
- **Precarga de los cuerpos de émbolo (re-auditoría FEA-R5-02).** Cada cuerpo se aprieta contra su collar a
  `REV_lock_T_Nm` con Loctite 243 (K `REV_lock_K`): con la precarga **máxima** F = T/(K_mín·d) se aplica, en **las dos
  orejas** (los dos émbolos están siempre apretados), compresión uniforme en la corona del collar sobre la cara
  interior, el tiro axial igual y opuesto en las facetas de la rosca M24 y la presión radial de los flancos
  p = tan 30°·F/(π·d·L_e) (L_e = espesor de la oreja) sobre esas facetas. Es autoequilibrada pero genera la tensión
  tangencial del lóbulo de la rosca que suma al σθ del borde. Se superpone en los casos de reversa (c/c2/d/d2) y es la
  **tensión media** de los de fatiga (f/f2, Goodman, ver Método). El caso **p** (informativo) es la precarga sola: su
  |σθ| en el borde de la rosca se compara en «Hallazgos» con la fila a mano «Rosca M24 de la oreja: tensión
  tangencial por la precarga…» (cilindro grueso). Los casos a/b (solo dirección) no la llevan: no cargan las orejas.
  La precarga del M12 del pivote (3,6–6,7 kN, compresión de la oreja ≈ 10 MPa entre brida y arandela ancha) no se
  modela; la cubren las filas a mano de presión de la brida y de la arandela.
- **Casos.** (c)/(c2) **DISEÑO**: reversa R12 con M_h completo en la traba +Y / −Y + precarga (FS ≥ 2 contra
  fluencia). (d)/(d2) c/c2 + (a) (maniobra en reversa). (f)/(f2) **DISEÑO, fatiga**: reversa de sizing con
  M_h completo en la traba +Y / −Y, corrida, con la precarga como media, contra `AL6061_FAT`. (p) precarga sola,
  informativo.
- **Borde de los agujeros** (pivotes Ø20 H7 y roscas M24): verificación de sección neta a ±90° de la carga
  aplicada (Método, 5).

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
- **Uniones de la oreja de STE-01.** El momento del perno de la traba se lleva a la cara interior de la oreja
  bajo el collar integral del cuerpo del émbolo (unión que no se abre: fila a mano de P1-REV-04 «Cuerpo del émbolo
  apretado contra su collar: la unión no se abre…» con la precarga mínima; presión del collar con la máxima en
  P1-STE-01). Si el cuerpo quedara flojo, se apoyaría en los extremos de la rosca (pares de apoyo opuestos), que el
  modelo no representa. La precarga del cuerpo se modela como cargas equivalentes (corona, tiro axial y presión
  radial uniforme de los flancos), no como contacto de rosca: los picos en el fondo de los filetes no se resuelven
  (zona excluida; el arrancamiento de la rosca es fila a mano). El piloto del pivote es una presión impuesta (rígido,
  sin juego H7/h6): con juego, el apoyo se concentra aún más en los bordes del agujero.

<!-- FEA:AUTO:INICIO (generado por fea_run.py; no editar a mano) -->

Corrida: 2026-10-02 · inputs v2.0 · 2081 s [CALCULADO]

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
| P1-STE-01 | gruesa | 8 | 29058 | 156501 | 0.000 | 0.018 | 402 |
| P1-STE-01 | fina | 4.5 | 91752 | 468678 | 0.000 | 0.182 | 520 |
| P1-INT-02 | gruesa | 14 | 47904 | 268719 | 0.000 | 0.228 | 112 |
| P1-INT-02 | fina | 8 | 93218 | 507585 | 0.000 | 0.307 | 168 |
| P1-CTL-02 | gruesa | 6 | 11240 | 65856 | 0.082 | 0.393 | 0 |
| P1-CTL-02 | fina | 3 | 46480 | 259596 | 0.208 | 0.454 | 0 |

### Resultados (malla fina) — tensiones en MPa; FS = admisible / σ de diseño

σ de diseño = σvm máx* (máximo fuera de r_excl de cargas y apoyos) si cambia ≤ 20 % de la malla gruesa a la fina; si no converge (arista viva del CAD o astilla de malla), el máximo del promedio en una esfera de radio 3 mm («prom.»). En PETG el FS es el menor de σvm, σ1 y σZ (el criterio va entre paréntesis). El FS del caso es el menor entre el del cuerpo y el del borde de los agujeros cargados (tabla de bordes; criterio «borde»). Casos de fatiga (reversa de sizing) contra el admisible de fatiga del material; casos «informativo» fuera del FS mínimo.

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
| P1-STE-01 | a: Desvío del chorro F_s = máx(sizing 323, R12 364) = 364 N repartido en el paso (centro de presión e = 66 mm, = structural) | 16.00 | 6.02 | 16.00 | 7.98 | 7.98 (promedio en volumen) | 0.069 | **30.06** | 39.84 | cumple |
| P1-STE-01 | b: F_s = 364 N en la boca de salida (últimos 20 mm; brazo ≈ L = 132 mm, conservador) | 35.04 | 11.33 | 35.04 | 14.71 | 35.04 (máx*) | 0.132 | **6.85** | 21.18 | cumple |
| P1-STE-01 | c: Reversa R12 (F_b = 1408 N, M_h = 135 N·m) con M_h COMPLETO en la traba +Y: pivote +Y (chorro/2 + traba), pivote −Y (chorro/2) y rosca M24 +Y (DISEÑO) | 77.32 | 35.57 | 61.37 | 55.32 | borde rosca_mas_y: σθ 78.03 | 0.238 | **3.08** (borde rosca_mas_y) | 6.75 | cumple |
| P1-STE-01 | c2: Reversa R12 con M_h COMPLETO en la traba −Y: pivote −Y (chorro/2 + traba), pivote +Y y rosca M24 −Y (DISEÑO) | 74.70 | 36.14 | 59.77 | 53.59 | borde rosca_menos_y: σθ 75.31 | 0.275 | **3.19** (borde rosca_menos_y) | 6.64 | cumple |
| P1-STE-01 | d: Combinado: reversa (c) + desvío F_s en el paso (a) (maniobra en reversa) | 77.26 | 35.60 | 61.40 | 55.35 | borde rosca_mas_y: σθ 77.96 | 0.246 | **3.08** (borde rosca_mas_y) | 6.74 | cumple |
| P1-STE-01 | d2: Combinado: reversa (c2) + desvío F_s en el paso (a) | 74.77 | 36.31 | 60.94 | 53.58 | borde rosca_menos_y: σθ 75.37 | 0.259 | **3.18** (borde rosca_menos_y) | 6.61 | cumple |
| P1-STE-01 | f: Reversa de sizing (F_b = 698 N, M_h = 67.1 N·m) con M_h completo en la traba +Y (fatiga) | 38.35 | 17.65 | 30.44 | 27.44 | borde rosca_mas_y: σθ 38.71 | 0.118 | **2.33** (borde rosca_mas_y) | 5.10 | cumple |
| P1-STE-01 | f2: Reversa de sizing con M_h completo en la traba −Y (fatiga) | 37.06 | 17.93 | 29.65 | 26.58 | borde rosca_menos_y: σθ 37.36 | 0.137 | **2.41** (borde rosca_menos_y) | 5.02 | cumple |
| P1-INT-02 | a: Espárragos del pórtico: precarga 6944 N (10 N·m, K 0.18) ± vuelco Fa·h/Δx/2 = 422 N (Φ = 0.25) + corte Fa/4 | 63.39 | 14.67 | 9.55 | 9.55 | 9.55 (máx*) | 0.023 | **13.09** | 8.52 | cumple |
| P1-INT-02 | b: Golpe de fondo 50 kPa + presión de cierre 67 kPa en la abertura + tiro de la brida del conducto 4049 N (placa sola, sin la rigidez del conducto: conservador) | 51.42 | 30.02 | 51.11 | 51.11 | 51.11 (máx*) | 0.216 | **2.45** | 4.16 | cumple |
| P1-INT-02 | b2: Ídem (b) con el conducto P1-INT-01 como rigidizador rígido abulonado (cota rígida; = modelo de structural_toma) | 20.86 | 10.66 | 18.26 | 17.44 | 18.26 (máx*) | 0.048 | **6.85** | 11.73 | cumple |
| P1-CTL-02 | a: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-10, 0) mm (nervio entre ranuras); A cargada 847 mm² | 7.03 | 2.88 | 7.03 | 6.85 | 7.03 (máx*) | 0.813 | **3.41** | 8.34 | cumple |
| P1-CTL-02 | b: Mano apoyada 150 N, palma Ø50 en (x, y)_U = (-62, -12) mm (tapa ancha junto a la ranura del bucket); A cargada 1472 mm² | 4.35 | 2.22 | 4.35 | 3.66 | σZ 2.63 (máx*) | 0.419 | **3.49** (Z) | 10.81 | cumple |

\* máximo fuera de las zonas de aplicación de cargas/apoyos concentrados (r_excl en la tabla de convergencia); el máximo global incluye singularidades de aplicación y se reporta para transparencia.

### Borde de los agujeros cargados por perno (sección neta, a ±90° de la carga)

Nodos de la superficie del agujero con |cos θ| ≤ 0,5 respecto de la dirección de la carga (θ = 60…120°), zona que la exclusión r_excl del máx* no mira (auditoría ronda 4, F3). Se verifica la tensión circunferencial |σθ| (sección neta del «lug»): FS = admisible del caso / |σθ| máx. (malla fina). σvm de la ventana: informativo (en el arco de contacto incluye el aplastamiento y el borde del contacto, que verifican las filas de aplastamiento). Si |σθ| cambia > 10 % de la gruesa a la fina se extrapola (tipo Richardson, p = 2, tamaños locales).

| Pieza | Caso | Agujero | σθ (valor abs.) gruesa → fina [MPa] | θ [°] | σvm ventana [MPa] (FS) | **FS** | Richardson σ_ext (FS) |
|---|---|---|---|---|---|---|---|
| P1-REV-01 | a | traba | 13.15 → 13.32 (+1 %) | 64 | 18.48 (6.77) | **9.39** | — |
| P1-REV-01 | a | traba_menos_y | 17.52 → 17.20 (-2 %) | 65 | 21.47 (5.82) | **7.27** | — |
| P1-REV-01 | a | pivote_mas_y | 23.85 → 24.56 (+3 %) | 87 | 25.93 (4.82) | **5.09** | — |
| P1-REV-01 | a | pivote_menos_y | 18.15 → 18.32 (+1 %) | 100 | 20.92 (5.97) | **6.82** | — |
| P1-REV-01 | b | traba | 25.65 → 27.66 (+7 %) | 98 | 65.59 (1.91) | **4.52** | — |
| P1-REV-01 | b | traba_menos_y | 8.11 → 10.98 (+26 %) | 61 | 8.54 (14.65) | **11.39** | 12.46 (10.03) |
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
| P1-STE-01 | c | pivote_mas_y | 63.75 → 64.93 (+2 %) | 73 | 67.48 (3.56) | **3.70** | — |
| P1-STE-01 | c | rosca_mas_y | 71.56 → 78.03 (+8 %) | 111 | 77.32 (3.10) | **3.08** | — |
| P1-STE-01 | c | pivote_menos_y | 13.16 → 11.98 (-10 %) | 71 | 12.77 (18.80) | **20.03** | — |
| P1-STE-01 | c2 | pivote_mas_y | 11.80 → 11.20 (-5 %) | 71 | 12.21 (19.65) | **21.43** | — |
| P1-STE-01 | c2 | pivote_menos_y | 58.97 → 55.20 (-7 %) | 71 | 57.31 (4.19) | **4.35** | — |
| P1-STE-01 | c2 | rosca_menos_y | 68.83 → 75.31 (+9 %) | 107 | 74.70 (3.21) | **3.19** | — |
| P1-STE-01 | d | pivote_mas_y | 63.72 → 64.89 (+2 %) | 73 | 67.44 (3.56) | **3.70** | — |
| P1-STE-01 | d | rosca_mas_y | 71.49 → 77.96 (+8 %) | 111 | 77.26 (3.11) | **3.08** | — |
| P1-STE-01 | d | pivote_menos_y | 13.15 → 11.98 (-10 %) | 71 | 12.73 (18.85) | **20.04** | — |
| P1-STE-01 | d2 | pivote_mas_y | 11.85 → 11.24 (-5 %) | 71 | 12.30 (19.52) | **21.36** | — |
| P1-STE-01 | d2 | pivote_menos_y | 59.00 → 55.23 (-7 %) | 71 | 57.33 (4.19) | **4.35** | — |
| P1-STE-01 | d2 | rosca_menos_y | 68.89 → 75.37 (+9 %) | 107 | 74.77 (3.21) | **3.18** | — |
| P1-STE-01 | f | pivote_mas_y | 31.62 → 32.21 (+2 %) | 73 | 33.47 (2.69) | **2.79** | — |
| P1-STE-01 | f | rosca_mas_y | 35.49 → 38.71 (+8 %) | 111 | 38.35 (2.35) | **2.33** | — |
| P1-STE-01 | f | pivote_menos_y | 6.53 → 5.94 (-10 %) | 71 | 6.33 (14.21) | **15.15** | — |
| P1-STE-01 | f2 | pivote_mas_y | 5.85 → 5.56 (-5 %) | 71 | 6.06 (14.86) | **16.20** | — |
| P1-STE-01 | f2 | pivote_menos_y | 29.25 → 27.38 (-7 %) | 71 | 28.43 (3.17) | **3.29** | — |
| P1-STE-01 | f2 | rosca_menos_y | 34.14 → 37.36 (+9 %) | 107 | 37.06 (2.43) | **2.41** | — |

### Convergencia (gruesa → fina)

Columna «Richardson»: si el máx* cambia > 10 %, σ_ext = σ_f + (σ_f − σ_g)/(r^p − 1) con r = h_g/h_f locales (esferas de refinamiento) y p = 2 [SUPUESTO: tensión con P2 en campo suave]; informativo, entre paréntesis el FS con σ_ext.

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
| P1-STE-01 | a | 4 | 6.35 → 6.02 (-5 %) | 12.25 → 16.00 (+23 %) | 13.53 → 16.00 (+15 %) | 0.0669 → 0.0688 (+3 %) | 17.73 (13.53) |
| P1-STE-01 | b | 4 | 11.78 → 11.33 (-4 %) | 30.61 → 35.04 (+13 %) | 30.61 → 35.04 (+13 %) | 0.1285 → 0.1316 (+2 %) | 37.09 (6.47) |
| P1-STE-01 | c | 4 | 38.46 → 35.57 (-8 %) | 58.10 → 61.37 (+5 %) | 70.12 → 77.32 (+9 %) | 0.2385 → 0.2378 (-0 %) | — |
| P1-STE-01 | c2 | 4 | 39.66 → 36.14 (-10 %) | 56.31 → 59.77 (+6 %) | 72.25 → 74.70 (+3 %) | 0.2706 → 0.2752 (+2 %) | — |
| P1-STE-01 | d | 4 | 38.44 → 35.60 (-8 %) | 58.13 → 61.40 (+5 %) | 70.06 → 77.26 (+9 %) | 0.2472 → 0.2465 (-0 %) | — |
| P1-STE-01 | d2 | 4 | 39.75 → 36.31 (-9 %) | 57.27 → 60.94 (+6 %) | 72.27 → 74.77 (+3 %) | 0.2543 → 0.2585 (+2 %) | — |
| P1-STE-01 | f | 4 | 19.08 → 17.65 (-8 %) | 28.82 → 30.44 (+5 %) | 34.78 → 38.35 (+9 %) | 0.1183 → 0.1180 (-0 %) | — |
| P1-STE-01 | f2 | 4 | 19.67 → 17.93 (-10 %) | 27.93 → 29.65 (+6 %) | 35.84 → 37.06 (+3 %) | 0.1342 → 0.1365 (+2 %) | — |
| P1-INT-02 | a | 8 | 14.07 → 14.67 (+4 %) | 9.00 → 9.55 (+6 %) | 63.94 → 63.39 (-1 %) | 0.0194 → 0.0226 (+14 %) | — |
| P1-INT-02 | b | 8 | 27.79 → 30.02 (+7 %) | 47.53 → 51.11 (+7 %) | 47.81 → 51.42 (+7 %) | 0.2047 → 0.2162 (+5 %) | — |
| P1-INT-02 | b2 | 8 | 10.29 → 10.66 (+3 %) | 17.57 → 18.26 (+4 %) | 17.71 → 20.86 (+15 %) | 0.0458 → 0.0485 (+5 %) | — |
| P1-CTL-02 | a | 4 | 3.20 → 2.88 (-11 %) | 6.89 → 7.03 (+2 %) | 6.89 → 7.03 (+2 %) | 0.7892 → 0.8127 (+3 %) | — |
| P1-CTL-02 | b | 4 | 2.26 → 2.22 (-2 %) | 4.05 → 4.35 (+7 %) | 4.05 → 4.35 (+7 %) | 0.4020 → 0.4195 (+4 %) | — |

### Comparación con el cálculo a mano (resultados/estructural.json)

σ FEA = σvm de la región de la pieza que modela la fila (máx* salvo que se indique promedio en volumen), escalada a la carga de la fila (columna «×»). FS con el admisible de la fila. Dif = (FS_FEA − FS_mano)/FS_mano.

| Pieza | Fila structural_*.py | Caso FEA · región | × | σ mano [MPa] | σ FEA [MPa] (p99) | FS mano | FS FEA | Dif |
|---|---|---|---|---|---|---|---|---|
| P1-DRV-03 | Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa) | a · mejillas (prom. esfera) | 1.00 | 1.02 | 17.98 (7.79) | 112.30 | 6.40 | -94 % ⚠ |
| P1-DRV-03 | Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico | a · tablero_y_alma (máx*) | 1.00 | 16.60 | 26.30 (22.81) | 6.93 | 4.37 | -37 % ⚠ |
| P1-DRV-03 | Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo | b · alojamiento (prom. esfera) | 1.00 | 2.99 | 9.47 (9.48) | 80.27 | 25.34 | -68 % ⚠ |
| P1-REV-01 | Brazo trabado: flexión en su plano con M_h completo (R12, corta) | d · brazos (máx*) | 1.00 | 28.18 | 60.12 (21.68) | 4.44 | 2.08 | -53 % ⚠ |
| P1-REV-01 | Brazo trabado: flexión en su plano con M_h completo (reversa sizing, fatiga de soldadura) | f · brazos (máx*) | 1.00 | 13.98 | 29.82 (10.76) | 4.86 | 2.28 | -53 % ⚠ |
| P1-REV-01 | Cuchara como viga entre brazos (bucket R12, corta) | a · cuchara (máx*) | 1.00 | 1.79 | 5.24 (4.20) | 69.79 | 23.87 | -66 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta) | a · cuchara (máx*) | 1.02 | 2.44 | 5.36 (4.29) | 51.25 | 23.34 | -54 % ⚠ |
| P1-REV-01 | Chapa de la cuchara: franja (fatiga de soldadura, 1e5) | a · cuchara (máx*) | 1.02 | 2.44 | 5.36 (4.29) | 27.88 | 12.70 | -54 % ⚠ |
| P1-REV-01 | Cuchara abierta a torsión con un solo brazo trabado (R12, corta) | d · cuchara (prom. esfera) | 1.00 | 57.73 | 20.33 (10.78) | 2.17 | 6.15 | +184 % ⚠ |
| P1-REV-01 | Cuchara abierta a torsión con un solo brazo trabado (reversa sizing, fatiga de soldadura) | f · cuchara (prom. esfera) | 1.00 | 28.64 | 10.08 (5.35) | 2.37 | 6.74 | +184 % ⚠ |
| P1-REV-01 | Pivote: aplastamiento del brazo + aro (buje Ø24 × 18), R12 | d · pivotes (promedio) | 1.00 | 7.64 | 9.16 (28.62) | 16.35 | 13.65 | -17 % |
| P1-REV-01 | Agujero de traba: aplastamiento del brazo (perno Ø16, M_h completo, R12) | d · traba (promedio) | 1.00 | 23.49 | 16.20 (52.49) | 5.32 | 7.72 | +45 % ⚠ |
| P1-STE-01 | Flexión del tubo por el desvío del chorro (fatiga, sizing) | a · tubo (máx*) | 0.89 | 0.62 | 6.56 (3.45) | 145.87 | 13.72 | -91 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión en su plano (R12, corta; pivote + traba con M_h completo) | c · orejas_bucket (máx*) | 1.00 | 38.36 | 61.37 (41.55) | 6.26 | 3.91 | -38 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión (reversa sizing, fatiga; M_h completo en su traba) | f · orejas_bucket (máx*) | 1.00 | 19.03 | 30.44 (20.61) | 4.73 | 2.96 | -38 % ⚠ |
| P1-STE-01 | Oreja del bucket: ligamento de la rosca M24 del émbolo (R12, M_h completo) | c · lobulo_rosca (máx*) | 1.00 | 27.12 | 61.37 (55.29) | 8.85 | 3.91 | -56 % ⚠ |
| P1-STE-01 | Oreja del bucket: flexión fuera del plano por el pivote en voladizo (R12, M_h completo) | c · orejas_bucket (máx*) | 1.00 | 51.59 | 61.37 (41.55) | 4.65 | 3.91 | -16 % |
| P1-STE-01 | Oreja del bucket: aplastamiento del piloto Ø16 del espaciador en el agujero H7 (R12, si la unión desliza) | c · anillo_piloto (promedio) | 1.00 | 17.20 | 16.16 (56.18) | 13.96 | 14.85 | +6 % |
| P1-STE-01 | Oreja de pivote (dentro de la de la bomba): flexión de la raíz | d · orejas_pivote (máx*) | 1.00 | 2.33 | 37.66 (15.46) | 103.14 | 6.37 | -94 % ⚠ |
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
  - ⚠ «Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa)»: FS mano 112.30 vs FS FEA 6.40 (-94 %). La fila solo mira la flexión de la mejilla en su plano por Fa/2 (sección 12 × 150, muy rígida). El FEA pone el máximo de la mejilla en su unión con el tablero: el tablero cargado por el alojamiento flexiona y arrastra el borde superior de la mejilla fuera de su plano (marco tablero + mejillas). Mecanismo que la fila no ve; nivel bajo.
  - ⚠ «Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico»: FS mano 6.93 vs FS FEA 4.37 (-37 %). El máximo está en la unión del alma central con el tablero (ahora con empalme r 3): el momento de Fa excéntrico y el radial entran al tablero por el alma; la viga biapoyada de la fila no ve esa concentración. FS sobre 2.
  - ⚠ «Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo»: FS mano 80.27 vs FS FEA 25.34 (-68 %). La fila es el corte medio del resalte (τ = Fa/(π·D·t)), un valor nominal; el FEA mide la flexión del resalte como placa anular (el aro apoya solo entre Da_max y D) y la del alojamiento en su unión con el alma. Ambos lejos del admisible.
- **P1-REV-01: FS = 2.08** (objetivo 2, cumple); caso d, criterio vm: σ de diseño 60.1 MPa (máx*, máx* gruesa→fina +6 %) en (358.0, 64.5, 37.7) mm; σvm p99 18.9 MPa (FS p99 6.61). Criterio de traba única (ronda 4): con una traba sola (d/e a R12, f/g con la reversa de sizing contra el admisible de fatiga de soldadura) todo M_h pasa por un brazo y la cuchara abierta gira hasta él; el máximo queda en la cara exterior del brazo trabado, sobre su borde, bajo el pivote (el punto caliente de la ronda 3, ahora dentro de una esfera de refinamiento en las dos mallas). Con las dos trabas sin desfase (a, informativo) cada una toma la mitad de M_h. El borde de los agujeros de traba y de pivote (|σθ| de sección neta a ±90°) queda por debajo del cuerpo; el σvm de la ventana de la traba incluye el borde del contacto del perno rígido (aplastamiento). Carga = balance de cantidad de movimiento del chorro, con resultante y momento verificados contra bucket_reactions.
  - ⚠ «Brazo trabado: flexión en su plano con M_h completo (R12, corta)»: FS mano 4.44 vs FS FEA 2.08 (-53 %). La fila es la flexión del brazo EN SU PLANO con M_h completo (sección t × 60). Con una traba sola (d, f) el FEA suma la flexión FUERA del plano y la torsión que mete la cuchara abierta al girar hasta el brazo trabado, con el pico en la cara exterior del brazo, sobre su borde bajo el pivote: mecanismo que la fila no ve; el FS de diseño es el del FEA.
  - ⚠ «Brazo trabado: flexión en su plano con M_h completo (reversa sizing, fatiga de soldadura)»: FS mano 4.86 vs FS FEA 2.28 (-53 %). La fila es la flexión del brazo EN SU PLANO con M_h completo (sección t × 60). Con una traba sola (d, f) el FEA suma la flexión FUERA del plano y la torsión que mete la cuchara abierta al girar hasta el brazo trabado, con el pico en la cara exterior del brazo, sobre su borde bajo el pivote: mecanismo que la fila no ve; el FS de diseño es el del FEA.
  - ⚠ «Cuchara como viga entre brazos (bucket R12, corta)»: FS mano 69.79 vs FS FEA 23.87 (-66 %). La fila trata la cuchara como viga entre brazos; con las dos trabas (a) la cuchara casi no trabaja (σ de pocos MPa en los dos modelos): diferencia relativa grande sobre valores chicos.
  - ⚠ «Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta)»: FS mano 51.25 vs FS FEA 23.34 (-54 %). La franja empotrada (p_dinámica) no incluye la flexión global de la cuchara; el FEA (caso a escalado a p_dinámica/q_entrada) mide la tensión total de la chapa. Ambos muy por debajo del admisible.
  - ⚠ «Chapa de la cuchara: franja (fatiga de soldadura, 1e5)»: FS mano 27.88 vs FS FEA 12.70 (-54 %). La franja empotrada (p_dinámica) no incluye la flexión global de la cuchara; el FEA (caso a escalado a p_dinámica/q_entrada) mide la tensión total de la chapa. Ambos muy por debajo del admisible.
  - ⚠ «Cuchara abierta a torsión con un solo brazo trabado (R12, corta)»: FS mano 2.17 vs FS FEA 6.15 (+184 %). La fila es torsión de Saint-Venant de la sección abierta con T = M_h en la unión con el brazo trabado, sin restricción de alabeo (cota). En el FEA (una traba sola) los brazos y el aro restringen el alabeo y parte del momento entra al brazo como flexión fuera del plano: la cuchara trabaja menos. Fila conservadora para la cuchara.
  - ⚠ «Cuchara abierta a torsión con un solo brazo trabado (reversa sizing, fatiga de soldadura)»: FS mano 2.37 vs FS FEA 6.74 (+184 %). La fila es torsión de Saint-Venant de la sección abierta con T = M_h en la unión con el brazo trabado, sin restricción de alabeo (cota). En el FEA (una traba sola) los brazos y el aro restringen el alabeo y parte del momento entra al brazo como flexión fuera del plano: la cuchara trabaja menos. Fila conservadora para la cuchara.
  - ⚠ «Agujero de traba: aplastamiento del brazo (perno Ø16, M_h completo, R12)»: FS mano 5.32 vs FS FEA 7.72 (+45 %). La fila es la presión media F/(d·t) con M_h completo en una traba; el FEA promedia σvm en un anillo de 3 mm alrededor del agujero de la traba cargada (caso d): por definición menor que el pico. Mismo orden de magnitud.
- **P1-STE-01: FS = 2.33** (objetivo 2, cumple); caso f, criterio borde: borde del agujero «rosca_mas_y» a ±90° de la carga: |σθ| 38.7 MPa, gruesa→fina +8 % en (398.0, 52.0, 87.4) mm (cuerpo: FS 2.96); σvm p99 17.6 MPa (FS p99 5.10). Cargas del bucket autoequilibradas por oreja (ronda 4, F1): fuerza en el piloto Ø16 y en la rosca M24 de la misma oreja, momentos del muñón y del perno en voladizo como pares de resultante nula (brida y contratuerca); resultante y momento verificados contra la estática. Con M_h completo en una traba gobierna la oreja de esa traba: el borde de la rosca M24 o del piloto a ±90° de la carga (|σθ| de sección neta, que la exclusión del máx* tapaba: F3) y el contorno del lóbulo de la rosca en la cara exterior. Los casos de fatiga (f/f2) tienen el menor FS: la reversa de sizing es la mitad de R12 pero el admisible de fatiga es bastante menos que la mitad de la fluencia. El pico donde la oreja de pivote toca el labio de entrada (radio de 2 mm, F-03) converge.
  - ⚠ «Flexión del tubo por el desvío del chorro (fatiga, sizing)»: FS mano 145.87 vs FS FEA 13.72 (-91 %). La fila trata el tubo Ø101 como viga (σ nominal < 1 MPa). En el FEA el máximo de la región del tubo está donde se le unen la torre y la oreja de pivote superior (entra el par del yugo y la reacción de los pernos): concentración local que la viga no ve. Nivel bajo (FS > 10).
  - ⚠ «Oreja del bucket: flexión en su plano (R12, corta; pivote + traba con M_h completo)»: FS mano 6.26 vs FS FEA 3.91 (-38 %). Las filas usan una sección de raíz STE_ear_t × 36 bajo el pivote (en su plano: pivote + traba con M_h completo; fuera del plano: momento del espaciador). El FEA pone el máximo de la oreja en el lóbulo de la rosca M24 y en el borde de los agujeros, donde la fuerza del perno, el par de la contratuerca y el del espaciador concentran: mecanismo local que la viga no ve; el FS de diseño es el del FEA.
  - ⚠ «Oreja del bucket: flexión (reversa sizing, fatiga; M_h completo en su traba)»: FS mano 4.73 vs FS FEA 2.96 (-38 %). Las filas usan una sección de raíz STE_ear_t × 36 bajo el pivote (en su plano: pivote + traba con M_h completo; fuera del plano: momento del espaciador). El FEA pone el máximo de la oreja en el lóbulo de la rosca M24 y en el borde de los agujeros, donde la fuerza del perno, el par de la contratuerca y el del espaciador concentran: mecanismo local que la viga no ve; el FS de diseño es el del FEA.
  - ⚠ «Oreja del bucket: ligamento de la rosca M24 del émbolo (R12, M_h completo)»: FS mano 8.85 vs FS FEA 3.91 (-56 %). La fila es el desgarro de los dos ligamentos de la rosca M24 (τ media). El FEA da el máx* del lóbulo de la rosca fuera de r_excl (flexión del lóbulo por la fuerza del perno y el par de la contratuerca) y el borde del agujero aparte (tabla de bordes): mecanismos distintos.
  - ⚠ «Oreja de pivote (dentro de la de la bomba): flexión de la raíz»: FS mano 103.14 vs FS FEA 6.37 (-94 %). La fila toma F/2 a 12 mm en 25 × 30. En el FEA los pernos de pivote reciben un par (reacciones opuestas en la mejilla Ø8 y en la rosca M6) porque el bucket empuja muy por encima del eje; el máximo está donde la oreja cilíndrica se une al frente esférico.
- **P1-INT-02: FS = 2.45** (objetivo 2, cumple); caso b, criterio vm: σ de diseño 51.1 MPa (máx*, máx* gruesa→fina +7 %) en (525.6, 149.4, 10.0) mm; σvm p99 30.0 MPa (FS p99 4.16). Gobierna el golpe de fondo con la placa sola (b): máximo en la cara superior sobre el borde del apoyo del ala (unión cuerpo–ala), convergido. Con el conducto como rigidizador (b2) baja a ≈ 18 MPa. Los avellanados M8 del pórtico: σvm promedio bajo el cono ≈ presión de la fila a mano.
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 6.85 (-94 %). La fila apoya el paño en la línea de bulones del conducto (luz 68 mm a lo ancho). Placa sola (b): sin el conducto, la franja entre la abertura y el ala trabaja a lo largo y el máximo sale en la unión cuerpo–ala; es la cota conservadora. Con el conducto rígido (b2) se recupera el modelo de la fila; la realidad está entre ambos.
  - ⚠ «Paño lateral entre bulones del conducto y del ala: golpe de fondo»: FS mano 106.56 vs FS FEA 2.45 (-98 %). La fila apoya el paño en la línea de bulones del conducto (luz 68 mm a lo ancho). Placa sola (b): sin el conducto, la franja entre la abertura y el ala trabaja a lo largo y el máximo sale en la unión cuerpo–ala; es la cota conservadora. Con el conducto rígido (b2) se recupera el modelo de la fila; la realidad está entre ambos.
  - ⚠ «Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono)»: FS mano 2.94 vs FS FEA 5.54 (+89 %). La fila usa τ media en el cilindro Ø dk × (t − h_cono) suponiendo que todo el tiro pasa por corte puro. En el FEA la compresión de la zapata sobre la cara superior equilibra la precarga en el mismo lugar y el cilindro no está en corte puro: el promedio de σvm en ese volumen es menor. Fila conservadora.
- **P1-CTL-02: FS = 3.41** (objetivo 3, cumple); caso a, criterio vm: σ de diseño 7.0 MPa (máx*, máx* gruesa→fina +2 %) en (1820.6, -108.8, 674.0) mm; σvm p99 2.9 MPa (FS p99 8.34). Paredes de 5 mm engrosadas hacia afuera (ronda 3, F-02; el entrehierro del sensor hall no cambia): gobierna la tapa (von Mises) y la tracción entre capas de las paredes ya no manda; la variante V1 (paredes de 4 mm) muestra la sensibilidad. La pieza real es 5 perímetros + 30 % giroide (solid_frac 0,55): el FEA macizo es optimista.
  - ⚠ «Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta)»: FS mano 3.84 vs FS FEA 5.51 (+44 %). La fila es una franja 50 × 6 apoyada con luz 50; la tapa real está casi toda ranurada (ranuras de las palancas), y la palma carga el nervio de 6 mm entre las dos ranuras o la tapa angosta junto a la del bucket.

<!-- FEA:AUTO:FIN -->
