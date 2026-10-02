# 05 — Fabricación del waterjet P1-J: qué se hace cómo, impresión, mecanizado, soldadura, CNC, anodizado y ensayos

**Estado:** verificado *en software* — rutas de fabricación cruzadas entre `resultados/manifest.json` y `bom.csv`, CAD de probetas cerrado y dentro de la envolvente (`build_probetas.py`), perfiles cargados y laminados con PrusaSlicer 2.7.2 CLI (`validar_perfiles.py` → `prusaslicer/slice_report.json`), criterios de ensayo leídos de `sizing.json` / `estructural.json`, `tests/test_probetas.py`. **Nada está impreso, torneado, soldado ni ensayado: todo lo físico es [NO EJECUTADO] — pendiente de taller.**

Las tablas entre `<!-- FAB:… -->` las genera `04_diseno/probetas/tabla_fabricacion.py` (lo llama `build_probetas.py`, paso 6e de `run_all.py`) desde `resultados/manifest.json`, `bom.csv`, `resultados/sizing.json`, `resultados/estructural.json`, `inputs.yaml`, `04_diseno/probetas/probetas_manifest.json`, `prusaslicer/slice_report.json` y el código de `04_diseno/piezas/`: **no editarlas a mano**. Los números sueltos del texto van con marcadores `<!--V:…-->` (los refresca `docgen.py`).

Fuentes: research/R05 (PETG, sellado, insertos), R06 §6 y R10b H21 (galvánica), R08b §6 (Tef-Gel, arandelas aislantes), R11 §6 (CNC 5 ejes y SLM 316L), R12 §3 (holgura de punta), §7.2 (presiones) y §7.6 (pasador de corte).

---

## 0. Resumen

- **El jet es casi todo metal.** De <!--V:manifest.totals.n_parts:-->65<!--/V--> tipos de pieza, solo cinco son impresas en PETG (tapa de inspección P1-INT-04, base y capota del controlador P1-ELE-01/02, caja de palancas P1-CTL-02, soporte del kill switch P1-CTL-03): <!--V:manifest.totals.printed_mass_g:.0f-->1051<!--/V--> g y <!--V:manifest.totals.printed_hours:.0f-->58<!--/V--> h según el manifest (PrusaSlicer da más: §2.6). El resto es Al 5083 cortado a láser y soldado (toma, bucket, placas), Al 6061/6082 y AISI 316L torneado, y **CNC 5 ejes** para impulsor (316L) y estator (6061-T6).
- **Servicios de fabricación** en la BOM: <!--V:bom.services_eur:.0f-->4040<!--/V--> € (CNC, torneado grande, láser, soldadura, anodizado); materia prima para el torno propio y el taller: <!--V:bom.raw_material_eur:.0f-->1339<!--/V--> €.
- **Torno propio** hasta el Ø que supone la BOM (`inputs.yaml bom.lathe_max_d_mm`, [SUPUESTO]: **medir**); carcasa y tobera fija lo superan y van a taller (§3).
- **Ensayos:** 4 probetas impresas (P1.1 holguras, P1.4 inserto M5, P1.6 tapa con O-ring y purga a la presión de cierre, P1.7 absorción) y 4 ensayos de taller sin CAD (P1.9 juego de semipasadores de corte, P1.10 bujes POM en agua, P1.11 hidrostática de la bomba, P1.12 holgura de punta), todos con criterio numérico tomado de los JSON (§7).
- **Hallazgos para el diseño:** §10.

---

## 1. Qué se fabrica cómo

Una fila por pieza del manifest; la ruta se deduce de los servicios `S-*` que la cubren en `bom.csv` (columna `cubre`) y de la materia prima `MP-*` que la nombra. Es un bloque **nuevo**, `FAB:procesos`, y no `AUTO:parts_list` de `docgen.py`: ese bloque solo trae el proceso del manifest, donde «torneada» agrupa torno, fresa, láser y soldadura.

<!-- FAB:procesos -->
| ID | Pieza | Material | Cant. | Proceso (manifest) | Ruta de fabricación | Servicio (bom.csv) | Materia prima (bom.csv) | g c/u (CAD) | Plano |
|---|---|---|---|---|---|---|---|---|---|
| P1-BAT-01 | bateria | referencia | 2 | comprada | Comprada (B-BAT) | — | — | 19 800 | — |
| P1-CTL-01 | placa_espejo | Al 5083 | 1 | torneada | corte láser/agua → taladrado/plegado propio | S-LASER | MP-5083-T6 | 476 | `P1-CTL-01_placa_espejo.svg` |
| P1-CTL-02 | caja_acel | PETG | 1 | impresa | Impresa PETG — perfil **cubiertas** (§2) | — | — | 134 | — |
| P1-CTL-03 | soporte_kill | PETG | 1 | impresa | Impresa PETG — perfil **estructural** (§2) | — | — | 120 | — |
| P1-CTL-04 | pasamuros_m66 | AISI 316 | 1 | torneada | torno propio | — | MP-316-D35 | 128 | `P1-CTL-04_pasamuros_m66.svg` |
| P1-CTL-05 | prensaestopas | referencia | 2 | comprada | Comprada (B-GLAND16, B-GLAND20) | — | — | 15 | — |
| P1-CTL-06 | terminal_m66 | Acero | 1 | comprada | Comprada (B-M66) | — | — | 350 | — |
| P1-CTL-07 | terminal_mach5_consola | Acero | 1 | comprada | Comprada (B-MACH5) | — | — | 120 | — |
| P1-CTL-08 | placa_central | Al 5083 | 1 | torneada | corte láser/agua → soldadura TIG (taller) | S-LASER, S-WELD-AL | MP-5083-T6 | 219 | `P1-CTL-08_placa_central.svg` |
| P1-CTL-09 | palanca_acel | Al 6061-T6 | 1 | torneada | corte láser/agua → taladrado/plegado propio | S-LASER | MP-6061-T8 | 102 | `P1-CTL-09_palanca_acel.svg` |
| P1-CTL-10 | palanca_bucket | Al 6061-T6 | 1 | torneada | corte láser/agua → soldadura TIG (taller) | S-LASER, S-WELD-AL | MP-6061-T8 | 116 | `P1-CTL-10_palanca_bucket.svg` |
| P1-CTL-11 | eje_palancas | AISI 316 | 1 | torneada | torno propio | — | MP-316-D20 | 39 | `P1-CTL-11_eje_palancas.svg` |
| P1-CTL-12 | perno_enclav | AISI 316 | 2 | torneada | torno propio | — | MP-316-D8 | 3 | `P1-CTL-12_perno_enclav.svg` |
| P1-CTL-13 | varilla_consola | AISI 316 | 1 | comprada | Comprada (B-ROD5) | — | — | 40 | — |
| P1-CTL-14 | gatillo | Al 6061-T6 | 1 | torneada | corte láser/agua → taladrado/plegado propio | S-LASER | MP-6061-T6 | 6 | `P1-CTL-14_gatillo.svg` |
| P1-CTL-20 | consola_ref | referencia | 1 | referencia | Referencia (no se fabrica: casco, consola, volante) | — | — | 0 | — |
| P1-CTL-21 | volante_ref | referencia | 1 | referencia | Referencia (no se fabrica: casco, consola, volante) | — | — | 0 | — |
| P1-DRV-01 | shaft | AISI 316 | 1 | torneada | torno propio | — | MP-316-D28 | 1 181 | `P1-DRV-01_shaft.svg` |
| P1-DRV-02 | seal_housing | AISI 316 | 1 | torneada | torno propio | — | MP-316-D75 | 311 | `P1-DRV-02_seal_housing.svg` |
| P1-DRV-03 | bearing_bracket | Al 5052/6082 | 1 | torneada | corte láser/agua → soldadura TIG (taller) | S-LASER, S-WELD-AL | MP-6082-T12 | 1 642 | `P1-DRV-03_bearing_bracket.svg` |
| P1-DRV-04 | bearing_7204BEP | Acero | 2 | comprada | Comprada (B-BRG) | — | — | 110 | — |
| P1-DRV-05 | locknut_KM4 | Acero | 1 | comprada | Comprada (B-KM4) | — | — | 25 | — |
| P1-DRV-06 | bearing_cover | Al 5052/6082 | 1 | torneada | torno propio | — | MP-6082-D70 | 44 | `P1-DRV-06_bearing_cover.svg` |
| P1-DRV-07 | mech_seal_MG1_20 | referencia | 1 | comprada | Comprada (B-SEAL) | — | — | 60 | — |
| P1-DRV-08 | coupling_rotex24 | referencia | 1 | comprada | Comprada (B-CPL) | — | — | 600 | — |
| P1-ELE-01 | esc_stand | PETG | 1 | impresa | Impresa PETG — perfil **cubiertas** (§2) | — | — | 263 | — |
| P1-ELE-02 | esc_hood | PETG | 1 | impresa | Impresa PETG — perfil **cubiertas** (§2) | — | — | 207 | — |
| P1-ELE-03 | cooling_outlet | AISI 316 | 1 | comprada | Comprada (B-COOL-THRU) | — | — | 45 | — |
| P1-ELE-04 | esc | referencia | 1 | comprada | Comprada (B-ESC) | — | — | 2 000 | — |
| P1-INT-01 | conducto | Al 5083 | 1 | torneada | corte láser/agua → soldadura TIG (taller) | S-LASER, S-WELD-INT | MP-5083-T5 | 4 699 | `P1-INT-01_conducto.svg` |
| P1-INT-02 | placa_base | Al 5083 | 1 | torneada | corte láser/agua → soldadura TIG (taller) | S-LASER, S-WELD-INT | MP-5083-T10 | 3 042 | `P1-INT-02_placa_base.svg` |
| P1-INT-03 | rejilla | AISI 316 | 1 | torneada | corte láser/agua → soldadura TIG (taller) | S-LASER, S-WELD-316 | MP-316-T4 | 2 014 | `P1-INT-03_rejilla.svg` |
| P1-INT-04 | tapa_inspeccion | PETG | 1 | impresa | Impresa PETG — perfil **sellado** (§2) | — | — | 327 | — |
| P1-MOT-01 | motor | referencia | 1 | comprada | Comprada (B-MOT) | — | — | 4 400 | — |
| P1-MOT-02 | motor_mount | Al 5052/6082 | 1 | torneada | corte láser/agua → soldadura TIG (taller) | S-LASER, S-WELD-AL | MP-6082-T10 | 842 | `P1-MOT-02_motor_mount.svg` |
| P1-PMP-01 | housing | Al 6061-T6 | 1 | torneada | torno de taller → anodizado duro | S-TURN-HSG, S-ANOD | MP-6061-TUBO-P1-PMP-01 | 1 492 | `P1-PMP-01_housing.svg` |
| P1-PMP-02 | wear_ring | AISI 316 | 1 | torneada | torno propio | — | MP-316-TUBO-P1-PMP-02 | 1 187 | `P1-PMP-02_wear_ring.svg` |
| P1-PMP-03 | impeller | AISI 316 | 1 | torneada | CNC 5 ejes (taller) | S-CNC-IMP | — | 1 336 | `P1-PMP-03_impeller_hub.svg`, `P1-PMP-03_tabla_angulos_alabes.svg` |
| P1-PMP-04 | pin_band | AISI 316 | 1 | torneada | torno propio | — | MP-316-D70 | 76 | `P1-PMP-04_pin_band.svg` |
| P1-PMP-05 | shear_pin | Al 6061-T6 | 2 | torneada | torno propio | — | MP-6061-D4 | 1 | `P1-PMP-05_shear_pin.svg` |
| P1-PMP-06 | stator | Al 6061-T6 | 1 | torneada | CNC 5 ejes (taller) → anodizado duro | S-CNC-STAT, S-ANOD | — | 1 518 | `P1-PMP-06_stator.svg` |
| P1-PMP-07 | water_bushing | POM-C | 1 | torneada | torno propio | — | MP-POM-D30 | 12 | `P1-PMP-07_water_bushing.svg` |
| P1-PMP-08 | fixed_nozzle | Al 6061-T6 | 1 | torneada | torno de taller → anodizado duro | S-TURN-NOZ, S-ANOD | MP-6061-TUBO-P1-PMP-08 | 1 408 | `P1-PMP-08_fixed_nozzle.svg` |
| P1-PMP-09 | transom_plate | Al 5083 | 1 | torneada | torno de taller | S-TURN-TP | MP-5083-BLQ-P1-PMP-09 | 449 | `P1-PMP-09_transom_plate.svg` |
| P1-PMP-10 | transom_gasket | NBR | 1 | comprada | Comprada (B-GASKET) | — | — | 35 | — |
| P1-PMP-11 | pivot_bushing | POM-C | 2 | torneada | torno propio | — | MP-POM-D14 | 2 | `P1-PMP-11_pivot_bushing.svg` |
| P1-REF-01 | casco | referencia | 1 | referencia | Referencia (no se fabrica: casco, consola, volante) | — | — | 0 | — |
| P1-REV-01 | bucket | Al 5083 | 1 | torneada | corte láser/agua → soldadura TIG (taller) | S-LASER, S-WELD-AL | MP-5083-T6 | 866 | `P1-REV-01_bucket_brazo_babor.svg`, `P1-REV-01_bucket_brazo_estribor.svg`, `P1-REV-01_bucket_cuchara.svg` |
| P1-REV-02 | perno_bucket | AISI 316 | 2 | torneada | torno propio | — | MP-316-D28 | 105 | `P1-REV-02_espaciador_pivote_bucket.svg` |
| P1-REV-03 | buje_bucket | POM-C | 2 | torneada | torno propio | — | MP-POM-D30 | 3 | `P1-REV-03_buje_bucket.svg` |
| P1-REV-04 | embolo | AISI 316 | 2 | comprada | Comprada (B-INDEX) | — | — | 160 | — |
| P1-REV-05 | soporte_mach5 | Al 5083 | 1 | torneada | corte láser/agua → soldadura TIG (taller) | S-LASER, S-WELD-AL | MP-5083-T6 | 188 | `P1-REV-05_soporte_mach5.svg` |
| P1-REV-06 | perno_varilla | AISI 316 | 1 | torneada | torno propio | — | MP-316-D16 | 10 | `P1-REV-06_perno_varilla.svg` |
| P1-REV-07 | terminal_mach5 | Acero | 1 | comprada | Comprada (B-MACH5) | — | — | 120 | — |
| P1-REV-08 | varilla_mach5 | AISI 316 | 1 | comprada | Comprada (B-ROD5) | — | — | 40 | — |
| P1-REV-09 | soporte_bowden | Al 5083 | 2 | torneada | corte láser/agua → taladrado/plegado propio | S-LASER | MP-5083-T4 | 13 | `P1-REV-09_soporte_bowden.svg` |
| P1-REV-10 | bowden_embolo | AISI 316 | 2 | comprada | Comprada (B-BOWDEN) | — | — | 60 | — |
| P1-STE-01 | boquilla | Al 6061-T6 | 1 | torneada | torno + fresado 4 ejes (taller) → anodizado duro | S-MILL-STE, S-ANOD | MP-6061-BLQ-P1-STE-01 | 890 | `P1-STE-01_boquilla.svg` |
| P1-STE-02 | perno_sup | AISI 316 | 1 | torneada | torno propio | — | MP-316-D16 | 20 | `P1-STE-02_perno_sup.svg` |
| P1-STE-03 | arandela_pom | POM-C | 3 | torneada | torno propio | — | MP-POM-D20 | 0 | `P1-STE-03_arandela_pom.svg` |
| P1-STE-04 | brida_yugo | Al 5083 | 1 | torneada | corte láser/agua → taladrado/plegado propio | S-LASER | MP-5083-T20 | 159 | `P1-STE-04_brida_yugo.svg` |
| P1-STE-05 | perno_inf | AISI 316 | 1 | torneada | torno propio | — | MP-316-D10 | 11 | `P1-STE-05_perno_inf.svg` |
| P1-STE-06 | poste | Al 6061-T6 | 1 | torneada | torno propio → anodizado duro | S-ANOD | MP-6061-D50 | 151 | `P1-STE-06_poste.svg` |
| P1-STE-07 | brazo | Al 5083 | 1 | torneada | corte láser/agua → taladrado/plegado propio | S-LASER | MP-5083-T10 | 34 | `P1-STE-07_brazo.svg` |
| P1-STE-08 | tope_direccion | Al 5083 | 1 | torneada | corte láser/agua → taladrado/plegado propio | S-LASER | MP-5083-BLQ-P1-STE-08 | 79 | `P1-STE-08_tope_direccion.svg` |

Piezas por proceso del manifest: comprada **17**, impresa **5**, referencia **3**, torneada **40** (65 tipos). «torneada» en el manifest = toda pieza mecanizada (torno, fresa, láser, soldada).
<!-- /FAB:procesos -->

---

## 2. Impresión 3D (PETG)

### 2.1 Material, secado y almacenamiento

| Paso | Valor | Etiqueta |
|---|---|---|
| Compra | PETG 1,75 mm con **HDT(1,8 MPa) ≥ 70 °C declarada** (PolyLite 75 °C; Prusament y Bambu 68 °C no llegan) | [VERIFICADO: research/R05 A1, S1–S3; inputs.yaml materials.PETG.hdt_min_purchase_c] |
| Temperatura de servicio | ≤ 50 °C en la pieza: controlador y consola al sol, lejos del motor | [ESTIMADO: inputs.yaml materials.PETG.t_service_max_c] |
| Color | Blanco, gris claro o natural (consola al sol) | [ESTIMADO: research/R05 A4] |
| Secado | **65 °C × 6–8 h**; 8 h si la bobina estuvo abierta | [VERIFICADO: S2 "65°C/6H"; S3 "Blast Drying Oven: 65 °C, 8 h"] |
| Almacenamiento | Caja estanca con desecante, **HR < 20 %**; la tapa P1-INT-04 (la impresión más larga) se imprime **desde la caja seca** | [VERIFICADO: S3] |
| Piezas impresas | **No** recocer ni secar a 60–70 °C: deforman | [VERIFICADO: S3] |

### 2.2 Perfiles PrusaSlicer (`prusaslicer/`)

Tres familias sobre impresora y filamento comunes (`P1_impresora_Ender3S1.ini`, `P1_filamento_PETG.ini`); la familia de cada pieza está en `04_diseno/probetas/familias.py` y cada probeta se imprime con la de la pieza que representa. Uso CLI: `prusa-slicer --load P1_impresora_Ender3S1.ini --load P1_filamento_PETG.ini --load P1_impresion_sellado_0.15.ini --export-gcode pieza.stl`; en la GUI, importar `completo/P1_<familia>_completo.ini` (guardado por el propio PrusaSlicer). El perfil «fusible» del diseño anterior (patín) se eliminó: ninguna pieza impresa del jet es fusible (el fusible de par es el pasador de Al, P1.9).

<!-- FAB:perfiles -->
| Parámetro (print) | estructural (`P1_impresion_estructural_0.20.ini`) | sellado (`P1_impresion_sellado_0.15.ini`) | cubiertas (`P1_impresion_cubiertas_0.20.ini`) |
|---|---|---|---|
| **piezas** | P1-CTL-03 | P1-INT-04 | P1-CTL-02, P1-ELE-01, P1-ELE-02 |
| capa [mm] | 0.2 | 0.15 | 0.2 |
| 1.ª capa [mm] | 0.2 | 0.2 | 0.2 |
| perímetros | 6 | 5 | 5 |
| generador de perímetros | arachne | arachne | arachne |
| capas sólidas arriba | 6 | 8 | 5 |
| capas sólidas abajo | 5 | 7 | 4 |
| relleno base | 85% | 100% | 30% |
| patrón | gyroid | rectilinear | gyroid |
| ángulo de relleno [°] | 45 | 45 | 45 |
| solape relleno–perímetro | 25% | 30% | 25% |
| costura | aligned | rear | aligned |
| costuras internas escalonadas | 1 | 1 | 0 |
| planchado | 0 | 1 | 0 |
| v perímetro externo [mm/s] | 25 | 20 | 30 |
| v perímetros [mm/s] | 40 | 30 | 45 |
| v relleno [mm/s] | 60 | 45 | 70 |
| v relleno sólido [mm/s] | 40 | 35 | 50 |
| soportes (por defecto) | 0 | 0 | 0 |
| compensación pata de elefante [mm] | 0.2 | 0.2 | 0.2 |

| Archivo | Clave | Valor |
|---|---|---|
| `P1_filamento_PETG.ini` | first_layer_temperature | 245 |
| `P1_filamento_PETG.ini` | temperature | 245 |
| `P1_filamento_PETG.ini` | first_layer_bed_temperature | 80 |
| `P1_filamento_PETG.ini` | bed_temperature | 75 |
| `P1_filamento_PETG.ini` | min_fan_speed | 15 |
| `P1_filamento_PETG.ini` | max_fan_speed | 35 |
| `P1_filamento_PETG.ini` | bridge_fan_speed | 60 |
| `P1_filamento_PETG.ini` | disable_fan_first_layers | 3 |
| `P1_filamento_PETG.ini` | filament_max_volumetric_speed | 8 |
| `P1_filamento_PETG.ini` | filament_retract_length | 1 |
| `P1_filamento_PETG.ini` | filament_retract_speed | 30 |
| `P1_impresora_Ender3S1.ini` | bed_shape | 5x5,215x5,215x215,5x215 |
| `P1_impresora_Ender3S1.ini` | max_print_height | 260 |
| `P1_impresora_Ender3S1.ini` | nozzle_diameter | 0.4 |
| `P1_impresora_Ender3S1.ini` | gcode_flavor | marlin2 |
| `P1_impresora_Ender3S1.ini` | machine_max_acceleration_extruding | 1000 |
<!-- /FAB:perfiles -->

**Por qué.**
- **sellado** (P1-INT-04): es la única pieza impresa **mojada y a presión** (presión de cierre de la bomba <!--V:sizing.loads.p_pump_max_Pa:.0f-->67222<!--/V--> Pa como succión o contrapresión; recuperación a 30 km/h <!--V:est.loads.structural_toma.p_ram_Pa:.0f-->24622<!--/V--> Pa). El PETG pierde agua "through the seams and contact points between perimeters and solid infill" [VERIFICADO: research/R05 S22] → 100 % de relleno con 30 % de solape, 5 perímetros, capa 0,15 (Sa 10–13 µm contra 20–24 µm a 0,21 mm [VERIFICADO: S18]). La **cara del O-ring va sobre la cama** (la más lisa y plana); planchado solo en la cara de arriba (apoyo de arandelas y de la arandela de estanqueidad de la purga).
- **cubiertas** (P1-ELE-01/02, P1-CTL-02): piezas **secas** y fuera de la ruta de carga de mando; 5 perímetros y 30 % gyroid, como pide la orientación del manifest para CTL-02. Con 0,45 mm de ancho de extrusión, 5 perímetros son 2,25 mm por lado y 4,5 mm entre las dos caras [CALCULADO]: una pared de hasta 4,5 mm queda maciza, pero las paredes de **5 mm de P1-CTL-02** (auditoría ronda 3, FEA: σZ entre capas) dejan en el medio una franja de ≈ 0,5 mm [CALCULADO] que llena el relleno de huecos (*gap fill*) de PrusaSlicer. Verificar en la vista previa del laminado que esa franja no quede vacía; si queda, usar 6 perímetros en la caja. FS mínimos de `estructural.json` en la tabla §2.3.
- **estructural** (P1-CTL-03 y peines P1.1): el soporte del kill switch es un **elemento de seguridad** (el tirón del cordón tiene que sacar el clip, no romper el soporte, y el golpe a la seta cruza capas): 6 perímetros, 85 % gyroid, velocidades moderadas.
- **Filamento y máquina:** boquilla 245 °C (techo 260 °C), cama 80/75 °C (techo 100 °C), cama PC con pegamento en barra, ventilador 15–35 %, retracción 1 mm [VERIFICADO: research/R05, S1–S3; ver comentarios de los `.ini`].

**Validación ejecutada** (`python prusaslicer/validar_perfiles.py`, PrusaSlicer 2.7.2 instalado): formato «clave = valor» sin duplicados; todas las claves existen en 2.7.2; límites de `inputs.yaml` (boquilla, cama, zona útil); PrusaSlicer carga y guarda las 3 familias; lamina las 8 probetas impresas y las 5 piezas del jet y el G-code repite temperatura, cama, perímetros, relleno, capa, costura, forma de cama y alto máximo. `slice_report.json` solo contiene piezas del waterjet.

### 2.3 Orientación por pieza

La orientación es la del CAD (`print_rot` de cada `META`; `build_all.py` exporta los STL ya orientados). El FS mínimo sale de `estructural.json`; soporte y avisos, del laminado real.

<!-- FAB:orientacion -->
| ID | Pieza | Cant. | Perfil, relleno | Por qué ese perfil (familias.py) | Orientación de impresión (manifest) | Envolvente [mm] | FS mín. (estructural.json) | Soporte auto / avisos PrusaSlicer | g c/u (CAD × solid_frac) | g c/u (PrusaSlicer) | h c/u (18 g/h) | h c/u (PrusaSlicer) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1-CTL-02 | caja_acel | 1 | **cubiertas** 30 % | tapa de la unidad de palancas: sin cargas de mando (van a P1-CTL-08); 5 perímetros, 30 % (orientación del manifest) | Tapa sobre la cama (ranuras planas, sin soportes); ala arriba. 0,2 mm, 5 perímetros, 30 % giroide `print_rot=(180, 0, 0)` | 184×82×68 | 3,84 (Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta)) | sí · Floating bridge anchors, Long bridging extrusions | 134 | 162 | 7,4 | 11,8 |
| P1-CTL-03 | soporte_kill | 1 | **estructural** 85 % | en la ruta de carga de un elemento de seguridad (tirón del cordón, golpe a la seta); FS en structural.py | Base sobre la cama; la cara inclinada a 45° no necesita soportes. 0,2 mm, 5 perímetros `print_rot=(0, 0, 0)` | 100×130×55 | 4,21 (Cara PETG 10 mm: golpe sobre la seta 200 N [SUPUESTO] (cor…) | sí · Collapsing overhang | 120 | 186 | 6,7 | 18,2 |
| P1-ELE-01 | esc_stand | 1 | **cubiertas** 30 % | seca, sobre el piso; FS ≥ 16 (estructural.json); insertos M5 en nervios macizos — P1.4 | Base abierta sobre la cama; tablero arriba (puentes de 3,2 mm entre nervios, sin soportes). `print_rot=(0, 0, 0)` | 208×138×60 | 16,02 (Insertos M5 de la capota: apriete de las tiras de EPDM (so…) | sí · Floating bridge anchors, Long bridging extrusions | 263 | 364 | 14,6 | 29,1 |
| P1-ELE-02 | esc_hood | 1 | **cubiertas** 30 % | capota antisalpicaduras, seca; FS ≥ 6 (estructural.json) | Techo sobre la cama, paredes y nervios hacia arriba (sin soportes). `print_rot=(180, 0, 0)` | 208×126×55 | 6,39 (Techo de la capota: reacción de las tiras de EPDM (sosteni…) | no | 207 | 216 | 11,5 | 18,0 |
| P1-INT-04 | tapa_inspeccion | 1 | **sellado** 100 % | mojada y a presión: O-ring de cara y purga; sección llena, sin canales entre cordones (research/R05 B4) — P1.6/P1.7 | Cara de la ranura del O-ring y del hexágono de la tuerca sobre la cama (fondos lisos), resalte arriba, 100 % relleno `print_rot=(0, 0, 0)` | 160×160×19 | 3,34 (Tapa: ciclo marcha ↔ punto fijo Δp = 42 kPa (olas/maniobras)) | sí · Long bridging extrusions | 327 | 327 | 18,2 | 33,6 |
<!-- /FAB:orientacion -->

- **Soportes:** imprimir **sin soportes**; los avisos son puentes cortos. P1-INT-04: el techo del hexágono de la tuerca de purga y el de la ranura del O-ring son puentes; revisar en la vista previa que el del hexágono quede plano (si cuelga, la tuerca no asienta → repasar con lima). P1-CTL-03: "Collapsing overhang" en los rebajes de los pulsadores por dentro de la cara inclinada: el panel apoya en la cara exterior, no importa. P1-ELE-01: puentes del tablero entre nervios (previstos en el CAD).
- **Borde (brim):** solo si alto/huella > 2 (`familias.brim`); hoy solo la probeta P1.4.

### 2.4 Tuercas cautivas e insertos (inox en zona húmeda)

<!-- FAB:roscas -->
| Pieza | Tipo | Rosca | Comentario en el CAD |
|---|---|---|---|
| P1-ELE-01 | inserto térmico M5 (agujero Ø 6,4 × 10,5 mm) | M5 | nervios exteriores para la capota (insertos M5 arriba) |
| P1-INT-04 | tuerca cautiva, bolsillo hexagonal | M6 A4 (ISO 4032: 10 e/c) | purga: resalte arriba, hexágono de tuerca M6 desde abajo, agujero Ø6,4 |
<!-- /FAB:roscas -->

- **Zona húmeda (P1-INT-04): solo inox.** La purga usa una **tuerca ISO 4032 M6 A4 cautiva** en hexágono abierto a la cara interior (la presión la aprieta contra su asiento) y tornillo M6 × 12 A4 con arandela de estanqueidad; nada de latón: descincificación en agua con Zn > ~15 % [VERIFICADO: research/R05 A10.2, S30]. Si en el futuro se agrega un inserto en una pieza mojada: **inserto de inox 300** [VERIFICADO: existen, R05 S29], soldador a ~250–260 °C [ESTIMADO: R05 A10.3].
- **Zona seca (P1-ELE-01):** 4 insertos M5 para la capota (`B-INS` de la BOM) — se valida el proceso con **P1.4** antes de tocar la pieza. Agujero 1 mm más profundo que el inserto (el CAD lo trae), hundir el 90 % con la punta y el resto con herramienta plana fría [VERIFICADO: R05 S28]; a ras ±0,2 mm, perpendicular, sin fisura (lupa 10×) [SUPUESTO].
- **Torques de partida sobre PETG:** M4 1,0 · M5 2,0 N·m [ESTIMADO: research/R05 A10.3]; los M6 de la tapa de inspección van **a mano con perillas** y arandela ancha (aplastamiento verificado en `estructural.json`).
- **Fijación de roscas:** nada de Loctite 243 ni anaeróbicos sobre PETG (agrietamiento por tensión [VERIFICADO: R05 S31]); Loctite 425 o tuerca nyloc A4 [VERIFICADO: S32].

### 2.5 Post-proceso y cara de sello de P1-INT-04

- Sacar de la cama **fría**; repasar pata de elefante (compensada 0,2 mm en el perfil; afecta el ancho de la ranura del O-ring en la 1.ª capa: medir con calibre).
- **Planitud de la cara de sello ≤ 0,10 mm** con regla y galgas (±0,15 mm de profundidad ya lleva la compresión a 21–29 % [CALCULADO: research/R05 B3]); si no cumple, lapear sobre vidrio con lija al agua P240 → P600 en "ochos" y corregir el **fondo** de la ranura, no la cara. Ranura **2,57–2,72 × 4,50–4,75 mm** para cordón 3,53 [VERIFICADO: R05 B3]. La contracara es la brida de Al de la chimenea (P1-INT-01): refrentada en el taller de soldadura (§4).
- **O-ring:** cordón NBR70 Ø3,53 con empalme a tope (cianoacrilato) y **grasa de silicona**; nunca grasa mineral [VERIFICADO: R05 S24].
- **Química:** limpieza IPA:agua 50:50; acetona, MEK, THF prohibidos (disuelven PETG) [VERIFICADO: R05 S34]; epoxi solo en piezas frías (West 105/205 HDT 48 °C [VERIFICADO: S21]).
- **Inspección:** antes de cada salida, tapa P1-INT-04 (fisura o blanqueo en el resalte de la purga = cambiarla) y soporte del kill switch P1-CTL-03.

### 2.6 Tiempos y gramos

<!-- FAB:totales -->
| Conjunto | Impresiones | g (CAD × solid_frac) | g (PrusaSlicer) | h (18 g/h, inputs.yaml) | h (PrusaSlicer) |
|---|---|---|---|---|---|
| Piezas del jet (5 tipos) | 5 | 1 051 | 1 255 | 58 | 111 |
| Probetas impresas (P1.1, P1.4, P1.6, P1.7) | 10 | 526 | 537 | 29 | 57 |
| **Total** |  | **1 577** | **1 792** | **88** | **168** |

Bobinas de 1 kg: **3** [CALCULADO: máx(g) × (1 + 0,30) de purga, fallas y reimpresiones (inputs.yaml bom.filament.margin_frac, = bom.py)]. Laminado: PrusaSlicer-2.7.2+UNKNOWN based on Slic3r (with GUI support), perfiles y ajustes por objeto de esta página, sin soportes. Ritmo real de las piezas: **11,3 g/h** contra 18 g/h de inputs.yaml (printer.print_rate_g_h); la masa real de PrusaSlicer es 23 % mayor que la del manifest (CAD × solid_frac): 5–6 perímetros llenan casi todas las paredes de 3–6 mm.
<!-- /FAB:totales -->

---

## 3. Mecanizado: torno propio vs. taller

La BOM supone que todo lo de revolución con barra de Ø ≤ `bom.lathe_max_d_mm` sale del **torno manual del usuario** y que lo mayor (y lo de 4–5 ejes) va a un servicio `S-*`. **Ese límite es un [SUPUESTO] de la BOM: medir el volteo real** (sobre la bancada y sobre el carro transversal) y la **distancia entre puntos**, y corregir `inputs.yaml` antes de pedir material.

<!-- FAB:torno -->
| ID | Pieza | Material | Cant. | Pieza Ø × largo [mm] | Barra (bom.csv) | Barra Ø × largo [mm] | Ø barra ≤ 180 mm | Quién | Plano |
|---|---|---|---|---|---|---|---|---|---|
| P1-CTL-04 | pasamuros_m66 | AISI 316 | 1 | 43×32×32 | MP-316-D35 | Ø35 × 58 | sí | **torno propio** | `P1-CTL-04_pasamuros_m66.svg` |
| P1-CTL-11 | eje_palancas | AISI 316 | 1 | 18×38×18 | MP-316-D20 | Ø20 × 53 | sí | **torno propio** | `P1-CTL-11_eje_palancas.svg` |
| P1-CTL-12 | perno_enclav | AISI 316 | 2 | 6×13×6 | MP-316-D8 | Ø8 × 28 | sí | **torno propio** | `P1-CTL-12_perno_enclav.svg` |
| P1-DRV-01 | shaft | AISI 316 | 1 | 470×26×26 | MP-316-D28 | Ø28 × 485 | sí | **torno propio** | `P1-DRV-01_shaft.svg` |
| P1-DRV-02 | seal_housing | AISI 316 | 1 | Ø70,0 × 43,5 | MP-316-D75 | Ø75 × 58 | sí | **torno propio** | `P1-DRV-02_seal_housing.svg` |
| P1-DRV-06 | bearing_cover | Al 5052/6082 | 1 | Ø65,0 × 7,0 | MP-6082-D70 | Ø70 × 22 | sí | **torno propio** | `P1-DRV-06_bearing_cover.svg` |
| P1-PMP-02 | wear_ring | AISI 316 | 1 | Ø142,8 × 68,6 | MP-316-TUBO-P1-PMP-02 | Ø150 × 84 | sí | **torno propio** | `P1-PMP-02_wear_ring.svg` |
| P1-PMP-04 | pin_band | AISI 316 | 1 | Ø66,0 × 16,0 | MP-316-D70 | Ø70 × 31 | sí | **torno propio** | `P1-PMP-04_pin_band.svg` |
| P1-PMP-05 | shear_pin | Al 6061-T6 | 2 | 4×30×4 | MP-6061-D4 | Ø4 × 44 | sí | **torno propio** | `P1-PMP-05_shear_pin.svg` |
| P1-PMP-07 | water_bushing | POM-C | 1 | 30×28×28 | MP-POM-D30 | Ø30 × 45 | sí | **torno propio** | `P1-PMP-07_water_bushing.svg` |
| P1-PMP-11 | pivot_bushing | POM-C | 2 | 12×12×26 | MP-POM-D14 | Ø14 × 41 | sí | **torno propio** | `P1-PMP-11_pivot_bushing.svg` |
| P1-REV-02 | perno_bucket | AISI 316 | 2 | 24×52×24 | MP-316-D28 | Ø28 × 68 | sí | **torno propio** | `P1-REV-02_espaciador_pivote_bucket.svg` |
| P1-REV-03 | buje_bucket | POM-C | 2 | Ø28,0 × 15,0 | MP-POM-D30 | Ø30 × 30 | sí | **torno propio** | `P1-REV-03_buje_bucket.svg` |
| P1-REV-06 | perno_varilla | AISI 316 | 1 | 13×24×13 | MP-316-D16 | Ø16 × 38 | sí | **torno propio** | `P1-REV-06_perno_varilla.svg` |
| P1-STE-02 | perno_sup | AISI 316 | 1 | 14×14×49 | MP-316-D16 | Ø16 × 64 | sí | **torno propio** | `P1-STE-02_perno_sup.svg` |
| P1-STE-03 | arandela_pom | POM-C | 3 | Ø18,0 × 1,0 | MP-POM-D20 | Ø20 × 16 | sí | **torno propio** | `P1-STE-03_arandela_pom.svg` |
| P1-STE-05 | perno_inf | AISI 316 | 1 | 8×8×33 | MP-316-D10 | Ø10 × 48 | sí | **torno propio** | `P1-STE-05_perno_inf.svg` |
| P1-STE-06 | poste | Al 6061-T6 | 1 | 44×44×140 | MP-6061-D50 | Ø50 × 155 | sí | **torno propio** | `P1-STE-06_poste.svg` |
| P1-PMP-01 | housing | Al 6061-T6 | 1 | Ø192,8 × 165,8 | MP-6061-TUBO-P1-PMP-01 | Ø200 × 181 | **NO** | taller (S-TURN-HSG) | `P1-PMP-01_housing.svg` |
| P1-PMP-08 | fixed_nozzle | Al 6061-T6 | 1 | Ø161,1 × 151,2 | MP-6061-TUBO-P1-PMP-08 | Ø180 × 166 | sí | taller (S-TURN-NOZ) | `P1-PMP-08_fixed_nozzle.svg` |

Límite supuesto del torno propio: **Ø 180 mm** (inputs.yaml `bom.lathe_max_d_mm`, [SUPUESTO] — **medir** volteo sobre la bancada y sobre el carro, y distancia entre puntos).
<!-- /FAB:torno -->

- **Casos al borde:** el **anillo de desgaste P1-PMP-02** (316L, barra hueca) entra en el límite supuesto pero lleva la cota más fina del jet (Ø interior = Ø de puntas + 2 × holgura = <!--V:manifest.params.D_bore:.2f-->132.79<!--/V--> mm, H7); en un torno manual liviano con 316L conviene mandarlo con la carcasa (S-TURN-HSG) o tornearlo **montado en la carcasa** para que quede concéntrico. El **eje P1-DRV-01** necesita distancia entre puntos mayor que su barra (tabla) y luneta: si no hay, a taller.
- **316L:** herramienta de metal duro positiva, avance constante, sin "frotar" (se endurece por deformación); refrigerante [ESTIMADO: práctica]. **POM-C** (bujes P1-PMP-07/11, P1-REV-03, P1-STE-03): herramienta afilada de HSS, sin refrigerante, dejar el Ø interior para el final y medir después del prensado (P1.10). **Semipasadores de corte P1-PMP-05** (<!--V:manifest.params.pmp_pin_n:-->2<!--/V--> por juego, Ø<!--V:sizing.mech.shear_pin.d_mm:.1f-->3.5<!--/V--> × <!--V:manifest.params.pmp_pin_half_len:.1f-->29.5<!--/V--> mm): de la **misma barra** 6061-T6 que los <!--V:manifest.params.pmp_pin_spares_sets:-->3<!--/V--> juegos de repuesto (R-PIN) y que los juegos de la probeta P1.9; extremos planos con chaflán chico (se tocan en el centro del eje).
- **Interfaces de la bomba (auditoría Pass 3, planos P1-PMP-01/05/06/08 y P1-INT-01):** carcasa con **espigón de centraje Ø<!--V:manifest.params.pmp_f1_spigot_d:.0f-->140<!--/V--> h6** concéntrico al asiento del anillo (una atada, TIR ≤ 0,03) y **8 × M5 ciegos** en la cara trasera (rosca <!--V:manifest.params.pmp_f2_thread_L:.0f-->9<!--/V--> mm, enmascarar en el anodizado); 2 × M5 radiales roscados en pared + saliente. Tobera con **brida Ø<!--V:manifest.params.pmp_f2_od:.1f-->161.1<!--/V-->** (más chica que el agujero del espejo), espiga <!--V:manifest.params.pmp_noz_spigot:.0f-->12<!--/V--> mm con ranura de O-ring **radial** y largo controlado (+0/+0,05: deja <!--V:manifest.params.pmp_stack_gap:.2f-->0.25<!--/V--> mm entre bridas). Estator: 2 agujeros **lisos** Ø5,5 × 3,5 (ya no roscados). Semipasadores P1-PMP-05: **2 por juego**, largo <!--V:manifest.params.pmp_pin_half_len:.1f-->29.5<!--/V--> mm.
- **Pórtico P1-DRV-03:** zapatas con **ranura de 9 mm abierta hacia popa** (no agujeros) y paso del resalte Ø<!--V:manifest.params.drv_brg_shoulder_hole:.1f-->32.5<!--/V--> (no roza el aro interior del 7204 BECBP); mecanizar el Ø47 H7 después de soldar.
- **Traba y pivote del bucket (ronda 4, torno propio; planos P1-REV-02, P1-REV-03 y P1-REV-04_embolo_*).** La tabla de arriba la genera `tabla_fabricacion.py` con la caja envolvente del CAD, que en P1-REV-02 incluye el tornillo y en P1-REV-04 la contratuerca: la barra real es la de esta lista (hallazgo 8 de §10).
  - **Espaciador del pivote P1-REV-02 (×2)**, AISI 316 de barra Ø40 [CALCULADO: brida Ø<!--V:manifest.params.REV_sp_fl_d:g-->36<!--/V--> + 2 de sobremedida → Ø38, comercial Ø40]: piloto Ø<!--V:manifest.params.REV_sp_pilot_d:g-->16<!--/V--> **h6** (entra en el Ø16 H7 de la oreja; 0,5 mm más corto que la oreja [CALCULADO: P1-REV-02.pilot_L]: aprieta la brida, no el piloto), brida Ø<!--V:manifest.params.REV_sp_fl_d:g-->36<!--/V--> × <!--V:manifest.params.REV_sp_fl_t:g-->3<!--/V--> con la cara de apoyo plana y a escuadra con el piloto ≤ 0,02 [SUPUESTO: plano P1-REV-02], muñón Ø<!--V:manifest.params.REV_pin_d:g-->20<!--/V--> **h7** Ra 0,8 (gira el buje POM) y agujero Ø12,5 pasante. Tornear piloto, cara de la brida y muñón en una atada.
  - **Émbolo P1-REV-04 (×2)**, AISI 316, propio porque el GN 617 de catálogo no llega (research/R08b, nota 2026-10-02). *Cuerpo* de barra Ø25–28 [SUPUESTO: plano Ø25; la regla de sobremedida de la BOM da Ø28]: rosca exterior M<!--V:manifest.params.REV_lock_thread_d:g-->24<!--/V-->×1,5-6g desde la punta (que queda enrasada con la cara exterior de la oreja) hasta pasar la contratuerca, cuerpo Ø24, interior **Ø16 H8** pasante Ra 0,8 (guía del perno y, a continuación, cámara del resorte) y rosca interior M20×1 × 6 atrás para la tapa; *tapa* M20×1 de 4 mm con agujero Ø10,2 para la cola. *Perno* de barra Ø18: Ø<!--V:manifest.params.REV_lock_pin_d:g-->16<!--/V--> **h9** Ra 0,8 con chaflán 1 × 45° en la punta, escalón (asiento del resorte) y cola Ø10 con M6 × 10 en el extremo; ajuste H8/h9: juego 0–0,07 mm [CALCULADO: ISO 286, Ø16]. *Pomo* Ø25 × 10 de POM (sobrante de la varilla de P1-REV-03) con rosca M6 y agujero transversal para el eslabón de cable Ø1,5 del balancín (P1-REV-09). Medidas en el plano y en `piezas/_release.PLG_*`; carrera <!--V:manifest.params.REV_plunger_stroke:g-->12<!--/V--> mm (liberar pide <!--V:manifest.params.REV_release_need:g-->9.5<!--/V-->). Resorte comprado (B-SPRING), contratuerca M24×1,5 A4 fina (B-NUT24); machos en B-TAP24.
  - **Buje P1-REV-03 (×2)**, POM-C de varilla Ø32 [CALCULADO: brida Ø<!--V:manifest.params.REV_bush_fl_d:g-->30<!--/V--> + 2]: exterior Ø<!--V:manifest.params.REV_bush_od:g-->24<!--/V--> con **0,05–0,10 mm de interferencia** [SUPUESTO: plano P1-REV-03] **contra el agujero real** del brazo (medirlo después de escariarlo, §4), largo <!--V:manifest.params.REV_bush_L:g-->18<!--/V-->; el interior se deja chico (Ø19,5 [SUPUESTO]) y se escaria a **Ø20,1 (+0,05/0)** DESPUÉS de prensar (el prensado cierra el agujero: R4-08). Entra en P1.10 (hinchamiento en agua) con P1-PMP-07/11.
- **Orejas del bucket en la boquilla P1-STE-01 (taller S-MILL-STE, plano P1-STE-01).** Orejas de <!--V:manifest.params.STE_ear_t:g-->12<!--/V--> mm; en cada una, agujero del pivote **Ø<!--V:manifest.params.REV_sp_pilot_d:g-->16<!--/V--> H7 escariado** (uno por oreja: ya no pasante de lado a lado) y rosca **M<!--V:manifest.params.REV_lock_thread_d:g-->24<!--/V-->×1,5-6H** del émbolo a <!--V:manifest.params.REV_lock_r:g-->45<!--/V--> mm del pivote, a <!--V:manifest.params.REV_lock_ang:g-->10<!--/V-->° (+Y) y <!--V:manifest.params.REV_lock_ang_m:g-->-25<!--/V-->° (−Y) del eje X, con ligamento hasta el borde del lóbulo r <!--V:manifest.params.STE_lock_lobe_r:g-->20<!--/V-->. Posición de la rosca ±0,1 respecto del pivote [SUPUESTO: plano P1-STE-01]: si no salen de la misma atada del CNC, con una **guía de roscado** referida al pivote (placa con espigón Ø16 h6 en el agujero H7, casquillo para la broca 22,5 y otro para el macho M24×1,5, a r 45 y al ángulo de esa oreja, orientada contra la cara mecanizada de la oreja). Cara exterior plana Ra 1,6 en Ø40 alrededor del pivote (apoyo de la brida del espaciador): **se anodiza** con el resto (no enmascarar: aísla el 316 del 6061; 06 §4); las roscas M24 sí se enmascaran y se repasan con el macho (B-TAP24) después del anodizado.
- **Chapa:** lo plano sale de **corte láser/agua** (S-LASER) con los planos de `04_diseno/planos/`; el taladrado, avellanado y plegado chico (P1-CTL-01/09/14, P1-STE-04/07/08, P1-REV-09) es propio. Tolerancias generales ISO 2768-m y Ra 1,6 en asientos (rótulo de los planos).

---

## 4. Soldadura (Al 5083, 6082 y 316L)

<!-- FAB:soldadura -->
| Servicio | Qué | Especificación (bom.csv) | Cubre | EUR | Etiqueta |
|---|---|---|---|---|---|
| S-WELD-INT | Soldadura TIG Al 5083 (aporte 5183) del conducto P1-INT-01 (rampa, transición, brida de bomba, chimenea) sobre la placa base P1-INT-02 + refrentado de la cara enrasada + prueba de estanqueidad | Soldador certificado en Al; plantilla de armado; prueba con agua/jabón y aire 0,3 bar | P1-INT-01 P1-INT-02 | 480 | [ESTIMADO: 6 h × 70 €/h + aporte y gas] |
| S-WELD-AL | Soldadura TIG de piezas chicas de Al: pórtico P1-DRV-03 y soporte del motor P1-MOT-02 (6082), bucket P1-REV-01 (chapa 6 mm, aros de refuerzo del pivote 8 mm; agujeros de traba se taladran DESPUÉS de soldar, montado) y soporte Mach5 P1-REV-05 (5083), grapas de P1-CTL-08, escalón de P1-CTL-10; rolado de la cuchara del bucket | Aporte 5183 (5083) / 4043 o 5356 (6082); planos de 04_diseno/planos | P1-DRV-03 P1-MOT-02 P1-REV-01 P1-REV-05 P1-CTL-08 P1-CTL-10 | 320 | [ESTIMADO: 4 h × 70 €/h + rolado] |
| S-WELD-316 | Soldadura TIG 316L de la rejilla P1-INT-03 (9 pletinas perfiladas + pletina de popa + tirantes) | Aporte 316LSi, plantilla para mantener el enrase; decapado/pasivado | P1-INT-03 | 140 | [ESTIMADO: 1,5 h × 70 €/h + decapado] |
| S-LASER | Corte láser / chorro de agua de las piezas de chapa (DXF de 04_diseno/planos) | 5083: placa base 10, placas de espejo/central/soporte 6, topes de dirección 8, bucket 6 (cuchara, brazos) y aros de refuerzo del pivote 8, soportes del Bowden 4 (plegado, ×2), brida yugo 20, brazo 10, conducto 5/12; 6061: palancas 8, gatillo 6; 6082: pórtico 12, soporte motor 10; 316: pletinas de rejilla 4 | P1-INT-01 P1-INT-02 P1-INT-03 P1-CTL-01 P1-CTL-08 P1-CTL-09 P1-CTL-10 P1-CTL-14 P1-REV-01 P1-REV-05 P1-REV-09 P1-STE-04 P1-STE-07 P1-STE-08 P1-DRV-03 P1-MOT-02 | 220 | [ESTIMADO: preparación 50 € + ≈ 12 €/pieza] |
<!-- /FAB:soldadura -->

**Procedimiento para el taller** (conducto P1-INT-01 sobre placa base P1-INT-02, bucket P1-REV-01, soporte P1-REV-05, grapas de P1-CTL-08):
- **Proceso:** TIG en **corriente alterna** (limpia el óxido) con aporte **ER5183** para 5083 (la BOM lo fija); MIG pulsado con 5183 es aceptable para las costuras largas del conducto si el taller lo domina [ESTIMADO: práctica de soldadura de aluminio naval; confirmar con el soldador]. 6082 (pórtico P1-DRV-03, soporte del motor P1-MOT-02): 5356 o 4043 (BOM). Rejilla 316L: TIG con 316LSi, decapado y pasivado (S-WELD-316); el diseño actual tiene **<!--V:manifest.params.grille_bars:-->9<!--/V--> pletinas** con luz de <!--V:manifest.params.toma_bar_gap:.2f-->12.24<!--/V--> mm y **no se suelda a la toma**: va aislada del 5083 con camisa/cinta de PTFE en las ranuras (06 §4), sin contacto metálico 316 ↔ 5083.
- **Preparación:** desengrasar, cepillo de **inox dedicado** al aluminio justo antes de soldar, punteado en **plantilla** (el enrase de la placa base con el casco y la concentricidad de la brida de la bomba importan más que la estética); chapas de 5 mm sin precalentar [ESTIMADO].
- **Secuencia del conducto:** puntear todo → costuras cortas alternadas para no torcer la brida → **refrentar la brida de la bomba, la brida de la chimenea y la cara enrasada después de soldar** (la BOM incluye el refrentado en S-WELD-INT). **Mecanizar después de soldar, en una atada:** cara y **rebaje de centraje Ø<!--V:manifest.params.pmp_f1_spigot_d:.0f-->140<!--/V--> H7** de la brida de la bomba, 8 agujeros, buje del sello Ø<!--V:manifest.params.seal_spigot_d:.0f-->42<!--/V--> H8 con sus 4 × M6 y cara de la chimenea; coaxialidad rebaje ↔ buje ≤ 0,05 (plano `P1-INT-01_conducto.svg`). Las ranuras de la rejilla llevan <!--V:manifest.params.toma_iso_gap:.1f-->0.5<!--/V--> mm por lado para la camisa de PTFE.
- **Alivio de tensiones: no se hace en 5083** [ESTIMADO: 5083 es una aleación no tratable térmicamente (H111, endurecida por deformación); un tratamiento de alivio o un mantenimiento prolongado a 65–200 °C puede **sensibilizar** las aleaciones 5xxx con > 3 % Mg a corrosión intergranular — **verificar** con el soldador / ficha del material]. La resistencia en la zona afectada por el calor (ZAT) ya está considerada: `structural_toma.py` y `structural_direccion.py` usan el Rp0,2 del 5083-O/H111 (= ZAT) y FAT 25 en las costuras; `structural_tren.py` usa el admisible de ZAT del 6082-T6 en el pórtico y el soporte del motor.
- **Bucket P1-REV-01 (ronda 4: criterio de traba única).** Cada traba sola lleva todo M_h (<!--V:est.loads.structural_direccion.M_hinge_Nm:.1f-->135.3<!--/V--> N·m con la reversa R12 [CALCULADO]; <!--V:est.loads.structural_direccion.F_lock_pin_N:.0f-->3006<!--/V--> N en el perno): la resistencia ya no depende de que los agujeros de los dos brazos coincidan, así que se eliminó el taladrado coincidente con el bucket montado y la prueba con comparador. Secuencia:
  1. **Corte (S-LASER):** cuchara (desarrollo) y brazos en chapa 5083 de <!--V:manifest.params.REV_t:g-->8<!--/V--> mm; 2 aros de refuerzo de <!--V:manifest.params.REV_ring_t:g-->10<!--/V--> mm (MP-5083-AROS) de radio <!--V:manifest.params.REV_boss_r:g-->20<!--/V--> mm (Ø40 [CALCULADO: 2 × REV_boss_r]). El agujero del buje sale del láser **chico** (Ø22 [SUPUESTO]) en brazos y aros; los agujeros de traba **no** se cortan (o solo un piloto ≤ Ø12 [SUPUESTO] que la broca se come).
  2. **Soldadura (S-WELD-AL):** cuchara rolada y brazos en la plantilla de armado en posición ABAJO (plano P1-REV-01_bucket_cuchara); cada aro en la cara exterior de su brazo, centrado con un perno en los agujeros chicos. TIG con ER5183.
  3. **Alojamiento del buje Ø<!--V:manifest.params.REV_bush_od:g-->24<!--/V--> H7, DESPUÉS de soldar:** broca 23,7 y escariador largo Ø24 H7 (B-REAM16) **de una pasada por los dos brazos** (brazo + aro), el segundo guiado por el primero, o los dos en una atada en la fresadora. Control: un perno patrón Ø24 h6 pasa por los dos a la vez.
  4. **Agujeros de traba Ø<!--V:manifest.params.REV_lock_hole_d:g-->16.5<!--/V-->, con plantilla referida al agujero del buje** (los 4: ARRIBA y ABAJO en los dos brazos). Plantilla (B-REAM16, de recortes): una placa de acero o Al de ≈ 10 mm por brazo, con espigón **Ø24 h6** que entra en el alojamiento recién escariado y **2 casquillos guía Ø16,5** a <!--V:manifest.params.REV_lock_r:g-->45<!--/V--> mm del centro: uno en el ángulo de la traba ABAJO de ese brazo (<!--V:manifest.params.REV_lock_ang:g-->10<!--/V-->° en el +Y, <!--V:manifest.params.REV_lock_ang_m:g-->-25<!--/V-->° en el −Y, marco de la boquilla con el bucket ABAJO) y otro girado <!--V:manifest.params.bucket_down_deg:g-->70<!--/V-->° alrededor del centro (traba ARRIBA): coordenadas de los planos P1-REV-01_bucket_brazo_estribor / _babor. Las dos placas van fijas a un mandril Ø24 h6 que pasa por los dos brazos (pasador o chaveta entre placa y mandril), así quedan **en fase** entre sí; la orientación del conjunto se toma del contorno del brazo con una escuadra (el ángulo absoluto solo cambia la posición del bucket trabado, no la resistencia). Broca 16,2 por el casquillo y escariador Ø16,5 (+0,1/0).
     **Tolerancia de posición ±0,2 mm** respecto del centro del buje [SUPUESTO: plano P1-REV-01]: alcanza porque el juego perno ↔ agujero es <!--V:manifest.params.REV_lock_hole_d:g-->16.5<!--/V--> − <!--V:manifest.params.REV_lock_pin_d:g-->16<!--/V--> = 0,5 mm en el diámetro [CALCULADO], el bucket gira libre en su pivote hasta que entra el primer perno y el chaflán 1 × 45° del perno centra el resto, y porque la resistencia ya no depende del reparto entre trabas. Lo que sí tiene que cumplirse —que **entren los dos pernos** ARRIBA y ABAJO— lo comprueba la prueba funcional de 06 (T0.M6b).
  5. **Buje P1-REV-03:** medir el Ø24 real; tornear el exterior del buje con 0,05–0,10 mm de interferencia (§3), prensar con prensa de husillo (sin golpes) y **escariar el interior a Ø20,1 (+0,05/0) con el buje ya prensado**, los dos brazos de una pasada. El espaciador P1-REV-02 (muñón Ø<!--V:manifest.params.REV_pin_d:g-->20<!--/V--> h7) tiene que girar a mano en los dos bujes. Después, P1.10.
- **Prueba de estanqueidad del conducto (antes de instalarlo):** tapar la brida de la bomba y la boca de la toma con placas + goma; la BOM pide **aire a 0,3 bar con agua jabonosa** (S-WELD-INT) → 0 burbujas en las costuras en 10 min [SUPUESTO: tiempo]. **Ojo:** 0,3 bar es menos que la presión de cierre <!--V:sizing.loads.p_pump_max_Pa:.0f-->67222<!--/V--> Pa y que el golpe de fondo <!--V:est.loads.structural_toma.p_slam_Pa:.0f-->50000<!--/V--> Pa que ve el conducto: sirve para encontrar poros, no como prueba de resistencia. Recomendado además: **prueba hidrostática con agua** a 1,5 × la presión de cierre, 15 min, sin gotas [SUPUESTO: mismo criterio que P1.11; ver §10].

---

## 5. CNC 5 ejes: impulsor y estator

<!-- FAB:cnc -->
| Pieza | Qué es | Qué mandar | Cotas críticas | Balanceo |
|---|---|---|---|---|
| Impulsor P1-PMP-03 | AISI 316; 5 álabes; Ø132,0 punta, cubo Ø66,0; masa CAD 1 336 g | `04_diseno/step/P1-PMP-03_impeller.step` + `P1-PMP-03_impeller_hub.svg`, `P1-PMP-03_tabla_angulos_alabes.svg` | Ø de puntas torneado a medida del anillo: holgura radial 0,40 mm (Ø anillo 132,79); agujero del eje y agujero del pasador según plano del cubo | G6.3 a 4 181 rpm: e_per = 14,4 µm → U_per = 19,2 g·mm (dos planos: la mitad por plano) |
| Estator P1-PMP-06 | Al 6061-T6; 7 álabes + camisa + cubo; masa CAD 1 518 g | `04_diseno/step/P1-PMP-06_stator.step` + `P1-PMP-06_stator.svg` | alojamiento del buje P1-PMP-07 (H7) y bridas según plano; anodizado duro después (S-ANOD) | no gira: sin balanceo |

| Sección | r [mm] | U [m/s] | β1 flujo [°] | β2 flujo [°] | Entrada al estator [°] | de Haller |
|---|---|---|---|---|---|---|
| cubo | 33,0 | 17,5 | 28,1 | 41,3 | 53,5 | 0,71 |
| medio | 52,2 | 27,7 | 18,6 | 21,8 | 64,9 | 0,86 |
| punta | 66,0 | 35,1 | 14,9 | 16,5 | 69,7 | 0,91 |

Ángulos de flujo de `resultados/sizing.json` (pump.sections, desde la tangencial); los de **pala** (con incidencia y desviación) están en `P1-PMP-03_tabla_angulos_alabes.svg`, que es lo que se manda.

| Servicio | Qué | EUR | Etiqueta |
|---|---|---|---|
| S-CNC-IMP | Impulsor 316L CNC 5 ejes, 1 u., con material, torneado del Ø exterior contra el anillo de desgaste y balanceo | 1 050 | [ESTIMADO: research/R11 §6 — CNC 5 ejes inox 600–1500 € (punto medio)] |
| S-CNC-STAT | Estator Al 6061-T6 CNC 5 ejes (7 álabes + camisa + cubo), 1 u., con material | 630 | [ESTIMADO: research/R11 §6 — Al ≈ 40 % menos que inox: 360–900 € (punto medio)] |
<!-- /FAB:cnc -->

**Qué mandar al taller** (S-CNC-IMP / S-CNC-STAT; cotizar con Xometry, Protolabs, JLCCNC o un taller UE [ESTIMADO: research/R11 §6]):
1. **STEP** de `04_diseno/step/` (P1-PMP-03 impulsor y P1-PMP-06 estator): es la geometría que manda.
2. **Tabla de ángulos de los álabes** `04_diseno/planos/P1-PMP-03_tabla_angulos_alabes.svg` (β de pala en cubo/medio/punta, cuerda, espesor, apilado) para que el programador controle la superficie, y los planos del cubo y del estator (`P1-PMP-03_impeller_hub.svg`, `P1-PMP-06_stator.svg`) con los asientos.
3. **Material:** impulsor **AISI 316L** (no 1.4301: no apto sumergido, research/R08b §2); estator **Al 6061-T6**, después **anodizado duro** (§6).
4. **Tolerancias:** generales ISO 2768-m; superficies de álabe ±0,2 mm de perfil y Ra ≤ 3,2 µm [ESTIMADO: práctica de impulsores chicos; acordar con el taller]; agujero del eje H7 y agujero transversal del pasador escariado a Ø<!--V:sizing.mech.shear_pin.d_mm:.1f-->3.5<!--/V--> + 0,05 (plano del cubo); **Ø de puntas con sobremedida**, a tornear al final contra el anillo de desgaste ya montado para dejar la holgura radial de <!--V:sizing.pump.tip_clearance_mm:.2f-->0.40<!--/V--> mm (P1.12).
5. **Balanceo dinámico G6.3** en dos planos a la velocidad máxima <!--V:sizing.mech.n_max_rpm:.0f-->4181<!--/V--> rpm (ISO 21940-11, grado usual de impulsores de bomba [ESTIMADO: verificar con el taller]); la tabla da la excentricidad y el desbalance residual admisibles con la masa del CAD. Corregir quitando material en el cubo, no en los álabes.

**Alternativa SLM 316L + torneado** (research/R11 §6): JLC3DP imprime 316L en 390 × 390 × 290 mm con ±0,3 mm o 0,4 %, Ra 3,2–12 µm, en ~72 h [VERIFICADO: R11 §6]; ≈ 330–610 € con el torneado del Ø exterior, del agujero y el balanceo [ESTIMADO: R11 §9]. Exige sobremedida en Ø de puntas, cubo y agujero para tornear después [SUPUESTO: 0,5 mm], granallado/pulido de los álabes (la rugosidad de SLM suma pérdidas) y los mismos controles: P1.12 y balanceo.

---

## 6. Anodizado duro y aislamiento galvánico

<!-- FAB:anodizado -->
| Ítem (bom.csv) | Qué | Especificación | Piezas | EUR | Etiqueta |
|---|---|---|---|---|---|
| B-TEFGEL | Antigalvánico Tikal Tef-Gel 60 g (todo A4/316 en contacto con Al: bridas, asientos, roscas) | PTFE, apto agua de mar | — | 42 | [VERIFICADO: research/R08b §6 — 41,89 €] |
| B-ISOW | Arandelas aislantes de fibra/nylon M3–M12 (200 u.) | Biltema art. 191083 | — | 11 | [VERIFICADO: research/R08b §6 — 84,90 kr] |
| B-ANODE | Ánodo de sacrificio de aluminio de placa atornillado a la carcasa/conducto (planos de la bomba: R06 §0, R10b H21) | Ánodo de Al (no Zn en agua salobre) ≈ 100 × 50 × 10, con espárragos; continuidad eléctrica con la carcasa | — | 20 | [ESTIMADO: research/R08b §6 — ánodo de eje Tecnoseal 96 kr VERIFICADO; de placa ≈ 15–25 €] |
| S-ANOD | Anodizado duro tipo III ~50 µm (lote): carcasa P1-PMP-01, estator P1-PMP-06, tobera P1-PMP-08, boquilla P1-STE-01, poste P1-STE-06 | MIL-A-8625 tipo III, sellado; enmascarar roscas, asientos H7 y ranuras de O-ring. Material incluido en el servicio [CALCULADO del bbox]: P1-PMP-06 168,8 × 142,8 × 142,8 → barra Al 6061-T6 (alt. 6082-T6) Ø150 × 184 mm | P1-PMP-01 (Al 6061-T6), P1-PMP-06 (Al 6061-T6), P1-PMP-08 (Al 6061-T6), P1-STE-01 (Al 6061-T6), P1-STE-06 (Al 6061-T6) | 220 | [ESTIMADO: mínimo de facturación de lote 150–300 €] |
<!-- /FAB:anodizado -->

- **Par galvánico:** 316 pasivo vs. aluminio en agua salobre ≈ 670 mV de diferencia, contra ~200 mV de límite práctico [VERIFICADO: research/R06 §0/§6; R10b H21 lo marca como riesgo medio]. El ánodo es el aluminio (carcasa, estator, tobera, conducto) y el cátodo es el impulsor + anillo de 316.
- **Anodizado duro tipo III** (~50 µm, sellado) de carcasa, estator, tobera, boquilla y poste (S-ANOD): aísla y resiste la erosión. **Enmascarar** roscas, asientos H7 y ranuras de O-ring; la capa crece en parte hacia afuera [ESTIMADO: pedir al anodizador el crecimiento por cara] → los asientos que no se enmascaran se mecanizan con esa compensación. Anodizar **después** de todo mecanizado y **antes** del montaje y de la prueba hidrostática P1.11.
- **Tef-Gel** en **toda** rosca, asiento y cara de contacto 316/A4 ↔ Al (bridas de la bomba, anillo de desgaste en la carcasa, espárragos del pórtico, pernos de la boquilla) [VERIFICADO: R06 §6 "ideal to isolate and separate dissimilar materials such as Aluminium and Stainless Steel"].
- **Arandelas aislantes** (fibra/nylon, B-ISOW) bajo cabezas y tuercas A4 sobre Al; **bujes POM** entre pernos 316 y orejas de Al (P1-PMP-11, P1-REV-03, P1-STE-03).
- **Ánodo de aluminio** (no zinc, no magnesio en agua salobre [VERIFICADO: R06 §6]) atornillado a la carcasa/conducto con **continuidad eléctrica** medida con multímetro (< 1 Ω [SUPUESTO]); cambiar al 50 % consumido o cada año [VERIFICADO: R06 §6, Fisheries Supply].
- Las piezas de 5083 sin anodizar (conducto, placa base, placas) son aleación marina: se dejan desnudas o con imprimación epoxi marina; nunca antifouling con cobre sobre aluminio [ESTIMADO].

---

## 7. Probetas y ensayos de taller (`04_diseno/probetas/`)

`python 04_diseno/probetas/build_probetas.py` construye las probetas impresas (STEP + STL en orientación de impresión en `step/` y `stl/`), registra los ensayos de taller, escribe `probetas_manifest.json` (envolvente, masa, malla cerrada, cotas verificadas y criterios con números) y regenera estas tablas. Cada módulo `PRB-P1.x_*.py` lee la geometría de `04_diseno/piezas/` y las cargas de `sizing.json` / `estructural.json`: si cambia el diseño, cambian las probetas y sus criterios. Se eliminaron las probetas de la cola larga (rodamiento en PETG, tuerca M6 de la horquilla, barras de flexión, cuello del patín).

### 7.1 Probetas impresas

<!-- FAB:probetas -->
| Ensayo | Archivo (step/ y stl/) | Perfil (ajustes por objeto) | Cant. | Envolvente [mm] | g c/u | h c/u (PrusaSlicer) | Malla cerrada | Descripción |
|---|---|---|---|---|---|---|---|---|
| P1.1 | `P1.1A_peine_agujeros` | estructural (fill_density=100%, fill_pattern=rectilinear) | 1 | 152×111×8 | 52,3 | 5,2 | sí | Agujeros Ø(d+c) de eje vertical para Ø5, Ø6, Ø22; holguras +.15, +.20, +.25, +.30 mm + las del CAD por Ø; bolsillos hexagonales M6: e/c del CAD +.1, +.2, +.3, +.4 |
| P1.1 | `P1.1H_agujeros_horizontales` | estructural (fill_density=100%, fill_pattern=rectilinear) | 1 | 106×26×34 | 24,7 | 2,6 | sí | Agujeros horizontales Ø(d+c) para Ø16 (los que las piezas reales imprimen acostados) |
| P1.4 | `P1.4_inserto_M5` | cubiertas (brim_width=5) | 3 | 21×15×32 | 6,6 | 0,9 | sí | Recorte del nervio de P1-ELE-01 (20 × 12 mm + pared 3.2) con el agujero de inserto Ø6.4 × 10.5; pasador de tiro Ø8.4 |
| P1.6 | `P1.6A_caja_brida` | sellado | 1 | 120×120×38 | 214,9 | 23,4 | sí | Vaso Ø72 × 38 con brida Ø120 × 10 (hace de chimenea), boca Ø60, 4 × M6 en Ø100, válvula de neumático Ø11.5 en el piso |
| P1.6 | `P1.6B_tapa_oring_purga` | sellado | 1 | 120×120×19 | 183,6 | 19,8 | sí | Tapa Ø120 × 13 (= espesor de P1-INT-04), ranura 2.65 × 4.73 en r = 38.4, resalte de purga Ø26 con tuerca M6 cautiva, 4 × M6 |
| P1.7 | `P1.7A_cubo_absorcion_A` | sellado | 1 | 20×20×21 | 10,2 | 1,2 | sí | Cubo 20 mm rotulado A |
| P1.7 | `P1.7B_cubo_absorcion_B` | sellado | 1 | 20×20×21 | 10,2 | 1,2 | sí | Cubo 20 mm rotulado B |
| P1.7 | `P1.7C_cubo_absorcion_C` | sellado | 1 | 20×20×21 | 10,2 | 1,2 | sí | Cubo 20 mm rotulado C |
<!-- /FAB:probetas -->

### 7.2 Criterios pasa / no-pasa (generado)

<!-- FAB:ensayos -->
| Ensayo | Tipo | Qué se ensaya | Piezas | Pasa si (números de los JSON) | Cotas/coherencia verificadas en software |
|---|---|---|---|---|---|
| P1.1 | impresa (CAD) | Peine de holguras (Ø reales de las piezas impresas) | P1-INT-04, P1-ELE-01, P1-ELE-02, P1-CTL-02, P1-CTL-03 | El agujero rotulado con la holgura del CAD mide d + c_CAD ± 0,10 mm y la pieza real entra a mano; la tuerca M6 entra en la fila del CAD y no cae al dar vuelta la probeta. Si no: la holgura a usar es la menor fila que acepta la pieza → corregir el CAD (inputs.yaml geometry.clearance_mm / bolt_clearance_mm) antes de imprimir las piezas. | 9/9 OK |
| P1.4 | impresa (CAD) | Inserto térmico M5 inox en el nervio de P1-ELE-01 | P1-ELE-01, P1-ELE-02 | Las 3 resisten ≥ 120 N (= FS 3 × 40 N por inserto, estructural.json) sin arrancar y el inserto no gira con ≥ 4 N·m (2 × apriete M5 sobre PETG) [SUPUESTO: criterio de giro]. A ras ±0,2 mm, sin fisura alrededor (lupa 10×). | 3/3 OK |
| P1.6 | impresa (CAD) | Tapa con O-ring de cara y purga (réplica de P1-INT-04) a la presión de la chimenea | P1-INT-04, P1-INT-01 | En (1), (2) y (3): caída ≤ 10 % de la presión de ensayo en 15 min, 0 gotas en el O-ring y en la purga (papel tisú alrededor) y sin burbujas con agua jabonosa; sin fisura ni blanqueo en el resalte de la purga. Si gotea: separar O-ring / purga / poros repitiendo con la purga sellada con teflón. | 10/10 OK |
| P1.7 | impresa (CAD) | Absorción de agua (perfil de P1-INT-04) | P1-INT-04 | Ganancia (m7 − m0)/m0 ≤ 1 % en los 3 cubos. Referencia: PETG macizo ~0,3 % a saturación [VERIFICADO: research/R05 S11]; impreso absorbe más por porosidad [VERIFICADO: R05 S14]. | 1/1 OK |
| P1.9 | taller (sin CAD) | Semipasadores de corte (juego de 2) en dispositivo de corte doble | P1-PMP-05, P1-PMP-03, P1-DRV-01 | Los 3 juegos cortan entre 26,8 y 40,2 N·m (0,8–1,2 × T_cut) = 54–80 N en el brazo, con las 2 secciones cortadas en la cara muñón ↔ manguito (una por semipasador) y los restos salen con el botador. Si cortan abajo: barra más blanda (no T6) → cambiar de barra; si cortan arriba: no subir el Ø, revisar material y agujeros (filo vivo); si un solo semipasador corta: agujeros desalineados. | 5/5 OK |
| P1.10 | taller (sin CAD) | Hinchamiento de los bujes POM-C a 48 h en agua | P1-PMP-07, P1-PMP-11 | P1-PMP-07: Ø int a 48 h ≥ Ø eje P1-DRV-01 medido + 0,10 mm (≥ 20,10 con Ø nominal 20; CAD 20,2); P1-PMP-11: Ø int a 48 h ≥ Ø perno con hombro de dirección medido + 0,05 mm (≥ 8,05 con Ø nominal 8; CAD 8,1). Si no: repasar el Ø int con escariador al Ø del CAD y repetir. | 2/2 OK |
| P1.11 | taller (sin CAD) | Prueba hidrostática de carcasa + estator + tobera | P1-PMP-01, P1-PMP-02, P1-PMP-06, P1-PMP-08 | A 0,30 MPa (3,0 bar) durante 15 min: caída ≤ 2 %, 0 gotas en la brida de entrada, en la luz entre bridas carcasa ↔ tobera (O-ring radial), en el puerto y en los tornillos anti-rotación del estator (papel tisú), y deformación permanente del Ø del asiento ≤ 0,02 mm. Sin aire en la prueba (seguridad: una prueba con aire guarda energía). | 5/5 OK |
| P1.12 | taller (sin CAD) | Holgura de punta impulsor ↔ anillo de desgaste | P1-PMP-02, P1-PMP-03 | Todas las lecturas entre 0,30 y 0,40 mm y diferencia máx. − mín. ≤ 0,05 mm; el impulsor gira sin roce. Menor: repasar el anillo (no el impulsor); mayor: anillo nuevo (el anillo es la pieza de desgaste). | 2/2 OK |
<!-- /FAB:ensayos -->

Datos de partida de los criterios: <!--V:manifest.params.pmp_pin_n:-->2<!--/V--> semipasadores por juego (cada uno cruza una vez la superficie del eje: 2 secciones de corte, como el pasador pasante de sizing), Ø<!--V:sizing.mech.shear_pin.d_mm:.1f-->3.5<!--/V--> mm de <!--V:sizing.mech.shear_pin.material:-->Al 6061-T6<!--/V-->, corte de diseño <!--V:sizing.mech.shear_pin.T_cut_Nm:.1f-->33.5<!--/V--> N·m contra <!--V:est.loads.structural_bomba.loads_used.T_ctrl:.1f-->18.6<!--/V--> N·m máximos del controlador; presión de diseño de la bomba <!--V:est.loads.structural_bomba.loads_used.p_design_Pa:.0f-->200000<!--/V--> Pa (prueba × 1,5, research/R12 §7.2); presión de la chimenea <!--V:est.loads.structural_toma.p_max_Pa:.0f-->67222<!--/V--> Pa; holgura de punta <!--V:sizing.pump.tip_clearance_mm:.3f-->0.396<!--/V--> mm sobre Ø<!--V:sizing.pump.D_mm:-->132<!--/V--> mm.

### 7.3 Procedimientos

<!-- FAB:procedimientos -->
- **P1.1 — Peine de holguras (Ø reales de las piezas impresas)** (impresa). Medir cada agujero con pernos patrón (vástagos de broca) o calibre; probar la pieza real: tornillo M5/M6 A4, cuerpo del prensaestopas M16, cuerpo del interruptor de cordón y de la seta (Ø22), tuerca ISO 4032 M6 A4 en los hexágonos (empujada con el pulgar desde la cara de cama).
- **P1.4 — Inserto térmico M5 inox en el nervio de P1-ELE-01** (impresa). Tornillo M5 A4 con cáncamo en el inserto; pasador M8 en el agujero inferior a una horquilla fija; tirar con dinamómetro a ~10 N/s. 3 probetas. Además: torque de giro del inserto con llave dinamométrica (o brazo + dinamómetro). *Instalación:* Inserto M5 de inox 300 (en zona húmeda solo inox: latón se descinfica, research/R05 A10.2) [VERIFICADO: research/R05 S29 existen]; soldador a ~250–260 °C [ESTIMADO: research/R05 A10.3]; hundir el 90 % con la punta y el resto con herramienta plana [VERIFICADO: R05 S28].
- **P1.6 — Tapa con O-ring de cara y purga (réplica de P1-INT-04) a la presión de la chimenea** (impresa). Medir ranura (profundidad y ancho) y planitud de las dos caras de sello (regla + galgas). Cordón NBR70 con empalme a tope y grasa de silicona; 4 × M6 A4 con arandela ancha apretados a mano (perillas, como INT-04); purga M6 × 12 con arandela de estanqueidad. Conjunto con la tapa arriba (como en el bote), apoyado en dos listones (la válvula queda abajo); un dedo de agua adentro para mojar el O-ring. (1) +p con inflador con manómetro, 15 min, agua jabonosa por fuera; (2) −p con bomba de vacío manual (válvula sin obús), 15 min; (3) 20 ciclos abrir/cerrar tapa y purga, repetir (1). Con aire la energía guardada es chica (cavidad 56 cm³: p·V = 3,8 J [CALCULADO]); igual, gafas.
- **P1.7 — Absorción de agua (perfil de P1-INT-04)** (impresa). Acondicionar 48 h con desecante (no secar a 65 °C: Tg ~69 °C); pesar m0 (balanza 0,01 g). Sumergir 7 días en agua con 25 g/L de sal a temperatura ambiente; secar la superficie con papel y pesar m7 en < 1 min. Opcional: seguir a 30 días (saturación en semanas, research/R05 A2). *Si no pasa:* Revisar secado del filamento y solape relleno–perímetro del perfil sellado; la tapa es reemplazable (el CAD está) — inspeccionarla cada temporada.
- **P1.9 — Semipasadores de corte (juego de 2) en dispositivo de corte doble** (taller). Tornear 3 juegos de 2 semipasadores Ø3,5 × 29,5 de la misma barra que los 3 juegos de repuesto (medir Ø con micrómetro y largo con calibre). Muñón Ø20 en la morsa; manguito Ø60 exterior con agujero Ø20 H7; agujero transversal Ø3,55 pasante en muñón y manguito (taladro + escariador, alineados juntos). Meter un semipasador desde cada lado hasta que se toquen en el centro (enrasados con el Ø exterior del manguito). Tirar del brazo de 500 mm con el dinamómetro, despacio (~10 s hasta el corte); anotar F máx. Después: sacar los restos con un botador corto desde un lado (es el procedimiento de cambio en el eje real).
- **P1.10 — Hinchamiento de los bujes POM-C a 48 h en agua** (taller). Tornear los bujes, prensarlos en su alojamiento definitivo (estator / orejas de la placa de espejo, ya anodizados). Medir Ø int en 3 alturas × 2 direcciones con pernos patrón o alesómetro, y el Ø real del eje/perno con micrómetro. Sumergir el conjunto 48 h en agua del lugar a temperatura ambiente; secar y medir dentro de 10 min. El eje/perno real tiene que girar a mano sin puntos duros.
- **P1.11 — Prueba hidrostática de carcasa + estator + tobera** (taller). Armar carcasa + anillo + estator; O-ring radial engrasado (silicona) en la espiga de la tobera, meterla en el asiento sin pellizcarlo (chaflán de entrada) y apretar los 8 × M5 en cruz; medir con galgas la luz entre bridas (diseño 0,25 mm, igual en los 8 tornillos: si es 0, la espiga no aprieta la camisa del estator). Entrada: brida ciega con rebaje H7 para el espigón Ø140 y O-ring de cara. Salida Ø87,1: tapón con O-ring radial y varilla roscada central M5 A4-70 hasta la brida ciega de entrada: pasa por el agujero Ø6 de la punta del cono de cola del estator y por el buje (sin impulsor); carga del tapón 1788 N a p_ensayo → σ = 126 MPa sobre A_s 14,2 mm², FS 3,6 contra Rp0,2 del A4-70. Tuercas con arandela de estanqueidad (bonded) en el tapón y en la brida ciega. Alternativa sin varilla: yugo exterior que apoya el tapón contra el resalte de la tobera. Medir el Ø del asiento del anillo antes. Llenar de agua purgando el aire por el puerto G1/8 (arriba); bomba de prueba hidrostática manual (o bomba de engrase + manómetro 0–6 bar). Subir en 3 escalones, retener 15 min a p_ensayo, bajar, desarmar y medir el asiento.
- **P1.12 — Holgura de punta impulsor ↔ anillo de desgaste** (taller). Anillo montado en la carcasa; impulsor en el eje con rodamientos y pasador. Galgas de espesores entre la punta de cada uno de los 5 álabes y el anillo, en la entrada, al medio y a la salida de la punta, girando a mano; repetir en 4 posiciones angulares del eje. Control cruzado: Ø del anillo con alesómetro y Ø de puntas del impulsor en el torno (reloj comparador sobre mandril).
<!-- /FAB:procedimientos -->

**Banco común:** dinamómetro con palanca de madera dura (F_probeta = relación de brazos × F_dinamómetro − tara) para P1.4; brazo sobre el manguito (con un juego de semipasadores, uno desde cada lado) para P1.9; inflador con manómetro y bomba de vacío manual de purgar frenos para P1.6; bomba de prueba hidrostática manual (o bomba de engrase + manómetro 0–6 bar) para P1.11; galgas de espesores, alesómetro y micrómetro para P1.10/P1.12. Anotar cada resultado con fecha, lote de filamento/barra y foto.

### 7.4 Ajustes que usa el CAD (escaneo de las piezas impresas en orientación de impresión)

<!-- FAB:ajustes -->
| Pieza | Nominal | Ø / e/c en CAD [mm] | Holgura CAD [mm] | Eje en impresión | Se calibra con |
|---|---|---|---|---|---|
| P1-CTL-02 | Ø5 | 5,50 | +0,50 | vertical | P1.1A |
| P1-CTL-03 | Ø5 | 5,50 | +0,50 | vertical | P1.1A |
| P1-ELE-02 | Ø5 | 5,50 | +0,50 | vertical | P1.1A |
| P1-ELE-01 | Ø6 | 6,40 | +0,40 | vertical | P1.1A |
| P1-INT-04 | Ø6 | 6,40 | +0,40 | vertical | P1.1A |
| P1-CTL-02 | Ø16 | 16,50 | +0,50 | horizontal | P1.1H (horizontal) |
| P1-CTL-03 | Ø22 | 22,00 | +0,00 | inclinado (32° de la vertical) | P1.1A |
| P1-INT-04 | tuerca M6 (e/c) | 10,30 | +0,30 | bolsillo abierto a la cama | P1.1A (fila hexagonal) |
<!-- /FAB:ajustes -->

---

## 8. Secuencia de fabricación y plazos estimados

| # | Paso | Depende de | Quién | Plazo estimado | Etiqueta |
|---|---|---|---|---|---|
| 0 | **Medir:** torno (volteo, entre puntos), casco real (recorte de la toma, espejo), consola | — | Gaspar / Jorge | 1 día | [SUPUESTO] |
| 1 | Pedir materia prima (MP-*), cordón O-ring, insertos, Tef-Gel; filamento PETG HDT ≥ 70 °C y secarlo | 0 | Gaspar | 1 semana (Dold/DE a DK) | [ESTIMADO: research/R08b §1] |
| 2 | Cotizar y pedir **CNC 5 ejes** (impulsor, estator) con STEP + tabla de ángulos: es el camino crítico | — | Gaspar | 3–6 semanas | [ESTIMADO: R11 §6; SLM ~72 h + torneado si se elige esa ruta] |
| 3 | Imprimir **probetas** P1.1/P1.4/P1.6/P1.7 y arrancar P1.7 (7 días en agua) | 1 | Gaspar | ~1 semana de impresora | [CALCULADO: horas de PrusaSlicer, §2.6] |
| 4 | Corte láser de chapas (S-LASER) | 0, 1 | taller | 1–2 semanas | [ESTIMADO] |
| 5 | Torno propio: eje, pasadores (+ P1.9), bujes POM, pernos, pin band, caja del sello, tapa de rodamiento; espaciadores del pivote P1-REV-02 y émbolos P1-REV-04 (cuerpo, tapa, perno y pomo, §3) | 1 | Gaspar | 2–3 semanas de taller propio | [ESTIMADO] |
| 6 | Torneado de taller: carcasa, tobera fija, placa de espejo, boquilla (S-TURN-*, S-MILL-STE) | 1 | taller | 2–3 semanas | [ESTIMADO] |
| 7 | Soldadura: conducto + placa base (refrentado, prueba de estanqueidad §4), bucket (después: Ø24 H7, agujeros de traba con plantilla y buje P1-REV-03, §4), soporte de reenvío P1-REV-09, pórtico, soporte del motor, rejilla | 4 | taller + Gaspar | 1–2 semanas | [ESTIMADO] |
| 8 | Anodizado duro del lote (carcasa, estator, tobera, boquilla, poste) | 2, 6 | anodizador | 1–2 semanas | [ESTIMADO] |
| 9 | Prensar bujes (P1-REV-03: escariar Ø20,1 después) y **P1.10**; anillo de desgaste en la carcasa; tornear Ø de puntas del impulsor y **P1.12**; balanceo | 2, 5, 8 | Gaspar / taller | 1 semana | [ESTIMADO] |
| 10 | Montaje de la bomba y **P1.11** (hidrostática) | 9 | Gaspar | 2 días | [ESTIMADO] |
| 11 | Imprimir piezas del jet (tapa P1-INT-04 tras pasar P1.6; controlador y consola tras P1.1/P1.4) | 3 | Gaspar | ~1 semana de impresora | [CALCULADO: horas de PrusaSlicer, §2.6] |
| 12 | Montaje en el casco (06_ensamblaje_y_pruebas.md) | 7, 10, 11 | Jorge + Gaspar | — | — |

Camino crítico: CNC del impulsor/estator → anodizado → P1.10/P1.12 → P1.11. Con todo en paralelo, **≈ 6–9 semanas** desde el pedido [ESTIMADO: suma de los plazos más largos de la tabla].

---

## 9. Scripts y cómo regenerar

```bash
python 04_diseno/probetas/build_probetas.py          # probetas + ensayos + tablas FAB de este documento (exit ≠ 0 si falla)
python prusaslicer/validar_perfiles.py               # perfiles: formato, límites, claves y laminado (PrusaSlicer CLI)
python 04_diseno/probetas/tabla_fabricacion.py       # solo las tablas FAB (sin reconstruir probetas)
python docgen.py; python tools_check_md.py 05_fabricacion.md   # valores <!--V--> del texto
python -m pytest tests/test_probetas.py -q           # manifold, envolvente, criterios, claves críticas de los .ini
```

---

## 10. Hallazgos para el diseño (de esta pasada de fabricación)

1. **Masa y tiempo de impresión reales mayores que el manifest:** PrusaSlicer da más gramos y casi el doble de horas (tabla §2.6): el `solid_frac` de P1-CTL-02/03 y P1-ELE-01 no cuenta que 5–6 perímetros llenan paredes de 3–6 mm, y `inputs.yaml printer.print_rate_g_h` es optimista. Afecta plan y BOM de filamento, no la resistencia.
2. **Prueba de estanqueidad del conducto (S-WELD-INT): 0,3 bar de aire** es menos que la presión de cierre y el golpe de fondo (§4). Conviene sumar una hidrostática con agua a 1,5 × la presión de cierre (o justificar los 0,3 bar): decisión del grupo de la toma/BOM.
3. **P1-CTL-10 (palanca del bucket, 6061-T6 con escalón soldado):** `estructural.json` verifica la flexión **en el escalón** con el admisible del 6061-T6 sin soldar; con el de ZAT (como hace `structural_tren.py` para el 6082) el FS queda en aproximadamente la mitad. Sigue ≥ 2, pero el modelo no es coherente con la soldadura: avisar a DIRECCIÓN.
4. **Límite del torno y entre puntos:** el anillo de desgaste y el eje dependen de medidas del torno que todavía nadie tomó (§3).
5. **P1-CTL-03:** los agujeros de panel de los pulsadores están inclinados respecto de la vertical (cara a ~32°) y en Ø nominal sin holgura; P1.1A los calibra en vertical. Si el interruptor real no entra, sumar la holgura que dé P1.1 en el CAD.
6. **Bujes POM:** la holgura mínima tras 48 h (P1.10) es un [SUPUESTO] (50 % de la del CAD) a confirmar con el fabricante del buje (Vesconite/igus) si se compra en vez de tornear.
7. **Auditoría Pass 3 (semipasadores y O-ring radial) — resuelto en las probetas:** P1.9 ensaya ahora **juegos de 2 semipasadores** (uno desde cada lado) en el mismo dispositivo de corte doble, con manguito del Ø del asiento del anillo retén para que queden enrasados como en el cubo; P1.11 arma la tobera con su **O-ring radial** en la espiga y los 8 × M5, mide con galgas la luz entre bridas antes de presurizar y tapa la salida con un tapón de O-ring radial y una varilla central dimensionada desde params (la mayor métrica A4-70 que pasa por el agujero de la punta del cono de cola del estator, Ø<!--V:manifest.params.pmp_tail_hole_d:.0f-->6<!--/V--> mm; tensión y FS con la carga del tapón en la tabla §7.3; ronda 2, R2-D04) — la tobera no tiene brida de salida. La rejilla (9 pletinas, aislada con PTFE) ya figura así en S-WELD-316 de `bom.csv`.
8. **Materia prima de P1-REV-02 y P1-REV-04 (ronda 4):** `bom.py` dimensiona la barra con la caja envolvente del sólido del manifest, que en P1-REV-02 incluye el tornillo M12 (Ø36 × 67,5 → `MP-316-D40` de 2 × 82 mm, cuando el espaciador mide 34,3 mm [CALCULADO: P1-REV-02.shoulder_L + pilot_L]) y en P1-REV-04 la contratuerca y los dos cuerpos cruzados (→ `MP-316-BLQ-P1-REV-04`, un **bloque** 47 × 80 × 41, cuando lo que hace falta es barra Ø25–28 para cuerpo y tapa y Ø18 para el perno, §3). `inputs.yaml bom.stock.overrides` no tiene una forma para «varias barras por pieza»: hace falta ese cambio en `bom.py` (o que el manifest exporte la envolvente de lo torneado). Hasta entonces, comprar según §3, no según la fila MP.
9. **Ensayo P1.10:** la tabla generada (`04_diseno/probetas`) ensaya P1-PMP-07 y P1-PMP-11; falta sumar los bujes P1-REV-03 del bucket (Ø20,1 sobre el muñón Ø20 h7 del espaciador), con el mismo criterio que P1-PMP-11 (≥ Ø del muñón medido + 0,05 a las 48 h [SUPUESTO: igual que P1-PMP-11]). PENDIENTES P1.7.
10. **Comentario del perfil `prusaslicer/P1_impresion_cubiertas_0.20.ini`:** dice que 5 perímetros dejan macizas «las paredes de 3,2–3,5 mm»; la caja P1-CTL-02 tiene ahora paredes de 5 mm (§2.2).
