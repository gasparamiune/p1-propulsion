<!-- generado por sizing.py — no editar a mano -->

## Resumen

| Magnitud | Valor | Etiqueta |
|---|---|---|
| Estado del optimizador | sin_solucion_dura | [CALCULADO] |
| Motor / controlador / batería | Maytech MTI120116 150 KV (inrunner refrigerado por agua, 10–16S) / Flipsky FSESC 75350 con caja de agua (VESC, filtro de fase, IP65) / 2 × LiTime 36 V 60 Ah Golf Cart en paralelo (12S2P, BMS 2 × 120 A) | [CALCULADO: optimizador] |
| Masa total / LCG desde el espejo | 217 kg / 1.12 m | [CALCULADO] |
| Calado / GM / escora con el piloto 0,1 m a un lado | 285 mm / 8 mm / 79° | [CALCULADO] |
| Eje del impulsor bajo la flotación (cebado) | 170 mm (ceba) | [CALCULADO] |
| Impulsor / cubo / tobera | Ø132 / Ø66 / Ø82 mm | [CALCULADO] |
| Punto de diseño de la bomba | 37.1 km/h, 5178 rpm, φ 0.212, ψ 0.063, Ω_s 5.64 | [CALCULADO] |
| ¿Planea? / margen mínimo en la joroba (a qué V) | NO / -6 % (19.8 km/h) — NO cumple el mínimo de 10% | [CALCULADO] |
| Puntos de planeo con Savitsky válido (L_K ≤ L_wl, λ ≤ 4, τ 2–15°) | 0 de 14 (el resto: limitado por eslora) | [CALCULADO; método ESTIMADO] |
| Tiempo de 0 a planeo | inf s | [CALCULADO] |
| V máx. sostenida (potencia continua, banda nominal) | 25.1 km/h (objetivo 30) | [CALCULADO] |
| V máx. sostenida, banda baja – alta de R (sin validar hasta T4) | 17.1 – 29.1 km/h | [CALCULADO; R ESTIMADO] |
| P de batería a V máx. / a 5 kn | 6723 W / 1724 W | [CALCULADO] |
| Empuje a punto fijo / en reversa | 665 N / 188 N | [CALCULADO] |
| Autonomía a V máx. / a 5 kn | 37 min (15.5 km) / 2.4 h | [CALCULADO] |
| Energía de la misión requerida / nominal | 3390 / 4608 Wh | [CALCULADO] |
| Cavitación S a V máx. (límite) | 3.45 (3.5) | [CALCULADO] |
| Velocidad periférica máx. | 32.6 m/s | [CALCULADO] |
| Corriente pico de batería / límite de fase | 192 A / 292 A | [CALCULADO] |
| I_q pico (FOC) / l_current_max / margen | 251 A / 292 A / 16 % | [CALCULADO; convención bus_foc SUPUESTO] |
| Motor a V máx. sostenida (estacionario) | 46 °C (máx. 120) | [CALCULADO] |
| Eje Ø / FS estático / FS fatiga | 20 mm / 4.0 / 10.3 | [CALCULADO] |
| Rodamientos L10 a V máx. / vel. crítica / sello | 711867 h / 3.4× n máx. / 4.9 m/s | [CALCULADO] |

## Curva a fondo (potencia pico, banda de diseño, batería nominal)

| V [km/h] | R diseño [N] | T pico [N] | rpm | P bat [W] | I bat [A] | S | Limita |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 665 | 4329 | 6180 | 161 | 3.50 | cavitación (S) |
| 4 | 25 | 610 | 4334 | 6196 | 161 | 3.50 | cavitación (S) |
| 7 | 114 | 561 | 4350 | 6242 | 163 | 3.50 | cavitación (S) |
| 11 | 279 | 518 | 4376 | 6322 | 165 | 3.50 | cavitación (S) |
| 14 | 439 | 480 | 4410 | 6428 | 167 | 3.50 | cavitación (S) |
| 18 | 456 | 445 | 4452 | 6560 | 171 | 3.50 | cavitación (S) |
| 22 | 444 | 413 | 4503 | 6725 | 175 | 3.50 | cavitación (S) |
| 25 | 420 | 384 | 4562 | 6928 | 180 | 3.50 | cavitación (S) |
| 29 | 409 | 357 | 4632 | 7183 | 187 | 3.50 | cavitación (S) |
| 32 | 409 | 327 | 4688 | 7373 | 192 | 3.47 | corriente de batería |
| 36 | 420 | 288 | 4706 | 7373 | 192 | 3.40 | corriente de batería |
| 40 | 439 | 250 | 4723 | 7373 | 192 | 3.32 | corriente de batería |

## Triángulos de velocidad del impulsor

| Sección | r [mm] | u [m/s] | c_m [m/s] | β1 [°] | β2 [°] | desvío [°] | entrada estator [°] | de Haller |
|---|---|---|---|---|---|---|---|---|
| cubo | 33.0 | 17.9 | 7.6 | 23.0 | 33.1 | 10.1 | 50.6 | 0.72 |
| medio | 52.2 | 28.3 | 7.6 | 15.0 | 17.3 | 2.3 | 62.6 | 0.87 |
| punta | 66.0 | 35.8 | 7.6 | 12.0 | 13.1 | 1.1 | 67.7 | 0.92 |

## Optimizador (15 mejores)

| Motor | Batería | Ø imp | D_t/D | V máx [km/h] | Margen joroba | Costo [€] | Duras OK |
|---|---|---|---|---|---|---|---|
| HPM5000B_48 | LT36_60x1 | 132 | 0.74 | 14.1 | -39 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.74 | 13.9 | -40 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.70 | 13.9 | -39 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.74 | 13.8 | -40 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.70 | 13.8 | -40 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.74 | 13.7 | -40 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.66 | 13.7 | -40 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.70 | 13.6 | -41 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.74 | 13.6 | -40 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.66 | 13.6 | -40 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.70 | 13.6 | -40 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.62 | 13.5 | -40 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.74 | 13.5 | -41 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.66 | 13.5 | -41 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.70 | 13.4 | -41 % | 1322 | no |
