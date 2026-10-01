# P1 — Propulsión eléctrica "cola larga" con piezas impresas para jon boat de aluminio

> Paquete de ingeniería del prototipo P1 (Sønderborg, Als Fjord). Todo se regenera desde
> [`inputs.yaml`](inputs.yaml) con `python run_all.py`. Los números de este README se
> actualizan automáticamente desde `resultados/*.json` (marcadores `<!--V:…-->`).

## Resumen ejecutivo

1. **Arquitectura:** cola larga (*long-tail*, tipo *mud motor*) eléctrica: motor BLDC **seco arriba del agua**, correa HTD-5M, eje inox 316 inclinado 25° dentro de un tubo de aluminio con bujes igus aptos bajo agua, hélice comprada de ~10" (trolling Minn Kota MKP-32; se mide antes de tornear) con pasador de corte, protector y patín fusible impresos, cardán (dirección + basculación con retén) sobre una abrazadera de popa impresa.
2. **Por qué:** cero sellos dinámicos y cero electrónica bajo el agua (agua salobre), basculación natural para arena y poca profundidad, todo reparable con herramienta común. Gana la matriz ponderada (03) con <!--V:arch.totals.A3:.2f-->4.25<!--/V--> / 5 frente a <!--V:arch.totals.F:.2f-->3.93<!--/V--> del motor comercial.
3. **Prestaciones calculadas (sin validar en agua):** crucero 6 km/h con <!--V:sizing.cruise.nominal.P_bat:.0f-->736<!--/V--> W de batería (banda nominal; <!--V:sizing.cruise.design.P_bat:.0f-->879<!--/V--> W en la banda alta de diseño) → **autonomía <!--V:sizing.cruise.autonomy_nominal_h:.1f-->3.1<!--/V--> h nominal / <!--V:sizing.cruise.autonomy_design_h:.1f-->2.6<!--/V--> h diseño** (requisito ≥ 2 h + 20 %).
4. **Velocidad máxima:** <!--V:sizing.vmax.nominal_vnom.V_kmh:.1f-->7.1<!--/V--> km/h con 2 personas (nominal); <!--V:sizing.legal_speed.vmax_full_load_with_cap_kmh:.1f-->7.1<!--/V--> km/h con el tope legal de rpm puesto. **Dentro de 300 m de la costa el límite legal es 5 kn = 9,26 km/h** (research/R07), así que 12 km/h no tiene uso legal; además no es alcanzable con 2 personas y ~1,5 kW (joroba de resistencia). Con 1 persona el bote sí pasaría 5 kn → el VESC lleva un tope de ERPM "modo costa" por defecto.
5. **Empuje a punto fijo:** <!--V:sizing.bollard_fwd.T_horiz:.0f-->253<!--/V--> N (≈ Torqeedo 1103 / ePropulsion 1.0 medidos: 290–310 N).
6. **Batería:** <!--V:sizing.selection.battery_desc:-->2 × Power Queen 12V 100Ah en serie (BMS 100 A c/u)<!--/V--> — 24 V, <!--V:sizing.battery.E_usable_wh:.0f-->2304<!--/V--> Wh usables.
7. **Costo total del sistema:** **<!--V:bom.total_eur:.0f-->2281<!--/V--> € ≈ <!--V:bom.total_dkk:.0f-->17052<!--/V--> DKK** con batería + cargador, IVA de importación, envíos e imprevistos 10 %; <!--V:bom.verified_frac_of_subtotal:.0%-->71%<!--/V--> del subtotal con precio verificado (2026-10-01, research/R08a). Equipo de seguridad para salir (chalecos, remos, ancla, luz): +<!--V:bom.operation_gear_eur:.0f-->270<!--/V--> € aparte.
8. **Riesgo n.º 1 (no es la propulsión):** la **capacidad del bote**. Un jon boat de ≤ 2,5 m carga ~100–185 kg según normas USCG/CE; 2 adultos + equipo + propulsión ≈ <!--V:sizing.masses.payload_kg:.0f-->248<!--/V--> kg = <!--V:sizing.masses.capacity_ratio:.0%-->155%<!--/V--> de la capacidad estimada. **Leer la placa / medir el bote antes de salir con 2 personas.**
9. **Honestidad:** todo está verificado *en software* (scripts, CAD sin interferencias, FS ≥ 3 calculados, tests). **Nada está probado físicamente**: faltan medidas del bote real, probetas, estanqueidad y pruebas en agua (ver [PENDIENTES_GASPAR.md](PENDIENTES_GASPAR.md)).

## Comparación honesta con comprar un motor

| Opción | Costo (con batería y cargador) | Energía | V máx con 2 p. | Basculación con protección | Marcha atrás | Comentario |
|---|---|---|---|---|---|---|
| **P1 cola larga (este proyecto)** | <!--V:bom.total_eur:.0f-->2281<!--/V--> € ≈ <!--V:bom.total_dkk:.0f-->17052<!--/V--> kr [CALCULADO: bom.py] | <!--V:sizing.battery.E_nom_wh:.0f-->2560<!--/V--> Wh | <!--V:sizing.vmax.design_vmin.V_kmh:.1f-->6.4<!--/V-->–<!--V:sizing.vmax.nominal_vnom.V_kmh:.1f-->7.1<!--/V--> km/h [CALCULADO] | Sí (retén + patín fusible + pasador de corte) | Sí | Motor seco, eje 316 sin ánodo (D-36); reparable, apto arena; ~<!--V:manifest.totals.printed_hours:.0f-->334<!--/V--> h de impresión + torno |
| Trolling de agua salada 55 lb + LiFePO4 12 V 100 Ah, tal cual | <!--V:cmp.F_eur:.0f-->1186<!--/V--> € ≈ <!--V:cmp.F_dkk:.0f-->8866<!--/V--> kr [CALCULADO: precios de research/R04 S42 y R08a] | 1 280 Wh | <!--V:cmp.trolling_vmax_kmh_min:.1f-->5.7<!--/V-->–<!--V:cmp.trolling_vmax_kmh_max:.1f-->6.2<!--/V--> km/h [CALCULADO: 620 W × η 0,30–0,40 ESTIMADO] | No (pata larga, sin protección ante golpes) | Sí | **La opción más barata** si basta ~6 km/h en agua profunda (plan B de 03 §4.2: <!--V:cmp.planB_eur_min:.0f-->1274<!--/V-->–<!--V:cmp.planB_eur_max:.0f-->1351<!--/V--> € con soporte basculante impreso) |
| Fueraborda eléctrico 1 kW (ePropulsion Spirit 1.0 Evo, completo) | <!--V:cmp.outboard_dk_dkk:.0f-->21886<!--/V--> kr ≈ <!--V:cmp.outboard_dk_eur:.0f-->2928<!--/V--> € en DK [VERIFICADO: research/R04 S32]; <!--V:cmp.outboard_de_eur:.0f-->2549<!--/V--> € en DE [VERIFICADO: research/R04 S33] | 1 276 Wh | <!--V:cmp.outboard_vmax_kmh_min:.1f-->7.6<!--/V-->–<!--V:cmp.outboard_vmax_kmh_max:.1f-->8.0<!--/V--> km/h [VERIFICADO: research/R04 §B.4, medido] | Sí | Sí | Producto terminado, IP67 y garantía; con la energía de P1 (2.ª batería) cuesta <!--V:cmp.outboard_2bat_eur:.0f-->4184<!--/V--> € |

**Veredicto honesto:** P1 cuesta **<!--V:cmp.ratio_p1_F:.1f-->1.9<!--/V-->× el trolling tal cual** y **<!--V:cmp.p1_below_outboard_dk_frac:.0%-->22%<!--/V--> menos que el fueraborda de 1 kW comprado en DK** (<!--V:cmp.p1_below_outboard_de_frac:.0%-->11%<!--/V--> menos que comprado en DE), sin contar la mano de obra [CALCULADO: resultados/comparacion.json]. Si el objetivo fuera solo "6 km/h al menor costo", **comprar el trolling (o el plan B) es más sensato**. El fueraborda es además más rápido. P1 se justifica por: <!--V:cmp.energy_ratio_p1_outboard:.1f-->2.0<!--/V-->× la energía del fueraborda por menos plata, basculación protegida en arena y aguas someras, marcha atrás, reparabilidad total con repuestos de skate eléctrico y el aprendizaje.

## Estado (verificado / no verificado)

| Ítem | Estado |
|---|---|
| Pipeline `run_all.py` (sizing → CAD → FS → planos → verify → BOM → docs → renders) | Ejecuta con exit 0 (ver bitácora en PROGRESS.md) |
| CAD: <!--V:manifest.totals.n_parts:d-->38<!--/V--> piezas, STEP + STL, manifold, envolvente ≤ 210×210×260 | [VERIFICADO en software] `verify_parts.py` |
| Interferencias, incluida basculación 0–25° × dirección ±35° | [VERIFICADO en software] <!--V:verify.n_pair_checks:d-->7846<!--/V--> pares×estados |
| FS ≥ 3 (impresas) / ≥ 2 (metal) por caso de carga | [CALCULADO] `structural.py` ([02_calculos.md](02_calculos.md) §9) — **depende de probetas** |
| R(v), potencia, autonomía | [CALCULADO + contrastado con datos medidos de botes análogos]; **calibrar con remolque** |
| Precios y links | Electrónica, batería, cargador y protecciones verificados (research/R08a, 2026-10-01); mecánica y equipo de seguridad [ESTIMADO] (ver `bom.csv`, columna etiqueta) |
| Normativa DK (velocidad, chalecos, luces, licencia) | [VERIFICADO: research/R07] — sin licencia ni matrícula (< 19 kW, < 2,5 m); 5 kn a < 300 m |
| Estanqueidad, probetas, pruebas en agua | **[NO EJECUTADO] — pendiente físico** |

## Cómo correr

```bash
pip install -r requirements.txt          # núcleo (build123d, numpy, trimesh, …)
# opcional FEA: sudo apt-get install libglu1-mesa   (gmsh lo necesita)
# opcional renders Blender: pip install -r requirements-render.txt
python run_all.py                        # todo; --fast = mallas gruesas; --skip-render
pytest -q                                # tests
```
Cambiar cualquier dato en `inputs.yaml` (p. ej. `boat.transom.thickness_range_mm`) y volver a correr regenera cálculos, geometría, planos, BOM y documentos (probado: [auditoria.md](auditoria.md) §Regeneración).

## Mapa del repositorio

| Archivo | Contenido |
|---|---|
| [01_investigacion.md](01_investigacion.md) | Videos, proyectos comparables, botes, materiales, sellado, BLDC, normativa DK (detalle en `research/`) |
| [02_calculos.md](02_calculos.md) + `sizing.py` | Resistencia, hélice, motor, batería, cables, térmico, mecánico, sensibilidad, criterios de éxito |
| [03_arquitectura.md](03_arquitectura.md) | Matriz ponderada + sensibilidad de pesos, plan B, imprimir/comprar/tornear, 5 riesgos |
| [04_diseno/](04_diseno/README.md) | `params.py`, `piezas/`, `build_all.py`, `verify_parts.py`, `structural.py`, STEP/STL, planos, electrónica |
| [05_fabricacion.md](05_fabricacion.md) + `prusaslicer/` | Probetas, perfiles, orientación, post-proceso |
| [06_ensamblaje_y_pruebas.md](06_ensamblaje_y_pruebas.md) + [checklist_salida.md](checklist_salida.md) | Montaje, sellado, aislamiento galvánico, pruebas T0–T4, FMEA |
| [07_roadmap_P2.md](07_roadmap_P2.md) | Próxima iteración |
| [decisiones.md](decisiones.md) · [auditoria.md](auditoria.md) · [PENDIENTES_GASPAR.md](PENDIENTES_GASPAR.md) | Decisiones, auditoría adversarial, acciones físicas |

## Próximos pasos físicos (los 5 primeros)

1. **Medir el bote real** (eslora, flotación, manga, fondo, puntal, espejo alto/espesor/material, peso, placa de capacidad) → actualizar `inputs.yaml` → `python run_all.py`.
2. **Ensayo de remolque con dinamómetro** a 3–4 velocidades con la carga real → calibrar `resistance.wave_cw` antes de comprar la batería.
3. **Imprimir y ensayar probetas** (holguras, tuercas cautivas, caja con O-ring 24 h, absorción 7 días) → confirmar factores de material.
4. Comprar motor/ESC y armar el **banco en seco T0** (kill switch, rampas, marcha atrás, corte < 1 s).
5. **T1–T2**: estanqueidad y tanque/muelle (bollard pull con el dinamómetro, temperaturas) antes de cualquier salida.
