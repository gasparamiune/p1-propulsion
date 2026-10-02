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
| Punto de diseño de la bomba | 43.6 km/h, 5073 rpm, φ 0.267, ψ 0.071, Ω_s 5.77 | [CALCULADO] |
| ¿Llega a planeo pleno (27.3 km/h) con la banda high? / margen mínimo 0–planeo pleno (a qué V) | NO / -7 % (27.0 km/h) — NO cumple el mínimo de 10% | [CALCULADO] |
| Puntos de planeo con Savitsky válido (L_K ≤ L_wl, λ ≤ 4, τ 2–15°) | 0 de 23 (el resto: limitado por eslora) | [CALCULADO; método ESTIMADO] |
| Tiempo de 0 a planeo pleno (banda nominal / alta) | 21.5 s / no llega | [CALCULADO] |
| ¿Se sostiene en planeo con potencia continua? (banda baja / nominal / alta) | sí / sí / NO | [CALCULADO; R ESTIMADO] |
| V máx. sostenida (potencia continua, banda nominal) | 24.7 km/h (objetivo 30) | [CALCULADO] |
| V máx. sostenida, banda baja – alta de R (sin validar hasta T4) | 18.0 – 28.7 km/h | [CALCULADO; R ESTIMADO] |
| P de batería a V máx. / a 5 kn | 6723 W / 1698 W | [CALCULADO] |
| Empuje a punto fijo / en reversa | 764 N / 217 N | [CALCULADO] |
| Autonomía a V máx. / a 5 kn | 37 min (15.2 km) / 2.4 h | [CALCULADO] |
| Energía de la misión requerida / nominal | 3373 / 4608 Wh | [CALCULADO] |
| Cavitación S a V máx. (límite) | 3.19 (3.5) | [CALCULADO] |
| Velocidad periférica máx. | 28.9 m/s | [CALCULADO] |
| Corriente pico de batería / límite de fase | 192 A / 292 A | [CALCULADO] |
| I_q pico (FOC) / l_current_max / margen | 287 A / 292 A / 2 % | [CALCULADO; convención bus_foc SUPUESTO] |
| Motor a V máx. sostenida (estacionario) | 49 °C (máx. 120) | [CALCULADO] |
| Eje Ø / FS estático / FS fatiga | 20 mm / 4.0 / 9.2 | [CALCULADO] |
| Rodamientos L10 a V máx. / vel. crítica / sello | 779929 h / 3.8× n máx. / 4.4 m/s | [CALCULADO] |

## Curva a fondo (potencia pico, banda de diseño, batería nominal)

| V [km/h] | R diseño [N] | T pico [N] | rpm | P bat [W] | I bat [A] | S | Limita |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 764 | 4044 | 7373 | 192 | 3.50 | corriente de batería |
| 4 | 25 | 700 | 4046 | 7373 | 192 | 3.49 | corriente de batería |
| 7 | 114 | 642 | 4051 | 7373 | 192 | 3.48 | corriente de batería |
| 11 | 279 | 588 | 4059 | 7373 | 192 | 3.46 | corriente de batería |
| 14 | 438 | 538 | 4069 | 7373 | 192 | 3.43 | corriente de batería |
| 18 | 456 | 491 | 4082 | 7373 | 192 | 3.40 | corriente de batería |
| 22 | 444 | 446 | 4096 | 7373 | 192 | 3.36 | corriente de batería |
| 25 | 419 | 404 | 4112 | 7373 | 192 | 3.32 | corriente de batería |
| 29 | 409 | 362 | 4129 | 7373 | 192 | 3.27 | corriente de batería |
| 32 | 409 | 320 | 4147 | 7373 | 192 | 3.21 | corriente de batería |
| 36 | 420 | 279 | 4164 | 7373 | 192 | 3.15 | corriente de batería |
| 40 | 439 | 238 | 4181 | 7373 | 192 | 3.09 | corriente de batería |

## Triángulos de velocidad del impulsor

| Sección | r [mm] | u [m/s] | c_m [m/s] | β1 [°] | β2 [°] | desvío [°] | entrada estator [°] | de Haller |
|---|---|---|---|---|---|---|---|---|
| cubo | 33.0 | 17.5 | 9.3 | 28.1 | 41.3 | 13.3 | 53.5 | 0.71 |
| medio | 52.2 | 27.7 | 9.3 | 18.6 | 21.8 | 3.2 | 65.0 | 0.86 |
| punta | 66.0 | 35.1 | 9.3 | 14.9 | 16.5 | 1.5 | 69.7 | 0.91 |

## Optimizador (15 mejores)

| Motor | Batería | Ø imp | D_t/D | V máx [km/h] | Margen joroba | Costo [€] | Duras OK |
|---|---|---|---|---|---|---|---|
| HPM5000B_48 | LT36_60x1 | 132 | 0.74 | 14.1 | -48 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.74 | 13.9 | -48 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.70 | 13.9 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.74 | 13.8 | -48 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.70 | 13.8 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.74 | 13.8 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.66 | 13.7 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.70 | 13.6 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.74 | 13.6 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.66 | 13.6 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.70 | 13.6 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.62 | 13.5 | -46 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.74 | 13.5 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.66 | 13.5 | -47 % | 1322 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.70 | 13.4 | -47 % | 1322 | no |
