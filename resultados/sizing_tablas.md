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
| Potencia de batería crucero (nominal / diseño) | 736 / 879 W | [CALCULADO] |
| Rendimiento total batería→R·V (diseño) | 30 % | [CALCULADO] |
| Relación de correa | 20T : 48T = 2.40 | [CALCULADO] |
| Batería elegida | 2 × Power Queen 12V 100Ah en serie (BMS 100 A c/u) | [CALCULADO] |
| Energía nominal requerida (2 h + reserva ÷ DoD) / nominal de la batería | 2343 / 2560 Wh | [CALCULADO] |
| Autonomía a crucero (nominal / diseño) | 3.13 / 2.62 h | [CALCULADO] |
| V máx. (diseño, batería baja) | 6.4 km/h — limita: tensión (duty) | [CALCULADO] |
| V máx. (nominal, batería nominal) | 7.1 km/h | [CALCULADO] |
| Bollard pull avante (horizontal) | 253 N (25.8 kgf) — limita: corriente de motor | [CALCULADO] |
| Bollard pull marcha atrás | 80 N | [CALCULADO] |
| Corriente pico de batería / margen ESC | 53 A / 67 % | [CALCULADO] |
| Cable DC / fases | 16 mm² (0.9 %) / 10 mm² (2.1 %) | [CALCULADO] |
| Fusible principal | 80 A | [CALCULADO] |
| Pasador de corte | Ø2.0 mm AISI 316 → corta a 12.4 N·m | [CALCULADO] |
| Velocidad crítica del eje / rpm máx. | 5834 / 1713 rpm | [CALCULADO] |
| Largo de eje / tubo | 1357 / 1171 mm | [CALCULADO] |

## Barrido de velocidad

| v [km/h] | Fr_L | R nom [N] | R diseño [N] | P_bat nom [W] | P_bat diseño [W] | rpm hélice | Autonomía nom [h] | Autonomía diseño [h] | Wh/km diseño |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.13 | 10 | 11 | 23 | 26 | 435 | 100.67 | 89.09 | 13 |
| 3 | 0.19 | 24 | 27 | 68 | 78 | 669 | 34.13 | 29.46 | 26 |
| 4 | 0.25 | 48 | 55 | 170 | 199 | 924 | 13.59 | 11.56 | 50 |
| 5 | 0.31 | 84 | 97 | 375 | 445 | 1201 | 6.14 | 5.18 | 89 |
| 6 | 0.38 | 135 | 156 | 736 | 879 | 1491 | 3.13 | 2.62 | 146 |
| 7 | 0.44 | 198 | 228 | 1285 | 1541 ✗ | 1781 | 1.79 | 1.49 | 220 |
| 8 | 0.50 | 267 | 307 | 2012 | 2420 ✗ | 2055 | 1.15 | 0.95 | 302 |
| 9 | 0.56 | 335 | 385 | 2865 | 3451 ✗ | 2307 | 0.80 | 0.67 | 383 |
| 10 | 0.63 | 398 | 458 | 3783 | 4559 ✗ | 2533 | 0.61 | 0.51 | 456 |
| 11 | 0.69 | 455 | 523 | 4715 | 5682 ✗ | 2735 | 0.49 | 0.41 | 517 |
| 12 | 0.75 | 505 | 580 | 5636 | 6787 ✗ | 2917 | 0.41 | 0.34 | 566 |
| 13 | 0.82 | 548 | 630 | 6533 | 7861 ✗ | 3085 | 0.35 | 0.29 | 605 |

## Tiempo sostenible a velocidad alta

| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1285 | 50 | 108 | 2 | 2 |
| 7 | design | no (tensión (duty)) | 1541 | 60 | 90 | 1 | 0 |
| 8 | nominal | no (tensión (duty), corriente de motor) | 2012 | 79 | 69 | 1 | 0 |
| 8 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2420 | 95 | 57 | 1 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2865 | 112 | 48 | 0 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3451 | 135 | 40 | 0 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3783 | 148 | 37 | 0 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4559 | 178 | 30 | 0 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4715 | 184 | 29 | 0 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5682 | 222 | 24 | 0 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5636 | 220 | 25 | 0 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 6787 | 265 | 20 | 0 | 0 |

## Sensibilidad

| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | T motor crucero (−/+) [°C] | Variación P | 
|---|---|---|---|---|---|
| Coef. de olas c_w (calibración) | ±30 % | 708 / 1061 | 6.8 / 6.1 | 69 / 92 ⚠ | 40 % |
| Pérdida por protector (0–25 %) | 0–0.25 | 768 / 1113 | 6.6 / 6.1 | 73 / 95 ⚠ | 39 % |
| Masa por persona | ±20 % | 743 / 1022 | 6.7 / 6.2 | 71 / 89 ⚠ | 32 % |
| Eslora de flotación | ±10 % | 1027 / 767 | 6.2 / 6.6 | 90 / 73 ⚠ | 30 % |
| Rendimiento de hélice (modelo) | ±10 % | 983 / 795 | 6.4 / 6.5 | 88 / 74 ⚠ | 21 % |
| Masa del casco | ±30 % | 832 / 926 | 6.5 / 6.3 | 77 / 83 | 11 % |
| Ancho de espejo sumergido | ±20 % | 807 / 899 | 6.6 / 6.4 | 75 / 81 | 10 % |
| Ángulo de eje | ±20 % | 853 / 913 | 6.4 / 6.4 | 78 / 83 | 7 % |
| Resistencia del motor | ±30 % | 853 / 904 | 6.6 / 6.3 | 69 / 91 ⚠ | 6 % |
| Diámetro de hélice (medir) | ±5 % | 892 / 869 | 6.2 / 6.6 | 79 / 81 | 3 % |
| Paso de hélice (medir) | ±10 % | 884 / 878 | 6.1 / 6.7 | 77 / 83 | 1 % |
| R_th del motor (térmico) | ±20 % | 879 / 879 | 6.4 / 6.4 | 70 / 90 ⚠ | 0 % |
| Temperatura del aire (20–35 °C) | 20–35 | 879 / 879 | 6.4 / 6.4 | 70 / 85 | 0 % |
