# Registro de decisiones y supuestos — P1

Formato: **Decisión** · Alternativas · Justificación · Etiqueta · *Qué cambia si el dato real difiere*.
Todos los valores numéricos viven en [`inputs.yaml`](inputs.yaml); aquí se explica el porqué.

## Embarcación y carga

**D-01 Bote de diseño: jon boat de 8 ft (LOA 2,44 m, LWL 2,0 m, manga 1,20 m, fondo 0,95 m, puntal 0,38 m, casco 45 kg).**
- Alternativas: 2,1 m (car-topper) o 2,5 m.
- Justificación: casi no hay jon boats < 2,5 m en catálogos actuales; el del usuario es probablemente un 8 ft estadounidense o similar (research/R04 §A.1). Se toma LWL corta (Fr mayor → más resistencia) y casco pesado: conservador para la propulsión.
- [ESTIMADO: research/R04 §A.4].
- *Si difiere:* medir y actualizar `boat.*`; `run_all.py` recalcula R(v), batería, largo de cola (la hélice se ubica a profundidad fija bajo la flotación) y abrazadera.

**D-02 Carga: 2 × 100 kg + 12 kg de equipo + 5 kg de margen.**
- Alternativas: 75–85 kg por persona (promedio).
- Justificación: conservador para resistencia y empuje.
- [SUPUESTO].
- *Si difiere:* menos masa → menos potencia de crucero (sensibilidad n.º 2, 02 §10).

**D-16 Capacidad del bote estimada en 160 kg y señalada como RIESGO N.º 1.**
- Alternativas: suponer 250 kg (valor inicial, descartado).
- Justificación: los aluminio de fondo plano cargan 34–63 kg/m² (LOA × manga) → 100–185 kg; la regla USCG 33 CFR 183.35 da ≈ 160 kg (research/R04 §A.3). Con 2 adultos + propulsión la carga útil supera la capacidad. No se "sube la placa por cálculo".
- [ESTIMADO: research/R04].
- *Si difiere:* si la placa real es ≥ carga útil, el riesgo baja; si no, operar con 1 adulto + equipo, o 2 personas livianas con batería chica (opción LFP24_50, LiTime 24 V 50 Ah, 9,6 kg, ~1,4 h de autonomía de diseño) y nunca con ola.

## Arquitectura

**D-03 Arquitectura A3 "cola larga" eléctrica (motor seco arriba, correa, eje inclinado, hélice comprada).**
- Alternativas: pod sellado (A1), pod inundado (A2), conversión de trolling (B), waterjet (C), entubada/rim (D), aérea (E), comercial (F).
- Justificación: matriz ponderada 03 (gana con amplio margen y en 86 % de 20 000 pesos aleatorios). Decisivo: **cero sellos dinámicos y cero electrónica sumergida** en agua salobre (research/R05, R06), basculación natural para arena (research/R02 B4: los surface drives regulan la profundidad en marcha).
- [CALCULADO: arquitectura.py].
- *Si difiere:* si la prioridad pasa a "mínimo costo con 6 km/h en agua profunda", conviene F/B (plan B).

**D-04 Ángulo de eje 25° y pivote 135 mm sobre el borde del espejo, 80 mm a popa.**
- Alternativas: 15–20° (más eficiente, cola más larga y ventilación a baja inmersión); 30° (más pérdida axial).
- Justificación: research/R02 B4 — a 15° la hélice ventilaba; a 20° duplicó la velocidad. 25° da 9,4 % de pérdida axial con cola de ~1,1 m. El pivote alto despeja el plato de dirección y la basculación (verificado por `verify_parts.py`).
- [SUPUESTO + CALCULADO].
- *Si difiere:* el tornillo de trimado (MNT-03) permite ±5° in situ; cambiar `architecture.shaft_angle_deg` y regenerar.

**D-17 Basculación máxima 25°.**
- Alternativas: 30–45° (choca el cubrecorrea con la base de la horquilla y el espejo).
- Justificación: con ~22° la punta de la hélice sale del agua; a 25° queda ~110 mm sobre la flotación ([CALCULADO], 02 §8). Más ángulo exige subir el pivote o adelgazar el tren de poleas.
- [CALCULADO + VERIFICADO en software].
- *Si difiere:* si se necesita varar o remolcar con la cola más alta, desmontar la unidad (2 tornillos de apriete).

## Hidrodinámica y propulsor

**D-05 Modelo de resistencia por componentes (ITTC-57 + espejo de Holtrop + olas/joroba calibrable) con banda [0,75; 1,15].**
- Alternativas: Savitsky (fuera de rango: no planea), series sistemáticas (L/∇^⅓ ≈ 3 fuera de rango), Gerr (solo contraste).
- Justificación: ninguna serie cubre un casco tan corto y lleno. La banda se ancló a datos medidos de botes de 2,4–2,75 m (R(6 km/h) = 95–150 N; research/R04 §C.3). Se dimensiona con el borde alto.
- [ESTIMADO + calibración pendiente].
- *Si difiere:* el remolque con dinamómetro (PENDIENTES P2) ajusta `resistance.wave_cw`; batería y relación de poleas se recalculan solas.

**D-06 Hélice comprada (no impresa); el optimizador solo elige entre productos concretos identificados → Minn Kota MKP-32 Weedless Wedge 2 (485 kr, Watski DK, con tuerca y pin). Objetivo de mejora: 10 × 8 in 3 palas de fueraborda eléctrico (no se halló producto).**
- Alternativas: Tohatsu 309B64107-0 aluminio 7,4 × 6 (verificada la ficha, no el precio ni el bore; con bore ~12 mm el asiento del eje no llega a FS 2 en torsión y no cierra la energía de diseño); 10 × 8 de fueraborda eléctrico (−13 % de energía de crucero, pero sin producto con link abierto: research/R08b §5); hélice de PETG.
- Justificación: una hélice de PETG a ~1 kW tiene σ en raíz ≈ 30 MPa frente a una admisible en fatiga < 1,5 MPa (02 §4.4) → inviable. La MKP-32 es la única opción comprable que cumple energía, asiento de eje y calado con la batería elegida (02 §4.1); η0 de crucero calculado ≈ 0,40, coherente con el 40–50 % medido en hélices de trolling (research/R02 S34).
- [CALCULADO + VERIFICADO: research/R04, R08b]; diámetro, paso y bore de la MKP-32 son [ESTIMADO].
- *Si difiere:* **comprar la hélice primero** (PENDIENTES P0.7), medir D, paso, bore, pasador y retención, cargarlos en `propeller.options.MKP32` y correr `run_all.py`: re-dimensiona eje, pasador, protector, patín y carcasa inferior. Si aparece una 10 × 8 de 3 palas con bore ≥ 14 mm, marcar `purchasable: true` y el optimizador la elige.

**D-07 Eje AISI 316 Ø16 con tramo superior Ø15 continuo (rodamientos 6202 + polea) que termina en el hombro Ø16; pila apretada por tuerca M12 desde arriba.**
- Alternativas: Ø12 (FS fatiga 1,1 y torsión en el pasador 1,3: **rechazado**), dúplex 2205 (mejor, más caro).
- Justificación: FS ≥ 2 en todas las secciones (02 §7); velocidad crítica ≥ 4× la máxima. **Corrección de Pasada 2:** la versión anterior tenía el muñón del rodamiento A (Ø15) entre dos tramos Ø16: el rodamiento no se podía montar. Ahora todo lo que va arriba del hombro es ≤ Ø15 (cota verificada en `build_all`), con separadores DRV-09/DRV-10.
- [CALCULADO]. Barra 316/316L: no se halló en tienda abierta (research/R08b §2) → pedir a un metalgrossist; **1.4301 no sirve sumergido**.
- *Si difiere:* el asiento de hélice se tornea al bore real medido.

**D-08 Polea conducida entre dos rodamientos (placa motriz + puente).**
- Alternativas: polea en voladizo con 2 rodamientos en un buje (FS fatiga 1,6 en el muñón).
- Justificación: momento en el eje ÷2; el puente trabaja en tracción en su plano.
- [CALCULADO].

**D-09 Tubo de cola Al 6061-T6 Ø40×3 (no inox 25×1,5).**
- Alternativas: inox 316 25×1,5 (capacidad ~120 N·m → **cede** con el momento dinámico de impacto ≈ 0,19·F·L ≈ 250 N·m), inox 38×2 (pesado), GFRP.
- Justificación: capacidad ≈ 720 N·m, 0,94 kg/m, mismo metal que el casco (no hay par galvánico con él); el eje inox está aislado por bujes de POM.
- [CALCULADO].

**D-10 Basculación con retén de bola (15 N·m) + gravedad; marcha atrás limitada al 50 % de corriente por firmware.**
- Alternativas: traba manual de marcha atrás (si se olvida, anula la protección), amortiguador.
- Justificación: momento de empuje en reversa ≈ 6 N·m ≪ gravedad + retén ≈ 40 N·m (FS ≈ 7); en avance el impacto libera con ~95 N horizontales en el patín.
- [CALCULADO].
- *Si difiere:* la precarga del émbolo es regulable; calibrar con dinamómetro (PENDIENTES P5).

**D-11 Pasador de corte de AISI 316 de diámetro chico (≈ Ø2 mm) → corta a ≈ 2× el torque máximo normal.**
- Alternativas: Al 6061 (versión anterior: en agua salobre, en contacto con el eje 316, es el ánodo del par y pierde sección → corte prematuro e impredecible); latón (descincifica).
- Justificación: protege eje, correa y placa (02 §7); mismo metal que el eje. El diámetro sale de τ_u ≈ 0,6·Su [ESTIMADO] → **calibrar con el ensayo P1.9** antes de navegar.
- [CALCULADO].

**D-12 Patín fusible: rompe con 300 N horizontales en su punta.**
- Justificación: con la cola trabada (reversa o retén atascado), 300 N × 1,13 m mantienen el tubo de Al con FS ≥ 2 y todas las piezas impresas aguas arriba con FS ≥ 3 (02 §9). Arena (contacto largo) no lo rompe; una piedra a 9 km/h sí → se reemplaza (impresión de ~4 h).
- [CALCULADO].

## Montaje

**D-13 Abrazadera en C impresa, tornillos altos (z = −35), apriete ≤ 2,5 N·m, placa de reparto A4 y re-apriete antes de cada salida.**
- Alternativas: pasantes al espejo (perforar el bote), soporte comercial de fueraborda.
- Justificación: con 5 N·m la esquina de la C quedaba en FS 1,7 a creep. La C no depende del apriete para el empuje (apoyo directo). Cabo de seguridad obligatorio.
- [CALCULADO].
- *Si difiere:* espejo de chapa desnuda de 1,2 mm → agregar taco de HDPE ≥ 25 mm (research/R04 §A.5).

**D-14 Dirección por plato giratorio sobre la abrazadera + horquilla de 3 piezas planas.**
- Justificación: el tubo pasa por encima del plato; cada pieza se imprime con la carga en el plano de capas.
- [SUPUESTO + VERIFICADO en software].

**D-15 Caña sobre placa de Al 6082 de 10 mm apretada por los pernos pasantes de la tapa de cuna, desplazada 70 mm a babor.**
- Alternativas: caña en la placa motriz (7 mm: σ ≈ 200 MPa → rechazado), soporte lateral impreso (aplastamiento FS 0,5 → rechazado).
- Justificación: el momento de la caña llega a la cuna como par de fuerzas de compresión.
- [CALCULADO].
- *Si difiere:* la ergonomía (puño ~34 cm sobre el borde) se revisa en P2.

**D-18 Uniones roscadas: tuerca A4 cautiva como estándar; nunca Loctite 243 sobre PETG.**
- Justificación: research/R05 (tuerca cautiva 166 kg vs inserto 119 kg; anaeróbicos fisuran termoplásticos).
- [VERIFICADO: research/R05].

## Eléctrico

**D-19 Batería LiFePO4 24 V: 2 × Power Queen 12,8 V 100 Ah en serie (BMS 100 A c/u), 475,18 € el par, elegida por el optimizador.**
- Alternativas: 16S 51,2 V (V máx 10 km/h, pero 58,4 V supera 48 V nominal y el umbral de 50 V CC de ISO 16315: **rechazada**); 12S LiTime 36 V 50 Ah (399,99 € + cargador 132,99 €: más barata y 7 kg más liviana, pero 1 920 Wh no cubren 2 h + 20 % en la banda alta de diseño por ~2,5 %; ver D-28); LiTime 24 V 50 Ah (309,99 €; BMS de solo 50 A y 1 280 Wh: no cumple energía); 2 × LiTime 12 V 100 Ah (519,98 €: igual energía, +45 €).
- Justificación: mínimo costo (batería + cargador + hélice) que cumple energía, corriente, tensión, cavitación y calado (02 §4.1, §6). Es además la de menor €/kWh verificado (186 €/kWh, research/R08a §4) y la única con BMS de 100 A en la franja de precio. LiFePO4 por seguridad térmica (research/R06). 2 BMS en serie: cargar cada 12 V por separado a 14,6 V de vez en cuando para balancear [ESTIMADO: research/R08a].
- [CALCULADO sobre precios VERIFICADOS: research/R08a §4, 2026-10-01].
- *Si difiere:* si el remolque da la banda nominal o menor, la LiTime 36 V 50 Ah (o una 24 V de 60–80 Ah) pasa a cumplir y se ahorra ~45 € y 7 kg; correr `run_all.py` con los puntos medidos lo decide solo.

**D-20 ESC + antichispa en caja estanca impresa (ELE-01, interior 160×110×45) con tapa de aluminio (ELE-02) y disipador de aletas comprado; caja a la sombra, dentro del bote, cerca de la batería.**
- Alternativas: caja comercial IP67 BOX4U 177×126×56 (14,65 €, research/R08a §10): estanqueidad certificada pero tapa plástica → el ESC (<!--V:sizing.thermal_esc.esc_cruise.P_loss_esc_W:.0f-->28<!--/V--> W de pérdida en crucero con η = 0,97) no tiene camino de calor; ESC refrigerado por agua (P2).
- Justificación: la caja impresa permite tapa de Al como camino térmico. Requisito calculado del disipador: **R_th ≤ <!--V:sizing.thermal_esc.heatsink.R_hs_required_K_W:.2f-->0.57<!--/V--> K/W** para que la caja no pase de 50 °C en crucero (02 §5.2). Los prensaestopas M20 no podían atravesar la pared de 18 mm del reborde (rosca ~10–15 mm): se rebaja la pared a 5 mm en cada prensaestopas y se fija con contratuerca por dentro (verificado con 10 cotas en `build_all`).
- [CALCULADO].
- *Si difiere:* si el ensayo T1 de la caja impresa no pasa (porosidad del PETG), usar la BOX4U IP67 con una ventana fresada en la tapa y la placa ELE-02 atornillada con junta como tapa-disipador.

**D-21 Cable DC 16 mm² (el fusible de 100 A lo protege), fases 10 mm²; fusible ≤ 178 mm del borne.**
- Justificación: caída ≤ 3 % y ampacidad ≥ calibre del fusible (un test detectó 10 mm² + 100 A: corregido).
- [CALCULADO + VERIFICADO: research/R06 ABYC E-11 7"].

**D-22 Corte de emergencia por contactor monoestable cuya bobina pasa por el cordón (contacto cerrado con clip) y la seta; antichispa MOSFET solo como arranque suave; corte por software en el VESC como redundancia.**
- Alternativas: kill switch cortando solo la señal del acelerador (el ESC puede fallar en conducción); antichispa como único corte (los MOSFET fallan en corto, research/R06).
- Justificación: falla segura (cable cortado, clip afuera, conector suelto = motor sin energía); el contactor corta bajo carga.
- [VERIFICADO: research/R06].
- *Si difiere:* si el contactor elegido no publica corte CC ≥ 48 V bajo carga, no se usa.

**D-23 Caja ESC con O-ring de cordón NBR70 Ø3,53 mm en ranura axial (aplastamiento 25 %, llenado 78 %) y cara de sellado refrentada/lijada.**
- Alternativas: cordón 2,5 mm (tolerancia de impresión del mismo orden que el aplastamiento); junta plana de goma espuma.
- Justificación: con 3,53 mm el aplastamiento (0,9 mm) es varias veces la planitud alcanzable en FDM tras lijado (research/R05 S24).
- [VERIFICADO: research/R05].

**D-25 Placa motriz (HSG-01) de aluminio 6082-T6 de 6 mm y cartucho de rodamiento A torneado en Al.**
- Alternativas: placa PETG de 14 mm (FS a fatiga < 3 con los factores de R05: fatiga 0,06 a 10⁷–10⁸ ciclos de paso de pala).
- Justificación: la placa recibe el tiro de la correa y el par a frecuencia de paso de pala; en PETG no cerraba fatiga con FS 3.
- [CALCULADO: structural.py con factores VERIFICADOS en research/R05].

**D-26 Aro protector perfilado (espesor NACA 15 %, cuerda 76 mm) en 6 segmentos con lengüetas; pérdida de empuje 10 % de diseño (rango de sensibilidad 0–25 %).**
- Alternativas: aro plano (más arrastre), tobera Kort (P2, research/R03).
- [ESTIMADO: research/R03].

**D-27 Placa antiventilación impresa (PRP-05) sobre la carcasa inferior.**
- Justificación: con la hélice a 0,4 D de inmersión y ola corta de fiordo, la ventilación es probable (research/R02).
- [ESTIMADO].

**D-28 12S / 36 V (LiTime 36 V 50 Ah + motor 140 KV) queda como alternativa documentada, no como elegida.**
- Justificación: 24 V vs 36 V lo deciden los accesorios marinos baratos (portafusibles de 32 V; desconectadores ≤ 48 V; research/R08a) y la energía: 1 920 Wh fallan la banda alta por ~2,5 %. Se compra el fusible/portafusible de 58 V para no cerrar la puerta.
- [CALCULADO + VERIFICADO: research/R08a].
- *Si difiere:* ver D-19.

**D-29 Admisibles del PETG con factores de R05 (agua 0,75 · temperatura 0,85 · proceso 0,80 · fluencia 0,35 · fatiga 0,06 a 10⁷–10⁸ / 0,15 a 10⁵–10⁶ · eje Z 0,40), T de servicio 50 °C, comprar PETG con HDT ≥ 70 °C.**
- [VERIFICADO: research/R05]. *Si difiere:* las probetas P1.5/P1.7 (PENDIENTES) recalibran `materials.*` y `structural.py` re-verifica.

**D-30 Límite legal 5 kn a < 300 m de la costa → V máx útil 9,26 km/h; tope de ERPM en el VESC ("modo costa") por defecto.**
- Alternativas: sin tope (con 1 persona el modelo da <!--V:sizing.legal_speed.vmax_light_low_kmh:.1f-->11.0<!--/V--> km/h: ilegal); limitador por GPS en el Arduino (P2).
- Justificación: Sejladsreglement Syd- og Sønderjyllands Politi §4 (research/R07). El tope = rpm del motor a 5 kn en el caso más rápido (carga liviana, banda baja, batería llena): <!--V:sizing.legal_speed.erpm_cap:.0f-->26073<!--/V--> ERPM; a plena carga baja la V máx nominal de <!--V:sizing.vmax.nominal_vnom.V_kmh:.1f-->7.4<!--/V--> a <!--V:sizing.legal_speed.vmax_full_load_with_cap_kmh:.1f-->7.4<!--/V--> km/h. Con 2 personas el bote no llega a 5 kn en ninguna banda (8,7 km/h en la baja), así que quitar el tope con 2 a bordo es legal. Los 12 km/h del pedido no se persiguen.
- [VERIFICADO: research/R07 §1.2 + CALCULADO: sizing.py `legal_speed`].
- *Si difiere:* recalibrar el tope con el GPS en T3 (velocidad a tope con 1 persona ≤ 9,0 km/h).

**D-31 Agua: temperatura máxima 24 °C (presión de vapor 2 984 Pa) para cavitación; mínima operativa 12 °C (temporada 15 jun–15 sep); salinidad de corrosión 20,5 PSU.**
- [VERIFICADO: research/R07 §2–3; presión de vapor ESTIMADO por ecuación de Buck]. Impacto en cavitación ≈ −0,6 % del margen.

**D-32 Motor Flipsky 6374 BH 190 KV y ESC Flipsky 75100 V2.0 comprados a Flipsky (China) con IVA de importación 25 % + envío (~105 € en total).**
- Alternativas: AliExpress con precio UE (188–243 € el trío motor/ESC/antichispa; vendedor/versión no verificables); Maytech MTO6374 (eje 26 mm, menos corriente).
- Justificación: datos técnicos publicados y links abiertos (research/R08a). **Declarar el valor real en aduana** (la FAQ del vendedor sugiere lo contrario: es fraude).
- [VERIFICADO: research/R08a §0–2; envío ESTIMADO 45 €].

**D-33 Protecciones con componentes verificados en DK: fusible MIDI 58 V (IMAXX midiOTO) + portafusible HMD4-MG1-H, desconectador Biltema AFD (12–48 V, 275 A), cordón Watski (cerrado con clip), conector Anderson SB50 batería ↔ instalación (el cargador usa el mismo).**
- Riesgo aceptado y ensayado: el interruptor Watski es de 12 V–15 A y se usa a 24 V con ≤ 0,6 A de bobina, con supresor en la bobina (sin arco inductivo en el contacto). Ensayo T0: 200 aperturas con la bobina real sin soldadura de contactos; si falla, relé auxiliar de 24 V.
- [VERIFICADO: research/R08a §3, §6, §8].

**D-34 Sin conversor DC-DC: el BEC 5 V / 1 A del VESC alimenta Arduino Nano + sensor hall (< 50 mA).**
- [VERIFICADO: research/R08a §2]. El Nano solo tiene energía con el contactor cerrado: tras un corte siempre arranca desarmado (firmware: armado solo con acelerador en cero).

**D-35 Equipo de seguridad de operación (2 chalecos con cuello, remos, ancla + cabo, luz todo horizonte, achicador, bolsa estanca) en la BOM como alcance aparte (~270 €).**
- Justificación: research/R07 §1.4 (viento de tierra W/SW dominante; agua < 15 °C fuera de temporada). No se suma al costo del sistema para compararlo con un motor comercial, pero es obligatorio para salir.
- [VERIFICADO requisito: research/R07; precios ESTIMADO].

**D-36 Sin ánodo de sacrificio en P1; aislamiento galvánico por diseño.**
- Alternativas: ánodo de collar de Al en el eje (no existe para Ø16 en DK: el más chico es Ø25, research/R08b §6); ánodo atornillado al tubo.
- Justificación: los metales mojados no forman pares conectados: grupo giratorio todo 316 (eje, pasador, tuerca A4; hélice de compuesto), tubo de Al aislado del eje (bujes igus en portabujes PETG) y del casco (montaje impreso); tornillería A4 sobre Al con Tef-Gel + arandelas/vainas de nylon; sistema eléctrico flotante (sin masa al casco). Si la hélice final es de aluminio, sí hace falta ánodo (buje adaptador Ø16→Ø25 + Tecnoseal Al Ø25, 96 kr).
- [ESTIMADO: criterio de diseño; ver mapa galvánico en 06].
- *Si difiere:* inspección de picaduras por temporada (checklist); si aparecen, agregar ánodo (P2).

**D-37 Rodamientos 6202-2RS de acero al cromo (Biltema) en zona seca, cambio por temporada.**
- Alternativas: 6002 inox (no hallado en tienda abierta), S6202 AISI 420 (Kugellager-Shop ya no envía a DK por la PPWR; posible vía paketshop en Flensburg).
- Justificación: comprable localmente (36,90 kr), en zona seca con sello 2RS. Cartucho Ø42 con brida Ø56; puente con rodamiento B flotante (deslizante y 1 mm de juego axial).
- [VERIFICADO: research/R08b §3].

**D-38 Bujes sumergidos igus iglidur H370 (Ø16×Ø18×20, 2 por portabuje) en portabujes de PETG impresos.**
- Alternativas: POM-C torneado (barra no hallada en tienda abierta), cutlass (no hay para Ø16).
- Justificación: igus recomienda H370 para uso bajo agua; 3,10 €/u; evita tornear 3 bujes. Presión de contacto en el portabuje < 1 MPa.
- [VERIFICADO: research/R08b §3].

**D-39 Poleas Dold Mechatronik (motor 14/16/20 T bore 8; eje 40/48/72 T re-mandrinada a Ø15 H7) y correa de un largo con stock.**
- Justificación: son los dientes y largos que existen (research/R08b §4); el optimizador elige solo entre ellos y `mech.belt_checks` toma el largo con stock más cercano y verifica que la distancia entre centros real quede dentro de los colisos (±8 mm).
- [VERIFICADO: research/R08b §4].

## Software y entorno

**D-24 Blender: `bpy` 5.0.1 (pip) en lugar de Blender 5.1.**
- Justificación: no hay `bpy` 5.1 para Python 3.11; el `.blend` generado abre en Blender 5.1. FEA con gmsh requiere `libglu1-mesa` del sistema.
- [VERIFICADO: instalación en esta sesión].
