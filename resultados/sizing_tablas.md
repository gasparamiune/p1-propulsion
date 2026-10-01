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
| Hélice | MKP32 — modelo lineal aproximada [ESTIMADO] | [SUPUESTO] |
| rpm hélice / J / η0 crucero (diseño) | 1542 rpm / 0.23 / 0.40 | [CALCULADO] |
| Potencia al eje crucero (diseño) | 726 W | [CALCULADO] |
| Potencia de batería crucero (nominal / diseño) | 770 / 920 W | [CALCULADO] |
| Rendimiento total batería→R·V (diseño) | 28 % | [CALCULADO] |
| Relación de correa | 20T : 40T = 2.00 | [CALCULADO] |
| Batería elegida | 2 × Power Queen 12V 100Ah en serie (BMS 100 A c/u) | [CALCULADO] |
| Energía requerida / usable | 2452 / 2304 Wh | [CALCULADO] |
| Autonomía a crucero (nominal / diseño) | 2.99 / 2.51 h | [CALCULADO] |
| V máx. (diseño, batería baja) | 6.7 km/h — limita: tensión (duty) | [CALCULADO] |
| V máx. (nominal, batería nominal) | 7.4 km/h | [CALCULADO] |
| Bollard pull avante (horizontal) | 280 N (28.6 kgf) — limita: corriente de motor | [CALCULADO] |
| Bollard pull marcha atrás | 89 N | [CALCULADO] |
| Corriente pico de batería / margen ESC | 62 A / 61 % | [CALCULADO] |
| Cable DC / fases | 16 mm² (1.1 %) / 10 mm² (2.7 %) | [CALCULADO] |
| Fusible principal | 80 A | [CALCULADO] |
| Pasador de corte | Ø2.0 mm AISI 316 → corta a 12.4 N·m | [CALCULADO] |
| Velocidad crítica del eje / rpm máx. | 5834 / 1831 rpm | [CALCULADO] |
| Largo de eje / tubo | 1357 / 1171 mm | [CALCULADO] |

## Barrido de velocidad

| v [km/h] | Fr_L | R nom [N] | R diseño [N] | P_bat nom [W] | P_bat diseño [W] | rpm hélice | Autonomía nom [h] | Autonomía diseño [h] | Wh/km diseño |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.13 | 10 | 11 | 22 | 25 | 450 | 102.68 | 90.45 | 13 |
| 3 | 0.19 | 24 | 27 | 68 | 80 | 692 | 33.66 | 28.97 | 27 |
| 4 | 0.25 | 48 | 55 | 175 | 206 | 956 | 13.18 | 11.20 | 51 |
| 5 | 0.31 | 84 | 97 | 390 | 463 | 1242 | 5.91 | 4.98 | 93 |
| 6 | 0.38 | 135 | 156 | 770 | 920 | 1542 | 2.99 | 2.51 | 153 |
| 7 | 0.44 | 198 | 228 | 1349 | 1619 ✗ | 1840 | 1.71 | 1.42 | 231 |
| 8 | 0.50 | 267 | 307 | 2119 | 2550 ✗ | 2124 | 1.09 | 0.90 | 319 |
| 9 | 0.56 | 335 | 385 | 3025 | 3646 ✗ | 2384 | 0.76 | 0.63 | 405 |
| 10 | 0.63 | 398 | 458 | 4002 | 4826 ✗ | 2618 | 0.58 | 0.48 | 483 |
| 11 | 0.69 | 455 | 523 | 4997 | 6026 ✗ | 2827 | 0.46 | 0.38 | 548 |
| 12 | 0.75 | 505 | 580 | 5982 | 7209 ✗ | 3017 | 0.39 | 0.32 | 601 |
| 13 | 0.82 | 548 | 630 | 6945 | 8361 ✗ | 3191 | 0.33 | 0.28 | 643 |

## Tiempo sostenible a velocidad alta

| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1349 | 53 | 102 | ∞ | 102 |
| 7 | design | no (corriente de motor) | 1619 | 63 | 85 | 21 | 0 |
| 8 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2119 | 83 | 65 | 10 | 0 |
| 8 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2550 | 100 | 54 | 7 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3025 | 118 | 46 | 6 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3646 | 142 | 38 | 4 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 4002 | 156 | 35 | 4 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4826 | 189 | 29 | 3 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4997 | 195 | 28 | 3 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 6026 | 235 | 23 | 2 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5982 | 234 | 23 | 2 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 7209 | 282 | 19 | 2 | 0 |

## Sensibilidad

| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | Variación P | 
|---|---|---|---|---|
| Coef. de olas c_w (calibración) | ±30 % | 740 / 1112 | 7.1 / 6.4 | 40 % |
| Pérdida por protector (0–25 %) | 0–0.25 | 804 / 1166 | 6.9 / 6.3 | 39 % |
| Masa por persona | ±20 % | 777 / 1070 | 7.0 / 6.4 | 32 % |
| Eslora de flotación | ±10 % | 1076 / 802 | 6.4 / 6.9 | 30 % |
| Rendimiento de hélice (modelo) | ±10 % | 1031 / 831 | 6.6 / 6.7 | 22 % |
| Masa del casco | ±30 % | 871 / 970 | 6.8 / 6.6 | 11 % |
| Ancho de espejo sumergido | ±20 % | 844 / 941 | 6.8 / 6.6 | 11 % |
| Ángulo de eje | ±20 % | 893 / 956 | 6.7 / 6.7 | 7 % |
| Resistencia del motor | ±30 % | 890 / 949 | 6.9 / 6.5 | 6 % |
