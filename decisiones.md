# Registro de decisiones y supuestos — P1-J (waterjet del jet boat de Jorge)

Formato: **Decisión** · Alternativas · Justificación · Etiqueta · *Qué cambia si el dato real difiere*.
Todos los valores numéricos viven en [`inputs.yaml`](inputs.yaml) o salen de `resultados/*.json`
(marcadores `<!--V:…-->`, que `docgen.py` actualiza); acá se explica el porqué.

## Requisitos y casco

**D-01 Cambio de arquitectura: de cola larga para un jon boat a waterjet eléctrico inboard para el jet boat de Jorge.**
- Alternativas: seguir con la cola larga (2 personas, 6 km/h); adaptar la cola larga al casco nuevo (opción E de la matriz).
- Justificación: Jorge mostró el tipo de motor que necesita (su plano "Waterjet para jet boat 2,30 m", su croquis de propulsor en chapa, su hoja de impulsor y una foto de la AWT JT132). Los requisitos pasan a ser los de su plano: 1 piloto, ≥ 30 km/h, motor directo de ~5 kW, toma enrasada, boquilla direccional y reversa.
- [VERIFICADO: referencias/2026-09-26_plano_preliminar_waterjet_jorge.png; pedido del usuario].
- *Si difiere:* si el uso real es mayormente dentro de 300 m (5 kn), un jet es la opción menos eficiente (matriz 03 §2, criterio eficiencia_5kn); revisar.

**D-02 Casco: el de Jorge (2,30 × 0,80 m, puntal 0,52 m, espejo 0,42 m) leído del plano.**
- Alternativas: ninguna; el plano no tiene escala única (R10b §4.1).
- Justificación: es el casco al que va la propulsión. Fondo, pantoque y astilla muerta se leyeron de la vista trasera.
- [ESTIMADO: research/R10b §4.3].
- *Si difiere:* medir el casco (PENDIENTES P0.1) y actualizar `boat.*`; cambian calado, cebado, resistencia, estabilidad y la placa de la toma.

**D-03 Masa de diseño con el CAD real: <!--V:sizing.masses.total_kg:.0f-->217<!--/V--> kg (1 piloto de 90 kg, batería, unidad de jet del CAD).**
- Alternativas: los 150 kg del plano de Jorge.
- Justificación: 150 kg no cierra (R10b §4.2: 165–242 kg). La masa de la unidad de jet sale del CAD (manifest) y la toma `sizing.py`.
- [CALCULADO].
- *Si difiere:* la masa es la 2.ª entrada más influyente en la V máx. (02 §10).

**D-04 La estabilidad del casco es el RIESGO N.º 1 y bloquea la navegación hasta resolverla.**
- Justificación: con 0,80 m de manga y el piloto sentado alto, GM = <!--V:sizing.hydrostatics.GM_m:.3f-->0.008<!--/V--> m [CALCULADO]: correr el piloto 0,1 m a una banda escora <!--V:sizing.heel_pilot_0p1m_deg:.0f-->79<!--/V-->° en el modelo lineal (o sea: vuelca). La propulsión no lo resuelve; es un cambio de casco (manga en la flotación ≥ 0,9 m, R10b H1, o flotadores laterales, asiento más bajo).
- [CALCULADO con casco ESTIMADO].
- *Si difiere:* ensayo de escora con carga desplazada (R13 §5) antes de cualquier prueba con motor.

## Arquitectura

**D-05 Recomendación: pedir cotización de la AWT JT132 en paralelo (opción B) y usar este diseño (A) si no cierra.**
- Alternativas: A (bomba propia, este paquete), C (bomba de Sea-Doo Spark usada), D (fueraborda eléctrico), E (cola larga), F (hélice entubada).
- Justificación: la matriz ponderada da B primero (<!--V:arch.totals.B:.2f-->3.75<!--/V--> contra <!--V:arch.totals.A:.2f-->3.24<!--/V--> de A) y gana en el <!--V:arch.mc_win_frac.B:.0%-->89%<!--/V--> del Monte Carlo de pesos: es la misma bomba de la foto de Jorge, más liviana (12 kg contra <!--V:cmp.A_jet_mass_kg:.1f-->20.1<!--/V--> kg de la toma + bomba + dirección propias) y sin impulsor a medida. El tren eléctrico, la toma de refrigeración, los mandos y el firmware de este paquete sirven para las dos.
- [CALCULADO: arquitectura.py; precio de la JT132 ESTIMADO, R11 §4].
- *Si difiere:* si AWT no confirma la brida de toma, la altura del eje (cebado) y la curva de la bomba, o el costo puesto en DK supera ~1 500 €, A queda como camino completo y fabricable.

## Bomba y toma

**D-06 Impulsor axial Ø<!--V:sizing.selection.D_imp_mm:.0f-->132<!--/V-->, 5 álabes, cubo 0,50·D, tobera Ø<!--V:sizing.selection.D_noz_mm:.0f-->82<!--/V-->.**
- Alternativas: el Ø108 / 4 álabes / tobera Ø72 del plano; Ø100–120.
- Justificación: el optimizador (02 §4) elige el diámetro y la tobera que planean con margen al menor costo. Con 217 kg el Ø108 no pasa la joroba con la potencia disponible. 5 álabes y cubo 0,50 por difusión (R12 §3: con cubo 0,40 el factor de difusión llega a 0,60).
- [CALCULADO: sizing.py; R12].
- *Si difiere:* el impulsor se re-diseña solo (triángulos de velocidad en `sizing.json` → CAD → tabla de ángulos para el taller).

**D-07 La bomba se diseña para absorber una potencia intermedia (P_cont + 50 %·(P_pico − P_cont)) a plena tensión.**
- Justificación: con motor directo las rpm las fija la tensión; si la bomba se diseña para la potencia continua, la potencia pico no se puede usar en la joroba. El controlador limita a la potencia continua en crucero.
- [CALCULADO: optimizador, variable design_power_frac].

**D-08 Toma enrasada entera a proa del impulsor (respuesta al comentario de Jorge "la rejilla está muy atrás").**
- Justificación: en el plano la rejilla quedaba a popa de la cara del impulsor, sin conducto y sobre la flotación: la bomba no ceba ni recibe agua (R10a). Ahora el labio está a <!--V:manifest.params.x_lip:.0f-->386<!--/V--> mm y la tangencia de la rampa a <!--V:manifest.params.x_tan:.0f-->766<!--/V--> mm del espejo; la cara del impulsor a <!--V:manifest.params.x_if:.0f-->268<!--/V--> mm. Rampa de 27°, techo de curvatura continua, rejilla de 7 pletinas 316 con luz de 16 mm.
- [CALCULADO: R10a §5, R12 §3.2; CAD P1-INT-*].
- *Si difiere:* si el fondo no es plano en esa zona o tiene refuerzos, la placa base cambia (PENDIENTES P0.1).

**D-09 Conducto de la toma en Al 5083 soldado y placa base enrasada con Sikaflex; NO en PETG.**
- Alternativas: conducto impreso en segmentos (lo que pedía el enfoque original del proyecto).
- Justificación: en PETG hacían falta ~20 mm de pared para FS 3 a fatiga por el ciclo de presión, más dos juntas en el límite estanco del casco; el 5083 es el metal del casco (sin par galvánico).
- [CALCULADO: 04_diseno/structural_toma.py].

**D-10 Carcasa, estator y tobera de Al mecanizado; anillo de desgaste de 316 torneado en sitio; holgura de punta 0,4 mm.**
- Justificación: la holgura no se mantiene en PETG (R10b H15); un estator de PETG da FS 0,33 sostenido. 0,3–0,4 mm con anillo torneado (R12 §3).
- [CALCULADO: structural_bomba.py; R12].

**D-11 Impulsor de 316 mecanizado en 5 ejes (o impreso en 316L SLM con el Ø torneado), arrastrado por un pasador de corte de Al 6061 Ø<!--V:sizing.mech.shear_pin.d_mm:.1f-->3.5<!--/V--> mm.**
- Justificación: una piedra libera ~490 J de energía del rotor; el límite de corriente no protege (R12 §7.6). El pasador corta a <!--V:sizing.mech.shear_pin.T_cut_Nm:.0f-->33<!--/V--> N·m, ~1,8 × el par máximo del controlador.
- [CALCULADO].
- *Si difiere:* calibrar el corte real con el ensayo de probeta (05 §4) y llevar 5 de repuesto.

## Tren

**D-12 Motor directo (sin reducción) Maytech MTI120116 150 KV refrigerado por agua, 12S.**
- Alternativas: Golden Motor HPM5000 (el del plano): 91,5 rpm/V a 48 V y 58,9 a 72 V de catálogo → no llega a las rpm del impulsor sin bobinado a pedido (R11 §1.3).
- Justificación: 4,4 kg, camisa de agua, eje Ø15 con chavetero; único de la clase con precio.
- [VERIFICADO: R11 §1.2; potencia continua no publicada → ESTIMADO 6 kW: pedir el dato a Maytech].
- *Si difiere:* es la entrada más influyente en la V máx. (02 §10).

**D-13 Tensión ≤ 50 V (LFP 12S, 2 × LiTime 36 V 60 Ah en paralelo) en lugar de los 72 V del plano.**
- Justificación: ISO 16315 fija 50 V CC como umbral de tensión segura (R06, R13 §4); a 72 V hacen falta componentes de clase 100 V y monitor de aislamiento (+709 €). No hay packs 13S comerciales en la UE y los "48 V" de catálogo son 16S (58,4 V) (R11 §3).
- [VERIFICADO: R11, R13].
- *Si difiere:* `electrical.allow_72v: true` habilita las opciones de 72 V en el optimizador.

**D-14 Eje 316L Ø20 con dos apoyos: par 7204 BEP en seco (toma todo el empuje) y buje de agua de POM en el cubo del estator; sello mecánico SiC/carbón con cámara de goteo y testigo.**
- Justificación: en voladizo la primera velocidad crítica caía debajo de la de servicio; con el buje queda en <!--V:sizing.mech.crit_ratio:.1f-->3.4<!--/V-->× las rpm máximas. El empuje va por un pórtico de Al sobre el conducto a la placa base, nunca al motor (acople Rotex 24 con juego axial).
- [CALCULADO: structural_tren.py; sizing.py].

**D-15 Refrigeración por agua desde la bomba: orificio Ø4 en la carcasa del estator → controlador → motor → testigo en el espejo.**
- Justificación: como los jetboards; <!--V:sizing.cooling.Q_l_min_top:.1f-->5.2<!--/V--> L/min a V máx. alcanzan con un salto de <!--V:sizing.cooling.dT_water_K:.1f-->1.7<!--/V--> K.
- [CALCULADO].

## Dirección, reversa y control

**D-16 Boquilla direccional de Al ±25° con cable Ultraflex M66 y timonería T85 al volante; topes mecánicos.**
- [VERIFICADO: R11 §7 (productos y precios)].

**D-17 Bucket de reversa obligatorio (Al 5083 soldado) con émbolo de traba; reversa limitada al 50 % de la potencia; enclavamiento mecánico de palancas en la consola.**
- Justificación: sin chorro no hay dirección ni freno (R10b H10). El bucket solo se mueve con el acelerador en 0.
- [CALCULADO: structural_direccion.py; firmware].

**D-18 Perfil "costa" (≤ 5 kn) por defecto al encender, perfil "abierto" a pedido del piloto; kill switch por cordón + contactor.**
- Justificación: dentro de 300 m el límite es 5 kn (R07, R13 §3). El tope de ERPM del perfil COSTA hace cumplir **solo esos 5 kn** (rpm a 5 kn con piloto liviano, banda baja de resistencia y batería llena; sizing `legal_speed`, 5 pares de polos del MTI120116). **No** hace cumplir los 4 kn de Sønderborg Havn (Als Sund) ni los 3 kn de las marinas (R13 §3): ahí la velocidad la controla el piloto con el acelerador (un tercer perfil de 3–4 kn exigiría un selector de 3 posiciones y otra línea al VESC: queda para P2).
- [VERIFICADO: R07, R13].

## Fabricación

**D-19 PETG impreso solo donde da FS ≥ 3: tapa de inspección de la toma, base y capota del controlador, caja de palancas y soporte del kill switch.**
- Alternativas: imprimir conducto, carcasa, estator y boquilla (no cierran a FS 3, D-09/D-10).
- Justificación: la bomba de un jet de 5–10 kW es una pieza de presión y de precisión; se imprime lo que no lo es.
- [CALCULADO].

## Legal

**D-20 Diseño para NO ser "vandscooter" ni "speedbåd".**
- Justificación: la definición de vandscooter pide operar "på – snarere end i – skroget" (BEK 809/2019); el piloto va sentado dentro con volante. Speedbåd desde 19 kW de potencia propulsiva (BEK 749/2020); el pico de este diseño es <!--V:sizing.performance.P_shaft_peak_kW:.1f-->6.6<!--/V--> kW. Los 30 km/h solo son legales a más de 300 m de la costa y nunca en Als Sund (4 kn) ni en Augustenborg Fjord.
- [VERIFICADO: research/R13]. Confirmar por escrito con Søfartsstyrelsen (preguntas en danés en R13 §8).

## Historia

El diseño anterior (cola larga eléctrica para un jon boat de 2 personas a 6 km/h, decisiones D-01 a D-43
de esa versión) quedó en el historial de git: commit `5dfada0`
(`git show 5dfada0:decisiones.md`). De esa versión se reutilizan: el kill switch por cordón + contactor,
el firmware del acelerador (adaptado al bucket), la investigación de materiales PETG (R05), la normativa
general (R07) y el marco de cálculo, CAD, verificación y documentación.
