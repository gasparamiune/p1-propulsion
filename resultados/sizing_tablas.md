<!-- generado por sizing.py — no editar a mano -->

## Resumen

| Magnitud | Valor | Etiqueta |
|---|---|---|
| Estado del optimizador | sin_vmax_objetivo | [CALCULADO] |
| Motor / controlador / batería | Maytech MTI120116 150 KV (inrunner refrigerado por agua, 10–16S) / Flipsky FSESC 75350 con caja de agua (VESC, filtro de fase, IP65) / 2 × LiTime 36 V 60 Ah Golf Cart en paralelo (12S2P, BMS 2 × 120 A) | [CALCULADO: optimizador] |
| Masa total / LCG desde el espejo | 217 kg / 1.12 m | [CALCULADO] |
| Calado / GM / escora con el piloto 0,1 m a un lado | 285 mm / 8 mm / 79° | [CALCULADO] |
| Eje del impulsor bajo la flotación (cebado) | 170 mm (ceba) | [CALCULADO] |
| Impulsor / cubo / tobera | Ø132 / Ø66 / Ø87 mm | [CALCULADO] |
| Punto de diseño de la bomba | 39.6 km/h, 5073 rpm, φ 0.260, ψ 0.073, Ω_s 5.59 | [CALCULADO] |
| ¿Planea? / margen mínimo en la joroba | sí / 19 % | [CALCULADO] |
| Tiempo de 0 a planeo | 6.7 s | [CALCULADO] |
| V máx. sostenida (potencia continua, banda nominal) | 26.3 km/h (objetivo 30) | [CALCULADO] |
| P de batería a V máx. / a 5 kn | 6723 W / 1680 W | [CALCULADO] |
| Empuje a punto fijo / en reversa | 765 N / 217 N | [CALCULADO] |
| Autonomía a V máx. / a 5 kn | 37 min (16.2 km) / 2.5 h | [CALCULADO] |
| Energía de la misión requerida / nominal | 3361 / 4608 Wh | [CALCULADO] |
| Cavitación S a V máx. (límite) | 3.17 (3.5) | [CALCULADO] |
| Velocidad periférica máx. | 29.0 m/s | [CALCULADO] |
| Corriente pico de batería / límite de fase | 192 A / 292 A | [CALCULADO] |
| Motor a V máx. sostenida (estacionario) | 49 °C (máx. 120) | [CALCULADO] |
| Eje Ø / FS estático / FS fatiga | 20 mm / 4.0 / 10.3 | [CALCULADO] |
| Rodamientos L10 a V máx. / vel. crítica / sello | 1053939 h / 3.1× n máx. / 4.4 m/s | [CALCULADO] |

## Curva a fondo (potencia pico, banda de diseño, batería nominal)

| V [km/h] | R diseño [N] | T pico [N] | rpm | P bat [W] | I bat [A] | S | Limita |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 765 | 4048 | 7270 | 189 | 3.50 | cavitación (S) |
| 4 | 25 | 701 | 4053 | 7289 | 190 | 3.50 | cavitación (S) |
| 7 | 114 | 646 | 4068 | 7344 | 191 | 3.50 | cavitación (S) |
| 11 | 279 | 593 | 4080 | 7373 | 192 | 3.48 | corriente de batería |
| 14 | 423 | 543 | 4090 | 7373 | 192 | 3.45 | corriente de batería |
| 18 | 402 | 495 | 4102 | 7373 | 192 | 3.42 | corriente de batería |
| 22 | 401 | 450 | 4116 | 7373 | 192 | 3.37 | corriente de batería |
| 25 | 404 | 406 | 4131 | 7373 | 192 | 3.32 | corriente de batería |
| 29 | 404 | 363 | 4146 | 7373 | 192 | 3.26 | corriente de batería |
| 32 | 408 | 321 | 4163 | 7373 | 192 | 3.20 | corriente de batería |
| 36 | 420 | 279 | 4179 | 7373 | 192 | 3.14 | corriente de batería |
| 40 | 440 | 237 | 4195 | 7373 | 192 | 3.07 | corriente de batería |

## Triángulos de velocidad del impulsor

| Sección | r [mm] | u [m/s] | c_m [m/s] | β1 [°] | β2 [°] | desvío [°] | entrada estator [°] | de Haller |
|---|---|---|---|---|---|---|---|---|
| cubo | 33.0 | 17.5 | 9.1 | 27.5 | 41.1 | 13.6 | 52.2 | 0.70 |
| medio | 52.2 | 27.7 | 9.1 | 18.2 | 21.4 | 3.2 | 63.8 | 0.86 |
| punta | 66.0 | 35.1 | 9.1 | 14.6 | 16.1 | 1.6 | 68.8 | 0.91 |

## Optimizador (15 mejores)

| Motor | Batería | Ø imp | D_t/D | V máx [km/h] | Margen joroba | Costo [€] | Duras OK |
|---|---|---|---|---|---|---|---|
| HPM5000B_48 | LT36_60x2 | 132 | 0.74 | 20.7 | 12 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 132 | 0.70 | 20.5 | 11 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 132 | 0.70 | 20.2 | 10 % | 1844 | sí |
| MTI120116_150 | LT36_60x2 | 132 | 0.66 | 26.3 | 19 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 120 | 0.66 | 26.2 | 12 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 120 | 0.74 | 26.2 | 19 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 132 | 0.58 | 26.1 | 16 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 132 | 0.62 | 26.1 | 17 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 108 | 0.74 | 26.1 | 10 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 120 | 0.70 | 26.1 | 18 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 120 | 0.62 | 25.9 | 15 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 120 | 0.66 | 25.9 | 16 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 108 | 0.70 | 25.9 | 15 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 132 | 0.58 | 25.8 | 15 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 120 | 0.62 | 25.6 | 14 % | 1896 | sí |
