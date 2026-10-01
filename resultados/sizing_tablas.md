<!-- generado por sizing.py — no editar a mano -->

## Resumen

| Magnitud | Valor | Etiqueta |
|---|---|---|
| Estado del optimizador | sin_solucion_dura | [CALCULADO] |
| Motor / controlador / batería | Golden Motor HPM5000B 48 V (BLDC refrigerado por aire) / Controlador VESC 75 V / 200 A (placeholder, research/R11) / LFP 13S 60 Ah (41,6 V; placeholder research/R11) | [CALCULADO: optimizador] |
| Masa total / LCG desde el espejo | 192 kg / 1.11 m | [CALCULADO] |
| Calado / GM / escora con el piloto 0,1 m a un lado | 260 mm / -11 mm / inf° | [CALCULADO] |
| Eje del impulsor bajo la flotación (cebado) | 145 mm (ceba) | [CALCULADO] |
| Impulsor / cubo / tobera | Ø132 / Ø66 / Ø87 mm | [CALCULADO] |
| Punto de diseño de la bomba | 25.2 km/h, 3988 rpm, φ 0.239, ψ 0.068, Ω_s 5.64 | [CALCULADO] |
| ¿Planea? / margen mínimo en la joroba | sí / 15 % | [CALCULADO] |
| Tiempo de 0 a planeo | 8.3 s | [CALCULADO] |
| V máx. sostenida (potencia continua, banda nominal) | 25.3 km/h (objetivo 30) | [CALCULADO] |
| P de batería a V máx. / a 5 kn | 5605 W / 1596 W | [CALCULADO] |
| Empuje a punto fijo / en reversa | 665 N / 188 N | [CALCULADO] |
| Autonomía a V máx. / a 5 kn | 24 min (10.2 km) / 1.4 h | [CALCULADO] |
| Energía de la misión requerida / nominal | 2932 / 2496 Wh | [CALCULADO] |
| Cavitación S a V máx. (límite) | 3.09 (3.5) | [CALCULADO] |
| Velocidad periférica máx. | 27.6 m/s | [CALCULADO] |
| Corriente pico de batería / límite de fase | 141 A / 167 A | [CALCULADO] |
| Motor a V máx. sostenida (estacionario) | 65 °C (máx. 120) | [CALCULADO] |
| Eje Ø / FS estático / FS fatiga | 20 mm / 4.9 / 12.4 | [CALCULADO] |
| Rodamientos L10 a V máx. / vel. crítica / sello | 1649687 h / 6.6× n máx. / 4.2 m/s | [CALCULADO] |

## Curva a fondo (potencia pico, banda de diseño, batería nominal)

| V [km/h] | R diseño [N] | T pico [N] | rpm | P bat [W] | I bat [A] | S | Limita |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 665 | 3981 | 5848 | 141 | 3.33 | tensión |
| 4 | 23 | 604 | 3982 | 5843 | 140 | 3.32 | tensión |
| 7 | 106 | 548 | 3982 | 5825 | 140 | 3.31 | tensión |
| 11 | 258 | 496 | 3983 | 5797 | 139 | 3.28 | tensión |
| 14 | 371 | 447 | 3984 | 5759 | 138 | 3.24 | tensión |
| 18 | 339 | 401 | 3985 | 5714 | 137 | 3.20 | tensión |
| 22 | 341 | 356 | 3987 | 5663 | 136 | 3.15 | tensión |
| 25 | 348 | 312 | 3988 | 5608 | 135 | 3.09 | tensión |
| 29 | 353 | 270 | 3990 | 5550 | 133 | 3.02 | tensión |
| 32 | 363 | 228 | 3992 | 5492 | 132 | 2.96 | tensión |
| 36 | 380 | 186 | 3993 | 5436 | 131 | 2.89 | tensión |
| 40 | 404 | 144 | 3995 | 5382 | 129 | 2.82 | tensión |

## Triángulos de velocidad del impulsor

| Sección | r [mm] | u [m/s] | c_m [m/s] | β1 [°] | β2 [°] | desvío [°] | entrada estator [°] | de Haller |
|---|---|---|---|---|---|---|---|---|
| cubo | 33.0 | 13.8 | 6.6 | 25.5 | 37.5 | 11.9 | 51.7 | 0.71 |
| medio | 52.2 | 21.8 | 6.6 | 16.8 | 19.6 | 2.8 | 63.5 | 0.86 |
| punta | 66.0 | 27.6 | 6.6 | 13.4 | 14.8 | 1.3 | 68.5 | 0.91 |

## Optimizador (15 mejores)

| Motor | Batería | Ø imp | D_t/D | V máx [km/h] | Margen joroba | Costo [€] | Duras OK |
|---|---|---|---|---|---|---|---|
| HPM5000B_48 | LFP_13S_60 | 132 | 0.70 | 25.3 | 18 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 132 | 0.66 | 25.3 | 16 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 132 | 0.70 | 25.3 | 20 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 132 | 0.66 | 25.3 | 18 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 132 | 0.74 | 25.3 | 20 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 132 | 0.74 | 25.3 | 21 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 132 | 0.62 | 25.2 | 14 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 132 | 0.62 | 25.2 | 17 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 120 | 0.74 | 25.2 | 17 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 120 | 0.74 | 25.2 | 19 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 120 | 0.70 | 25.2 | 15 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 120 | 0.70 | 25.2 | 17 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 120 | 0.66 | 25.1 | 16 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 120 | 0.66 | 25.1 | 13 % | 2706 | no |
| HPM5000B_48 | LFP_13S_60 | 132 | 0.58 | 25.0 | 12 % | 2706 | no |
