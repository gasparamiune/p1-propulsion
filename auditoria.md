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
| W-15 | Objetivo 30 km/h no alcanzado sostenido (<!--V:sizing.performance.vmax_cont_kmh:.1f-->25.1<!--/V--> km/h) con < 50 V y la batería que entra | Media (requisito) | Reportado; alternativas en 07 (72 V con declaración, motor mayor) |

## Ronda 1

(En curso.)

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
