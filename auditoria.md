# Auditoría adversarial (Pasada 3)

(Pendiente — se completa en la Pasada 3.)

## Hallazgos detectados durante las Pasadas 1–2 (ya corregidos)

| # | Hallazgo | Severidad | Resolución |
|---|---|---|---|
| A-01 | Eje Ø12: FS fatiga 1,1 y torsión en el pasador 1,3 | Alta | Eje Ø16 + polea entre rodamientos (D-07, D-08) |
| A-02 | Tubo inox 25×1,5 cede con el momento dinámico de impacto | Crítica | Tubo Al 40×3 (D-09) |
| A-03 | Caña colgando de la placa motriz de 7 mm (σ ≈ 200 MPa) | Crítica | Placa Al sobre la cuna (D-15) |
| A-04 | Fusible 100 A sobre cable de 10 mm² (75 A): no lo protegía (detectado por pytest) | Alta | Cable DC 16 mm² (D-21) |
| A-05 | Optimizador elegía 51,2 V (> 48 V) y luego una batería que no cumplía autonomía | Alta | Restricciones duras vs blandas (02 §4.1) |
| A-06 | Separadores del puente atravesaban la polea (plano de correa mal modelado) | Alta | Separadores fuera del lazo (verify lo detectó) |
| A-07 | Capacidad del bote supuesta 250 kg | Crítica (seguridad) | 160 kg estimado + advertencia + P0.2 (D-16) |
| A-08 | **Eje imposible de montar**: el muñón del rodamiento A (Ø15) estaba entre dos tramos Ø16 (verify no lo veía: no hay interferencia, es un problema de secuencia de montaje) | Crítica | Tramo Ø15 continuo + hombro Ø16, pila con separadores DRV-09/DRV-10 y tuerca; nueva cota automática "Ø máx. sobre el hombro ≤ Ø muñón" (D-07) |
| A-09 | Límite de Burrill 0,3σ^0,6 no conservador para σ > 0,6 (+15 % a +81 %) | Media | Curva de 5 % digitalizada por interpolación (research/R09 §3.2) + test |
| A-10 | Pasador de corte de Al sobre eje 316 en agua salobre: par galvánico → el pasador pierde sección y corta antes de tiempo | Alta | Pasador 316 Ø2 calibrado + ensayo P1.9 + cambio cada 10 h (D-11) |
| A-11 | Productos inexistentes en la selección: hélice 10×8 "objetivo", poleas de 44/60 T, correas sin stock, rodamientos 6002 inox, ánodo de collar Ø16 (research/R08b) | Alta | Optimizador restringido a productos/dientes/largos existentes (D-06, D-37, D-39); ánodo descartado con justificación (D-36) |
| A-12 | Largo de agarre del tubo en la cuna tomado como 90 mm en vez de 138 mm (FS de fatiga lateral subestimado) | Baja (conservador) | Corregido en `structural.py` |
| A-13 | Prensaestopas M20 especificados en una pared de 18 mm (rosca ~10–15 mm) y caja ESC sin lugar para el antichispa | Media | Rebaje a pared de 5 mm, caja 160×110×45, 10 cotas nuevas (D-20) |
| A-14 | Batería LiTime 24 V 50 Ah supuesta con BMS 100 A (real: 50 A) | Media | Catálogo con datos verificados (D-19) |
| A-15 | Con 1 persona el bote superaría el límite legal de 5 kn a < 300 m de la costa | Media (legal) | Tope de ERPM calculado (D-30) + ensayo T3 |
