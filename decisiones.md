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
- Justificación: la matriz ponderada da B primero (<!--V:arch.totals.B:.2f-->3.47<!--/V--> contra <!--V:arch.totals.A:.2f-->2.96<!--/V--> de A) y gana en el <!--V:arch.mc_win_frac.B:.0%-->62%<!--/V--> del Monte Carlo de pesos: es la misma bomba de la foto de Jorge, más liviana (12 kg contra <!--V:cmp.A_jet_mass_kg:.1f-->20.1<!--/V--> kg de la toma + bomba + dirección propias) y sin impulsor a medida. El tren eléctrico, la toma de refrigeración, los mandos y el firmware de este paquete sirven para las dos.
- [CALCULADO: arquitectura.py; precio de la JT132 ESTIMADO, R11 §4].
- *Si difiere:* si AWT no confirma la brida de toma, la altura del eje (cebado) y la curva de la bomba, o el costo puesto en DK supera ~1 500 €, A queda como camino completo y fabricable.

## Bomba y toma

**D-06 Impulsor axial Ø<!--V:sizing.selection.D_imp_mm:.0f-->132<!--/V-->, 5 álabes, cubo 0,50·D, tobera Ø<!--V:sizing.selection.D_noz_mm:.0f-->87<!--/V-->.**
- Alternativas: el Ø108 / 4 álabes / tobera Ø72 del plano; Ø100–120.
- Justificación: el optimizador (02 §4) elige el diámetro y la tobera de mayor margen en la joroba al menor costo. Con la resistencia corregida (D-21) **ninguna** combinación de 48 V llega al 10 % de margen con la banda alta (estado `<!--V:sizing.status:-->sin_solucion_dura<!--/V-->`); esta queda a ≤ <!--V:sizing.optimization.hump_tie_band:.0%-->1%<!--/V--> (puntos porcentuales, `waterjet.hump_tie_band`) del mejor margen en la joroba (su margen: <!--V:sizing.performance.hump_margin_min:.1%-->-7.3%<!--/V-->) y, dentro de esa banda, es la de mayor V máx. (banda y no redondeo para que la selección no salte con cambios chicos de masa; auditoría ronda 3, R3-04, y ronda 4, M1). Con 217 kg el Ø108 queda peor. 5 álabes y cubo 0,50 por difusión (R12 §3: con cubo 0,40 el factor de difusión llega a 0,60).
- [CALCULADO: sizing.py; R12].
- *Si difiere:* el impulsor se re-diseña solo (triángulos de velocidad en `sizing.json` → CAD → tabla de ángulos para el taller).

**D-07 La bomba se diseña para absorber P_d = P_cont + f·(P_pico − P_cont) a plena tensión; el optimizador elige f = <!--V:sizing.selection.f_pow:.1f-->1.0<!--/V--> (P_d = <!--V:sizing.selection.P_design_W:.0f-->11760<!--/V--> W al eje).**
- Justificación: con motor directo las rpm las fija la tensión; si la bomba se diseña para la potencia continua, la potencia pico no se puede usar en la joroba. El controlador limita a la potencia continua en crucero. El punto de diseño es la V más alta en que el empuje con P_d iguala a R nominal: <!--V:sizing.pump.V_design_kmh:.1f-->43.6<!--/V--> km/h (resuelto sin tope de grilla; es un punto "virtual", 02 §4.4).
- [CALCULADO: optimizador, variable design_power_frac ∈ {0; 0,5; 1}].

**D-08 Toma enrasada entera a proa del impulsor (respuesta al comentario de Jorge "la rejilla está muy atrás").**
- Justificación: en el plano la rejilla quedaba a popa de la cara del impulsor, sin conducto y sobre la flotación: la bomba no ceba ni recibe agua (R10a). Ahora el labio está a <!--V:manifest.params.x_lip:.0f-->386<!--/V--> mm y la tangencia de la rampa a <!--V:manifest.params.x_tan:.0f-->766<!--/V--> mm del espejo; la cara del impulsor a <!--V:manifest.params.x_if:.0f-->268<!--/V--> mm. Rampa de 27°, techo de curvatura continua, rejilla de <!--V:manifest.params.grille_bars:d-->9<!--/V--> pletinas 316 aisladas con PTFE, con luz de <!--V:manifest.params.toma_bar_gap:.1f-->12.2<!--/V--> mm (auditoría C14).
- [CALCULADO: R10a §5, R12 §3.2; CAD P1-INT-*].
- *Si difiere:* si el fondo no es plano en esa zona o tiene refuerzos, la placa base cambia (PENDIENTES P0.1).

**D-09 Conducto de la toma en Al 5083 soldado y placa base enrasada con Sikaflex; NO en PETG.**
- Alternativas: conducto impreso en segmentos (lo que pedía el enfoque original del proyecto).
- Justificación: en PETG hacían falta ~20 mm de pared para FS 3 a fatiga por el ciclo de presión, más dos juntas en el límite estanco del casco; el 5083 es el metal del casco (sin par galvánico).
- [CALCULADO: 04_diseno/structural_toma.py].

**D-10 Carcasa, estator y tobera de Al mecanizado; anillo de desgaste de 316 torneado en sitio; holgura de punta 0,4 mm.**
- Justificación: la holgura no se mantiene en PETG (R10b H15); un estator de PETG da FS 0,33 sostenido. 0,3–0,4 mm con anillo torneado (R12 §3).
- [CALCULADO: structural_bomba.py; R12].

**D-11 Impulsor de 316 mecanizado en 5 ejes (o impreso en 316L SLM con el Ø torneado), arrastrado por un juego de 2 semipasadores de corte de Al 6061 Ø<!--V:sizing.mech.shear_pin.d_mm:.1f-->3.5<!--/V--> mm (equivalen a un pasador en corte doble).**
- Justificación: una piedra libera ~490 J de energía del rotor; el límite de corriente no protege (R12 §7.6). El juego corta a <!--V:sizing.mech.shear_pin.T_cut_Nm:.0f-->33<!--/V--> N·m con τ_u 174 MPa (~1,8 × el par máximo del controlador) y a <!--V:sizing.mech.shear_pin.T_cut_hi_Nm:.0f-->40<!--/V--> N·m con 207 MPa (FS del eje al corte <!--V:sizing.mech.shear_pin.fs_shaft_at_cut_hi:.2f-->1.87<!--/V-->).
- [CALCULADO].
- *Si difiere:* calibrar el corte real con el ensayo de probeta P1.9 (05) y llevar 3 juegos de repuesto (BOM).

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

**D-14 Eje 316L Ø20 con dos apoyos: par 7204 BECBP en O, en seco (toma todo el empuje) y buje de agua de POM en el cubo del estator; sello mecánico SiC/carbón con cámara de goteo y testigo.**
- Justificación: en voladizo la primera velocidad crítica caía debajo de la de servicio; con el buje queda en <!--V:sizing.mech.crit_ratio:.1f-->3.8<!--/V-->× las rpm máximas. El empuje va por un pórtico de Al sobre el conducto a la placa base, nunca al motor (acople Rotex 24 con juego axial).
- [CALCULADO: structural_tren.py; sizing.py].

**D-15 Refrigeración por agua desde la bomba: orificio Ø4 en la carcasa del estator → controlador → motor → testigo en el espejo.**
- Justificación: como los jetboards; <!--V:sizing.cooling.Q_l_min_top:.1f-->4.9<!--/V--> L/min a V máx. alcanzan con un salto de <!--V:sizing.cooling.dT_water_K:.1f-->1.9<!--/V--> K.
- [CALCULADO].

## Dirección, reversa y control

**D-16 Boquilla direccional de Al ±25° con cable Ultraflex M66 y timonería T85 al volante; topes mecánicos.**
- [VERIFICADO: R11 §7 (productos y precios)].

**D-17 Bucket de reversa obligatorio (Al 5083 soldado) con émbolo de traba; reversa limitada al 50 % de la potencia; enclavamiento mecánico de palancas en la consola.**
- Justificación: sin chorro no hay dirección ni freno (R10b H10). El bucket solo se mueve con el acelerador en 0.
- [CALCULADO: structural_direccion.py; firmware].

**D-17b [REEMPLAZADA por D-17c, auditoría ronda 4] Traba del bucket en LOS DOS brazos con reparto por desfase, chapa de 6 mm y pivote de espaciador + M12 (auditoría ronda 3, 2026-10-02).**
- Se conserva como historia; los valores de esta entrada son los de la ronda 3 [CALCULADO en la ronda 3, commit `ce8faed`] y ya no están en el CAD.
- Hallazgo de entonces: con la traba en un solo brazo el momento de la cuchara llegaba a ese brazo por torsión de la sección abierta (FEA de la ronda 3: FS 0,44). La reacción de la traba (tangencial, M_h/r) se suma al chorro en el pivote: ≈ 1,6–3,0 kN por pivote con R12 según el reparto, no F_b/2 = 0,7 kN como suponía el cálculo a mano.
- Decisión de entonces: un émbolo por brazo (+Y a 10°, −Y a −25°), chapa de 6 mm, lóbulo de traba r 16, aros de refuerzo de 8 mm; pivote = espaciador 316 Ø18 apretado por un M12 A4-80 en un agujero pasante Ø12,4; buje POM-C Ø18/Ø22 × 14; émbolo de catálogo «GN 617 M20 con perno Ø12». Pivote y buje se verificaban con un reparto máximo de 0,78 de M_h, admitiendo ≤ 0,10 mm de desfase entre agujeros medido con comparador (06 T0.M6b); casos de «falla» y «falla doble» con objetivos 2 y 1.
- Por qué se reemplazó (ronda 4): el reparto con desfase depende de la carga y el desfase no estaba controlado (la cota 0,78 era no conservadora en fatiga); el espaciador podía deslizar en el agujero con juego; M_h estaba subestimado y F_z con el signo cambiado; el émbolo «GN 617 M20 perno Ø12» no existe; y la frase «con una sola traba hacen falta ~10 mm de chapa para FS 2 (FEA)» no tenía un FEA que la respaldara (auditoría ronda 4, M8). Ver D-17c.

**D-17c Criterio de traba única, émbolo propio Ø16 / M24×1,5 y pivote con brida y piloto (auditoría ronda 4, 2026-10-02). Reemplaza a D-17b.**
- Hallazgos (auditoría ronda 4, tres auditores independientes) [CALCULADO: auditoría ronda 4, auditoria.md R4-01…R4-05]:
  1. **El reparto entre las dos trabas depende de la carga.** Con un desfase fijo la segunda traba recién apoya cuando la primera ya lleva ≈ 1,4 kN; con la reversa de servicio (sizing) UNA traba lleva ≈ 100 % de M_h. Las filas de fatiga con reparto 0,78 eran no conservadoras (buje POM FS ≈ 1,70; oreja de STE-01 en fatiga ≈ 1,4 escalando el FEA).
  2. **El desfase no estaba controlado:** el taladrado coincidente metía ≈ 0,25 mm; el espaciador del pivote flotaba en un agujero Ø12,4 (la unión desliza a R12) y la prueba con comparador no tenía dirección ni fuerza definidas.
  3. **Las cargas del chorro estaban mal:** M_h subestimado (126,8 N·m en la ronda 3) y F_z con el signo cambiado (+81 N). Con el balance de cantidad de movimiento (salida por el labio inferior, 02 §8): M_h = <!--V:est.loads.structural_direccion.M_hinge_Nm:.1f-->135.3<!--/V--> N·m y F_z = <!--V:est.loads.structural_direccion.F_z_bucket_N:.0f-->-210<!--/V--> N con R12; M_h = <!--V:est.loads.structural_direccion.M_hinge_sizing_Nm:.1f-->67.1<!--/V--> N·m con la reversa de sizing [CALCULADO].
  - Además, el émbolo de catálogo supuesto no existe: el GN 617 inoxidable más grande (GN 617-10-…-NI) tiene perno Ø10 −0,02/−0,04 de AISI 303 niquelado, cuerpo M20×1,5 de AISI 303, l2 = 10 mm, resorte de 17 N inicial a 40 N final [VERIFICADO: catálogo Elesa/Ganter GN 617, pág. 809, https://www.elesa.com/siteassets/PDF/PDF_US/GN%20617.pdf, abierto el 2026-10-02]. Con el perno Ø10 y la carga de una traba sola el FS queda por debajo de 1 [CALCULADO: la fila del perno Ø16 escalada por (16/10)³ ≈ 4].
- Decisión:
  - **Criterio de traba única:** <!--V:est.loads.structural_direccion.n_locks:d-->2<!--/V--> trabas (una por brazo, +Y a <!--V:manifest.params.REV_lock_ang:g-->10<!--/V-->°, −Y a <!--V:manifest.params.REV_lock_ang_m:g-->-25<!--/V-->°, a r <!--V:manifest.params.REV_lock_r:g-->45<!--/V--> mm), pero «<!--V:est.loads.structural_direccion.lock_criterion:-->cada traba sola lleva M_h completo<!--/V-->»: cada traba con su brazo, su pivote, su oreja y su émbolo verifica sola la reversa R12 (corta) y la de sizing (fatiga), las dos con FS ≥ 2. Perno de una traba <!--V:est.loads.structural_direccion.F_lock_pin_N:.0f-->3006<!--/V--> N (R12) / <!--V:est.loads.structural_direccion.F_lock_pin_sizing_N:.0f-->1491<!--/V--> N (sizing); pivote del brazo trabado <!--V:est.loads.structural_direccion.R_bucket_pivot_design_N:.0f-->3302<!--/V--> N / <!--V:est.loads.structural_direccion.R_bucket_pivot_sizing_N:.0f-->1638<!--/V--> N [CALCULADO]. La segunda traba es redundancia. Desaparecen el reparto admitido, el desfase admitido, los casos de «falla»/«falla doble» y la prueba con comparador (B-DIAL); queda una prueba FUNCIONAL: los dos pernos entran solos (resorte) ARRIBA y ABAJO, sobresalen ≥ 0,5 mm de la cara exterior del brazo y salen los dos con el gatillo.
  - **Bucket P1-REV-01:** chapa Al 5083 de <!--V:manifest.params.REV_t:g-->8<!--/V--> mm, aro de refuerzo del pivote de <!--V:manifest.params.REV_ring_t:g-->10<!--/V--> mm, agujeros de traba Ø<!--V:manifest.params.REV_lock_hole_d:g-->16.5<!--/V-->, lóbulo de traba r <!--V:manifest.params.REV_lock_lobe_r:g-->18<!--/V-->.
  - **Pivote P1-REV-02 con brida y piloto:** espaciador 316 con muñón Ø<!--V:manifest.params.REV_pin_d:g-->20<!--/V--> h7, brida Ø<!--V:manifest.params.REV_sp_fl_d:g-->36<!--/V--> × <!--V:manifest.params.REV_sp_fl_t:g-->3<!--/V--> contra la cara exterior de la oreja y piloto Ø<!--V:manifest.params.REV_sp_pilot_d:g-->16<!--/V--> h6 en el agujero Ø16 H7 escariado de cada oreja (ya no pasante de lado a lado: no desliza y no muerde la torre del yugo); M12 A4-80 con arandelas y tuerca DIN 985, <!--V:est.loads.structural_direccion.bolt_torque_Nm:.0f-->45<!--/V--> N·m con Tef-Gel (precarga <!--V:est.loads.structural_direccion.bolt_pre_min_N:.0f-->17045<!--/V-->–<!--V:est.loads.structural_direccion.bolt_pre_max_N:.0f-->31250<!--/V--> N con K 0,12–0,22 [ESTIMADO]). Buje POM-C Ø<!--V:manifest.params.REV_bush_od:g-->24<!--/V--> × <!--V:manifest.params.REV_bush_L:g-->18<!--/V--> prensado y escariado después de prensar.
  - **Émbolo propio P1-REV-04:** torneado en 316 + resorte inox comprado: perno Ø<!--V:manifest.params.REV_lock_pin_d:g-->16<!--/V--> h9, cuerpo M<!--V:manifest.params.REV_lock_thread_d:g-->24<!--/V-->×1,5 roscado en la oreja con contratuerca, carrera <!--V:manifest.params.REV_plunger_stroke:g-->12<!--/V--> mm (liberar pide <!--V:manifest.params.REV_release_need:g-->9.5<!--/V--> mm), resorte ≈ 20 N de precarga a ≈ 45 N final [ESTIMADO: como el GN 617-10].
  - **Orejas de la boquilla P1-STE-01:** <!--V:manifest.params.STE_ear_t:g-->12<!--/V--> mm (crecen hacia adentro), radio <!--V:manifest.params.STE_ear_r:g-->22<!--/V--> alrededor del pivote, lóbulo r <!--V:manifest.params.STE_lock_lobe_r:g-->20<!--/V--> alrededor de la rosca M24.
  - Resultados a mano (02 §9) [CALCULADO]: P1-REV-01 FS <!--V:est.min_by_part.P1-REV-01.FS:.2f-->2.17<!--/V-->, P1-REV-02 FS <!--V:est.min_by_part.P1-REV-02.FS:.2f-->2.10<!--/V-->, P1-REV-03 FS <!--V:est.min_by_part.P1-REV-03.FS:.2f-->2.18<!--/V-->, P1-REV-04 FS <!--V:est.min_by_part.P1-REV-04.FS:.2f-->2.83<!--/V-->, P1-STE-01 FS <!--V:est.min_by_part.P1-STE-01.FS:.2f-->4.65<!--/V--> (filas más justas de cada pieza). FEA de REV-01 y STE-01 con los casos de una traba sola: 04_diseno/fea/README.md.
- Por qué así y no la alternativa: (a) mantener el reparto con un desfase más chico exige controlar en fabricación una cota que depende de la carga y no se puede medir de forma útil; (b) una sola traba (en un brazo) deja al otro sin redundancia y la cuchara abierta a torsión manda igual; con dos trabas que verifican solas, el bote vuelve aunque un émbolo no entre. El émbolo propio es la única forma de tener perno Ø16 con carrera suficiente.
- [CALCULADO: structural_direccion.py, params_direccion.py; FEA en 04_diseno/fea].
- *Si el dato real difiere:* si la corrida fina del FEA de REV-01 da FS < 2, se agrega sección al brazo trabado en su borde inferior-delantero, por debajo del pivote (nervio radial desde el aro de refuerzo) y se vuelve a correr; si la fuerza de liberación medida supera lo que da el gatillo (resorte y rendimiento del Bowden son [ESTIMADO]), se cambia el resorte; si la prueba funcional falla (un perno no entra solo), se repasa el agujero del brazo con la plantilla, nunca se agranda el juego.

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
- Justificación: la definición de vandscooter pide operar "på – snarere end i – skroget" (BEK 809/2019); el piloto va sentado dentro con volante. Speedbåd desde 19 kW de potencia propulsiva (BEK 749/2020); el pico de este diseño es <!--V:sizing.performance.P_shaft_peak_kW:.1f-->6.5<!--/V--> kW. Los 30 km/h solo son legales a más de 300 m de la costa y nunca en Als Sund (4 kn) ni en Augustenborg Fjord.
- [VERIFICADO: research/R13]. Confirmar por escrito con Søfartsstyrelsen (preguntas en danés en R13 §8).

## Cálculo (auditoría Pass 3, ronda 1)

**D-21 Savitsky solo donde es válido; con el casco corto, "Savitsky limitado por eslora" y banda ensanchada; el margen de empuje se exige de 0 a planeo pleno. Con la banda alta el bote no llega a planeo pleno y con potencia continua se cae del planeo; la V máx. queda sin base validada hasta T4.**
- Hallazgo: el equilibrio libre de Savitsky daba eslora mojada en la quilla L_K mayor que el fondo (2,1 m a 20 km/h contra L_wl 1,75 m) en todo el rango de planeo; el margen de 19 % y la V máx. de 26,3 km/h salían de puntos fuera de validez.
- Alternativas: (a) seguir con Savitsky libre (optimista: supone un fondo más largo); (b) Savitsky–Brown 1976 o Blount–Fox 1976 para el pre-planeo (no tengo fuente abierta, R12 §6.3); (c) Mercier–Savitsky (solo Fn∇ 1–2, ~17 km/h); (d) equilibrio vertical con L_K = L_wl.
- Elegida (d) como nominal [ESTIMADO: método propio, no validado; el momento de cabeceo no cierra], (a) × 0,92 como banda baja y (d) × 1,12 como banda alta [SUPUESTO en este régimen: el ×1,12 viene de cascos con Savitsky válido; sensibilidad 1,00–1,25]; la validez de cada punto (L_K, λ, τ, C_V) va en `sizing.json`.
- Ventana del margen (ronda 2, R2-C01): de 0 hasta el planeo pleno (<!--V:sizing.resistance.v_full_planing_kmh:.1f-->27.3<!--/V--> km/h, donde el limitado y el libre difieren < 2 %), no hasta el primer nodo de Savitsky: cortada ahí daba 3 % y el margen seguía cayendo. Así el resultado tampoco depende del corte arbitrario fn_planing.
- Consecuencia [CALCULADO]: margen de 0 a planeo pleno <!--V:sizing.verdict.hump_margin_min_high:.1%-->-7.3%<!--/V--> (banda alta: a fondo se queda en <!--V:sizing.verdict.V_eq_peak_high_kmh:.1f-->22.3<!--/V--> km/h, no llega a planeo pleno; con potencia continua cae a <!--V:sizing.verdict.vmax_cont_kmh.high:.1f-->18.0<!--/V--> km/h, debajo del inicio del planeo) y <!--V:sizing.verdict.hump_margin_min_nominal:.1%-->3.9%<!--/V--> (nominal); V máx. sostenida <!--V:sizing.verdict.vmax_cont_kmh.high:.1f-->18.0<!--/V-->–<!--V:sizing.verdict.vmax_cont_kmh.low:.1f-->28.7<!--/V--> km/h según la banda (02 §0, §3, §3.2).
- *Si difiere:* con el casco medido (P0.1) se vuelve a correr; con <!--V:sizing.verdict.recovery_mass_text:-->22 kg menos<!--/V--> de masa total o <!--V:sizing.verdict.recovery_lwl_text:-->L_wl ≥ 1,96 m<!--/V--> el margen vuelve al 10 % con la banda alta. T4.1 (tiempo a planeo con la batería al 20 %) decide.

**D-22 Deducción de empuje t = 0 y fracción de estela w = 0 se mantienen, pero t = 0 se declara NO conservador y se lleva en la sensibilidad (0–0,10).**
- Justificación: no hay fuente abierta con valores de t para jets chicos; poner un número sería inventarlo. w = 0 sí es conservador para el empuje (no recupera estela).
- Consecuencia [CALCULADO]: con t = 0,10 el margen de 0 a planeo pleno cae a <!--V:sizing.sensitivity.by_key.waterjet_thrust_deduction.hi.hump:.1%-->-16.5%<!--/V--> (con t = 0: <!--V:sizing.sensitivity.by_key.waterjet_thrust_deduction.lo.hump:.1%-->-7.3%<!--/V-->) (02 §10).
- *Si difiere:* la prueba de punto fijo da el empuje sin casco en movimiento; el t real sale de comparar la curva P–V medida (T4) con el modelo.

## Historia

El diseño anterior (cola larga eléctrica para un jon boat de 2 personas a 6 km/h, decisiones D-01 a D-43
de esa versión) quedó en el historial de git: commit `5dfada0`
(`git show 5dfada0:decisiones.md`). De esa versión se reutilizan: el kill switch por cordón + contactor,
el firmware del acelerador (adaptado al bucket), la investigación de materiales PETG (R05), la normativa
general (R07) y el marco de cálculo, CAD, verificación y documentación.
