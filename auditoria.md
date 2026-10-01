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
