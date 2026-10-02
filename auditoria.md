# Auditoría adversarial — P1-J waterjet (Pasada 3)

Método: auditores independientes por área (cálculo/física, CAD/estructural, BOM/eléctrico/legal,
documentos) que intentan refutar el paquete leyendo código y recalculando a mano; cada hallazgo se
verifica antes de corregirlo; se repiten rondas hasta que una ronda no encuentra nada relevante.

## Hallazgos detectados durante el diseño del waterjet (Pasadas 1–2, ya corregidos)

| # | Hallazgo | Severidad | Resolución |
|---|---|---|---|
| W-01 | **Plano de Jorge: la rejilla/toma estaba detrás del impulsor** → la bomba no se ceba ni recibe flujo ordenado | Crítica | Toma enrasada entera a proa del impulsor, rampa 27°, labio con radio (D-06; research/R10b) |
| W-02 | Bomba dimensionada a la potencia continua: no podía usar la potencia pico del tren directo limitado por tensión | Alta | Variable `design_power_frac` en el optimizador (02 §5) |
| W-03 | `params.py`: la posición del sello usaba una x del marco BOTE como distancia sobre el eje | Alta | Distancia sobre el eje / cos α; test de interfaz |
| W-04 | Caja del sello dentro del conducto (la salida del eje cortaba la curva del techo) | Alta | Salida del eje a 1,85·D (techo de curvatura continua) |
| W-05 | Pie del soporte de rodamientos sobre la abertura de la toma | Alta | Pórtico con apoyos a \|y\| = W_open/2 + 45 mm, espárragos M8 |
| W-06 | Roscas M8 en Al del soporte con FS 1,97 < 2 | Media | Espárragos avellanados A4 + tuerca |
| W-07 | Pernos de pivote de la boquilla FS 1,48 en voladizo | Alta | Biempotrado (STE-02) y espárrago con hombro (STE-05) |
| W-08 | Bucket bajado a 3,7 mm de la quilla | Media | 12,6 mm (REV-01) |
| W-09 | Resalte del eje Ø25 < d_a mín 25,6 mm del 7204 BEP (el aro interior no apoya) | Media | Resalte Ø26 |
| W-10 | Cambio de tobera Ø82 → Ø87 rompía dirección y placa de espejo | Alta | Geometría robusta para D_tobera 76,6–97,7 mm (orejas en PMP-09, bujes POM) + verify en todo el rango del optimizador |
| W-11 | `comparacion.py`: costo de B nulo (columnas de la BOM mal leídas) | Media | Lee `cubre` y `precio_total_EUR`; valores en README |
| W-12 | Batería ubicada contra un largo de casco de referencia (1,4 m) en vez del casco real | Baja | Chequeo contra 0,75·LOA |
| W-13 | Ensamblaje STEP de 69 MB (límite de GitHub) | Baja | `.step.gz` versionado |

## Abiertos declarados (no se resuelven desde la propulsión)

| # | Hallazgo | Severidad | Estado |
|---|---|---|---|
| W-14 | **Estabilidad del casco**: GM ≈ <!--V:sizing.hydrostatics.GM_m:.3f-->0.009<!--/V--> m, capacidad 33 CFR 183.33 = <!--V:sizing.capacity.persons_gear_kg:.0f-->46<!--/V--> kg con casco ESTIMADO | Crítica (seguridad) | Bloquea las pruebas en agua: ensayo de escora (PENDIENTES P0) y probablemente ensanchar el casco o bajar el asiento. Declarado en README, D-04, 06 y checklist |
| W-16 | **Holgura de la bomba sobre el fondo interior**: con el fondo [SUPUESTO] de 4 mm, la tobera fija queda a 4,5 mm del fondo interior (carcasa 5,6 mm). Un fondo de ≥ 6,5 mm (p. ej. PRFV, o una sobreplaca) no entra con el eje a 115 mm. Lo encontró la prueba de regeneración completa (+4 mm de fondo → `verify` falla) | Media | `verify_parts.py` lo detecta y detiene el pipeline (no pasa en silencio). Acción: medir el espesor real del fondo (PENDIENTES P0) y, si es > 6 mm, subir `waterjet.axis_height_m` lo mismo (cada mm resta sumersión: ver `sizing.priming`) |
| W-15 | Objetivo 30 km/h no alcanzado sostenido (<!--V:sizing.performance.vmax_cont_kmh:.1f-->24.4<!--/V--> km/h) con < 50 V y la batería que entra | Media (requisito) | Reportado; alternativas en 07 (72 V con declaración, motor mayor) |

## Ronda 1 (3 auditores independientes: cálculo, CAD/estructural, BOM/eléctrico/legal)

44 hallazgos verificados; corregidos por subsistema (commits `5d1be64`, `8c0bf1d`, `aca5edb` y siguientes).

### Cálculo (A)

| # | Hallazgo | Sev. | Resolución |
|---|---|---|---|
| A1 | **Savitsky fuera de validez**: largo mojado de quilla 1,77–2,10 m > fondo 1,75 m en todo el tramo que define la joroba y la V máx.; `valid` solo miraba τ | Alta | Validez L_K ≤ L_wl, λ ≤ 4 por punto en `sizing.json`; "Savitsky limitado por eslora" [ESTIMADO, D-21] con banda ensanchada. **Resultado: margen en la joroba <!--V:sizing.performance.hump_margin_min:.0%-->-8%<!--/V--> < 10 % (banda alta) — no cumple**; V máx. sostenida <!--V:sizing.performance.vmax_cont_kmh:.1f-->24.4<!--/V--> km/h sin base validada hasta T4. Lo que recupera el 10 %: <!--V:sizing.hump_recovery.mass_text:s-->21 kg menos<!--/V--> o <!--V:sizing.hump_recovery.lwl_text:s-->L_wl ≥ 1,96 m<!--/V--> (02 §3.2) |
| A2 | Sensibilidad de masa del casco sin efecto (dos fuentes del mismo dato) | Media | Una sola fuente; test: cada sensibilidad mueve alguna salida |
| A3 | Sensibilidad informaba "planea" en vez de "cumple 10 %" | Media | `hump_ok` y `any_hump_fail` en la tabla de 02 §10 |
| A4 | IVR con área anular (×1,33): "lejos de la separación" era falso | Media | IVR en la garganta: 0,61 a V máx. → **dentro de la zona de separación** (02 lo dice) |
| A5 | t = w = 0 etiquetados "conservador": no lo son cerca de la joroba | Media | Sensibilidad t, w 0–0,10 (t = 0,10 → margen −7 %); D-22 |
| A6 | Límite del VESC sobre I_q (FOC) no sobre I_m: margen real 2,4 % | Media | Convención en inputs [SUPUESTO], medir λ con VESC Tool (T0) |
| A7 | `sizing.json` desactualizado respecto de inputs sin que nada lo detecte | Baja | Hash de inputs en `sizing.json` + test duro |
| A8 | Tope de cavitación de 02 ≠ firmware | Baja | `sizing.cavitation_cap`; no se programa (lo cumple el límite de corriente a punto fijo; un tope fijo recortaría la V pico); verificar en T2 |
| A9 | Perfil COSTA: P y autonomía "a 5 kn" calculadas a rpm que el perfil no permite | Baja | Tabla con V y P reales con el tope (piloto de diseño ~7,8 km/h) |
| A10 | Masa del impulsor y ondulación de par distintas en dos cálculos | Baja | Una fuente (CAD) y una entrada |
| A11 | NPSH con inmersión estática en planeo | Baja | h_sub(V): S = 3,20 a V máx. (cumple) |

### CAD / estructural (C)

| # | Hallazgo | Sev. | Resolución |
|---|---|---|---|
| C1 | **Pasador, impulsor y estator no se podían cambiar** sin desarmar todo el tren (bridas > agujero del espejo; pasador pasante que no entraba ni en el montaje inicial) | Alta | Brida de la tobera que pasa por el espejo, 2 semipasadores, `service_paths()` con 11 caminos de extracción verificados en `verify_parts` (V7) |
| C2 | Pórtico de rodamientos imposible de montar en la secuencia documentada | Alta | Zapatas con ranura abierta, desliza axialmente; pasadores Ø6 toman el corte; secuencia en 06 M6/M7 |
| C3 | Unión carcasa–tobera y M5 del estator sin sello, presurizados dentro del casco | Alta | O-ring radial en la espiga, M5 del lado seco con arandela bonded, espiga +0,25 mm |
| C4 | Ranuras DIN 471 de TREN ≠ BOMBA | Media | Derivadas de una sola fuente + check |
| C5 | Avellanado M8 en Al subestimado (FS 1,67) y precargas distintas | Media | Un par (10 N·m), área proyectada: FS 2,46 |
| C6 | Arranque de rosca M6 en 5083 sin verificar (FS 1,6) | Media | Precarga 2,2 kN + Loctite: FS 2,33 |
| C7 | Brida de la bomba sin centraje; eje hiperestático | Media | Espigón Ø140 h6/H7; alineación con mandril (06 M7) |
| C8 | 7204 BEP no apareable: precarga indefinida; resalte que roza el aro interior | Media | 7204 BECBP; resalte Ø32,5 [datos SKF ESTIMADO] |
| C9 | Sin plano del conducto soldado | Media | Plano P1-INT-01 (mecanizar después de soldar) |
| C10 | Aplastamiento del pasador en el cubo con sección inexistente | Baja | Modelo corregido: FS 3,21 |
| C11 | `verify_parts` devolvía 0 si fallaba la booleana; tolerancias laxas | Baja | Falla explícita; allow = máx(5, 2 × medido); barrido extra de dirección/bucket |
| C12 | Rosca M5 del estator < 1 d | Baja | Rosca en la carcasa, 8 mm |
| C13 | Chaveta del motor (Ø15, 5 × 5) sin caso de carga | Baja | Caso agregado: **FS 1,74 < 2 — abierto y justificado**: medir el chavetero del motor recibido, cubo de acero + Loctite 648 |
| C14 | Rejilla con luz de 16 mm (pasa un dedo) y 316 tocando 5083 bajo el agua | Media | 9 pletinas, luz 12,2 mm; aislación PTFE + nylon (06 §4) |
| W-16/17 | Regeneración: con fondo +4 mm la bomba tocaba el fondo; con eje +5 mm el tope de dirección chocaba con la placa del espejo | Media | La placa se ubica desde el tope; la bomba quedó a 9,4 mm del fondo interior; los checks dicen a cuánto subir el eje. Rango probado: eje +0…+9 mm, fondo 3–6 mm |

### BOM / eléctrico / legal (E)

| # | Hallazgo | Sev. | Resolución |
|---|---|---|---|
| E1 | **Pares de polos 2 en vez de 5** (Maytech 12N/10P): el perfil ABIERTO no dejaba planear | Alta | 5 [VERIFICADO]; ERPM generados por `calc_electronica.py` en el perfil del VESC |
| E2 | Sin fusible por rama de batería | Alta | 2 × MRBF 125 A en los bornes |
| E3 | Cordón de 12 V cortando una bobina a 43,8 V | Alta | Contactor EV200 con bobina a 12 V desde el DC-DC |
| E4 | README de electrónica con restos de 8S / 24 V | Alta | Reescrito para 12S2P |
| E5–E11 | Contactor/F1 no unificados; reparto entre baterías; costo de B mal prorrateado; B sin salvedad; motor sin hall (trae NTC); FW de fábrica 5.02; terminales de fase | Media | Corregidos (README de electrónica, `comparacion.py` con prorrateo y base CIF, B-MOT con hall, T0.0 flasheo FW ≥ 6.0, cables propios del motor/ESC) |
| E12 | R13 escrito para otra potencia; < 19 kW depende de la configuración | Media | R13 §2 con la potencia configurada; XML y hojas a bordo |
| E13–E19 | 4 kn de Als Sund no los hace cumplir el firmware; cantidad de baterías; etiquetas VERIFICADO con links de búsqueda; arancel; compilación AVR; riesgos residuales del firmware | Baja | Corregidos o documentados (D-18, README de electrónica §8) |

## Ronda 2 (3 auditores nuevos sobre el paquete corregido)

27 hallazgos verificados, ninguno de los de la ronda 1 reabierto; corregidos (commits `70dc3d9`, `4dbb05d`, `f0b8b13`, `8868d14`).

| # | Hallazgo | Sev. | Resolución |
|---|---|---|---|
| R2-E1 | **Fuente de 12 V RSD-60G (9–36 V) con un pack de 36–43,8 V** (rango del modelo L copiado al G; cita circular a la BOM) | Crítica | RSD-60L-12 (18–72 V) [VERIFICADO: hoja Mean Well] |
| R2-C01 | **Margen de joroba cortado en Fn∇ 2,3**: más allá el margen seguía bajando; con la resistencia alta no llega a planeo pleno y con potencia continua se cae del planeo | Alta | Margen de 0 a planeo pleno (<!--V:sizing.verdict.V_full_planing_kmh:.1f-->27.1<!--/V--> km/h); `sizing.verdict` con veredicto por banda: alta <!--V:sizing.verdict.hump_margin_min_high:.0%-->-8%<!--/V-->, nominal <!--V:sizing.verdict.hump_margin_min_nominal:.0%-->3%<!--/V-->; README, 02, 03, visor lo dicen |
| R2-C02 | El veredicto lo fijan `planing_band.high` y `fn_planing`, fuera de la sensibilidad | Alta | Entradas nuevas de sensibilidad (incl. factor sobre las 3 bandas); ×1,12 etiquetado SUPUESTO en el régimen limitado por eslora |
| R2-D01 | Pasadores del pórtico Ø6 × 30 atravesaban el fondo mojado y no se podían extraer | Media-Alta | ISO 8735 Ø6 × 16 con rosca M4, ciegos 6 mm (quedan 4 mm), acotados en planos |
| R2-D02 | M5 × 25 de la tobera tocaban fondo antes de apretar | Media | M5 × 20 + check de largo contra agujero |
| R2-D03 | Camino de extracción sin la inclinación del eje (luz real 1,17 mm < 1,5) | Media | R/cos α + t·tan α; agujero del espejo Ø166 +1/0, concentricidad ≤ 0,5 mm |
| R2-D05 | Placa de espejo pegada con Sikaflex pero se desmonta en cada cambio de semipasadores | Media | NBR + butilo no adhesivo + arandelas bonded |
| R2-E2 | Un riel de 12 V para bobina de K1 + achique: corte espurio al arrancar la bomba | Media | Retención 1N5822 + 22 mF (≥ 9 V por 0,28 s) + prueba T0.4b; F5 removible, invernada |
| R2-E3 | Poder de corte del MRBF citado como 10 kA (a 58 V son 2 kA); cortocircuito presunto 1,8–8,8 kA [ESTIMADO] | Media | F1 y ramas Class T (20 kA, 160 V CC) [VERIFICADO: Blue Sea 5113] |
| R2-E4–E6 | Fusible de rama con otro criterio que F1; fusible abierto no detectable por tensión; toma Anderson sin fusible | Media | 150 A con el criterio de F1; pinza CC por rama; F6 32 A |
| R2-C03–C05, R2-D04, D06–D10, R2-E7–E10 | Punto de diseño de la bomba recortado por la grilla (ahora 43,6 km/h); tabla por batería con bandas mezcladas; varilla de la hidrostática que no pasaba (M5); ligamento M5; alineación con el propio eje; fuerzas de dirección unificadas; restos de textos (7204 BEP, 7 pletinas, B-NTC, 24 V, T0.0); checklist | Media/Baja | Corregidos |

## Ronda 3 (FEA de las piezas críticas, 04_diseno/fea) — superada por la ronda 4

El FEA de la ronda 3 encontró F-01…F-03; al corregirlos aparecieron R3-01…R3-11 (verificados con el código y,
donde aplica, con el FEA). Commits de la ronda: `e3c0bd1`, `546e4bf`, `ce8faed`, `68e93f5`.

**No quedó cerrada** (auditoría ronda 4, H2): la corrida fina de la ronda 3 dio P1-STE-01 FS 1,80 < 2 en un caso de
diseño (R3-11 decía 2,00, escrito a mano) y el criterio de reparto entre trabas de R3-01/R3-02 no se sostiene
(R4-01…R4-05). La tabla queda como historia: los valores del bucket, de la boquilla y del FEA de REV-01/STE-01 son
los de la ronda 3 [CALCULADO en la ronda 3, commit `ce8faed` y `04_diseno/fea/resultados_fea.json` de esa corrida]
y ya no están en el CAD; los marcadores que siguen vigentes (CTL-02, DRV-03, optimizador) se actualizan solos.

| # | Hallazgo | Sev. | Resolución |
|---|---|---|---|
| F-01 | **P1-REV-01 bucket: FS 0,44** en el brazo con la traba (reversa 1408 N): con la traba en un solo brazo todo el momento de la cuchara llega a ese brazo por torsión de la sección abierta; el cálculo a mano repartía F/2 por brazo (no conservador) | Crítica | Traba en **los dos brazos** (émbolo +Y a <!--V:manifest.params.REV_lock_ang:g-->10<!--/V-->°, −Y a <!--V:manifest.params.REV_lock_ang_m:g-->-25<!--/V-->°: pomos y Bowden pasan uno al lado del otro), chapa de 6 mm, los dos émbolos liberados por el mismo gatillo (2 Bowden). Cálculo a mano: brazo, agujero, perno del émbolo y oreja con **M_h completo en una traba**. FEA de la ronda 3: FS 2,51 (caso c, con el reparto por desfase). **Reemplazado por D-17c** (R4-01) |
| F-02 | P1-CTL-02 (PETG): tracción entre capas en las paredes, FS 2,74 < 3 | Media | Paredes de 5 mm engrosadas **hacia afuera** (el entrehierro del hall no cambia; tornillos del ala derivados de la misma constante): FEA FS <!--V:fea.piezas.P1-CTL-02.FS_min:.2f-->3.41<!--/V--> |
| F-03 | Aristas vivas sin radio (STE-01 oreja de pivote/labio, DRV-03 alma/alojamiento): picos que no convergían | Baja | Empalmes de arco verdadero (`cadlib.prism_arc`): r 2 oreja–labio en STE-01; en DRV-03 alma de ±0,35·Ø con r 3 alma–tablero y alma–alojamiento (antes el alojamiento entraba al tablero en una cuña de ~30°). Los picos convergen; DRV-03 FS <!--V:fea.piezas.P1-DRV-03.FS_min:.2f-->3.89<!--/V--> |
| R3-01 | **Reacción del pivote del bucket subestimada**: la traba solo reacciona tangencialmente (M_h/r ≈ 2·F_b) y esa fuerza se suma al chorro en el pivote de su brazo; el cálculo a mano usaba F_b/2 = 0,7 kN por pivote. Con la reacción real (≈ 1,6–3,0 kN) el perno Ø10 con M8 en voladizo y el buje POM Ø10 × 8 quedaban bajo FS 2 (el M8 por debajo de 1) | Alta | Pivote nuevo P1-REV-02: **espaciador 316 Ø18 apretado contra la oreja por un M12 A4-80** (tuerca DIN 985 por dentro, precarga 10 000 N), buje POM-C Ø18/Ø22 × 14 (brazo + aro de 8 mm), oreja de la boquilla de radio 15 alrededor del pivote. Estática del bucket en UNA función (`structural_direccion.bucket_reactions`) que usan el cálculo a mano y el FEA; reacción de diseño 2385 N (con el reparto 0,78); filas nuevas del espaciador, del M12 (unión abierta) y del momento fuera del plano en la oreja |
| R3-02 | **El reparto entre las dos trabas depende del desfase entre sus agujeros**: la cuchara abierta es blanda a torsión, así que hasta que apoya el segundo perno un solo brazo lleva M_h. FEA: con 0,3 mm de desfase el diseño V2 volvía casi a una sola traba; además la muesca entre el lóbulo de traba (r 12) y el borde del brazo concentraba | Alta | Lóbulo de traba r 16 unido al labio superior de la cuchara (sin muesca). Agujeros taladrados en conjunto después de soldar (05 §4) y **prueba de desfase con comparador** (06 T0.M6b): ≤ 0,10 mm en el agujero; si no, casquillo excéntrico. FEA casos b/c con ese desfase: reparto máx. 0,75 ≤ cota 0,78 que usa el cálculo a mano (test). Falla (un émbolo no entró) con la reversa de sizing: casos d/e FS ≥ 2; falla doble (+ R12 sin límite): V1/V2 FS 1,71–1,85 (criterio sin fluencia). FMEA F19b y checklist (los dos pomos adentro). **Reemplazado por el criterio de traba única** (D-17c; R4-01, R4-02) |
| R3-03 | Modelo FEA de la traba: contacto en todo el agujero (holgura 0) — no podía representar un desfase ni un émbolo ausente; el primer intento (émbolo corrido 50 mm con k = 10⁷) metía 5·10⁸ N en el lado derecho y la tolerancia relativa del CG dejaba ~50 N de error: FS 0,06 espurio | Media | Contacto solo en la mitad de apoyo de cada agujero; émbolo tardío corrido el desfase con k = 10⁶ N/mm; émbolo ausente = interfaz desactivada (`Interface.enabled`), también al reportar reacciones; reacciones de pivote por lado |
| R3-04 | **Selección del optimizador inestable**: sin solución dura, el desempate redondeaba el margen de joroba al punto porcentual; +0,8 kg de masa CAD del jet cambiaba el impulsor de Ø132 a Ø120 (0,27 pp de diferencia de margen, menos V máx.) y el Ø120 podía volver a dar Ø132 en la corrida siguiente | Media | Banda de <!--V:sizing.optimization.hump_tie_band:.0%-->1%<!--/V--> alrededor del mejor margen y desempate por V máx. (`waterjet.hump_tie_band`, 02 §4): vuelve a Ø<!--V:sizing.selection.D_imp_mm:.0f-->132<!--/V--> |
| R3-05 | `np.trapz` no existe en numpy 2.4 (requirements sin versión fija): `sizing.py` fallaba en una instalación nueva | Media | `trapezoid` con respaldo a `trapz` (`p1calc/hull.py`) |
| R3-06 | 02 citaba filas de `estructural.json` **por índice** (`est.rows.104…`): al agregar filas en dirección, la tabla de los FS más justos y la cita de la chaveta habrían mostrado filas equivocadas sin aviso | Baja | Tabla AUTO `estructural_justos` (10 filas con menor FS/objetivo) y `est.min_by_part.<ID>`; los marcadores aceptan IDs con guion |
| R3-07 | Cotas de P1-STE-04 y P1-REV-05 contra el pivote del bucket solo en X' (ignoraban que la brida y el alma están 17–43 mm más arriba): con el aro más grande daban falla falsa | Baja | Distancia real en el plano (X', z) al aro/cabeza del pivote |
| R3-08 | CTL-02: el FEA fijaba los tornillos en la posición vieja después de engrosar la pared y reportaba la pared interior (3,5); el META decía "pisada 300 N" y se calcula 150 N | Baja | `bolt_xy()` y `W_OUT` como fuente única (FEA y CAD); META con el caso analizado |
| R3-09 | Cuatro copias de la posición de la traba (REV-01, REV-04, STE-01, `_release`) y planos con fórmulas propias | Baja | Fuente única `piezas/_release.lock_xz`; planos de los dos brazos del bucket por separado (estribor y babor) |
| R3-10 | Dos vainas de Bowden por un prensaestopas M16 de un solo agujero | Baja | Inserto M16 de 2 agujeros 2 × 4,5 mm [VERIFICADO: MDE16-2x45] + Sikaflex (paso sobre la flotación); vainas Ø4,5–5 |
| R3-11 | STE-01 en reversa con **M_h completo en una traba a R12**: FS 1,80 en la oreja alrededor del pivote (con el momento del espaciador en voladizo, que el modelo anterior no aplicaba) | Media | Ese caso es una falla doble (un émbolo fuera + sin límite de firmware): se declaró variante V1 (criterio sin fluencia) y los casos de diseño c/c2 pasaron al reparto máximo admitido; oreja de radio 15. Se escribió «FEA STE-01 FS 2,00» a mano, pero la corrida fina de la ronda 3 dio **FS 1,80 en el caso de diseño d2** (`resultados_fea.json` de esa corrida): **no cerrado**. Lo retoma la ronda 4 (R4-01, F1: además la reacción del pivote se aplicaba mal) |

## Ronda 4 (auditoría adversarial del rediseño de la ronda 3)

Tres auditores independientes (mecánico, FEA, documentación/BOM) sobre el paquete de la ronda 3. Decisión que
resulta: **D-17c** (criterio de traba única, émbolo propio Ø16 / M24×1,5, pivote con brida y piloto; reemplaza a
D-17b). Commits de la ronda: `e716311`, `51c068f`, `1a8bf50` y siguientes. Estado «corregido» solo cuando el arreglo
está en el repositorio; los del FEA quedan «corregido; FS en `resultados_fea.json` tras la corrida fina» hasta que
esa corrida se fusione (`fea_run.py --merge`). **La ronda no está cerrada**: falta la corrida fina, los abiertos de
abajo y una re-auditoría. Los números de los hallazgos son los que midieron los auditores [CALCULADO: auditoría
ronda 4] salvo los marcadores, que salen de `resultados/*.json`.

### Mecánico / cálculo (R4)

| # | Sev. | Hallazgo | Arreglo | Estado | Evidencia |
|---|---|---|---|---|---|
| R4-01 | Crítica | **El reparto entre las dos trabas depende de la carga**: con un desfase fijo la 2.ª traba apoya recién cuando la 1.ª lleva ≈ 1,4 kN; con la reversa de servicio (sizing) UNA traba lleva ≈ 100 % de M_h. Las filas de fatiga con reparto 0,78 eran no conservadoras (buje POM FS ≈ 1,70; oreja STE-01 a fatiga ≈ 1,4 escalando el FEA) | Criterio de traba única (D-17c): cada traba sola, con su brazo, pivote, oreja y émbolo, lleva M_h completo a R12 (corta) y con la reversa de sizing (fatiga), FS ≥ 2; se eliminan `REV_lock_share_max`, `REV_lock_mismatch` y los casos «FALLA»/«FALLA DOBLE» | corregido (cálculo a mano y CAD); FEA: corregido; FS en `resultados_fea.json` tras la corrida fina | Criterio en `estructural.json`: «<!--V:est.loads.structural_direccion.lock_criterion:-->cada traba sola lleva M_h completo<!--/V-->»; filas bajo objetivo: <!--V:est.n_fail:d-->0<!--/V--> |
| R4-02 | Alta | **El desfase entre trabas no estaba controlado**: el taladrado coincidente metía δ ≈ 0,25 mm y la prueba con comparador no tenía dirección ni fuerza definidas | El desfase deja de entrar en la resistencia (R4-01); queda una prueba FUNCIONAL (los dos pernos entran solos ARRIBA y ABAJO, sobresalen ≥ 0,5 mm y salen con el gatillo); agujeros con plantilla referida al pivote | corregido en cálculo y CAD; **abierto** en 05/06/BOM (ver M2–M4) | `params_direccion.py` sin `REV_test_r`/`REV_test_dial_mm` |
| R4-03 | Alta | **El espaciador del pivote flotaba** en un agujero pasante Ø12,4: la unión desliza a R12 y la reacción pasa por el tornillo | Espaciador con brida Ø<!--V:manifest.params.REV_sp_fl_d:g-->36<!--/V--> y piloto Ø<!--V:manifest.params.REV_sp_pilot_d:g-->16<!--/V--> h6 en Ø16 H7 escariado por oreja; M12 A4-80 a <!--V:est.loads.structural_direccion.bolt_torque_Nm:.0f-->45<!--/V--> N·m con Tef-Gel; filas: unión que no se abre con la precarga mínima, presión de la brida y tornillo al montar con la máxima | corregido | P1-REV-02 «<!--V:est.min_by_part.P1-REV-02.load_case:-->Unión brida–oreja: no se abre con la precarga mínima (R12, una traba) [N·m]<!--/V-->» FS <!--V:est.min_by_part.P1-REV-02.FS:.2f-->2.10<!--/V--> |
| R4-04 | Alta | **Cargas del chorro**: M_h subestimado (126,8 N·m) y F_z con el signo cambiado (+81 N) | Balance de cantidad de movimiento con salida por el labio inferior (`structural_direccion.jet_momentum`, 02 §8), usado por el cálculo a mano y por el FEA | corregido | M_h <!--V:est.loads.structural_direccion.M_hinge_Nm:.1f-->135.3<!--/V--> N·m, F_z <!--V:est.loads.structural_direccion.F_z_bucket_N:.0f-->-210<!--/V--> N (R12) |
| R4-05 | Alta | **El émbolo de catálogo supuesto («GN 617-12 M20 A4», perno Ø12) no existe**: el GN 617 inox M20×1,5 trae perno Ø10 de AISI 303, resorte 17–40 N [VERIFICADO: catálogo Elesa/Ganter, link en D-17c]; con 3 kN no llega a FS 2 | Émbolo propio P1-REV-04: perno 316 Ø<!--V:manifest.params.REV_lock_pin_d:g-->16<!--/V--> h9, cuerpo M<!--V:manifest.params.REV_lock_thread_d:g-->24<!--/V-->×1,5 con contratuerca, carrera <!--V:manifest.params.REV_plunger_stroke:g-->12<!--/V--> mm, resorte comprado | corregido (CAD, cálculo); BOM **abierta** (en curso: `inputs.yaml` ya cambia B-INDEX por resorte B-SPRING + contratuerca B-NUT24; falta regenerar y verificar la BOM, M7) | P1-REV-04 FS <!--V:est.min_by_part.P1-REV-04.FS:.2f-->2.83<!--/V--> |
| R4-06 | Alta | **Desbloqueo imposible de montar**: la vaina −Y pasaba a 3,5 mm del eje del émbolo +Y y sus curvas chocaban con la contratuerca, la oreja o el cuerpo (nada modelado); recorrido del gatillo 11,03 mm contra 12,5 necesarios (verify fallaba); dos cables en un barril sin igualador | Reenvío por balancines 1:1 (P1-REV-09, una pieza), vainas modeladas como tubos barridos (P1-REV-10, curva R40) y verificadas en −25/0/+25°, bucket arriba/abajo y barrido; gatillo con barra igualadora (P1-CTL-14) y regulador M6 por cable; recorrido del cable 14,98 mm contra 12,5 [CALCULADO: checks de P1-CTL-14] | corregido | Pares×estados sin interferencias: <!--V:verify.n_pair_checks:d-->14160<!--/V-->; P1-REV-09 FS <!--V:est.min_by_part.P1-REV-09.FS:.2f-->2.45<!--/V-->, P1-CTL-14 FS <!--V:est.min_by_part.P1-CTL-14.FS:.2f-->4.66<!--/V--> |
| R4-07 | Media | **Soporte del Bowden sin fijación real**: apoyaba en la oreja con un canto de 4 × 16, el lazo de agujeros M5 estaba vacío y STE-01 no tenía roscas M5; el plano omitía la pata | La base apoya de cara en un pad fresado arriba del cuerpo de la boquilla, lejos de los ligamentos del pivote y de la M24; 2 × ISO 4762 M5 × 12 A4-70 en roscas M5 × 7,5 de STE-01; planos nuevos | corregido | Fila del tornillo M5 en 02 §9 (tabla completa) |
| R4-08 | Media | Buje POM del pivote: prensado con interferencia sin repasar el interior (el prensado cierra el juego) | Interferencia 0,05–0,10 mm en Ø24 H7 y **escariado del interior después de prensar** | corregido (P1-REV-03 y plano); 05 lo repite con el procedimiento nuevo (M2) | P1-REV-03 FS <!--V:est.min_by_part.P1-REV-03.FS:.2f-->2.18<!--/V--> |
| R4-09 | Baja | Posición del poste del yugo como suma fija de la geometría vieja (aro de 4 mm): con el aro y las orejas nuevas no libraba | `STE_post_y` derivado de la cara exterior del aro del bucket | corregido | `STE_post_y` = <!--V:manifest.params.STE_post_y:.1f-->-99.0<!--/V--> mm (ronda 3: −90,3) |
| R4-10 | Media | (aparecido al corregir) Cota de P1-REV-04 «contratuerca sobre el cuerpo de la boquilla»: el círculo de esquinas de la contratuerca −Y llega al cuerpo (−0,077 mm contra ≥ 2); el hexágono modelado no interfiere, pero apretada en un ángulo cualquiera una esquina puede tocar | Por definir en P1-REV-04 o en params (contratuerca de menos entrecaras, rebaje del cuerpo o mover el émbolo −Y) | **abierto** | `verify.json` ok = <!--V:verify.ok:-->False<!--/V--> |
| R4-11 | Media | (aparecido al corregir) El momento del perno en voladizo sobre la oreja (3006 N × 14,5 mm ≈ 44 N·m [CALCULADO: agente FEA]) supone la contratuerca M24 apretada: no hay par de apriete especificado ni fila a mano para ese momento en la oreja | El FEA de STE-01 ya lo aplica (par autoequilibrado bajo la contratuerca); falta par de apriete y fila a mano | **abierto** | 04_diseno/fea/README.md (STE-01) |
| R4-12 | Baja | (aparecido al corregir) Fuerza de liberación sin confirmar: resorte 45 N y rendimiento del Bowden 0,6 [ESTIMADO] → ≈ 82 N de mano contra 100 N de diseño; el eslabón +Y trabaja a 7,7° del eje del émbolo y el cable pasa a 1,4 mm del cubo del balancín +Y [CALCULADO: checks de P1-REV-09] | Medir en banco con la prueba funcional; cambiar el resorte si no alcanza | **abierto** (medición física) | 02 §12 |
| R4-13 | Baja | (aparecido al corregir) Ruta de las vainas bajo la pestaña de tope y su paso por la consola sin modelar; B-GLINS tiene 2 agujeros de 4,5 contra vaina Ø5; el plano de P1-CTL-10 no muestra la placa lateral nueva; queda sin uso el lóbulo de la oreja −Y que apoyaba la pata del soporte viejo | — | **abierto** | — |

### FEA (F)

| # | Sev. | Hallazgo | Arreglo | Estado | Evidencia |
|---|---|---|---|---|---|
| F1 | Crítica | Casos de reversa de STE-01 sin la reacción del bucket bien aplicada: el agujero pasante mordía la torre del yugo y `sel_cyl` tomaba ese festón; el par de caras no era autoequilibrado; la resultante aplicada ≠ estática | Selección limitada a la oreja (\|y\| ≥ STE_ear_y0 − 0,5) y agujero Ø16 por oreja en el CAD; pivote en el piloto, traba en la rosca M24, par del espaciador autoequilibrado en la cara de la brida; assert de fuerza y momento contra la estática (1 %) en el setup y en los tests | corregido; FS en `resultados_fea.json` tras la corrida fina | P1-STE-01 FS mínimo de diseño <!--V:fea.piezas.P1-STE-01.FS_min:.2f-->1.80<!--/V--> (caso <!--V:fea.piezas.P1-STE-01.caso_gobernante:-->d2<!--/V-->) |
| F2 | Alta | Reparto dependiente de la carga en el FEA de REV-01 (casos con desfase escalados linealmente); carga del chorro que no salía de la cantidad de movimiento | Casos de diseño de una traba sola por lado a R12 (fluencia) y con la reversa de sizing (fatiga de soldadura); dos trabas como informativos; casos con contacto sin escalar; carga de `jet_momentum` (entrada uniforme en x sobre la proyección, salida −J·t_out en una franja junto al labio inferior) con fuerza y momento verificados contra `bucket_reactions` | corregido; FS en `resultados_fea.json` tras la corrida fina | P1-REV-01 FS mínimo de diseño <!--V:fea.piezas.P1-REV-01.FS_min:.2f-->2.51<!--/V--> (caso <!--V:fea.piezas.P1-REV-01.caso_gobernante:-->c<!--/V-->) |
| F3 | Alta | La zona de exclusión alrededor de los agujeros cargados por perno escondía el pico de «lug» y el ligamento de la rosca | Verificación aparte del borde: σθ a 60–120° de la carga, FS = admisible / \|σθ\| (objetivo 2), en los agujeros de traba y pivote de REV-01 y de pivote y M24 de STE-01; el FS del caso es el menor entre cuerpo y borde | corregido; FS en `resultados_fea.json` tras la corrida fina | 04_diseno/fea/README.md |
| F4 | Media | Convergencia de REV-01: el punto caliente (cara exterior del brazo, por debajo del pivote) quedaba fuera de las esferas de refinamiento; +18 % de gruesa a fina | Esfera de refinamiento en el punto caliente; Richardson informado cuando el cambio gruesa → fina supera 10 % | corregido; FS en `resultados_fea.json` tras la corrida fina. **Margen justo**: una sonda de malla fina del caso d dio FS ≈ 2,08 [CALCULADO: sonda del agente FEA, no guardada en el repo]; si la corrida fina da < 2, agregar sección al brazo trabado (D-17c) | 04_diseno/fea/README.md |
| F5 | Media | Tests tautológicos (la interfaz deshabilitada devuelve 0: «una es cero» siempre pasaba) | Tests: la traba activa lleva M_h/r (3 %) y equilibra el momento; carga aplicada = estática en REV-01 y STE-01; borde de agujeros verificado; `cumple` por pieza | corregido (pasan con los resultados finos) | `tests/test_fea.py` |
| F6 | Baja | README de DRV-03 con un modelo de corte que el código no usa; docstring de REV-01 con «corrido 50 mm»; agujero deshabilitado todavía en las zonas | Texto, docstring y zonas corregidos | corregido | 04_diseno/fea/README.md |
| M5 | Baja | La tabla de variantes imprimía «NO CUMPLE» en casos con objetivo 1 | Objetivo por variante; las variantes de falla doble desaparecen con D-17c | corregido | `fea_run.py` |

### Documentación / BOM (H, M, LOW)

| # | Sev. | Hallazgo | Arreglo | Estado | Evidencia |
|---|---|---|---|---|---|
| H1 | Alta | 02, decisiones y auditoría con el criterio de reparto y marcadores a claves que ya no existen (`lock_share_max`, `lock_mismatch_mm`, `REV_lock_share_max`, `REV_lock_mismatch`, variantes V1/V2 del FEA) | 02 §8–§9 reescritos con las cargas y el criterio nuevos; D-17c; ronda 3 marcada como historia con sus valores | corregido | `tools_check_md.py`: sin marcadores rotos en 02, decisiones y auditoría |
| H2 | Alta | «Ronda 3 — cerrada» no se sostenía (STE-01 FS 1,80 en la corrida fina; R3-11 escrito a mano); hallazgos viejos en el README del FEA; HANDOFF y PROGRESS viejos | Ronda 3 marcada «superada por la ronda 4» con R3-11 corregido; HANDOFF y PROGRESS al día; README del FEA reescrito por el agente FEA | corregido; el bloque AUTO del README del FEA se regenera con `--merge` | Esta sección |
| M1 | Media | D-06 decía «la de mayor margen y, empatada, la de mayor V máx.» | Con la banda de desempate (`waterjet.hump_tie_band`): la elegida está a ≤ <!--V:sizing.optimization.hump_tie_band:.0%-->1%<!--/V--> del mejor margen y dentro de la banda es la de mayor V máx. | corregido | decisiones.md D-06 |
| M2 | Media | 05 §4: taladrado coincidente de los agujeros de traba y prueba de desfase | Reescribir con el criterio nuevo: agujeros de traba con plantilla referida al agujero del pivote, escariado Ø16,5; orejas: Ø16 H7 escariado y M24×1,5 roscado con plantilla; buje escariado después de prensar | **abierto** (05 todavía con el procedimiento viejo y marcadores a `REV_test_r`) | — |
| M3 | Media | 06 T0.M6b: prueba de desfase con comparador | Reemplazar por la prueba funcional (los dos pernos entran solos ARRIBA y ABAJO, sobresalen ≥ 0,5 mm, salen con el gatillo); FMEA F19b con el criterio nuevo | **abierto** (06 sin actualizar) | — |
| M4 | Media | BOM: B-REAM12 (casquillo M20 / Ø12,5) y B-DIAL ya no aplican | Quitar B-DIAL; herramienta de escariado Ø16 H7 / Ø16,5 y plantillas | **abierto** (en curso: `inputs.yaml` ya trae B-REAM16 y B-TAP24 y B-DIAL sin el ensayo de desfase; falta regenerar y verificar la BOM) | — |
| M6 | Media | 06 §4 tabla galvánica: falta el espaciador 316 apretado contra la oreja 6061 | Tef-Gel en la cara de apoyo, el agujero H7 y la rosca; la cara de apoyo anodizada (no enmascarar); émbolo M24 en lugar de M20 | **abierto** (06 sin actualizar) | — |
| M7 | Media | BOM: falta chapa/barra para los aros de refuerzo (10 mm); MP-316-D28 dimensionado con el bbox de P1-REV-02 (incluye el tornillo); doble barril y tope de consola sin línea; 06 §1 etapas de compra sin B-GLINS, B-PIVM12, B-REAM12 | Líneas nuevas del desbloqueo (B-BOWDEN reescrita, B-RELKIT, overrides de P1-REV-09 y P1-CTL-10, S-LASER) y del émbolo propio (resorte + barra 316 + contratuerca M24×1,5 en lugar de B-INDEX); material del bucket 8 mm | **abierto** (en curso: `inputs.yaml` ya trae bucket de 8 mm, MP-5083-AROS, B-RELKIT, B-BOWDEN nueva y los overrides; falta regenerar la BOM, revisar MP-316-D28 y las etapas de compra de 06 §1) | — |
| M8 | Media | D-17b decía «~10 mm de chapa para FS 2 (FEA)» sin un FEA que lo respaldara | D-17b marcada reemplazada (se conserva como historia) y D-17c con el criterio nuevo | corregido | decisiones.md D-17b/D-17c |
| L1 | Baja | Docstrings viejas: P1-REV-04 (M16/Ø10), META de STE-01, REV-01 «A4-70», encabezado de params, P1-CTL-14 «2 × 6 mm» | Reescritas con las piezas nuevas | corregido | piezas/*.py |
| L2 | Baja | Plano de P1-REV-02 «barra Ø25» contra MP-316-D28 de la BOM | El plano usa ahora la barra del espaciador con brida; la BOM queda con M7 | **abierto** (BOM) | — |
| L3 | Baja | R3-01 «1,6–3,0 kN» contra D-17b «1,6–2,4» | D-17b (historia) con 1,6–3,0 | corregido | decisiones.md D-17b |
| L4 | Baja | 04_diseno/README.md «pernos 316 con hombro» para el pivote del bucket | Texto con el espaciador con brida y piloto | corregido | 04_diseno/README.md (Ajustes) |
| L5 | Baja | Números sin etiqueta: 02 §4 «+0,8 kg / 0,27 pp» y 06 M13 «≈ 24 N·m» | 02 etiquetado | 02 corregido; 06 **abierto** | 02 §4.3 |
| L6 | Baja | 05: CTL-02 «paredes de 3,2–3,5 mm» (ahora 5 mm; 5 perímetros = 4,5 mm), «aro Ø17 mm de radio»; 06 líneas 180, F19 y M15 en singular (ahora dos trabas); 06 R7 «solo dos pares calculados»; mantenimiento sin la prueba funcional de temporada; PENDIENTES sin control de recepción de émbolos/resortes; probeta P1.10 (POM en agua) sin P1-REV-03; B-GLINS [VERIFICADO] solo cubre el precio (ajuste en el prensaestopas Biltema M16 y vaina Ø5 contra 4,5 sin verificar) | Corregir en 05, 06, PENDIENTES y la BOM | **abierto** (archivos de otro frente de esta ronda) | — |

## Regeneración desde inputs.yaml

`tests/test_regeneration.py` (rápido) cambia `boat.bottom_thickness_mm` y `waterjet.axis_height_m`
y comprueba que cambian el casco de referencia, la placa de la toma y la cota de la tobera.
`tests/test_regeneration_full.py` (lento, `P1_SKIP_SLOW=1` lo salta) copia el proyecto a un
directorio temporal, cambia **el espesor del fondo (+2 mm)**, **la altura del eje (+5 mm)** y **la masa del
piloto (−15 kg)**, corre `run_all.py --fast --skip-render` completo y verifica: masa total menor, margen de
joroba ≥ al anterior, menos sumersión del impulsor, volumen de la placa base de la toma distinto, BOM
regenerada y el README con el margen nuevo. La primera versión (+4 mm de fondo sin tocar el eje) hizo
fallar `verify` con la tobera a 0,5 mm del fondo interior: así se encontró W-16.

## Historial (versión anterior: cola larga, archivada)

| # | Hallazgo | Severidad | Resolución |
|---|---|---|---|
| A-01 | Eje Ø12: FS fatiga 1,1 y torsión en el pasador 1,3 | Alta | Eje Ø16 + polea entre rodamientos (D-07, D-08) |
| A-02 | Tubo inox 25×1,5 cede con el momento dinámico de impacto | Crítica | Tubo Al 40×3 (D-09) |
| A-03 | Caña colgando de la placa motriz de 7 mm (σ ≈ 200 MPa) | Crítica | Placa Al sobre la cuna (D-15) |
| A-04 | Fusible 100 A sobre cable de 10 mm² (75 A): no lo protegía (detectado por pytest) | Alta | Cable DC 16 mm² (D-21) |
| A-05 | Optimizador elegía 51,2 V (> 48 V) y luego una batería que no cumplía autonomía | Alta | Restricciones duras vs blandas (02 §4.1) |
| A-06 | Separadores del puente atravesaban la polea (plano de correa mal modelado) | Alta | Separadores fuera del lazo (verify lo detectó) |
| A-07 | Capacidad del bote supuesta 250 kg | Crítica (seguridad) | 160 kg estimado + advertencia + P0.2 (D-16) |
| A-08 | **Eje imposible de montar**: el muñón del rodamiento A (Ø15) estaba entre dos tramos Ø16 (verify no lo veía: no hay interferencia, es un problema de secuencia de montaje) | Crítica | Tramo Ø15 continuo + hombro Ø16, pila con separadores DRV-09/DRV-10 y tuerca; nueva cota automática "Ø máx. sobre el hombro ≤ Ø muñón" (D-07) |
| A-09 | Límite de Burrill 0,3σ^0,6 no conservador para σ > 0,6 (+15 % a +81 %) | Media | Curva de 5 % digitalizada por interpolación (research/R09 §3.2) + test |
| A-10 | Pasador de corte de Al sobre eje 316 en agua salobre: par galvánico → el pasador pierde sección y corta antes de tiempo | Alta | Pasador 316 Ø2 calibrado + ensayo P1.9 + cambio cada 10 h (D-11) |
| A-11 | Productos inexistentes en la selección: hélice 10×8 "objetivo", poleas de 44/60 T, correas sin stock, rodamientos 6002 inox, ánodo de collar Ø16 (research/R08b) | Alta | Optimizador restringido a productos/dientes/largos existentes (D-06, D-37, D-39); ánodo descartado con justificación (D-36) |
| A-12 | Largo de agarre del tubo en la cuna tomado como 90 mm en vez de 138 mm (FS de fatiga lateral subestimado) | Baja (conservador) | Corregido en `structural.py` |
| A-13 | Prensaestopas M20 especificados en una pared de 18 mm (rosca ~10–15 mm) y caja ESC sin lugar para el antichispa | Media | Rebaje a pared de 5 mm, caja 160×110×45, 10 cotas nuevas (D-20) |
| A-14 | Batería LiTime 24 V 50 Ah supuesta con BMS 100 A (real: 50 A) | Media | Catálogo con datos verificados (D-19) |
| A-15 | Con 1 persona el bote superaría el límite legal de 5 kn a < 300 m de la costa | Media (legal) | Tope de ERPM calculado (D-30) + ensayo T3 |
