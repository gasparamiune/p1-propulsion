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
| Potencia de batería crucero (nominal / diseño) | 661 / 798 W | [CALCULADO] |
| Rendimiento total batería→R·V (diseño) | 33 % | [CALCULADO] |
| Relación de correa | 15T : 44T = 2.93 | [CALCULADO] |
| Batería elegida | 2 × Power Queen 12V 100Ah en serie (BMS 100 A c/u) | [CALCULADO] |
| Energía requerida / usable | 2127 / 2304 Wh | [CALCULADO] |
| Autonomía a crucero (nominal / diseño) | 3.49 / 2.89 h | [CALCULADO] |
| V máx. (diseño, batería baja) | 7.1 km/h — limita: tensión (duty) | [CALCULADO] |
| V máx. (nominal, batería nominal) | 7.6 km/h | [CALCULADO] |
| Bollard pull avante (horizontal) | 291 N (29.6 kgf) — limita: corriente de motor | [CALCULADO] |
| Bollard pull marcha atrás | 92 N | [CALCULADO] |
| Corriente pico de batería / margen ESC | 66 A / 52 % | [CALCULADO] |
| Cable DC / fases | 16 mm² (1.2 %) / 10 mm² (2.7 %) | [CALCULADO] |
| Fusible principal | 100 A | [CALCULADO] |
| Pasador de corte | Ø2.5 mm Al6061-T6 → corta a 16.3 N·m | [CALCULADO] |
| Velocidad crítica del eje / rpm máx. | 5763 / 1203 rpm | [CALCULADO] |
| Largo de eje / tubo | 1352 / 1178 mm | [CALCULADO] |

## Barrido de velocidad

| v [km/h] | Fr_L | R nom [N] | R diseño [N] | P_bat nom [W] | P_bat diseño [W] | rpm hélice | Autonomía nom [h] | Autonomía diseño [h] | Wh/km diseño |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.13 | 10 | 11 | 19 | 22 | 279 | 120.89 | 105.54 | 11 |
| 3 | 0.19 | 24 | 27 | 58 | 68 | 430 | 39.91 | 34.01 | 23 |
| 4 | 0.25 | 48 | 55 | 148 | 176 | 598 | 15.57 | 13.09 | 44 |
| 5 | 0.31 | 84 | 97 | 333 | 399 | 782 | 6.93 | 5.77 | 80 |
| 6 | 0.38 | 135 | 156 | 661 | 798 | 976 | 3.49 | 2.89 | 133 |
| 7 | 0.44 | 198 | 228 | 1164 | 1411 | 1170 | 1.98 | 1.63 | 202 |
| 8 | 0.50 | 267 | 307 | 1832 | 2225 ✗ | 1352 | 1.26 | 1.04 | 278 |
| 9 | 0.56 | 335 | 385 | 2613 | 3180 ✗ | 1517 | 0.88 | 0.72 | 353 |
| 10 | 0.63 | 398 | 458 | 3447 | 4198 ✗ | 1662 | 0.67 | 0.55 | 420 |
| 11 | 0.69 | 455 | 523 | 4286 | 5220 ✗ | 1790 | 0.54 | 0.44 | 475 |
| 12 | 0.75 | 505 | 580 | 5102 | 6213 ✗ | 1903 | 0.45 | 0.37 | 518 |
| 13 | 0.82 | 548 | 630 | 5886 | 7165 ✗ | 2005 | 0.39 | 0.32 | 551 |

## Tiempo sostenible a velocidad alta

| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1164 | 45 | 119 | ∞ | 119 |
| 7 | design | sí | 1411 | 55 | 98 | 47 | 47 |
| 8 | nominal | no (corriente de motor) | 1832 | 72 | 75 | 14 | 0 |
| 8 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2225 | 87 | 62 | 9 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2613 | 102 | 53 | 7 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3180 | 124 | 43 | 5 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3447 | 135 | 40 | 4 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 4198 | 164 | 33 | 3 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 4286 | 167 | 32 | 3 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5220 | 204 | 26 | 2 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5102 | 199 | 27 | 3 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 6213 | 243 | 22 | 2 | 0 |

## Sensibilidad

| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | Variación P | 
|---|---|---|---|---|
| Coef. de olas c_w (calibración) | ±30 % | 634 / 974 | 7.6 / 6.7 | 43 % |
| Pérdida por protector (0–25 %) | 0–0.25 | 692 / 1024 | 7.3 / 6.6 | 42 % |
| Masa por persona | ±20 % | 668 / 936 | 7.4 / 6.8 | 34 % |
| Eslora de flotación | ±10 % | 941 / 690 | 6.8 / 7.3 | 31 % |
| Rendimiento de hélice (modelo) | ±10 % | 894 / 721 | 6.9 / 7.1 | 22 % |
| Masa del casco | ±30 % | 753 / 843 | 7.2 / 7.0 | 11 % |
| Ancho de espejo sumergido | ±20 % | 729 / 817 | 7.2 / 7.0 | 11 % |
| Ángulo de eje | ±20 % | 769 / 837 | 7.1 / 7.0 | 8 % |
| Resistencia del motor | ±30 % | 772 / 824 | 7.2 / 6.9 | 7 % |
