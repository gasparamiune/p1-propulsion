<!-- generado por sizing.py — no editar a mano -->

## Resumen

| Magnitud | Valor | Etiqueta |
|---|---|---|
| Masa total de diseño | 293 kg | [CALCULADO] |
| Carga útil vs placa de capacidad | 248 / 160 kg (155 %) | [CALCULADO] |
| Calado / francobordo | 198 / 182 mm | [CALCULADO] |
| Velocidad de casco (Fr_L=0.40) | 6.36 km/h | [CALCULADO] |
| Fr_L a velocidad de crucero | 0.376 | [CALCULADO] |
| R crucero (nominal / diseño) | 130 / 150 N | [CALCULADO] |
| Empuje en el eje en crucero (diseño) | 180 N | [CALCULADO] |
| Hélice | EO10x8 — modelo lineal aproximada [ESTIMADO] | [SUPUESTO] |
| rpm hélice / J / η0 crucero (diseño) | 948 rpm / 0.37 / 0.47 | [CALCULADO] |
| Potencia al eje crucero (diseño) | 564 W | [CALCULADO] |
| Potencia de batería crucero (nominal / diseño) | 580 / 697 W | [CALCULADO] |
| Rendimiento total batería→R·V (diseño) | 36 % | [CALCULADO] |
| Relación de correa | 15T : 44T = 2.93 | [CALCULADO] |
| Batería elegida | 2 × LiFePO4 12.8 V 100 Ah en serie (BMS 100 A c/u) | [CALCULADO] |
| Energía requerida / usable | 1859 / 2304 Wh | [CALCULADO] |
| Autonomía a crucero (nominal / diseño) | 3.98 / 3.31 h | [CALCULADO] |
| V máx. (diseño, batería baja) | 7.4 km/h — limita: tensión (duty), corriente de motor | [CALCULADO] |
| V máx. (nominal, batería nominal) | 7.9 km/h | [CALCULADO] |
| Bollard pull avante (horizontal) | 291 N (29.6 kgf) — limita: corriente de motor | [CALCULADO] |
| Bollard pull marcha atrás | 92 N | [CALCULADO] |
| Corriente pico de batería / margen ESC | 68 A / 46 % | [CALCULADO] |
| Cable DC / fases | 16 mm² (1.2 %) / 10 mm² (2.7 %) | [CALCULADO] |
| Fusible principal | 100 A | [CALCULADO] |
| Pasador de corte | Ø2.5 mm Al6061-T6 → corta a 16.3 N·m | [CALCULADO] |
| Velocidad crítica del eje / rpm máx. | 5692 / 1212 rpm | [CALCULADO] |
| Largo de eje / tubo | 1353 / 1185 mm | [CALCULADO] |

## Barrido de velocidad

| v [km/h] | Fr_L | R nom [N] | R diseño [N] | P_bat nom [W] | P_bat diseño [W] | rpm hélice | Autonomía nom [h] | Autonomía diseño [h] | Wh/km diseño |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.13 | 9 | 10 | 17 | 20 | 269 | 134.28 | 117.80 | 10 |
| 3 | 0.19 | 22 | 26 | 51 | 60 | 416 | 45.02 | 38.51 | 20 |
| 4 | 0.25 | 45 | 52 | 130 | 155 | 580 | 17.66 | 14.90 | 39 |
| 5 | 0.31 | 81 | 93 | 292 | 350 | 759 | 7.88 | 6.59 | 70 |
| 6 | 0.38 | 130 | 150 | 580 | 697 | 948 | 3.98 | 3.31 | 116 |
| 7 | 0.44 | 191 | 220 | 1018 | 1228 | 1137 | 2.26 | 1.88 | 175 |
| 8 | 0.50 | 258 | 297 | 1594 | 1929 ✗ | 1314 | 1.45 | 1.19 | 241 |
| 9 | 0.56 | 324 | 373 | 2264 | 2743 ✗ | 1474 | 1.02 | 0.84 | 305 |
| 10 | 0.63 | 385 | 443 | 2972 | 3603 ✗ | 1615 | 0.78 | 0.64 | 360 |
| 11 | 0.69 | 439 | 504 | 3677 | 4457 ✗ | 1739 | 0.63 | 0.52 | 405 |
| 12 | 0.75 | 485 | 558 | 4355 | 5277 ✗ | 1848 | 0.53 | 0.44 | 440 |
| 13 | 0.82 | 524 | 603 | 4997 | 6052 ✗ | 1945 | 0.46 | 0.38 | 466 |

## Tiempo sostenible a velocidad alta

| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1018 | 40 | 136 | ∞ | 136 |
| 7 | design | sí | 1228 | 48 | 113 | ∞ | 113 |
| 8 | nominal | no (corriente de motor) | 1594 | 62 | 87 | ∞ | 0 |
| 8 | design | no (corriente de motor) | 1929 | 75 | 72 | 19 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor) | 2264 | 88 | 61 | 13 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2743 | 107 | 50 | 8 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2972 | 116 | 47 | 7 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 3603 | 141 | 38 | 5 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 3677 | 144 | 38 | 5 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4457 | 174 | 31 | 4 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4355 | 170 | 32 | 4 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5277 | 206 | 26 | 3 | 0 |

## Sensibilidad

| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | Variación P | 
|---|---|---|---|---|
| Coef. de olas c_w (calibración) | ±30 % | 551 / 854 | 8.0 / 6.9 | 43 % |
| Masa por persona | ±20 % | 582 / 819 | 7.8 / 7.0 | 34 % |
| Eslora de flotación | ±10 % | 824 / 602 | 7.1 / 7.7 | 32 % |
| Rendimiento de hélice (modelo) | ±10 % | 778 / 631 | 7.1 / 7.5 | 21 % |
| Masa del casco | ±30 % | 657 / 738 | 7.6 / 7.3 | 12 % |
| Ancho de espejo sumergido | ±20 % | 636 / 714 | 7.6 / 7.4 | 11 % |
| Pérdida por protector | ±50 % | 669 / 728 | 7.5 / 7.3 | 9 % |
| Ángulo de eje | ±20 % | 673 / 730 | 7.5 / 7.3 | 8 % |
| Resistencia del motor | ±30 % | 680 / 714 | 7.4 / 7.3 | 5 % |
