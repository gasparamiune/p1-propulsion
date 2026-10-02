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
| W-14 | **Estabilidad del casco**: GM ≈ <!--V:sizing.hydrostatics.GM_m:.3f-->0.008<!--/V--> m, capacidad 33 CFR 183.33 = <!--V:sizing.capacity.persons_gear_kg:.0f-->46<!--/V--> kg con casco ESTIMADO | Crítica (seguridad) | Bloquea las pruebas en agua: ensayo de escora (PENDIENTES P0) y probablemente ensanchar el casco o bajar el asiento. Declarado en README, D-04, 06 y checklist |
| W-16 | **Holgura de la bomba sobre el fondo interior**: con el fondo [SUPUESTO] de 4 mm, la tobera fija queda a 4,5 mm del fondo interior (carcasa 5,6 mm). Un fondo de ≥ 6,5 mm (p. ej. PRFV, o una sobreplaca) no entra con el eje a 115 mm. Lo encontró la prueba de regeneración completa (+4 mm de fondo → `verify` falla) | Media | `verify_parts.py` lo detecta y detiene el pipeline (no pasa en silencio). Acción: medir el espesor real del fondo (PENDIENTES P0) y, si es > 6 mm, subir `waterjet.axis_height_m` lo mismo (cada mm resta sumersión: ver `sizing.priming`) |
| W-15 | Objetivo 30 km/h no alcanzado sostenido (<!--V:sizing.performance.vmax_cont_kmh:.1f-->24.7<!--/V--> km/h) con < 50 V y la batería que entra | Media (requisito) | Reportado; alternativas en 07 (72 V con declaración, motor mayor) |

## Ronda 1 (3 auditores independientes: cálculo, CAD/estructural, BOM/eléctrico/legal)

44 hallazgos verificados; corregidos por subsistema (commits `5d1be64`, `8c0bf1d`, `aca5edb` y siguientes).

### Cálculo (A)

| # | Hallazgo | Sev. | Resolución |
|---|---|---|---|
| A1 | **Savitsky fuera de validez**: largo mojado de quilla 1,77–2,10 m > fondo 1,75 m en todo el tramo que define la joroba y la V máx.; `valid` solo miraba τ | Alta | Validez L_K ≤ L_wl, λ ≤ 4 por punto en `sizing.json`; "Savitsky limitado por eslora" [ESTIMADO, D-21] con banda ensanchada. **Resultado: margen en la joroba <!--V:sizing.performance.hump_margin_min:.0%-->-7%<!--/V--> < 10 % (banda alta) — no cumple**; V máx. sostenida <!--V:sizing.performance.vmax_cont_kmh:.1f-->24.7<!--/V--> km/h sin base validada hasta T4. Lo que recupera el 10 %: <!--V:sizing.hump_recovery.mass_text:s-->22 kg menos<!--/V--> o <!--V:sizing.hump_recovery.lwl_text:s-->L_wl ≥ 1,96 m<!--/V--> (02 §3.2) |
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
