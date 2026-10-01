<!-- generado por sizing.py — no editar a mano -->

## Resumen

| Magnitud | Valor | Etiqueta |
|---|---|---|
| Estado del optimizador | sin_vmax_objetivo | [CALCULADO] |
| Motor / controlador / batería | Maytech MTI120116 150 KV (inrunner refrigerado por agua, 10–16S) / Flipsky FSESC 75350 con caja de agua (VESC, filtro de fase, IP65) / 2 × LiTime 36 V 60 Ah Golf Cart en paralelo (12S2P, BMS 2 × 120 A) | [CALCULADO: optimizador] |
| Masa total / LCG desde el espejo | 205 kg / 1.12 m | [CALCULADO] |
| Calado / GM / escora con el piloto 0,1 m a un lado | 273 mm / 2 mm / 87° | [CALCULADO] |
| Eje del impulsor bajo la flotación (cebado) | 158 mm (ceba) | [CALCULADO] |
| Impulsor / cubo / tobera | Ø132 / Ø66 / Ø82 mm | [CALCULADO] |
| Punto de diseño de la bomba | 38.2 km/h, 5178 rpm, φ 0.214, ψ 0.062, Ω_s 5.69 | [CALCULADO] |
| ¿Planea? / margen mínimo en la joroba | sí / 19 % | [CALCULADO] |
| Tiempo de 0 a planeo | 8.1 s | [CALCULADO] |
| V máx. sostenida (potencia continua, banda nominal) | 28.6 km/h (objetivo 30) | [CALCULADO] |
| P de batería a V máx. / a 5 kn | 6723 W / 1651 W | [CALCULADO] |
| Empuje a punto fijo / en reversa | 664 N / 188 N | [CALCULADO] |
| Autonomía a V máx. / a 5 kn | 37 min (17.6 km) / 2.5 h | [CALCULADO] |
| Energía de la misión requerida / nominal | 3342 / 4608 Wh | [CALCULADO] |
| Cavitación S a V máx. (límite) | 3.37 (3.5) | [CALCULADO] |
| Velocidad periférica máx. | 34.1 m/s | [CALCULADO] |
| Corriente pico de batería / límite de fase | 221 A / 292 A | [CALCULADO] |
| Motor a V máx. sostenida (estacionario) | 46 °C (máx. 120) | [CALCULADO] |
| Eje Ø / FS estático / FS fatiga | 20 mm / 4.0 / 11.5 | [CALCULADO] |
| Rodamientos L10 a V máx. / vel. crítica / sello | 1156250 h / 5.3× n máx. / 5.2 m/s | [CALCULADO] |

## Curva a fondo (potencia pico, banda de diseño, batería nominal)

| V [km/h] | R diseño [N] | T pico [N] | rpm | P bat [W] | I bat [A] | S | Limita |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 664 | 4326 | 6194 | 161 | 3.50 | cavitación (S) |
| 4 | 24 | 609 | 4331 | 6210 | 162 | 3.50 | cavitación (S) |
| 7 | 110 | 561 | 4347 | 6256 | 163 | 3.50 | cavitación (S) |
| 11 | 269 | 518 | 4373 | 6335 | 165 | 3.50 | cavitación (S) |
| 14 | 398 | 480 | 4409 | 6448 | 168 | 3.50 | cavitación (S) |
| 18 | 369 | 446 | 4455 | 6599 | 172 | 3.50 | cavitación (S) |
| 22 | 369 | 416 | 4511 | 6790 | 177 | 3.50 | cavitación (S) |
| 25 | 375 | 388 | 4577 | 7025 | 183 | 3.50 | cavitación (S) |
| 29 | 378 | 363 | 4652 | 7307 | 190 | 3.50 | cavitación (S) |
| 32 | 386 | 339 | 4737 | 7640 | 199 | 3.50 | cavitación (S) |
| 36 | 400 | 317 | 4830 | 8028 | 209 | 3.50 | cavitación (S) |
| 40 | 423 | 295 | 4932 | 8474 | 221 | 3.50 | cavitación (S) |

## Triángulos de velocidad del impulsor

| Sección | r [mm] | u [m/s] | c_m [m/s] | β1 [°] | β2 [°] | desvío [°] | entrada estator [°] | de Haller |
|---|---|---|---|---|---|---|---|---|
| cubo | 33.0 | 17.9 | 7.7 | 23.2 | 33.2 | 10.0 | 51.0 | 0.72 |
| medio | 52.2 | 28.3 | 7.7 | 15.1 | 17.4 | 2.3 | 62.9 | 0.87 |
| punta | 66.0 | 35.8 | 7.7 | 12.1 | 13.2 | 1.1 | 68.0 | 0.92 |

## Optimizador (15 mejores)

| Motor | Batería | Ø imp | D_t/D | V máx [km/h] | Margen joroba | Costo [€] | Duras OK |
|---|---|---|---|---|---|---|---|
| HPM5000B_48 | LT36_60x2 | 132 | 0.74 | 22.8 | 23 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 132 | 0.70 | 22.7 | 22 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 132 | 0.66 | 22.5 | 20 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 132 | 0.62 | 22.2 | 18 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 132 | 0.66 | 22.2 | 38 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 120 | 0.66 | 22.0 | 16 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 132 | 0.62 | 21.9 | 35 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 132 | 0.58 | 21.9 | 15 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 120 | 0.62 | 21.6 | 14 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 132 | 0.58 | 21.5 | 33 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 120 | 0.62 | 21.3 | 31 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 120 | 0.58 | 21.1 | 12 % | 1844 | sí |
| HPM5000B_48 | LT36_60x2 | 120 | 0.58 | 20.8 | 28 % | 1844 | sí |
| MTI120116_150 | LT36_60x2 | 132 | 0.62 | 28.6 | 19 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 120 | 0.70 | 28.5 | 16 % | 1896 | sí |
