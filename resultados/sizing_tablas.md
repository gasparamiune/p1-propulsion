<!-- generado por sizing.py — no editar a mano -->

## Resumen

| Magnitud | Valor | Etiqueta |
|---|---|---|
| Estado del optimizador | sin_solucion_dura | [CALCULADO] |
| Motor / controlador / batería | Maytech MTI120116 150 KV (inrunner refrigerado por agua, 10–16S) / Flipsky FSESC 75350 con caja de agua (VESC, filtro de fase, IP65) / 2 × LiTime 36 V 60 Ah Golf Cart en paralelo (12S2P, BMS 2 × 120 A) | [CALCULADO: optimizador] |
| Masa total / LCG desde el espejo | 217 kg / 1.12 m | [CALCULADO] |
| Calado / GM / escora con el piloto 0,1 m a un lado | 285 mm / 8 mm / 79° | [CALCULADO] |
| Eje del impulsor bajo la flotación (cebado) | 170 mm (ceba) | [CALCULADO] |
| Impulsor / cubo / tobera | Ø132 / Ø66 / Ø87 mm | [CALCULADO] |
| Punto de diseño de la bomba | 39.6 km/h, 5073 rpm, φ 0.260, ψ 0.073, Ω_s 5.59 | [CALCULADO] |
| ¿Planea? / margen mínimo en la joroba (a qué V) | sí / 3 % (19.8 km/h) — NO cumple el mínimo de 10% | [CALCULADO] |
| Puntos de planeo con Savitsky válido (L_K ≤ L_wl, λ ≤ 4, τ 2–15°) | 0 de 14 (el resto: limitado por eslora) | [CALCULADO; método ESTIMADO] |
| Tiempo de 0 a planeo | 13.6 s | [CALCULADO] |
| V máx. sostenida (potencia continua, banda nominal) | 25.0 km/h (objetivo 30) | [CALCULADO] |
| V máx. sostenida, banda baja – alta de R (sin validar hasta T4) | 18.2 – 28.8 km/h | [CALCULADO; R ESTIMADO] |
| P de batería a V máx. / a 5 kn | 6723 W / 1680 W | [CALCULADO] |
| Empuje a punto fijo / en reversa | 765 N / 217 N | [CALCULADO] |
| Autonomía a V máx. / a 5 kn | 37 min (15.4 km) / 2.5 h | [CALCULADO] |
| Energía de la misión requerida / nominal | 3361 / 4608 Wh | [CALCULADO] |
| Cavitación S a V máx. (límite) | 3.20 (3.5) | [CALCULADO] |
| Velocidad periférica máx. | 29.0 m/s | [CALCULADO] |
| Corriente pico de batería / límite de fase | 192 A / 292 A | [CALCULADO] |
| I_q pico (FOC) / l_current_max / margen | 285 A / 292 A / 2 % | [CALCULADO; convención bus_foc SUPUESTO] |
| Motor a V máx. sostenida (estacionario) | 49 °C (máx. 120) | [CALCULADO] |
| Eje Ø / FS estático / FS fatiga | 20 mm / 4.0 / 9.3 | [CALCULADO] |
| Rodamientos L10 a V máx. / vel. crítica / sello | 781878 h / 3.8× n máx. / 4.4 m/s | [CALCULADO] |

## Curva a fondo (potencia pico, banda de diseño, batería nominal)

| V [km/h] | R diseño [N] | T pico [N] | rpm | P bat [W] | I bat [A] | S | Limita |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 765 | 4048 | 7270 | 189 | 3.50 | cavitación (S) |
| 4 | 25 | 701 | 4053 | 7289 | 190 | 3.50 | cavitación (S) |
| 7 | 114 | 646 | 4068 | 7344 | 191 | 3.50 | cavitación (S) |
| 11 | 279 | 593 | 4080 | 7373 | 192 | 3.48 | corriente de batería |
| 14 | 439 | 543 | 4090 | 7373 | 192 | 3.46 | corriente de batería |
| 18 | 456 | 495 | 4102 | 7373 | 192 | 3.42 | corriente de batería |
| 22 | 444 | 450 | 4116 | 7373 | 192 | 3.38 | corriente de batería |
| 25 | 420 | 406 | 4131 | 7373 | 192 | 3.34 | corriente de batería |
| 29 | 409 | 363 | 4146 | 7373 | 192 | 3.29 | corriente de batería |
| 32 | 409 | 321 | 4163 | 7373 | 192 | 3.23 | corriente de batería |
| 36 | 420 | 279 | 4179 | 7373 | 192 | 3.16 | corriente de batería |
| 40 | 439 | 237 | 4195 | 7373 | 192 | 3.10 | corriente de batería |

## Triángulos de velocidad del impulsor

| Sección | r [mm] | u [m/s] | c_m [m/s] | β1 [°] | β2 [°] | desvío [°] | entrada estator [°] | de Haller |
|---|---|---|---|---|---|---|---|---|
| cubo | 33.0 | 17.5 | 9.1 | 27.5 | 41.1 | 13.6 | 52.2 | 0.70 |
| medio | 52.2 | 27.7 | 9.1 | 18.2 | 21.4 | 3.2 | 63.8 | 0.86 |
| punta | 66.0 | 35.1 | 9.1 | 14.6 | 16.1 | 1.6 | 68.8 | 0.91 |

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
