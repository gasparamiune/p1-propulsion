# 03 — Arquitectura: qué propulsión para el jet boat de Jorge

Matriz ponderada de seis arquitecturas, recomendación y plan de fabricación. Los puntajes viven en
[`inputs.yaml → architecture_matrix`](inputs.yaml) y los procesa [`arquitectura.py`](arquitectura.py); la
comparación comprar / construir la hace [`comparacion.py`](comparacion.py). Los números del modelo van entre
marcadores `<!--V:…-->` (los actualiza `docgen.py`).

Etiquetas: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO].

## 1. Requisitos

| # | Requisito | Valor | Origen | Etiqueta |
|---|---|---|---|---|
| R1 | Casco | 2,30 × 0,80 m, puntal 0,52 m, espejo 0,42 m | Plano de Jorge | [VERIFICADO: plano; geometría fina ESTIMADA, R10b §4.3] |
| R2 | Ocupantes | 1 piloto, sentado dentro del casco, con volante | Plano de Jorge; R10b H6; R13 §1.4 | [VERIFICADO] |
| R3 | Propulsión | Waterjet inboard, motor directo, toma enrasada, boquilla direccional, nada colgando del espejo | Plano de Jorge (y foto de la JT132) | [VERIFICADO: D-01] |
| R4 | Velocidad | ≥ 30 km/h a > 300 m de la costa; 5 kn dentro de los 300 m (4 kn en Als Sund) | Plano de Jorge; R07; R13 §3 | [VERIFICADO] |
| R5 | Reversa y freno | Bucket obligatorio | R10b H10 | [VERIFICADO: "no jet thrust, no steering"] |
| R6 | Cebado | Eje del impulsor ≥ 20 mm bajo la flotación en reposo | R10a §3.2, §8 | [VERIFICADO / SUPUESTO margen] |
| R7 | Tensión | ≤ 50 V CC nominal (12S LFP) | ISO 16315 3.1; R06; R13 §4 | [VERIFICADO; D-13] |
| R8 | Speedbåd | Potencia pico < 19 kW | BEK 749/2020; R13 §2 | [VERIFICADO] |
| R9 | Corte de emergencia | Cordón + seta, contactor, corte < 1 s | Requisito del usuario; R06 §3.5 | [VERIFICADO] |
| R10 | Factores de seguridad | ≥ 3 en piezas impresas, ≥ 2 en metales | Requisito del usuario / `inputs.yaml` | [VERIFICADO] / [SUPUESTO] |
| R11 | Fabricación | Torno manual, Ender-3 S1 (210 × 210 × 260 mm, PETG), servicios comprables | Datos del usuario | [VERIFICADO] |
| R12 | Caída de tensión | ≤ 3 % | Requisito del usuario | [VERIFICADO] |
| R13 | Estabilidad | Pasar el ensayo de escora E1 antes de navegar | R13 §5 | [SUPUESTO: criterio] |

## 2. Matriz ponderada

Puntajes de 1 a 5 [SUPUESTO, justificados abajo]. Sensibilidad: cada peso ±50 % y Monte Carlo de 20 000
juegos de pesos (Dirichlet alrededor de los nominales) [CALCULADO: `arquitectura.py`].

<!-- AUTO:arch -->
| Opción | seguridad (18 %) | concepto (12 %) | prestaciones (14 %) | eficiencia_5kn (8 %) | poca_prof (8 %) | viabilidad (10 %) | costo (10 %) | tiempo (7 %) | reparabilidad (6 %) | riesgo (7 %) | **Total** | Gana en MC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **B** Waterjet comercial AWT JT132 (Ø130) + el tren eléctrico de este diseño | 4 | 5 | 4 | 2 | 3 | 4 | 4 | 4 | 3 | 3 | **3.75** | 89 % |
| **C** Bomba de jet ski usada (Sea-Doo Spark 140) adaptada | 4 | 5 | 3 | 2 | 3 | 3 | 4 | 3 | 4 | 3 | **3.50** | 1 % |
| **A** Waterjet propio (impulsor CNC + bomba Al + toma soldada) — este diseño | 4 | 5 | 4 | 2 | 3 | 2 | 3 | 2 | 3 | 2 | **3.24** | 0 % |
| **E** Cola larga / surface drive (diseño P1 anterior, adaptado) | 3 | 1 | 2 | 4 | 5 | 4 | 4 | 3 | 5 | 3 | **3.18** | 6 % |
| **D** Fueraborda eléctrico de 3–6 kW con hélice | 2 | 1 | 4 | 4 | 2 | 5 | 2 | 5 | 2 | 5 | **3.04** | 3 % |
| **F** Hélice entubada en túnel bajo el casco (pump-jet / rim-drive) | 4 | 3 | 3 | 3 | 2 | 2 | 3 | 2 | 2 | 2 | **2.80** | 0 % |

Sensibilidad: variando cada peso ±50 % (renormalizado), el ganador **no cambia** en ninguno de los 20 casos.
Monte Carlo (20000 juegos de pesos Dirichlet alrededor de los nominales): B 89 %, C 1 %, D 3 %, E 6 %.
<!-- /AUTO:arch -->

**Pesos.** Seguridad primero (<!--V:arch.weights.0:.0%-->18%<!--/V-->): el piloto puede caer al agua junto a la
propulsión y el agua está fría (R07 §3). Después prestaciones (<!--V:arch.weights.2:.0%-->14%<!--/V-->) y el concepto que
pidió Jorge (<!--V:arch.weights.1:.0%-->12%<!--/V-->). Eficiencia a 5 kn pesa
<!--V:arch.weights.3:.0%-->8%<!--/V--> aunque sea el uso más frecuente dentro de los 300 m: el pedido es un bote que planee.

### 2.1 Justificación de cada puntaje

| Criterio | A — bomba propia | B — JT132 + este tren | C — bomba de Spark usada | D — fueraborda eléctrico | E — cola larga | F — hélice entubada |
|---|---|---|---|---|---|---|
| Seguridad | <!--V:arch.scores.0.0:.0f-->4<!--/V-->: sin hélice expuesta; rejilla y bucket; pasador de corte | <!--V:arch.scores.1.0:.0f-->4<!--/V-->: igual que A | <!--V:arch.scores.2.0:.0f-->4<!--/V-->: igual que A | <!--V:arch.scores.3.0:.0f-->2<!--/V-->: hélice abierta junto a un piloto que cae al agua y a bañistas | <!--V:arch.scores.4.0:.0f-->3<!--/V-->: hélice en superficie, detrás del espejo, con protector | <!--V:arch.scores.5.0:.0f-->4<!--/V-->: hélice dentro de un túnel |
| Concepto de Jorge | <!--V:arch.scores.0.1:.0f-->5<!--/V-->: jet inboard, nada colgando | <!--V:arch.scores.1.1:.0f-->5<!--/V-->: es la bomba de su foto | <!--V:arch.scores.2.1:.0f-->5<!--/V-->: jet inboard | <!--V:arch.scores.3.1:.0f-->1<!--/V-->: motor colgado del espejo | <!--V:arch.scores.4.1:.0f-->1<!--/V-->: cola larga colgada | <!--V:arch.scores.5.1:.0f-->3<!--/V-->: nada cuelga, pero no es jet y necesita timón |
| Prestaciones | <!--V:arch.scores.0.2:.0f-->4<!--/V-->: planea; <!--V:cmp.A_vmax_kmh:.1f-->25.1<!--/V--> km/h sostenidos [CALCULADO] | <!--V:arch.scores.1.2:.0f-->4<!--/V-->: <!--V:cmp.B_vmax_kmh:.1f-->27.4<!--/V--> km/h con la geometría de la JT132 [CALCULADO] | <!--V:arch.scores.2.2:.0f-->3<!--/V-->: bomba de 60–90 hp a 5 kW, fuera de su punto (R11 §4) | <!--V:arch.scores.3.2:.0f-->4<!--/V-->: una hélice rinde bien a 25–30 km/h | <!--V:arch.scores.4.2:.0f-->2<!--/V-->: diseñada para 6 km/h en desplazamiento | <!--V:arch.scores.5.2:.0f-->3<!--/V-->: buena a baja velocidad, pierde en planeo por el túnel |
| Eficiencia a 5 kn | <!--V:arch.scores.0.3:.0f-->2<!--/V-->: η del chorro a 5 kn <!--V:sizing.performance.legal.eta_jet:.2f-->0.33<!--/V--> [CALCULADO] | <!--V:arch.scores.1.3:.0f-->2<!--/V-->: igual (jet) | <!--V:arch.scores.2.3:.0f-->2<!--/V-->: igual (jet) | <!--V:arch.scores.3.3:.0f-->4<!--/V-->: hélice | <!--V:arch.scores.4.3:.0f-->4<!--/V-->: hélice grande y lenta | <!--V:arch.scores.5.3:.0f-->3<!--/V-->: hélice con pérdidas de túnel |
| Poca profundidad | <!--V:arch.scores.0.4:.0f-->3<!--/V-->: nada bajo el casco, pero la toma succiona arena; ~30 cm de luz en desplazamiento (R03 S12) | <!--V:arch.scores.1.4:.0f-->3<!--/V-->: igual | <!--V:arch.scores.2.4:.0f-->3<!--/V-->: igual | <!--V:arch.scores.3.4:.0f-->2<!--/V-->: pata y hélice bajo el casco | <!--V:arch.scores.4.4:.0f-->5<!--/V-->: la cola se levanta | <!--V:arch.scores.5.4:.0f-->2<!--/V-->: túnel bajo el fondo, aspira lo que hay |
| Viabilidad con torno + Ender-3 | <!--V:arch.scores.0.5:.0f-->2<!--/V-->: impulsor y estator CNC 5 ejes, toma soldada, holgura 0,4 mm: depende de servicios | <!--V:arch.scores.1.5:.0f-->4<!--/V-->: se compra la bomba; queda adaptar la toma al fondo | <!--V:arch.scores.2.5:.0f-->3<!--/V-->: repuestos fuera de la UE; carcasa y toma a adaptar | <!--V:arch.scores.3.5:.0f-->5<!--/V-->: se compra entero | <!--V:arch.scores.4.5:.0f-->4<!--/V-->: diseño anterior existente, a adaptar | <!--V:arch.scores.5.5:.0f-->2<!--/V-->: túnel en el casco + motor sumergido o eje |
| Costo | <!--V:arch.scores.0.6:.0f-->3<!--/V-->: los servicios de fabricación pesan (<!--V:bom.services_eur:.0f-->3910<!--/V--> € en la BOM) | <!--V:arch.scores.1.6:.0f-->4<!--/V-->: JT132 puesta en DK <!--V:cmp.B_jt132_landed_eur_min:.0f-->1437<!--/V-->–<!--V:cmp.B_jt132_landed_eur_max:.0f-->1549<!--/V--> € [ESTIMADO] | <!--V:arch.scores.2.6:.0f-->4<!--/V-->: impulsor + anillo de Spark <!--V:cmp.spark_parts_eur:.0f-->537<!--/V--> € [VERIFICADO: R11 §4] | <!--V:arch.scores.3.6:.0f-->2<!--/V-->: fueraborda eléctrico comercial de esta potencia [ESTIMADO] | <!--V:arch.scores.4.6:.0f-->4<!--/V-->: reutiliza el diseño P1 anterior | <!--V:arch.scores.5.6:.0f-->3<!--/V-->: casco + propulsor a medida |
| Tiempo al prototipo | <!--V:arch.scores.0.7:.0f-->2<!--/V-->: CNC, soldaduras y ajuste de holgura | <!--V:arch.scores.1.7:.0f-->4<!--/V-->: cotizar e importar | <!--V:arch.scores.2.7:.0f-->3<!--/V-->: conseguir y adaptar | <!--V:arch.scores.3.7:.0f-->5<!--/V-->: inmediato | <!--V:arch.scores.4.7:.0f-->3<!--/V-->: adaptar | <!--V:arch.scores.5.7:.0f-->2<!--/V-->: desarrollo |
| Reparabilidad | <!--V:arch.scores.0.8:.0f-->3<!--/V-->: planos propios, pero impulsor y estator por servicio | <!--V:arch.scores.1.8:.0f-->3<!--/V-->: repuestos del fabricante chino | <!--V:arch.scores.2.8:.0f-->4<!--/V-->: repuestos de Spark abundantes | <!--V:arch.scores.3.8:.0f-->2<!--/V-->: producto cerrado | <!--V:arch.scores.4.8:.0f-->5<!--/V-->: todo torneable en casa | <!--V:arch.scores.5.8:.0f-->2<!--/V-->: motor sumergido / túnel |
| Riesgo técnico | <!--V:arch.scores.0.9:.0f-->2<!--/V-->: bomba sin ensayo; η, curva y cavitación estimadas | <!--V:arch.scores.1.9:.0f-->3<!--/V-->: curva desconocida; toma y cebado a confirmar | <!--V:arch.scores.2.9:.0f-->3<!--/V-->: bomba fuera de su punto; toma a adaptar | <!--V:arch.scores.3.9:.0f-->5<!--/V-->: producto probado | <!--V:arch.scores.4.9:.0f-->3<!--/V-->: probado en otro casco y otro uso | <!--V:arch.scores.5.9:.0f-->2<!--/V-->: rozamiento y freno hidrodinámico en proyectos DIY (R03 §1, D3–D5) |

**Lectura.** B gana (<!--V:arch.totals.B:.2f-->3.75<!--/V-->) y lo sigue haciendo en el
<!--V:arch.mc_win_frac.B:.0%-->89%<!--/V--> de los juegos de pesos del Monte Carlo; A queda en
<!--V:arch.totals.A:.2f-->3.24<!--/V-->. La diferencia entre A y B está entera en viabilidad, costo, tiempo y riesgo: en
seguridad, concepto y prestaciones son iguales. D y E ganan en eficiencia a 5 kn y en riesgo, pero no son lo
que pidió Jorge.

## 3. Recomendación

**Pedir ya la cotización de la AWT JT132 (opción B) con el tren eléctrico, la refrigeración, los mandos y el
firmware de este paquete, y tener A (bomba propia) como plan completo y fabricable si B no cierra (D-05).**
Antes de cualquiera de las dos: resolver la estabilidad del casco (§5, riesgo 1).

| Magnitud | A — bomba propia | B — JT132 | Etiqueta |
|---|---|---|---|
| Masa de la unidad de jet | <!--V:cmp.A_jet_mass_kg:.1f-->20.1<!--/V--> kg (toma + bomba + dirección + bucket, CAD) | <!--V:cmp.B_jet_mass_kg:.1f-->12.0<!--/V--> kg | [CALCULADO] / [VERIFICADO: R11 §4] |
| Masa total | <!--V:sizing.masses.total_kg:.0f-->217<!--/V--> kg | <!--V:cmp.B_mass_total_kg:.0f-->206<!--/V--> kg | [CALCULADO] |
| V máx. sostenida | <!--V:cmp.A_vmax_kmh:.1f-->25.1<!--/V--> km/h | <!--V:cmp.B_vmax_kmh:.1f-->27.4<!--/V--> km/h | [CALCULADO] |
| Margen mínimo en la joroba | <!--V:cmp.A_hump_margin:.0%-->-6%<!--/V--> | <!--V:cmp.B_hump_margin:.0%-->5%<!--/V--> | [CALCULADO] |
| S a V máx. (límite 3,5) | <!--V:sizing.performance.top.S:.2f-->3.45<!--/V--> | <!--V:cmp.B_S_top:.2f-->3.05<!--/V--> | [CALCULADO] |
| P de batería a 5 kn | <!--V:sizing.performance.legal.P_bat:.0f-->1724<!--/V--> W | <!--V:cmp.B_P_bat_legal_W:.0f-->1786<!--/V--> W | [CALCULADO] |
| Bomba | Impulsor y estator CNC, carcasa y tobera de taller, toma soldada | <!--V:cmp.B_jt132_landed_eur_min:.0f-->1437<!--/V-->–<!--V:cmp.B_jt132_landed_eur_max:.0f-->1549<!--/V--> € puesta en DK (FOB + flete + arancel + IVA) | [CALCULADO con precio ESTIMADO: R11 §4] |
| Costo del sistema | <!--V:bom.total_eur:.0f-->10865<!--/V--> € (BOM completa) | total de A − piezas del grupo jet + JT132 puesta en DK | [CALCULADO: `bom.py`, `comparacion.py`] |
| Núcleo común (motor + controlador + batería + cargador) | <!--V:sizing.selection.cost_core_eur:.0f-->1952<!--/V--> € | ídem | [CALCULADO] |

Las prestaciones de B usan el mismo modelo de `sizing.py` con la geometría verificada de la JT132 (Ø130,
tobera Ø70) y el η de diseño del impulsor propio, porque AWT no publica su curva [ESTIMADO]. Con la JT132 el
bote es más liviano y por eso planea con más margen; **ninguna de las dos llega a 30 km/h sostenidos** con
la potencia continua estimada del motor (02 §4.3). Lo que acerca a 30 km/h está en 07 §2.4–2.5.

Referencia comercial del mismo tamaño en planta: Lampuga Air, <!--V:cmp.lampuga.loa_m:.2f-->2.30<!--/V--> ×
<!--V:cmp.lampuga.beam_m:.2f-->0.75<!--/V--> m, <!--V:cmp.lampuga.power_kw:.0f-->10<!--/V--> kW,
<!--V:cmp.lampuga.battery_kwh:.1f-->3.6<!--/V--> kWh, hasta <!--V:cmp.lampuga.v_max_kmh:.0f-->50<!--/V--> km/h
[VERIFICADO: R12 §8], con un equipo de ~55 kg más el piloto: menos de la mitad de la masa de este bote.

**Por qué B primero.**
- Es la bomba que Jorge mostró. Resuelve en una pieza lo que el plano no tenía (R10b H3, H4, H10, H15):
  conducto, sello, holgura metálica, estator, boquilla externa y reversa.
- Es la unidad de jet más liviana, y la masa es la segunda entrada más influyente (02 §10).
- Evita las piezas de este paquete que más dependen de servicios caros y de una precisión que no se puede
  verificar en casa (impulsor 5 ejes, holgura de 0,4 mm).

**Condiciones para comprarla** (si alguna falla, A): AWT confirma por escrito (1) el plano de la brida de
toma y que entra en el fondo del casco; (2) la altura del eje sobre el fondo, para que quede ≥ 20 mm bajo
la flotación en reposo (R10a); (3) la curva H-Q o el empuje con el impulsor estándar a ~4000 rpm y 6 kW; y
(4) el costo puesto en DK no supera ~1500 € [SUPUESTO: D-05].

**Qué se reutiliza de este paquete con B:** motor, controlador, batería, caja de batería y cableado;
refrigeración por agua; kill switch y firmware; mandos (T85, M66, Mach5, consola, palancas con
enclavamiento); pórtico de rodamientos y acople si la JT132 se acopla con eje propio; flotación y achique.
Se reemplazan los grupos de toma, bomba, dirección y reversa (P1-INT, P1-PMP, P1-STE, P1-REV).

**Cuándo A.** Si AWT no responde o no confirma las cuatro condiciones, o si el casco medido obliga a una toma
que la JT132 no admite. A está completo: CAD, planos, BOM, casos estructurales y verificación de
interferencias en `04_diseno/`.

**Advertencia de uso (D-01).** Si el uso real es mayormente dentro de los 300 m a 5 kn, el jet es la opción
menos eficiente (η del chorro <!--V:sizing.performance.legal.eta_jet:.2f-->0.33<!--/V--> a 5 kn): D o E rinden más.

## 4. Qué se imprime, qué se mecaniza y qué se compra (D-19)

| Proceso | Piezas | Por qué |
|---|---|---|
| **Impreso en PETG** (Ender-3 S1) | Caja de palancas (P1-CTL-02), soporte del kill switch y la seta (P1-CTL-03), base y capota del controlador (P1-ELE-01/02), tapa de inspección de la toma (P1-INT-04) | Piezas secas o de baja carga que cumplen FS ≥ 3 con los admisibles de R05. Total: <!--V:manifest.totals.printed_mass_g:.0f-->1020<!--/V--> g, <!--V:manifest.totals.printed_hours:.0f-->57<!--/V--> h de impresión [CALCULADO] |
| **Mecanizado por servicio** (CNC 5 ejes, torno de taller) | Impulsor 316L (CNC o SLM + torneado), estator Al 6061-T6, carcasa (P1-PMP-01), tobera fija (P1-PMP-08), placa de espejo (P1-PMP-09), boquilla direccional (P1-STE-01) | Geometría de álabes en 5 ejes; diámetros mayores que el volteo del torno propio [SUPUESTO: 180 mm, medir]; holgura de punta de 0,4 mm |
| **Soldado por servicio** (TIG) | Conducto de la toma sobre la placa base (Al 5083), pórtico de rodamientos y soporte del motor, bucket, rejilla 316 | Límite estanco del casco y piezas de chapa; mismo metal que el casco (5083) para no tener par galvánico |
| **Torno propio** | Eje, pernos y bujes (316, POM), pasador de corte, piezas chicas de mandos | Diámetros chicos y tolerancias de torno manual |
| **Comprado** | Motor, controlador, batería, cargador, sello mecánico, rodamientos 7204 BEP, acople Rotex 24, dirección T85 + M66, cable Mach5, eléctricos y seguridad (contactor, fusible, cordón, seta), achique, espuma | Productos con datos verificados (R11) |

**Por qué no se imprime la bomba** [CALCULADO: `04_diseno/structural_*.py`]:
- Estator de PETG: FS sostenido <!--V:est.loads.structural_bomba.stator_PETG_FS_sust:.2f-->0.31<!--/V--> (hace falta 3) y
  la holgura de punta no se mantiene en PETG (R10b H15) → metal (D-10).
- Conducto de la toma de PETG: haría falta una pared de
  <!--V:est.loads.structural_toma.petg_wall_req_mm:.1f-->19.9<!--/V--> mm para FS 3 a fatiga por el ciclo de presión,
  más dos juntas en el límite estanco → Al 5083 soldado (D-09).
- Boquilla de PETG: FS <!--V:est.loads.structural_direccion.PETG_boquilla.FS:.2f-->0.59<!--/V--> en la oreja del bucket → Al
  6061-T6.

Con B, todo el grupo de bomba, dirección y reversa se compra y la lista de servicios se reduce a la placa de
adaptación de la toma, el pórtico y el soporte del motor.

## 5. Los cinco riesgos principales

| # | Riesgo | Por qué | Mitigación | Prueba que lo cierra |
|---|---|---|---|---|
| 1 | **Estabilidad del casco** (vuelco estando quieto, al subir o al reabordar) | GM = <!--V:sizing.hydrostatics.GM_m:.3f-->0.008<!--/V--> m; correr el piloto 0,1 m da <!--V:sizing.heel_pilot_0p1m_deg:.0f-->79<!--/V-->° en el modelo lineal [CALCULADO]; capacidad 33 CFR 183.33 <!--V:sizing.capacity.persons_gear_kg:.0f-->46<!--/V--> kg; agua < 15 °C fuera del verano | Medir el casco; manga en la flotación ≥ 0,9 m o flotadores laterales; asiento bajo; batería en el fondo; flotación fija y achique (D-04) | Ensayos E1–E4 de R13 §5 (escora con carga desplazada, inundado, reabordaje) **antes** de instalar la electrónica |
| 2 | **No llega a 30 km/h** | V máx. sostenida <!--V:sizing.performance.vmax_cont_kmh:.1f-->25.1<!--/V--> km/h; la potencia continua del motor no está publicada y es la entrada más influyente (02 §10) | Pedir el dato a Maytech; JT132 (menos masa); subir potencia o corriente de batería dentro de ≤ 50 V (07 §2.4) | V máx. con GPS ≥ <!--V:sizing.success.vmax_min_kmh:.1f-->21.3<!--/V--> km/h y prueba térmica de 30 min (02 §11) |
| 3 | **Cavitación, aire en la toma o piedras** | S a V máx. <!--V:sizing.performance.top.S:.2f-->3.45<!--/V--> contra 3,5 de límite; fondo plano y ola corta del fiordo meten aire (R10a §7); una piedra traba el impulsor con ~490 J (R12 §7.6) | Ley anti-cavitación (02 §4.6); toma en crujía sin nada delante; pasador de corte Ø<!--V:sizing.mech.shear_pin.d_mm:.1f-->3.5<!--/V--> mm y repuestos; ralentí en aguas bajas | Rampa de punto fijo sin rpm que sube sin empuje; empuje ≥ <!--V:sizing.success.bollard_min_N:.0f-->532<!--/V--> N; recorrido con ola corta (picos de rpm ≤ 10 %) |
| 4 | **Estanqueidad del límite del casco** (abertura de la toma de <!--V:manifest.params.L_open:.0f-->380<!--/V--> mm de largo en el fondo, pasaje del eje, tapa de inspección) | Una fisura o un sello que falla inunda el bote (R10a §0.3); el sello mecánico no debe girar en seco | Conducto soldado en 5083 con prueba de estanqueidad; sello carbón/SiC con cámara de goteo y testigo; tapa sobre la flotación; achique con alarma; flotación ~100 L | Prueba hidrostática de toma y bomba a 0,3 MPa (R12 §7.2); 24 h a flote amarrado sin agua en la sentina (R10a §8.5) |
| 5 | **Clasificación legal** (vandscooter o speedbåd) | Si fuera vandscooter: prohibido a < 300 m salvo tránsito perpendicular, inutiliza Als Sund; bevis y seguro obligatorios (R13 §1.3) | Cockpit "dentro" del casco con volante, palanca y respaldo (R13 §1.4); potencia pico < 19 kW documentada | Respuesta escrita de Søfartsstyrelsen y de Sønderborg Kommune (R13 §8, Q1–Q4) antes de construir |

El costo y el plazo de fabricar la bomba propia (impulsor CNC, holgura) son el sexto riesgo; se mitigan con
B (§3).
