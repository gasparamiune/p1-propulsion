# 03 — Arquitectura

Elección de la arquitectura de propulsión de P1 por matriz ponderada, plan B, costo comparado,
reparto imprimir / comprar / tornear y los cinco riesgos principales. Etiquetas: [VERIFICADO: fuente] ·
[CALCULADO] · [ESTIMADO: base] · [SUPUESTO]. Los puntajes viven en `inputs.yaml → architecture_matrix`;
el bloque `AUTO:arch` lo regenera `arquitectura.py` y los números entre marcadores `<!--V:…-->` los
actualiza `docgen.py`. Estado al 2026-10-01; tipo de cambio 7,4755 DKK/EUR [VERIFICADO: BCE, `inputs.yaml`].

## 1. Opciones evaluadas

| Id | Opción | Esencia | Evidencia que más pesa |
|---|---|---|---|
| A1 | Fueraborda, motor en pod **seco sellado** | Motor en cápsula bajo el agua con retén dinámico en el eje | Un retén radial pide eje ≥ 45 HRC y Ra 0,2–0,8 µm [VERIFICADO: research/R05 §B6]; el 316 no se templa [ESTIMADO: research/R05 §B6]. Pod DIY: el ingreso de agua fue el problema principal [VERIFICADO: research/R02 C1]; bombeo térmico en pods de eFoil [VERIFICADO: research/R03 §5] |
| A2 | Fueraborda, motor en pod **inundado** | Outrunner o inrunner mojado (estilo eFoil) | En el mar: vida de 10 sesiones a ~3 años, siempre con mantenimiento; un usuario recibió una descarga al tocar la carcasa del ESC [VERIFICADO: research/R03 §5]. Desarme y enjuague tras cada uso [VERIFICADO: research/R06 §0] |
| **A3** | **Cola larga (long-tail) eléctrica — elegida** | Motor seco arriba (Flipsky 6374 190 KV + ESC Flipsky 75100 V2.0), correa HTD-5M <!--V:sizing.selection.z_motor:d-->20<!--/V-->T : <!--V:sizing.selection.z_shaft:d-->40<!--/V-->T, eje AISI 316 Ø16 a 25° dentro de un tubo de Al Ø40×3 con 3 portabujes impresos (bujes igus H370), hélice comprada Minn Kota MKP-32 con pasador de corte 316 Ø2, kick-up con retén, patín fusible y aro protector impreso | Long-tail con motor seco: −33 % de potencia frente a un trolling ya optimizado, medido por el mismo autor [CALCULADO: research/R02 B1]. Surface drive con trim: navegó en ~200 mm de agua [VERIFICADO: research/R02 B5]. Un 6374 sin reducción quemó motores en un long-tail [VERIFICADO: research/R02 B4] → reducción por correa y límite de corriente |
| B | Conversión de trolling motor | Trolling de agua salada + soporte basculante, protector, patín y extensión de caña impresos | Trolling de 55 lb: 620 W, sin basculación protegida, pata de 107 cm [VERIFICADO: research/R04 §B.1, §B.4]. Los trolling con controlador dentro de la carcasa sumergida fallan en salado [VERIFICADO: research/R02 D2] |
| C | Waterjet impreso | Impulsor + estator + tobera impresos (videos V1/V2) | A 6 km/h necesita 1,35–5,4× la potencia al eje de la hélice [CALCULADO: research/R03 §2.3]. V1/V2 no muestran la unidad andando [VERIFICADO: research/R01] |
| D | Hélice entubada / rim-driven | Tobera o motor anular impresos | Hélice con anillo impreso: de 38 A a 100 A a igual velocidad; arena en el entrehierro [VERIFICADO: research/R03 §4]. Tobera Kort: hasta +30 % solo en bollard [VERIFICADO: research/R03 §3] |
| E | Propulsión aérea eléctrica | Hélice de aire (solo comparación) | Sin fuente específica: juicio de ingeniería [SUPUESTO] |
| F | Motor comercial completo (referencia) | Trolling de agua salada 55 lb + LiFePO4 12 V, tal cual. Techo de referencia: fueraborda eléctrico de 1 kW | Riptide Endura C2 55: 5 499 kr; ePropulsion Spirit 1.0 Evo completo: 21 886 kr [VERIFICADO: research/R04 §B.4] |

## 2. Pesos (justificación)

- **Seguridad 18 %** — uso en el mar con personas; manda sobre el alcance (requisito 1).
- **Eficiencia 15 % y costo 12 %** — prioridad declarada del usuario: autonomía + costo.
- **Poca profundidad/arena 10 %** — requisito explícito (basculación, protección, pasador).
- **Viabilidad con PETG/herramientas 10 %** — el proyecto existe para imprimir lo razonable con la Ender-3 S1 y el torno.
- **Sellado 8 %, corrosión 7 %, consecuencia de falla 7 %, reparabilidad 7 %, tiempo 6 %** — agua salobre (11,3–20,5 PSU [VERIFICADO: research/R07 §0]), casco de aluminio, < 300 m de la costa, prototipo.

Los pesos suman 100 % y son [SUPUESTO] de diseño. Los puntajes 1–5 son juicio de ingeniería
[SUPUESTO] apoyado en research/R02–R09; los motivos, con datos, están en §3.2. La sensibilidad de
abajo comprueba que el ganador no depende de un peso puntual ni de un puntaje aislado.

## 3. Matriz ponderada y sensibilidad

<!-- AUTO:arch -->
| Opción | eficiencia (15 %) | seguridad (18 %) | viabilidad_petg (10 %) | sellado (8 %) | corrosion (7 %) | costo (12 %) | tiempo (6 %) | reparabilidad (7 %) | poca_prof (10 %) | falla_mar (7 %) | **Total** | Gana en MC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A3** Cola larga: motor seco arriba + correa + eje inclinado | 4 | 5 | 4 | 5 | 4 | 3 | 3 | 5 | 5 | 4 | **4.25** | 86 % |
| **F** Motor comercial completo (trolling de agua salada 55 lb + LiFePO4) | 3 | 5 | 5 | 5 | 4 | 4 | 5 | 2 | 2 | 4 | **3.93** | 14 % |
| **B** Conversión de trolling motor (soporte kick-up + protector impresos) | 3 | 4 | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 4 | **3.68** | 0 % |
| **A2** Fueraborda con motor en pod inundado | 4 | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 2 | 3 | **2.98** | 0 % |
| **C** Waterjet impreso | 2 | 4 | 2 | 3 | 3 | 3 | 2 | 3 | 4 | 3 | **2.97** | 0 % |
| **E** Propulsión aérea eléctrica (solo comparación) | 1 | 1 | 3 | 5 | 5 | 4 | 3 | 4 | 5 | 2 | **2.96** | 0 % |
| **D** Hélice entubada / rim-driven impreso | 3 | 4 | 2 | 2 | 2 | 3 | 2 | 2 | 3 | 3 | **2.80** | 0 % |
| **A1** Fueraborda con motor en pod seco sellado | 4 | 3 | 2 | 1 | 3 | 3 | 2 | 2 | 2 | 3 | **2.66** | 0 % |

Sensibilidad: variando cada peso ±50 % (renormalizado), el ganador **no cambia** en ninguno de los 20 casos.
Monte Carlo (20000 juegos de pesos Dirichlet alrededor de los nominales): A3 86 %, F 14 %.
<!-- /AUTO:arch -->

### 3.1 Sensibilidad a los puntajes [CALCULADO: sobre `resultados/arquitectura.json`, sin re-correr]

- Margen A3 − F = <!--V:arch.totals.A3:.2f-->4.25<!--/V--> − <!--V:arch.totals.F:.2f-->3.93<!--/V--> = 0,32. B queda en <!--V:arch.totals.B:.2f-->3.68<!--/V-->.
- Bajar 1 punto a A3 en **un** criterio cualquiera no cambia el ganador (el peso máximo es 0,18).
- Bajar a la vez eficiencia **y** seguridad de A3 sí lo cambia: A3 3,92 contra F 3,93. De las 120 combinaciones de tres bajas de 1 punto, 44 dejan a A3 empatado o detrás de F.
- Subir 1 o 2 puntos a F en cualquier criterio no lo hace ganar (como mucho 4,20).
- **Lectura:** A3 gana mientras se sostengan sus puntajes de eficiencia y de seguridad. Los dos tienen hoy un punto débil (§3.2): el rendimiento total calculado y tres piezas de PETG con FS < 1 en el FEA (riesgo 3 de §6). Se re-evalúan después de T2/T3 y del rediseño de H-1…H-3.

### 3.2 Motivos de los puntajes

**A3 — cola larga (<!--V:arch.totals.A3:.2f-->4.25<!--/V-->; gana en el <!--V:arch.mc_win_frac.A3:.0%-->86%<!--/V--> del Monte Carlo)**
- **Eficiencia 4.** Hélice grande y lenta con reducción: <!--V:sizing.cruise.design.prop_n_rpm:.0f-->1491<!--/V--> rpm y η0 <!--V:sizing.cruise.design.prop_eta0:.2f-->0.41<!--/V--> en crucero de diseño [CALCULADO: 02 §1]. El long-tail seco gastó un 33 % menos que un trolling optimizado [CALCULADO: research/R02 B1]. **Punto débil:** el rendimiento total batería → R·V de diseño es <!--V:sizing.cruise.design.eta_total:.0%-->29%<!--/V--> [CALCULADO], debajo del 44–55 % máximo de los fuerabordas eléctricos de 1 kW [VERIFICADO: research/R04 §B.1]. Lo bajan el eje a 25° (1 − cos 25° = 9,4 % [CALCULADO]), el aro (−10 % de empuje [ESTIMADO: D-26]) y una hélice de trolling (P/D ≈ 0,4) fuera de la serie B (D-40). El 4 es optimista [SUPUESTO]; con 3, A3 sigue primero (4,10 contra 3,93) [CALCULADO].
- **Seguridad 5.** Ni electrónica ni sellos dinámicos bajo el agua [VERIFICADO: research/R05 §1, R06 §0]. Corte de emergencia por contactor monoestable con cordón y seta; el antichispa MOSFET no cuenta como corte porque falla en corto [VERIFICADO: research/R06 §0; D-22]. Sistema eléctrico flotante, aislado del casco [VERIFICADO: research/R06 §6.4]. **Condición:** el 5 vale solo con H-1…H-3 resueltos (riesgo 3).
- **Viabilidad PETG 4.** Lo impreso queda fuera de la ruta de carga alterna, como pide research/R05 §A6 (f_fatiga 0,06): placa motriz y cartucho en Al (D-25), tubo de Al, pernos de 316. Precio en impresión: <!--V:manifest.totals.printed_mass_g:.0f-->6011<!--/V--> g y <!--V:manifest.totals.printed_hours:.0f-->334<!--/V--> h [CALCULADO: manifest].
- **Sellado 5.** Solo sellos estáticos sobre la flotación (caja ESC con O-ring de 3,53 mm, D-23) y un V-ring excluidor en la boca del tubo. Ningún sello trabaja contra el eje bajo el agua.
- **Corrosión 4, no 5.** El 316 en rendija bajo los bujes pasa a activo (−550 mV) y se pica [VERIFICADO: research/R06 §6.2]. "Propeller shafts made from 316 are usually galvanically protected" [VERIFICADO: research/R05 §A12], y P1 va sin ánodo (D-36).
- **Costo 3.** <!--V:bom.total_eur:.0f-->2255<!--/V--> € con batería [CALCULADO: bom.py]: ~1,7–1,8× el plan B y ~1,9× F (§4.3).
- **Tiempo 3.** 334 h de impresión, más el torneado de eje, pernos, separadores y cartucho y el mecanizado de tres piezas de chapa de Al.
- **Reparabilidad 5.** Todo lo que se rompe está arriba del agua o es estándar y barato: 6202-2RS de Biltema, poleas y correa de Dold, bujes igus, pasadores. Patín y segmentos de aro se reimprimen [VERIFICADO: research/R08b §3–4].
- **Poca profundidad 5.** Kick-up de 25° con retén de 15 N·m que libera con <!--V:sizing.mech.kickup.F_release_at_skeg_fwd_N:.0f-->89<!--/V--> N en el patín [CALCULADO: 02 §8], patín fusible de <!--V:est.loads.F_skeg_fuse_N:.0f-->300<!--/V--> N (D-12) y pasador de corte. La punta de pala queda ≈ 356 mm bajo la flotación, ≈ 158 mm bajo el fondo del espejo [CALCULADO: `sizing.json → layout`]. En research/R02 B5 el trimado del eje permitió navegar en ~200 mm de agua; en P1 el equivalente es bascular la cola y el tornillo de trimado (±5°, D-04).
- **Falla en el mar 4.** Las fallas probables (pasador, correa, patín) se arreglan a bordo con el kit de 06 §9. Si no, remos y ancla (D-35).

**F — trolling de agua salada + LiFePO4, tal cual (<!--V:arch.totals.F:.2f-->3.93<!--/V-->; <!--V:arch.mc_win_frac.F:.0%-->14%<!--/V--> del Monte Carlo)**
- **Eficiencia 3.** 620 W eléctricos (50 A × 12 V) en el Riptide Endura C2 55 [VERIFICADO: research/R04 §B.1]: menos de la mitad de los <!--V:sizing.vmax.design_vmin.P_bat:.0f-->1359<!--/V-->–<!--V:sizing.vmax.nominal_vnom.P_bat:.0f-->1624<!--/V--> W de batería de P1 a V máx [CALCULADO: 02 §1]. Su empuje declarado (0,40 N/W) es optimista en un 10–20 % [CALCULADO: research/R04 §B.2].
- **Seguridad, sellado, viabilidad PETG y tiempo 5.** Producto terminado y garantizado. En salado se recomienda la serie Riptide y se evitan los modelos con controlador dentro de la carcasa sumergida [VERIFICADO: research/R02 D2].
- **Corrosión 4.** Está hecho para salado, pero el Riptide 55 SC trae ánodo de zinc [VERIFICADO: research/R04 §B.1], que en agua salobre protege poco [VERIFICADO: research/R06 §6.3].
- **Costo 4.** ≈ 1 190 € con batería, cargador, protecciones y 10 % de imprevistos [CALCULADO: §4.3].
- **Reparabilidad 2.** Motor sellado y sumergido, sin repuestos de usuario.
- **Poca profundidad 2.** Sin basculación protegida y con una pata de 107 cm para un espejo de 381 mm [VERIFICADO: research/R04 §B.1, §B.4; espejo ESTIMADO: `inputs.yaml`].

**B — conversión de trolling (<!--V:arch.totals.B:.2f-->3.68<!--/V-->).** Lo mismo que F más un soporte basculante, un protector y un patín impresos: sube poca profundidad a 3 y reparabilidad a 3. Pierde un punto en seguridad y en sellado: el soporte impreso entra en la ruta de carga, hereda el riesgo de fluencia del PETG (riesgo 3) y la columna del trolling se sujeta con una abrazadera que no es la de fábrica. Pierde otro en viabilidad PETG y en tiempo, porque hay que diseñar, imprimir y ensayar ese soporte.

**A1 — pod seco sellado (2,66).** Sellado 1: un retén radial necesita eje ≥ 45 HRC, Ra 0,2–0,8 µm y presión ≤ 0,03 MPa [VERIFICADO: research/R05 §B6], y en los pods el bombeo térmico mete agua [VERIFICADO: research/R03 §5]. Viabilidad PETG 2: una cápsula impresa no sella sin mecanizar (Sa 10–24 µm contra Ra ≤ 0,8–1,6 µm requerido [VERIFICADO: research/R05 §1]).

**A2 — pod inundado (2,98).** Corrosión 2: imanes y rodamientos en agua salada, con vida observada de 10 sesiones a ~3 años [VERIFICADO: research/R03 §5]. Su ventaja real, la refrigeración por agua, no hace falta a la potencia de crucero de P1 [VERIFICADO: research/R03 §5].

**C — waterjet impreso (2,97).** Eficiencia 2: con la batería de P1, la autonomía de crucero caería a 0,46–1,1 h [CALCULADO: research/R03 §2.3]. El 4 en poca profundidad es generoso: en desplazamiento el jet necesita ~305 mm de luz bajo su fondo, más su calado [VERIFICADO: research/R03 §2.2]. Con 2 también pierde [CALCULADO].

**D — tobera o rim-driven impreso (2,80).** Corriente ×2,6 con anillo impreso y arena en el entrehierro [VERIFICADO: research/R03 §4]. La tobera Kort gana solo en bollard: queda como experimento de P2 (07).

**E — aérea (2,96), solo comparación.** Seguridad 1: hélice expuesta a la altura de las personas [SUPUESTO]. Eficiencia 1: con el mismo disco y la misma potencia, el empuje estático ideal en aire es ≈ 0,11 del de agua [CALCULADO: T ∝ (ρ·A·P²)^⅓, (1,2/1010)^⅓].

## 4. Recomendación, plan B y costo

### 4.1 Recomendada: A3 cola larga

Gana por 0,32 puntos y en el <!--V:arch.mc_win_frac.A3:.0%-->86%<!--/V--> de 20 000 juegos de pesos aleatorios
[CALCULADO: arquitectura.py]. Lo decisivo: cero sellos dinámicos y cero electrónica bajo el agua salobre, y
una basculación con fusibles mecánicos (patín y pasador) para arena. **Se mantiene si** (1) P0.2 pasa
(capacidad del bote), (2) H-1…H-3 se resuelven antes de T3 y (3) T2 confirma el bollard
(≥ <!--V:sizing.success.bollard_pull_min_N:.0f-->238<!--/V--> N). Si alguna falla y no tiene arreglo en la temporada → plan B.

### 4.2 Plan B (concepto documentado): trolling de agua salada + soporte basculante y protector impresos

**Comprar**

| Ítem | Producto | Precio | Etiqueta |
|---|---|---|---|
| Trolling de agua salada 55 lb, 12 V | Minn Kota Riptide Endura C2 55 (50 A, 620 W, pata 107 cm) | 5 499 kr ≈ 736 € | [VERIFICADO: research/R04 §B.1, S42]; € [CALCULADO] |
| Alternativa | Minn Kota Riptide Transom 55 SC (600 W, 9,6 kg, ánodo de zinc) | 659 € | [VERIFICADO: research/R04 §B.1, S40, S41] |
| Alternativas fuera de DK | Watersnake Venom SXW 54/42 · Newport NV 55 | 3 199 SEK · USD 239,99 | [VERIFICADO: research/R04 §B.1, S44, S46] |
| **No sirve** | Minn Kota Endura C2 30 12 V: es de **agua dulce** ("Hækmonteret ferskvand") | 1 799 kr | [VERIFICADO: research/R08b §0] |
| Batería | 1 × Power Queen 12,8 V 100 Ah (BMS 100 A), 1 280 Wh | ≈ 238 € | [ESTIMADO: mitad del pack de 2 a 475,18 €, research/R08a §4] |
| Cargador | LiTime 14,6 V 10 A (Anderson 50 A) | 65,99 € | [VERIFICADO: research/R08a §5] |
| Protecciones | Fusible MIDI + portafusible HMD4 + desconectador Biltema AFD (los mismos de P1) | ≈ 39 € | [CALCULADO: suma de precios VERIFICADOS en research/R08a §3, §6] |
| Impreso y herrajes | PETG 2–3 kg, A4, pernos 316, émbolos de bola | 80–150 € | [ESTIMADO: precios de research/R08b §7–8] |
| **Total** | Con 10 % de imprevistos, como la BOM de P1; sin envíos | **≈ 1 270–1 350 € (≈ 9 500–10 100 kr)** | [ESTIMADO] |

**Imprimir (reutilizando el diseño de P1):** (i) soporte de popa basculante con retén y tope (familia
MNT-01…MNT-06, con la cuna adaptada a la columna del trolling; diámetro: buscar: Minn Kota Riptide Endura
C2 55 shaft diameter); (ii) aro protector segmentado (PRP-01 re-escalado a la hélice del trolling, a medir)
y patín fusible (PRP-02); (iii) extensión de caña. Valen las mismas reglas: FS ≥ 3 a fluencia, cabo de
seguridad, tuercas A4 cautivas.

**Prestaciones esperadas:** 620 W × η_total 0,30–0,40 = 186–248 W útiles [ESTIMADO: 29 % de P1 en 02 §1;
47 % que el autor de research/R02 B1 estima para un Minn Kota], contra <!--V:sizing.cruise.nominal.P_eff:.0f-->225<!--/V--> W (banda nominal) y <!--V:sizing.cruise.design.P_eff:.0f-->259<!--/V--> W (banda de diseño)
que pide el casco a 6 km/h [CALCULADO: 02 §1]. Resultado: V máx ≈ 5,5–6 km/h con 2 personas, sin reserva
para viento ni corriente [ESTIMADO]. A fondo: 1 152 Wh útiles (DoD 0,90 como en 02 §6) / 620 W ≈ 1,9 h [CALCULADO].

**Ventajas:** días en vez de semanas; producto con garantía; ~55–60 % del costo de P1 [CALCULADO: §4.3].
**Desventajas:** menos de la mitad de la potencia y la mitad de la energía de P1; pata larga para un espejo de 381 mm (la
abrazadera de fábrica: buscar: Minn Kota Endura bracket max transom thickness); motor sumergido no
reparable; el ánodo de zinc del 55 SC protege poco en agua salobre [VERIFICADO: research/R06 §6.3]
(buscar: Minn Kota Riptide aluminium anode).
**Usarlo si:** P0.2 obliga a operar con 1 persona; el objetivo se reduce a ≤ 6 km/h en agua profunda; T1
o T2 de P1 no pasan y hace falta propulsión para la temporada; o H-1…H-3 no se cierran.

### 4.3 Costo comparado (honesto)

| Solución | Costo | Energía | Potencia | Basculación protegida y fusibles mecánicos | Fuente |
|---|---|---|---|---|---|
| **P1 (A3)** | <!--V:bom.total_eur:.0f-->2255<!--/V--> € ≈ <!--V:bom.total_dkk:.0f-->16854<!--/V--> kr; sin batería ni cargador <!--V:bom.fixed_excl_battery_eur:.0f-->1619<!--/V--> € | <!--V:sizing.battery.E_nom_wh:.0f-->2560<!--/V--> Wh | <!--V:sizing.vmax.nominal_vnom.P_shaft_W:.0f-->1228<!--/V--> W al eje a V máx | Sí: kick-up, patín, pasador | [CALCULADO: bom.py, con envíos, IVA de importación y 10 % de imprevistos; <!--V:bom.verified_frac_of_subtotal:.0%-->72%<!--/V--> del subtotal con precio verificado] |
| Plan B | ≈ 1 270–1 350 € ≈ 9 500–10 100 kr | 1 280 Wh | 620 W eléctricos | Kick-up y patín impresos | [ESTIMADO: §4.2] |
| F tal cual | ≈ 1 190 € ≈ 8 860 kr | 1 280 Wh | 620 W eléctricos | No | [CALCULADO: §4.2 sin impresos] |
| ePropulsion Spirit 1.0 Plus + batería | 8 930 + 9 390 = 18 320 kr ≈ 2 451 € | 1 276 Wh | 1 kW | De fábrica | [VERIFICADO: research/R08b §0]; suma [CALCULADO]; si incluye caña y cargador: no verificado |
| ePropulsion Spirit 1.0 Evo completo, DK | 21 886 kr ≈ 2 928 € (motor, batería, caña y cargador) | 1 276 Wh | 1 kW | De fábrica | [VERIFICADO: research/R04 §B.4, S32] |
| ídem, comprado en DE | 2 549 € | 1 276 Wh | 1 kW | De fábrica | [VERIFICADO: research/R04 §B.4, S33]; envío a DK no verificado |
| Spirit Evo + 2.ª batería (la energía de P1) | 31 276 kr ≈ 4 184 € | 2 552 Wh | 1 kW | De fábrica | [CALCULADO] |

El equipo de seguridad para salir (+<!--V:bom.operation_gear_eur:.0f-->270<!--/V--> €, D-35) es igual para todas y no se suma.

**Lectura.**
- P1 cuesta ~1,9× el trolling tal cual y ~1,7–1,8× el plan B [CALCULADO].
- Frente al fueraborda de 1 kW comprado en DK cuesta un 23 % menos, y un 8 % menos que el Spirit Plus con batería [CALCULADO]. A igual energía (dos baterías) cuesta un 46 % menos [CALCULADO].
- research/R04 §B.4 fija el criterio: el DIY se justifica si cuesta "bastante menos" que 19 000–21 900 kr **y** da ~1 kW, basculación protegida y marcha atrás. P1 queda 11–23 % debajo [CALCULADO]: cumple en lo técnico y apenas en el precio.
- Ese margen no incluye la mano de obra (334 h de impresión, torneado, montaje). El 28 % del subtotal todavía es precio estimado [CALCULADO: bom_resumen.json].
- El fueraborda comercial es además más rápido: 7,6–8,0 km/h medidos con 1 kW en botes chicos [VERIFICADO: research/R04 §B.4]. P1 da <!--V:sizing.vmax.design_vmin.V_kmh:.1f-->6.7<!--/V-->–<!--V:sizing.vmax.nominal_vnom.V_kmh:.1f-->7.4<!--/V--> km/h [CALCULADO: 02 §1].

**Veredicto:** si el objetivo fuera solo "6 km/h al menor costo", conviene el plan B o F. P1 se justifica por
el doble de energía y potencia que un trolling, la basculación con fusibles mecánicos para arena, la
reparabilidad con repuestos estándar y el aprendizaje; no por el precio.

## 5. Se imprime / se compra / se tornea

| Subsistema | Se imprime (PETG) | Se compra | Se tornea / mecaniza |
|---|---|---|---|
| Montaje al espejo y dirección | MNT-01 abrazadera en C + plato de dirección; MNT-02 zapatas (×2); MNT-03 base de horquilla; MNT-04 mejillas (×2); MNT-05 cuna basculante; MNT-06 tapa de cuna | Tornillos de apriete M12 A4 con mango en T; émbolos de bola M12 inox (retén); arandela UHMW/PTFE Ø90; tope de goma Ø25; tornillería A4 Comstedt; Tef-Gel y arandelas de nylon | MNT-07 perno de dirección y MNT-08 perno de basculación (316); MNT-09 y MNT-10 bujes de POM-C |
| Tren motriz (seco) | HSG-02 puente del rodamiento B; HSG-03 cubrecorrea; HSG-05 capó ventilado | Motor Flipsky 6374 190 KV; poleas Dold HTD-5M de <!--V:sizing.selection.z_motor:d-->20<!--/V-->T (bore 8) y <!--V:sizing.selection.z_shaft:d-->40<!--/V-->T; correa HTD-5M 15 mm de <!--V:sizing.mech.belt.length_std_mm:.0f-->405<!--/V--> mm (+1 de repuesto); rodamientos 6202-2RS Biltema (2 + 1, zona seca, D-37) | HSG-01 placa motriz Al 6082-T6 de 6 mm (D-25); DRV-08 cartucho del rodamiento A (Al); DRV-03 separadores del puente, DRV-09 y DRV-10 separadores de la pila del eje (316); re-mandrinado de la polea del eje a Ø15 H7 (plano DRV-06) |
| Eje y cola | DRV-02 portabujes (×3) | Bujes igus iglidur H370SM-1618-20 (2 por portabuje + 1, D-38); tubo de cola Al 6061-T6 Ø40×3; V-ring excluidor; barra 316/316L Ø16 h9 (**no 1.4301**) | DRV-01 eje AISI 316 Ø16 con tramo Ø15 y pila apretada por tuerca M12 (D-07) |
| Hélice y protección | PRP-01 aro protector (6 segmentos); PRP-02 patín fusible; PRP-05 placa antiventilación; STR-01 carcasa inferior | Hélice Minn Kota MKP-32 con tuerca y pin (485 kr [VERIFICADO: research/R08b §5]) | PRP-04 pasadores de corte AISI 316 Ø<!--V:sizing.mech.shear_pin.d_std_mm:.1f-->2.0<!--/V--> (1 + 5, del mismo lote, plano PRP-04); asiento de la hélice al bore **medido** (P0.7) |
| Caña y mando | HSG-04 abrazaderas de caña (×2); ELE-03 puño del acelerador; ELE-04 collar del sensor hall; SAF-01 soporte del kill switch | Tubo de caña Al 6061-T6 Ø30×3 (HSG-06); sensor hall A1324 + imanes; Arduino Nano; conectores IP68 de 4 y 2 polos | HSG-07 placa de caña Al 6082-T6 de 10 mm |
| Electrónica y potencia | ELE-01 caja del ESC (interior 160×110×45, D-20) | ESC Flipsky 75100 V2.0; antichispa Flipsky (solo arranque suave); contactor monoestable + cordón Watski + seta; fusible MIDI 58 V + portafusible; desconectador Biltema AFD; Anderson SB50; cable 16 y 10 mm²; prensaestopas M20/M16; respiradero; cordón de O-ring NBR 3,53 mm; disipador de aletas con R_th ≤ <!--V:sizing.thermal_esc.heatsink.R_hs_required_K_W:.2f-->0.58<!--/V--> K/W; 2 × Power Queen 12 V 100 Ah en serie + cargador 29,2 V 20 A; cajas de batería Biltema | ELE-02 tapa-disipador Al de 4 mm (taladrar, refrentar la cara de sellado) |

Sin ánodo de sacrificio (D-36). Detalle de cantidades, links y precios en `bom.csv`; piezas, masas y
orientación de impresión en 04_diseno/README.md.

## 6. Cinco riesgos principales y mitigación

| # | Riesgo y dato actual | Consecuencia | Mitigación | Prueba que lo cierra (pasa si…) |
|---|---|---|---|---|
| 1 | **Capacidad del bote.** Carga útil <!--V:sizing.masses.payload_kg:.0f-->248<!--/V--> kg contra capacidad estimada <!--V:sizing.masses.capacity_kg:.0f-->160<!--/V--> kg (<!--V:sizing.masses.capacity_ratio:.0%-->155%<!--/V-->) [ESTIMADO: research/R04 §A.3, regla USCG; D-16]; francobordo calculado <!--V:sizing.hydrostatics.freeboard_m:.2f-->0.18<!--/V--> m [CALCULADO]. Un casco < 2,5 m puede no traer placa [ESTIMADO: research/R04 §A.1] | Embarque de agua con ola, vuelco; agua < 15 °C fuera de temporada [VERIFICADO: research/R07 §0] | P0.2 antes de comprar nada. Si no pasa: 1 adulto, o batería LFP24_50 (9,6 kg) [VERIFICADO: research/R08a §4]. Solo en calma, chalecos puestos, < 300 m (FMEA F2) | **P0.2:** carga útil ≤ placa **y** francobordo en popa ≥ 150 mm con 2 personas [SUPUESTO: criterio de PENDIENTES] |
| 2 | **Medidas reales de la hélice MKP-32.** D 254 mm, paso 102 mm, bore 12,7 mm y 2 palas son [ESTIMADO] (D-06); η0 fuera de la serie B (D-40). De ahí salen el asiento del eje (Ø<!--V:sizing.mech.shaft.d_prop_seat_mm:.1f-->12.7<!--/V--> mm), el pasador, el aro y el patín | Eje de 316 torneado inservible (la barra 316 no se consigue en tienda abierta [VERIFICADO: research/R08b §2]); rpm, relación de poleas y autonomía distintas; aro sin la holgura de 6 mm [ESTIMADO: research/R03 §3] | Comprar la hélice primero (485 kr) y medir D, paso, bore, ranura del pin, retención y cubo (P0.7); cargar en `propeller.options.MKP32` y correr `run_all.py`; no tornear DRV-01 antes. Bore < 12 mm → otra hélice | **P0.7:** `run_all.py` en verde con los valores medidos; **T2.2:** bollard ≥ <!--V:sizing.success.bollard_pull_min_N:.0f-->238<!--/V--> N; T3 con GPS para ajustar `propeller.efficiency_factor` |
| 3 | **Fatiga y fluencia del PETG.** `structural.py` da <!--V:est.n_fail:d-->0<!--/V--> fallas, pero el FEA 3D da FS 0,32 a fluencia en el puente de la C (MNT-01, apriete 2,5 N·m), 0,74 en la tapa de cuna con la cola trabada (MNT-06) y 0,86 en las ranuras de tuercas de las mejillas (MNT-04; 2,20 con p99), objetivo 3 [CALCULADO: 04_diseno/fea/README.md; 06 §10 H-1…H-3]. Admisibles con f_creep 0,35 y f_fatiga 0,06 [VERIFICADO: research/R05 §A7] | La C se abre o la tapa se aplasta: la unidad se suelta con la hélice girando (FMEA F1 y F3, S = 9) | Rediseño antes de T3: puente de la C con t ≥ 38,5 mm o menos brazo o apriete [CALCULADO: FEA]; apoyo del tope en MNT-06; arandelas y limitadores de compresión metálicos en MNT-04 [ESTIMADO: research/R05 §A5]; re-correr el FEA. Ruta de carga alterna en metal (D-25); cabo de seguridad; inspección PU.3 en cada salida; PETG con HDT ≥ 70 °C (D-29) | **FEA** con FS ≥ 3 en las tres piezas; **T0.M6:** apertura de la C ≤ 0,5 mm en 24 h; **P1.3:** tuerca cautiva ≥ 2,1 kN; **P1.5:** pérdida en agua salada ≤ 25 % |
| 4 | **Estanqueidad y térmico de la caja ESC.** Caja PETG impresa con O-ring NBR de 3,53 mm (D-23); una cara impresa no sella sin refrentar [VERIFICADO: research/R05 §1]; faltan pasos de cable (H-10). El ESC pierde <!--V:sizing.thermal_esc.esc_cruise.P_loss_esc_W:.0f-->27<!--/V--> W en crucero; el disipador necesita R_th ≤ <!--V:sizing.thermal_esc.heatsink.R_hs_required_K_W:.2f-->0.58<!--/V--> K/W para que la caja no pase de 50 °C; a V máx sostenida llegaría a <!--V:sizing.thermal_esc.heatsink.T_vmax_steady_C:.0f-->60<!--/V--> °C [CALCULADO: 02 §5.2] | Agua en el VESC: pérdida de propulsión (K1 sigue cortando). Sin barniz, el aire salino corroe un VESC en semanas [VERIFICADO: research/R03 §5]. Recorte térmico o PETG > 50 °C | Cara refrentada y lijada; epoxi interior (PETG sin tratar, entre los peores en ensayo de cajas [VERIFICADO: research/R05, hallazgos]); un cable por prensaestopas; respiradero contra bombeo térmico [VERIFICADO: research/R03 §5]; barniz conformal en el VESC; caja a la sombra; la V máx es "por ratos" (8 min, 02 §5.1). Plan B: caja comercial IP67 BOX4U con ventana en la tapa y ELE-02 como tapa-disipador (D-20) | **P1.6:** 24 h a 0,5 m, papel seco; **T1.1–T1.3:** 30 min a 0,5 m con 0 g de agua, ciclo térmico, 20 aperturas; **T2.5:** 30 min a crucero con la tapa ELE-02 ≤ 50 °C |
| 5 | **Pasador de corte y galvánica del grupo sumergido.** Pasador 316 Ø<!--V:sizing.mech.shear_pin.d_std_mm:.1f-->2.0<!--/V--> mm: corta a <!--V:sizing.mech.shear_pin.Q_shear_Nm:.1f-->12.4<!--/V--> N·m (≈ 2× los <!--V:sizing.mech.Q_normal_max_Nm:.1f-->6.6<!--/V--> N·m normales) con τ_u [ESTIMADO: 0,6·Su]; FS Goodman en crucero <!--V:sizing.mech.shear_pin.fatigue_cruise.fs_goodman:.2f-->1.46<!--/V--> [CALCULADO]. El 316 en rendija bajo los bujes se pica [VERIFICADO: research/R06 §6.2, R05 §A12]; sin ánodo (D-36) | Corte prematuro: sin propulsión con viento de tierra W/SW [VERIFICADO: research/R07 §4.1]. Si no corta, el golpe pasa a correa, placa y abrazadera. Picado del eje en el asiento de la hélice | Calibrar con 3 pasadores del lote (P1.9) y usar solo ese lote; cambio cada 10 h; 5 repuestos y botador a bordo. Enjuague con agua dulce; cola basculada fuera del agua y escurrida [VERIFICADO: research/R05 §A12]; Tef-Gel y nylon en A4 sobre Al. Si aparecen picaduras o la hélice final es de Al: buje adaptador Ø16→Ø25 + ánodo Tecnoseal Al Ø25 (96 kr [VERIFICADO: research/R08b §6]) | **P1.9:** corta entre 0,8 y 1,2 × 12,4 N·m; **T0.M8:** eje ↔ tubo y tornillos ↔ casco > 1 MΩ [ESTIMADO: research/R06 §6.4]; inspección de picaduras por temporada (06 §9) |

**Otros riesgos abiertos** (detalle en el FMEA y en los bloqueos de 06 §8 y §10):
- **Térmico del motor (H-7):** <!--V:sizing.thermal.cruise_design.T_motor_steady_C:.0f-->93<!--/V--> °C estacionario en crucero de diseño, contra el límite de 85 °C del VESC [VERIFICADO: research/R09 §6]; llegaría en ≈ <!--V:sizing.thermal.cruise_design.t_to_limit_min:.0f-->20<!--/V--> min [CALCULADO]. R_th del motor [ESTIMADO]. Lo cierra T2.5.
- **Límite legal:** 5 kn a < 300 m de la costa [VERIFICADO: research/R07 §1.2]. Con 1 persona el modelo da <!--V:sizing.legal_speed.vmax_light_low_kmh:.1f-->11.1<!--/V--> km/h, así que va el tope de <!--V:sizing.legal_speed.erpm_cap:.0f-->25137<!--/V--> ERPM [CALCULADO: D-30]; 06 §10 registra que el README de electrónica ponía 30 000 (H-8). Lo cierran T0.M9 y T3 (media ≤ 9,0 km/h con 1 persona).
- **Autonomía con poco margen:** <!--V:sizing.cruise.autonomy_design_h:.2f-->2.53<!--/V--> h de diseño contra 2,4 h exigidas (2 h + 20 %) [CALCULADO]. Calibrar R(v) por remolque (P0.3) antes de comprar la batería; si no alcanza, crucero a 5,5 km/h.
