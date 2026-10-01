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
| Hélice | EO10x8 — modelo lineal aproximada [ESTIMADO] | [SUPUESTO] |
| rpm hélice / J / η0 crucero (diseño) | 976 rpm / 0.36 / 0.46 | [CALCULADO] |
| Potencia al eje crucero (diseño) | 628 W | [CALCULADO] |
| Potencia de batería crucero (nominal / diseño) | 643 / 774 W | [CALCULADO] |
| Rendimiento total batería→R·V (diseño) | 34 % | [CALCULADO] |
| Relación de correa | 16T : 48T = 3.00 | [CALCULADO] |
| Batería elegida | 2 × LiFePO4 12.8 V 100 Ah en serie (BMS 100 A c/u) | [CALCULADO] |
| Energía requerida / usable | 2064 / 2304 Wh | [CALCULADO] |
| Autonomía a crucero (nominal / diseño) | 3.58 / 2.98 h | [CALCULADO] |
| V máx. (diseño, batería baja) | 7.1 km/h — limita: tensión (duty) | [CALCULADO] |
| V máx. (nominal, batería nominal) | 7.7 km/h | [CALCULADO] |
| Bollard pull avante (horizontal) | 297 N (30.3 kgf) — limita: corriente de motor | [CALCULADO] |
| Bollard pull marcha atrás | 94 N | [CALCULADO] |
| Corriente pico de batería / margen ESC | 66 A / 51 % | [CALCULADO] |
| Cable DC / fases | 16 mm² (1.2 %) / 10 mm² (2.7 %) | [CALCULADO] |
| Fusible principal | 100 A | [CALCULADO] |
| Pasador de corte | Ø3.0 mm Al6061-T6 → corta a 23.4 N·m | [CALCULADO] |
| Velocidad crítica del eje / rpm máx. | 5763 / 1216 rpm | [CALCULADO] |
| Largo de eje / tubo | 1352 / 1178 mm | [CALCULADO] |

## Barrido de velocidad

| v [km/h] | Fr_L | R nom [N] | R diseño [N] | P_bat nom [W] | P_bat diseño [W] | rpm hélice | Autonomía nom [h] | Autonomía diseño [h] | Wh/km diseño |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.13 | 10 | 11 | 19 | 22 | 279 | 121.30 | 106.02 | 11 |
| 3 | 0.19 | 24 | 27 | 57 | 67 | 430 | 40.32 | 34.40 | 22 |
| 4 | 0.25 | 48 | 55 | 146 | 173 | 598 | 15.82 | 13.32 | 43 |
| 5 | 0.31 | 84 | 97 | 325 | 390 | 782 | 7.08 | 5.91 | 78 |
| 6 | 0.38 | 135 | 156 | 643 | 774 | 976 | 3.58 | 2.98 | 129 |
| 7 | 0.44 | 198 | 228 | 1126 | 1361 | 1170 | 2.05 | 1.69 | 194 |
| 8 | 0.50 | 267 | 307 | 1763 | 2135 ✗ | 1352 | 1.31 | 1.08 | 267 |
| 9 | 0.56 | 335 | 385 | 2504 | 3038 ✗ | 1517 | 0.92 | 0.76 | 338 |
| 10 | 0.63 | 398 | 458 | 3293 | 3997 ✗ | 1662 | 0.70 | 0.58 | 400 |
| 11 | 0.69 | 455 | 523 | 4084 | 4957 ✗ | 1790 | 0.56 | 0.46 | 451 |
| 12 | 0.75 | 505 | 580 | 4854 | 5889 ✗ | 1903 | 0.47 | 0.39 | 491 |
| 13 | 0.82 | 548 | 630 | 5592 | 6781 ✗ | 2005 | 0.41 | 0.34 | 522 |

## Tiempo sostenible a velocidad alta

| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1126 | 44 | 123 | ∞ | 123 |
| 7 | design | sí | 1361 | 53 | 102 | ∞ | 102 |
| 8 | nominal | no (corriente de motor) | 1763 | 69 | 78 | 43 | 0 |
| 8 | design | no (corriente de motor, corriente de batería/ESC) | 2135 | 83 | 65 | 15 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2504 | 98 | 55 | 11 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3038 | 119 | 46 | 7 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3293 | 129 | 42 | 6 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 3997 | 156 | 35 | 5 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4084 | 160 | 34 | 5 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4957 | 194 | 28 | 3 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4854 | 190 | 28 | 4 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5889 | 230 | 23 | 3 | 0 |

## Sensibilidad

| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | Variación P | 
|---|---|---|---|---|
| Coef. de olas c_w (calibración) | ±30 % | 617 / 942 | 7.6 / 6.8 | 42 % |
| Pérdida por protector (0–25 %) | 0–0.25 | 673 / 990 | 7.4 / 6.7 | 41 % |
| Masa por persona | ±20 % | 650 / 906 | 7.5 / 6.9 | 33 % |
| Eslora de flotación | ±10 % | 911 / 671 | 6.9 / 7.4 | 31 % |
| Rendimiento de hélice (modelo) | ±10 % | 864 / 701 | 6.9 / 7.2 | 21 % |
| Masa del casco | ±30 % | 731 / 818 | 7.2 / 7.0 | 11 % |
| Ancho de espejo sumergido | ±20 % | 708 / 793 | 7.3 / 7.1 | 11 % |
| Ángulo de eje | ±20 % | 747 / 811 | 7.2 / 7.1 | 8 % |
| Resistencia del motor | ±30 % | 755 / 793 | 7.2 / 7.0 | 5 % |
