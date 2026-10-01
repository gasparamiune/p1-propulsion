<!-- generado por sizing.py — no editar a mano -->

## Resumen

| Magnitud | Valor | Etiqueta |
|---|---|---|
| Masa total de diseño | 293 kg | [CALCULADO] |
| Carga útil vs placa de capacidad | 248 / 160 kg (155 %) | [CALCULADO] |
| Calado / francobordo | 198 / 182 mm | [CALCULADO] |
| Velocidad de casco (Fr_L=0.40) | 6.36 km/h | [CALCULADO] |
| Fr_L a velocidad de crucero | 0.376 | [CALCULADO] |
| R crucero (nominal / diseño) | 135 / 156 N | [CALCULADO] |
| Empuje en el eje en crucero (diseño) | 195 N | [CALCULADO] |
| Hélice | MKP32 — modelo lineal calibrada a B-series, fuera del rango de la serie [ESTIMADO] | [SUPUESTO] |
| rpm hélice / J / η0 crucero (diseño) | 1491 rpm / 0.23 / 0.41 | [CALCULADO] |
| Potencia al eje crucero (diseño) | 698 W | [CALCULADO] |
| Potencia de batería crucero (nominal / diseño) | 759 / 910 W | [CALCULADO] |
| Rendimiento total batería→R·V (diseño) | 29 % | [CALCULADO] |
| Relación de correa | 20T : 40T = 2.00 | [CALCULADO] |
| Batería elegida | 2 × Power Queen 12V 100Ah en serie (BMS 100 A c/u) | [CALCULADO] |
| Energía requerida / usable | 2426 / 2304 Wh | [CALCULADO] |
| Autonomía a crucero (nominal / diseño) | 3.04 / 2.53 h | [CALCULADO] |
| V máx. (diseño, batería baja) | 6.7 km/h — limita: tensión (duty) | [CALCULADO] |
| V máx. (nominal, batería nominal) | 7.4 km/h | [CALCULADO] |
| Bollard pull avante (horizontal) | 280 N (28.6 kgf) — limita: corriente de motor | [CALCULADO] |
| Bollard pull marcha atrás | 89 N | [CALCULADO] |
| Corriente pico de batería / margen ESC | 62 A / 62 % | [CALCULADO] |
| Cable DC / fases | 16 mm² (1.1 %) / 10 mm² (2.7 %) | [CALCULADO] |
| Fusible principal | 80 A | [CALCULADO] |
| Pasador de corte | Ø2.0 mm AISI 316 → corta a 12.4 N·m | [CALCULADO] |
| Velocidad crítica del eje / rpm máx. | 5834 / 1777 rpm | [CALCULADO] |
| Largo de eje / tubo | 1357 / 1171 mm | [CALCULADO] |

## Barrido de velocidad

| v [km/h] | Fr_L | R nom [N] | R diseño [N] | P_bat nom [W] | P_bat diseño [W] | rpm hélice | Autonomía nom [h] | Autonomía diseño [h] | Wh/km diseño |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.13 | 10 | 11 | 22 | 25 | 435 | 105.95 | 93.20 | 12 |
| 3 | 0.19 | 24 | 27 | 66 | 77 | 669 | 34.66 | 29.78 | 26 |
| 4 | 0.25 | 48 | 55 | 170 | 201 | 924 | 13.52 | 11.45 | 50 |
| 5 | 0.31 | 84 | 97 | 382 | 455 | 1201 | 6.03 | 5.06 | 91 |
| 6 | 0.38 | 135 | 156 | 759 | 910 | 1491 | 3.04 | 2.53 | 152 |
| 7 | 0.44 | 198 | 228 | 1338 | 1611 ✗ | 1781 | 1.72 | 1.43 | 230 |
| 8 | 0.50 | 267 | 307 | 2110 | 2549 ✗ | 2055 | 1.09 | 0.90 | 319 |
| 9 | 0.56 | 335 | 385 | 3023 | 3657 ✗ | 2307 | 0.76 | 0.63 | 406 |
| 10 | 0.63 | 398 | 458 | 4008 | 4853 ✗ | 2533 | 0.57 | 0.47 | 485 |
| 11 | 0.69 | 455 | 523 | 5013 | 6070 ✗ | 2735 | 0.46 | 0.38 | 552 |
| 12 | 0.75 | 505 | 580 | 6006 | 7270 ✗ | 2917 | 0.38 | 0.32 | 606 |
| 13 | 0.82 | 548 | 630 | 6975 | 8436 ✗ | 3085 | 0.33 | 0.27 | 649 |

## Tiempo sostenible a velocidad alta

| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1338 | 52 | 103 | 8 | 8 |
| 7 | design | no (corriente de motor) | 1611 | 63 | 86 | 6 | 0 |
| 8 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2110 | 82 | 66 | 4 | 0 |
| 8 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2549 | 100 | 54 | 3 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3023 | 118 | 46 | 2 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3657 | 143 | 38 | 2 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 4008 | 157 | 34 | 2 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4853 | 190 | 28 | 1 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5013 | 196 | 28 | 1 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 6070 | 237 | 23 | 1 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 6006 | 235 | 23 | 1 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 7270 | 284 | 19 | 1 | 0 |

## Sensibilidad

| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | Variación P | 
|---|---|---|---|---|
| Coef. de olas c_w (calibración) | ±30 % | 729 / 1104 | 7.1 / 6.4 | 41 % |
| Pérdida por protector (0–25 %) | 0–0.25 | 793 / 1159 | 6.9 / 6.3 | 40 % |
| Masa por persona | ±20 % | 767 / 1061 | 7.0 / 6.4 | 32 % |
| Eslora de flotación | ±10 % | 1067 / 791 | 6.4 / 6.9 | 30 % |
| Rendimiento de hélice (modelo) | ±10 % | 1022 / 820 | 6.6 / 6.7 | 22 % |
| Masa del casco | ±30 % | 861 / 960 | 6.8 / 6.6 | 11 % |
| Ancho de espejo sumergido | ±20 % | 834 / 931 | 6.8 / 6.6 | 11 % |
| Resistencia del motor | ±30 % | 873 / 946 | 6.9 / 6.5 | 8 % |
| Ángulo de eje | ±20 % | 882 / 947 | 6.7 / 6.7 | 7 % |
