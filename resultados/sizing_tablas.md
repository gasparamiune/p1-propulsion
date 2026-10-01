<!-- generado por sizing.py — no editar a mano -->

## Resumen

| Magnitud | Valor | Etiqueta |
|---|---|---|
| Masa total de diseño | 293 kg | [CALCULADO] |
| Carga útil vs placa de capacidad | 248 / 250 kg (99 %) | [CALCULADO] |
| Calado / francobordo | 198 / 182 mm | [CALCULADO] |
| Velocidad de casco (Fr_L=0.40) | 6.36 km/h | [CALCULADO] |
| Fr_L a velocidad de crucero | 0.376 | [CALCULADO] |
| R crucero (nominal / diseño) | 130 / 169 N | [CALCULADO] |
| Empuje en el eje en crucero (diseño) | 203 N | [CALCULADO] |
| Hélice | EO10x8 — modelo lineal aproximada [ESTIMADO] | [SUPUESTO] |
| rpm hélice / J / η0 crucero (diseño) | 991 rpm / 0.35 / 0.45 | [CALCULADO] |
| Potencia al eje crucero (diseño) | 664 W | [CALCULADO] |
| Potencia de batería crucero (nominal / diseño) | 578 / 819 W | [CALCULADO] |
| Rendimiento total batería→R·V (diseño) | 34 % | [CALCULADO] |
| Relación de correa | 16T : 48T = 3.00 | [CALCULADO] |
| Batería elegida | 2 × LiFePO4 12.8 V 100 Ah en serie (BMS 100 A c/u) | [CALCULADO] |
| Energía requerida / usable | 2184 / 2304 Wh | [CALCULADO] |
| Autonomía a crucero (nominal / diseño) | 3.98 / 2.81 h | [CALCULADO] |
| V máx. (diseño, batería baja) | 7.0 km/h — limita: tensión (duty) | [CALCULADO] |
| V máx. (nominal, batería nominal) | 8.0 km/h | [CALCULADO] |
| Bollard pull avante (horizontal) | 297 N (30.3 kgf) — limita: corriente de motor | [CALCULADO] |
| Bollard pull marcha atrás | 94 N | [CALCULADO] |
| Corriente pico de batería / margen ESC | 67 A / 50 % | [CALCULADO] |
| Cable DC / fases | 10 mm² (1.9 %) / 10 mm² (2.7 %) | [CALCULADO] |
| Fusible principal | 100 A | [CALCULADO] |
| Pasador de corte | Ø3.0 mm Al6061-T6 → corta a 23.4 N·m | [CALCULADO] |
| Velocidad crítica del eje / rpm máx. | 5936 / 1211 rpm | [CALCULADO] |
| Largo de eje / tubo | 1329 / 1161 mm | [CALCULADO] |

## Barrido de velocidad

| v [km/h] | Fr_L | R nom [N] | R diseño [N] | P_bat nom [W] | P_bat diseño [W] | rpm hélice | Autonomía nom [h] | Autonomía diseño [h] | Wh/km diseño |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.13 | 9 | 12 | 17 | 22 | 280 | 133.30 | 103.88 | 11 |
| 3 | 0.19 | 22 | 29 | 51 | 69 | 434 | 44.89 | 33.39 | 23 |
| 4 | 0.25 | 45 | 59 | 131 | 180 | 605 | 17.66 | 12.80 | 45 |
| 5 | 0.31 | 81 | 105 | 292 | 409 | 793 | 7.89 | 5.63 | 82 |
| 6 | 0.38 | 130 | 169 | 578 | 819 | 991 | 3.98 | 2.81 | 136 |
| 7 | 0.44 | 191 | 249 | 1014 | 1446 | 1189 | 2.27 | 1.59 | 207 |
| 8 | 0.50 | 258 | 335 | 1588 | 2275 ✗ | 1375 | 1.45 | 1.01 | 284 |
| 9 | 0.56 | 324 | 421 | 2254 | 3236 ✗ | 1543 | 1.02 | 0.71 | 360 |
| 10 | 0.63 | 385 | 500 | 2958 | 4251 ✗ | 1690 | 0.78 | 0.54 | 425 |
| 11 | 0.69 | 439 | 570 | 3657 | 5257 ✗ | 1818 | 0.63 | 0.44 | 478 |
| 12 | 0.75 | 485 | 630 | 4331 | 6221 ✗ | 1931 | 0.53 | 0.37 | 518 |
| 13 | 0.82 | 524 | 682 | 4969 | 7129 ✗ | 2031 | 0.46 | 0.32 | 548 |

## Tiempo sostenible a velocidad alta

| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1014 | 40 | 136 | ∞ | 136 |
| 7 | design | sí | 1446 | 56 | 96 | ∞ | 96 |
| 8 | nominal | no (corriente de motor) | 1588 | 62 | 87 | ∞ | 0 |
| 8 | design | no (tensión (duty), corriente de motor) | 2275 | 89 | 61 | 13 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor) | 2254 | 88 | 61 | 14 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3236 | 126 | 43 | 6 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2958 | 116 | 47 | 8 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4251 | 166 | 33 | 4 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 3657 | 143 | 38 | 6 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5257 | 205 | 26 | 3 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4331 | 169 | 32 | 4 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 6221 | 243 | 22 | 2 | 0 |

## Sensibilidad

| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | Variación P | 
|---|---|---|---|---|
| Coef. de olas c_w (calibración) | ±30 % | 646 / 1005 | 7.5 / 6.7 | 44 % |
| Masa por persona | ±20 % | 682 / 964 | 7.4 / 6.7 | 35 % |
| Eslora de flotación | ±10 % | 970 / 705 | 6.7 / 7.3 | 32 % |
| Rendimiento de hélice (modelo) | ±10 % | 915 / 741 | 6.8 / 7.1 | 21 % |
| Masa del casco | ±30 % | 772 / 867 | 7.1 / 6.9 | 12 % |
| Ancho de espejo sumergido | ±20 % | 746 / 840 | 7.2 / 7.0 | 11 % |
| Pérdida por protector | ±50 % | 785 / 855 | 7.1 / 7.0 | 9 % |
| Ángulo de eje | ±20 % | 790 / 859 | 7.1 / 7.0 | 8 % |
| Resistencia del motor | ±30 % | 799 / 839 | 7.1 / 6.9 | 5 % |
