# 07 — Roadmap P2: próxima iteración

Qué cambiar después de P1, en qué orden y qué resultado de prueba de P1 activa cada cambio.
**Orden:** relación beneficio/esfuerzo. Los ítems de seguridad o integridad (**S**) van primero aunque cuesten más.
**Etiquetas:** [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO]. Los números entre marcadores
los actualiza `docgen.py` desde `resultados/*.json`; el resto cita su fuente. Pruebas de P1: P0–P5 en
[`PENDIENTES_GASPAR.md`](PENDIENTES_GASPAR.md); T0–T4 en [`06_ensamblaje_y_pruebas.md`](06_ensamblaje_y_pruebas.md).
Ningún ítem cambia el código de P1: cada uno entra en P2 cuando se cumple su disparador.

## 0. Línea base de P1 (contra la que se mide cada mejora)

| Magnitud | P1 | Etiqueta |
|---|---|---|
| P_bat a 6 km/h (nominal / diseño) | <!--V:sizing.cruise.nominal.P_bat:.0f-->736<!--/V--> / <!--V:sizing.cruise.design.P_bat:.0f-->879<!--/V--> W | [CALCULADO] |
| Autonomía a 6 km/h (nominal / diseño) | <!--V:sizing.cruise.autonomy_nominal_h:.2f-->3.13<!--/V--> / <!--V:sizing.cruise.autonomy_design_h:.2f-->2.62<!--/V--> h | [CALCULADO] |
| Energía por km (diseño) | ≈ 152 Wh/km | [CALCULADO: P_bat de diseño / 6 km/h] |
| η0 de la hélice MKP-32 en crucero / rendimiento total batería → R·V | <!--V:sizing.cruise.design.prop_eta0:.2f-->0.41<!--/V--> / <!--V:sizing.cruise.design.eta_total:.0%-->30%<!--/V--> | [ESTIMADO: fuera del rango B-series, D-40] / [CALCULADO] |
| V máx con 2 personas (nominal) · bollard avante · bollard atrás | <!--V:sizing.vmax.nominal_vnom.V_kmh:.1f-->7.1<!--/V--> km/h · <!--V:sizing.bollard_fwd.T_horiz:.0f-->287<!--/V--> N · <!--V:sizing.bollard_rev.T_horiz:.0f-->91<!--/V--> N | [CALCULADO] |
| Motor en crucero de diseño: T estacionaria / tiempo hasta 85 °C | <!--V:sizing.thermal.cruise_design.T_motor_steady_C:.0f-->80<!--/V--> °C / <!--V:sizing.thermal.cruise_design.t_to_limit_min:.0f-->inf<!--/V--> min | [CALCULADO con R_th 0,45 K/W ESTIMADO y aire a 30 °C] |
| ESC: pérdida en crucero / disipador exigido | <!--V:sizing.thermal_esc.esc_cruise.P_loss_esc_W:.0f-->26<!--/V--> W / ≤ <!--V:sizing.thermal_esc.heatsink.R_hs_required_K_W:.2f-->0.61<!--/V--> K/W | [CALCULADO: 02 §5.2] |
| Batería (2 × 12 V 100 Ah LFP) | <!--V:sizing.battery.E_nom_wh:.0f-->2560<!--/V--> Wh, <!--V:sizing.battery.mass_kg:.0f-->22<!--/V--> kg | [CALCULADO] |
| Impresión total PETG | <!--V:manifest.totals.printed_hours:.0f-->334<!--/V--> h, <!--V:manifest.totals.printed_mass_g:.0f-->6011<!--/V--> g | [CALCULADO: resultados/manifest.json] |
| Carga útil / placa de capacidad estimada | <!--V:sizing.masses.payload_kg:.0f-->248<!--/V--> / <!--V:sizing.masses.capacity_kg:.0f-->160<!--/V--> kg | [CALCULADO] / [ESTIMADO: R04, D-16] |

## 1. Resumen priorizado

| # | Ítem | Beneficio esperado | Esfuerzo / costo | Lo dispara (resultado de P1) |
|---|---|---|---|---|
| **P2 inmediato** | | | | |
| 2.1 **S** | Abrazadera de popa y cuna/tapa en Al 6082 | FS ≥ 3 (FEA hoy: 0,32 y 0,74); −177 h de impresión | 4–5 días [ESTIMADO]; placa: buscar | FEA (ya disparado) · P1.3/P1.5 · aflojamiento en T3/T4 |
| 2.2 **S** | Cordón de hombre al agua de 2 canales | Elimina la única falla latente peligrosa | 0,5 día [ESTIMADO]; interruptor: buscar | Análisis de elec §8 (ya disparado) · falla en P2.1 |
| 2.3 | Calibración del modelo con P0.3, T2, T3, T4 | Rango de sensibilidad de P_bat 729–1 159 W → ±10 % | 0 €, 1–2 días [ESTIMADO] | Siempre tras T4; desvío > 10 % |
| 2.4 | Trimado: menos espejo sumergido | −6 a −8 % de P_bat | 0 €, 0,5 día [ESTIMADO] | P0.2 · estela del espejo en T3 |
| 2.5 | Marcha atrás: datos de 4 cuadrantes | Reemplaza el factor 0,65 [ESTIMADO] | 0 €, 2 h dentro de T2 [ESTIMADO] | Siempre en T2 |
| 2.6 | Protector: medir la pérdida y rediseñar | Hasta −13 % de P_bat | ≈ 38 h de impresión por variante | T2 con/sin protector: pérdida > 10 % |
| 2.7 | Hélice 10 × 8 in de 3 palas | −7 % de P_bat; autonomía 2,53 → 2,72 h | Producto no hallado: buscar; 1 día | T2 bollard < 238 N · T4 P_bat > 910 W |
| 2.8 | Telemetría VESC + ESP32 y límite de velocidad por GPS | Datos para 2.3, 2.9; límite legal medido | 3–5 días [ESTIMADO]; módulos: buscar | T4 sin Wh/km · T3 con 1 persona > 9,0 km/h |
| 2.9 | Refrigeración del ESC (agua o reubicación) y del motor | Sin recorte a 85 °C; R admisible 0,58 → 0,80 K/W | 1–3 días [ESTIMADO] | T2: tapa > 50 °C o motor > 80 °C |
| **Más adelante** | | | | |
| 3.1 | Hélice B3-50 de 0,30–0,34 m a ~550 rpm, ~5:1 | +15 % de η0 frente a la 10 × 8; ≈ −23 a −25 % de P_bat | Alto: calado 420–476 mm, eje Ø18–20 | T4 calibrado + zona con ≥ 0,5 m de agua |
| 3.2 | 36 V (D-28) | −7 kg, ≈ −45 € | Batería, cargador y motor 140 KV | 2.3 con R ≤ nominal y/o 3.1 hecho |
| 3.3 | Carenado del tubo | ≤ 3 % de P_bat en P1 (R02: −16 % en un trolling) | 10–15 h de impresión [ESTIMADO] | Residuo de R tras 2.3 |
| 3.4 | Ánodo (solo con hélice de Al) | Protege la hélice de Al | 96 kr + buje torneado | Hélice de Al · picaduras |
| 3.5 | Materiales | Ninguno con la impresora actual: queda PETG | — | P1.5 > 25 % · P1.7 > 1 % |
| **Descartado** | | | | |
| 4 | Tobera Kort; waterjet; rim | Crucero 0 a +5 %; jet/rim gastan 1,35–5,4× | Holgura ≤ 1,3 mm inviable con arena | — |

## 2. P2 inmediato

### 2.1 S — Abrazadera de popa (MNT-01) y cuna/tapa (MNT-05/06) en aluminio
- **Qué:** reemplazar la C impresa y la tapa de la cuna por placas de Al 6082-T6 atornilladas, hechas con sierra, taladro, machos y torno (sin fresadora), como ya se hacen HSG-01 y HSG-07. Se mantienen las zapatas aislantes (MNT-02) y el aislamiento galvánico con Tef-Gel y arandelas de nylon contra el espejo y el casco (D-36).
- **Por qué:** el FEA da FS 0,32 en el puente de la C con el apriete de diseño (2,5 N·m → 1 042 N por tornillo) y FS 0,74 en la tapa MNT-06 con la cola trabada. structural.py daba 3,23 y 7,71 porque toma la sección de la pata y otro brazo del tope [CALCULADO: 04_diseno/fea/README.md]. Además, la C depende de un apriete de 2,5 N·m que no se controla a mano con un mango en T (con 5 N·m caía a FS 1,7 a fluencia, D-13). Admisible sostenido del PETG: <!--V:est.allowables_MPa.sust:.2f-->8.39<!--/V--> MPa [CALCULADO: factores de R05, D-29].
- **Beneficio:** FS ≥ 3 sin depender de la fluencia ni del apriete. Ahorra ≈ 177 h de impresión (MNT-01 103 h, MNT-05 65 h, MNT-06 9 h) [CALCULADO: resultados/manifest.json]. La alternativa impresa necesita un puente de t ≥ 38,5 mm [CALCULADO: 04_diseno/fea].
- **Costo / tiempo:** CAD 2–3 días y taller 2 días [ESTIMADO: complejidad similar a HSG-01/HSG-07]. Placa: buscar: "aluminium plade 6082 10 mm". Si se terceriza: buscar: "CNC fræsning aluminium Sønderborg". Mientras siga impresa: llave dinamométrica para el apriete (ver checklist §3).
- **Disparador:** ya disparado por el FEA, salvo que el rediseño impreso de P1 recupere FS ≥ 3. Además: P1.3 con tuerca cautiva < 2,1 kN, P1.5 con pérdida > 25 % (D-29), o en T3/T4 tornillos que piden re-apriete, una C que se abre o fisuras.

### 2.2 S — Interruptor de cordón de dos canales
- **Qué:** interruptor de hombre al agua de doble contacto: un canal a la bobina del contactor K1 y otro, independiente, a la entrada del MCU [elec §8, §11].
- **Por qué:** un corto entre los dos conductores del cordón (cable aplastado en la caña, agua salada en J2) puentea a la vez K1 y U2/U3: tirar del cordón no corta. Es la única combinación peligrosa de la tabla de verdad, y es latente: solo la detecta la prueba previa a cada salida [CALCULADO: elec §3, §8].
- **Beneficio:** ninguna falla simple anula el cordón.
- **Costo / tiempo:** buscar: "kill switch lanyard double pole marine"; 0,5 día de cableado y repetir los ensayos de corte de T0 [ESTIMADO].
- **Disparador:** ya justificado por el análisis. Urgente si P2.1 (200 aperturas) falla o si la prueba de corte previa falla una sola vez.

### 2.3 Calibración del modelo con datos de P0.3, T2, T3 y T4
- **Qué:** cargar en `inputs.yaml` la R(v) del remolque (P0.3), el bollard (T2), los pares V–P_bat (T3/T4) y la R_th del motor medida por resistencia (D-41). Ajustar `resistance.wave_cw`, `propeller.efficiency_factor`, `propeller.guard.thrust_loss_frac` y `rth_k_w`, y correr `run_all.py`.
- **Por qué:** las entradas que más mueven P_bat son inciertas. c_w ±30 % → 729–1 104 W; pérdida del protector 0–25 % → 793–1 159 W; masa por persona ±20 % → 767–1 061 W [CALCULADO: resultados/sizing.json → sensitivity]. El η0 de la MKP-32 es [ESTIMADO] porque su P/D ≈ 0,4 queda fuera de la B-series (D-40).
- **Beneficio:** la banda de P_bat de crucero pasa de ≈ ±20 % a ≤ ±10 % [SUPUESTO: criterio de P0.4]. Decide 2.6, 2.7, 3.1 y 3.2. Si la R medida es ≤ nominal, abre la batería de 36 V (3.2).
- **Costo / tiempo:** 0 €; 1–2 días de análisis [ESTIMADO].
- **Disparador:** siempre después de T4. Prioridad alta si la P_bat medida a 6 km/h se aparta más de 10 % de la banda <!--V:sizing.cruise.nominal.P_bat:.0f-->736<!--/V-->–<!--V:sizing.cruise.design.P_bat:.0f-->879<!--/V--> W, o si el bollard da < <!--V:sizing.success.bollard_pull_min_N:.0f-->244<!--/V--> N.

### 2.4 Trimado: menos espejo sumergido
- **Qué:** batería y bultos hacia el centro/proa hasta que el espejo deje de arrastrar agua; marca de flotación de popa pintada en el casco.
- **Por qué:** el espejo sumergido aporta 40 N de 134 N a 6 km/h (30 %), es el término con menos base empírica y, según la fórmula, no se ventila por debajo de 24,5 km/h [VERIFICADO: R09 §1.4, Holtrop-Mennen]. Hoy el bote va a <!--V:sizing.masses.capacity_ratio:.0%-->155%<!--/V--> de la placa estimada, con calado <!--V:sizing.hydrostatics.draft_m:.3f-->0.198<!--/V--> m.
- **Beneficio:** A_T −25 % → R_TR −20 % ≈ −8 N ≈ −6 % de R [CALCULADO: R09 §1.4]. En el modelo, −20 % de ancho de espejo sumergido → P_bat 834 W (−8 %) [CALCULADO: resultados/sizing.json → sensitivity].
- **Costo / tiempo:** 0 €; 0,5 día. Llevar la batería 1 m más a proa alarga el cable DC: la caída pasa de <!--V:sizing.cables.dc.drop_frac:.1%-->1.2%<!--/V--> a ≈ 1,8 %, debajo del 3 % [CALCULADO: caída ∝ largo].
- **Disparador:** P0.2 con francobordo de popa cerca de 150 mm; estela del espejo en las fotos de T3; Wh/km de T4 por encima del modelo.

### 2.5 Marcha atrás: datos de cuatro cuadrantes
- **Qué:** medir en T2 el empuje atrás al 25 y al 50 % de corriente, y en T3 la parada desde 6 km/h (tiempo y distancia con GPS). Reemplazar el rendimiento de hélice invertida 0,65 de 02 §3.
- **Por qué:** no hay datos abiertos de la B-series en cuatro cuadrantes [VERIFICADO: R09 §2.1, propy]. El bollard atrás de <!--V:sizing.bollard_rev.T_horiz:.0f-->91<!--/V--> N usa ese 0,65 [ESTIMADO]. Con protector, la reversa puede no mejorar (R03 §3: −1,5 % con una tobera impresa).
- **Beneficio:** reemplaza un [ESTIMADO] y permite decidir si se sube la reversa del 50 al 70 % de corriente. El FS de retención de la basculación bajaría de <!--V:sizing.mech.kickup.fs_reverse_hold:.1f-->7.4<!--/V--> a ≈ 5,4 [ESTIMADO: momento de empuje ∝ corriente en punto fijo; D-10].
- **Costo / tiempo:** 0 €; 2 h dentro de T2 [ESTIMADO].
- **Disparador:** siempre en T2. Subir el límite solo si en T3 el bote no frena o no maniobra con el viento de diseño de 6 m/s.

### 2.6 Protector: medir la pérdida y rediseñar
- **Qué:** bollard en T2 sin protector, con el aro perfilado actual (D-26) y, si da mal, con un aro "neutral" de menos cuerda; misma corriente y 3 niveles de acelerador [R03 hallazgos].
- **Por qué:** la pérdida de diseño de 10 % es [ESTIMADO: R03, D-26] y es la 2.ª entrada más sensible. Con holgura de 2,4 % D el aro no es tobera: no se le acredita ganancia (R09 §4).
- **Beneficio:** con pérdida 0 %, P_bat 793 W (−13 %); con 25 %, 1 159 W (+27 %) [CALCULADO: resultados/sizing.json → sensitivity].
- **Costo / tiempo:** 6 segmentos × 6,3 h ≈ 38 h y ≈ 0,7 kg de PETG por variante [CALCULADO: resultados/manifest.json, PRP-01].
- **Disparador:** T2 con pérdida en avance > 10 % a igual corriente, o reversa con protector < 90 % de la sin protector [SUPUESTO: criterio de R03].

### 2.7 Hélice 10 × 8 in de 3 palas
- **Qué:** comprar una 10 × 8 in de 3 palas con cubo para pasador (objetivo de D-06), marcar `purchasable: true` en `propeller.options.EO10x8` y correr `run_all.py`. El optimizador elige poleas 16:48 (3:1).
- **Por qué:** la MKP-32 es de trolling (P/D ≈ 0,4) y queda fuera de la B-series. Una 10 × 8 está dentro: η0 0,49 contra 0,42 de una 7,8 in [CALCULADO: R09 §2.3].
- **Beneficio:** P_bat 910 → 848 W (−7 %); autonomía de diseño 2,53 → 2,72 h [CALCULADO: resultados/sizing.json → optimization, EO10x8 con LFP12_100x2].
- **Costo / tiempo:** no se halló producto (R08b §5): buscar: "electric outboard spare propeller 10 inch 3 blade shear pin". Asiento del eje re-torneado al bore real; 1 día [ESTIMADO].
- **Disparador:** T2 con bollard < 0,85 × <!--V:sizing.bollard_fwd.T_horiz:.0f-->287<!--/V--> N, T4 con P_bat a 6 km/h > 910 W, o η0 calibrado de la MKP-32 por debajo del modelado.

### 2.8 Telemetría (VESC + ESP32) y límite de velocidad por GPS
- **Qué:** ESP32 en la UART del VESC para leer V, I, Wh, rpm, duty y temperaturas de motor y MOSFET, más un GPS (velocidad sobre el fondo). Registro CSV a 10 Hz y lectura de Wh consumidos a bordo. Usa el gancho `use_vesc_ok` del firmware del Nano [elec §5.3]. Que el VESC atienda PPM y UART a la vez es [ESTIMADO: memoria técnica, app "PPM_UART"; confirmar en VESC Tool].
- **Límite GPS:** el ESP32 baja el comando si la velocidad GPS supera 9,0 km/h; el tope de ERPM queda como respaldo fijo. El limitador **nunca** entra en la cadena de corte (elec §2): solo reduce el comando.
- **Por qué:** P1 no mide SoC ni Wh (el checklist exige "carga completa ≤ 48 h"). La calibración (2.3) necesita cientos de puntos V–P, no 3–4. El tope de ERPM se calcula en agua calma, con 1 persona y batería llena (D-30): no ve la corriente a favor.
- **Beneficio:** Wh/km, temperaturas y recortes reales en cada salida; límite legal sobre la velocidad medida. Con 2 personas recupera V máx de <!--V:sizing.legal_speed.vmax_full_load_with_cap_kmh:.1f-->7.1<!--/V--> a <!--V:sizing.vmax.nominal_vnom.V_kmh:.1f-->7.1<!--/V--> km/h [CALCULADO], que es poco: el valor está en los datos y en la certeza legal.
- **Costo / tiempo:** buscar: "ESP32 DevKit", "GPS NEO-M8N", "microSD SPI module"; firmware y caja estanca 3–5 días [ESTIMADO].
- **Disparador:** T4 sin Wh/km reales para 2.3; T3 con 1 persona a fondo y media > 9,0 km/h (P4); sospecha de recorte térmico (2.9).

### 2.9 Refrigeración del ESC (por agua o reubicación) y del motor
- **Qué:** (a) ESC: apoyar la tapa-disipador ELE-02 sobre una placa de Al en contacto con el fondo del casco, con pad térmico **aislante** para que el sistema siga flotante (R06 §3.5, D-36); o placa fría con agua del fiordo tomada en la carcasa inferior. (b) Motor: capó con entrada y salida de aire y ventilación forzada [ESTIMADO: R03 §5 remite a motores secos con ventilación forzada de R02].
- **Por qué:** con R_th 0,45 K/W [ESTIMADO] y aire a 30 °C, el motor llega a <!--V:sizing.thermal.cruise_design.T_motor_steady_C:.0f-->80<!--/V--> °C estacionario en el crucero de diseño y el VESC empieza a recortar a 85 °C a los <!--V:sizing.thermal.cruise_design.t_to_limit_min:.0f-->inf<!--/V--> min [CALCULADO]. En la banda nominal queda en ≈ 81 °C [CALCULADO: 30 °C + 0,45 K/W × <!--V:sizing.cruise.nominal.P_loss_motor:.0f-->91<!--/V--> W]. El ESC necesita un disipador ≤ <!--V:sizing.thermal_esc.heatsink.R_hs_required_K_W:.2f-->0.61<!--/V--> K/W en convección natural para que la caja impresa no pase de 50 °C (02 §5.2).
- **Beneficio:** motor: bajar R_th 13 % (0,45 → 0,39 K/W) elimina el recorte en la banda de diseño [CALCULADO: (85 − 30) °C / <!--V:sizing.thermal.cruise_design.P_loss_motor_W:.0f-->111<!--/V--> W]. ESC: con un sumidero a ≤ 24 °C (agua, D-31) la R admisible sube de 0,58 a ≈ 0,80 K/W [CALCULADO: (50 − 24) °C / 27 W − 0,15 K/W de interfaz].
- **Costo / tiempo:** pad aislante y placa de Al (referencia: B-ALPLATE, 12 € [ESTIMADO en bom.csv]); 1–3 días [ESTIMADO]. La toma de agua agrega un punto que se tapa con arena: usarla solo si (a) no alcanza.
- **Disparador:** T2 con 30 min a potencia de crucero: tapa del ESC > 50 °C (P2.3) o carcasa del motor > 80 °C (02 §11); recorte por temperatura en el registro de 2.8; R_th medida > 0,39 K/W (D-41).

## 3. Más adelante

### 3.1 Hélice grande y lenta: B3-50 de 0,30–0,34 m a ~550 rpm
- **Qué:** hélice de 3 palas, AE/A0 0,5, P/D 0,8, D 0,30–0,34 m, a 530–585 rpm, con reducción ≈ 5:1 (Dold 14 T : 72 T = 5,14:1, R08b §4).
- **Por qué:** es el óptimo de la cuadrícula B3-50 en crucero: η0 0,56–0,58 contra 0,49 de la 10 × 8, o sea +15 % [CALCULADO: R09 §2.3 y hallazgos].
- **Beneficio:** con el factor de escala 0,95 (D-40), η0 0,53–0,55 contra 0,41 de la MKP-32. Eso da P_bat ≈ 680–700 W (−23 a −25 %) y autonomía ≈ 3,3 h con la batería actual. La energía requerida, ≈ 1 820–1 880 Wh, entraría en una LiTime 36 V 50 Ah de 1 920 Wh (3.2) [ESTIMADO: misma eficiencia de cadena que el crucero de diseño de sizing].
- **Costo / tiempo:** alto.
  - Calado: con la regla actual (eje a 0,9 D, punta superior a 0,4 D) la punta inferior baja a 420–476 mm, sobre el límite de 380 mm de `operation.max_prop_tip_depth_mm` (hoy: <!--V:sizing.layout.prop_center_depth_mm:.0f-->229<!--/V--> + 127 = 356 mm) [CALCULADO]. Si se respetan los 380 mm, la punta superior queda a 80–40 mm (0,27–0,12 D) y ventila (R02 B5, D-27). Solo sirve donde haya ≥ 0,5 m de agua [ESTIMADO].
  - Par: el par de rotor trabado en el eje sube de <!--V:sizing.mech.Q_lock_shaft_Nm:.1f-->6.8<!--/V--> a ≈ 17 N·m [CALCULADO: <!--V:sizing.mech.Q_lock_motor_Nm:.2f-->3.02<!--/V--> N·m × 5,14 × 0,94]. El pasador 316 pasa de Ø<!--V:sizing.mech.shear_pin.d_std_mm:.1f-->2.0<!--/V--> a ≈ Ø3,3 mm, y el asiento Ø<!--V:sizing.mech.shaft.d_prop_seat_mm:.1f-->12.7<!--/V--> quedaría con FS ≈ 0,9 en torsión al corte (hoy <!--V:sizing.mech.shaft.fs_torsion_at_shear_pin:.2f-->2.40<!--/V-->). Hace falta un asiento ≥ Ø17 mm y un eje Ø18–20 [CALCULADO: escala d ∝ Q^⅓ desde sizing].
  - Producto: no identificado. buscar: "13 inch 3 blade propeller shear pin 20 mm bore"; verificar cavitación (Burrill, 02 §4.3) a 550 rpm.
- **Disparador:** T4 calibrado muestra que la hélice es la pérdida dominante (η0 de la MKP-32 por debajo del modelo) **y** la zona de uso tiene ≥ 0,5 m de agua; o 2.7 no encuentra producto.

### 3.2 Batería de 36 V (D-28)
- **Qué:** LiTime 36 V 50 Ah (12S) y motor de 140 KV (D-28) en lugar de 2 × 12 V 100 Ah.
- **Por qué:** es más liviana y más barata: 15 kg contra 22 kg, y 399,99 + 132,99 € (cargador) contra <!--V:bom.battery_charger_eur:.2f-->578.17<!--/V--> € del par actual con su cargador [VERIFICADO precios: R08a, D-19].
- **Beneficio:** −7 kg (≈ −3 % de P_bat, [ESTIMADO: sensibilidad de masa de sizing, ≈ 3,7 W/kg]) y ≈ −45 € [CALCULADO]. La V máx no mejora de forma útil: con 2 personas el bote no llega a 5 kn en ninguna banda (D-30).
- **Costo / tiempo:** con la hélice y la R actuales **no cumple**: requiere 2 222 Wh contra 1 920 Wh, y el BMS es de 50 A [CALCULADO: resultados/sizing.json → optimization, MKP32 con LFP36_50]. Cumple solo junto con 3.1, o si la calibración (2.3) da R ≤ banda nominal. El fusible y el portafusible de 58 V ya quedan comprados (D-28).
- **Disparador:** 2.3 con R medida ≤ nominal y/o 3.1 hecho; o el reemplazo de la batería al final de su vida.

### 3.3 Carenado del tubo
- **Qué:** perfil NACA simétrico impreso alrededor del tubo Ø40 sumergido (≈ 0,45 m), en 2–3 segmentos, con la cuerda alineada con el flujo y no con el eje.
- **Por qué:** en R02, carenar el tubo de un trolling bajó la corriente 16 % (4,9 → 4,1 A) [VERIFICADO: R02 §3 B1, S8], y carenado + spinner dieron −27 % en una canoa [CALCULADO en R02 §4 D1]. Pero esos tubos son verticales, en flujo cruzado pleno, y los cascos tienen R baja.
- **Beneficio en P1:** el tubo va a 25°, así que el arrastre escala con sin² 25° = 0,18. Los apéndices (tubo, carcasa, patín y aleta: CdA 0,0035 m², `resistance.appendage_cda_m2`) suman ≈ 4,9 N a 6 km/h, 3–4 % de R [CALCULADO: ½ρV²·CdA]. La ganancia esperada es ≤ 3 % de P_bat, no 16 % [ESTIMADO].
- **Costo / tiempo:** ≈ 10–15 h de impresión [ESTIMADO: similar a STR-01, 15 h]. Riesgo de enganchar algas y de interferir con la basculación y el buje inferior (re-correr `verify_parts.py`).
- **Disparador:** después de 2.3, si queda un residuo de R no explicado > 5 % [SUPUESTO], o si en T3/T4 el tubo levanta rociones o vibra.

### 3.4 Ánodo (solo si la hélice final es de aluminio)
- **Qué:** buje adaptador Ø16 → Ø25 torneado **en 316** (el ánodo necesita contacto metálico con el eje) y ánodo de collar Tecnoseal de aluminio Ø25 junto a la hélice (D-36).
- **Por qué:** P1 va sin ánodo porque no hay pares metálicos mojados conectados: el grupo giratorio es todo 316 y la hélice es de compuesto (D-36). Una hélice de Al sobre un eje 316 en agua de 20,5 PSU (D-31) es el ánodo del par.
- **Beneficio:** protege la hélice y el cubo de Al. En agua salobre, ánodo de aleación de aluminio, no de zinc [ESTIMADO: R07 hallazgos].
- **Costo / tiempo:** 96 kr [VERIFICADO: R08b §6] y 1–2 h de torno [ESTIMADO].
- **Disparador:** cambio a una hélice de Al (3.1, o la Tohatsu 309B64107-0 de R08b §5), o picaduras en la inspección (checklist §6).

### 3.5 Materiales
- **Qué / por qué:** con la Ender-3 S1 de serie (Sprite ≤ 260 °C, sin cerramiento) solo se imprimen PETG y PETG-CF. ASA pide 260 ± 5 °C, cama a 110 °C y cerramiento [VERIFICADO: R08b §8]. PC pide cámara a 70–100 °C; PA6-CF y PA12-CF piden boquilla a 280–300 °C [VERIFICADO: R05 §1, §A1].
- **Beneficio:** PETG-CF da +75 % de módulo en XY, pero no gana temperatura (HDT 65,7 °C), es frágil en Z y exige boquilla templada (14,99 €, R08b §8) [VERIFICADO: R05 §1, §A8]: sirve solo para placas rígidas y frías. El PA12-CF sería el mejor en agua (−7 % en XY mojado) **solo tercerizado** [VERIFICADO: R05 §A8]; el PA6-CF pierde 50–71 % mojado.
- **Costo / tiempo:** boquilla 14,99 €; impresión tercerizada: buscar: "PA12 CF 3D print service Danmark". Cambiar de impresora queda fuera del alcance fijo del pedido.
- **Disparador:** P1.5 con pérdida en flexión mojada > 25 %, P1.7 con absorción > 1 %, o fisuras/fluencia en T3/T4 en piezas que no pasen a Al (2.1).

## 4. Descartado para P2
- **Tobera Kort 19A:** exige holgura de punta ≤ 0,5 % D ≈ 1,3 mm, inviable con arena, con PETG que flexa, con basculación y con una hélice comercial; lo que se traba entre hélice y tobera es difícil de sacar [VERIFICADO: R09 §4, R03 §3]. La ganancia está en el bollard (+26–30 %) [VERIFICADO: R09 §4], que P1 no necesita (<!--V:sizing.bollard_fwd.T_horiz:.0f-->287<!--/V--> N ≥ <!--V:sizing.success.bollard_pull_min_N:.0f-->244<!--/V--> N). En crucero da 0 a +5 % neto [ESTIMADO: R03]. Reabrir solo si el uso pasa a agua profunda sin arena, con banco de ensayo.
- **Waterjet y rim-drive:** a 6 km/h necesitan 1,35–5,4 veces la potencia al eje de la cola larga [CALCULADO: R03 §2.3].

## 5. Disparadores por prueba

| Prueba de P1 | Resultado | Ítem que se activa |
|---|---|---|
| FEA · P1.3 · P1.5 | FS < 3 · arranque < 2,1 kN · pérdida > 25 % | 2.1, 3.5 |
| P2.1 (200 aperturas del cordón) | Falla | 2.2 |
| P0.2 | Francobordo de popa cerca de 150 mm o carga > placa | 2.4 (y no salir con 2 adultos) |
| P0.3 + T4 | P_bat a 6 km/h fuera de la banda en > 10 % | 2.3 → 2.7, 3.1, 3.2 |
| T2 bollard avante | < 238 N | 2.3, 2.7 |
| T2 con/sin protector | Pérdida > 10 % o reversa < 90 % | 2.6 |
| T2 bollard atrás y T3 parada | Siempre (dato) | 2.5 |
| T2, 30 min a crucero | Tapa del ESC > 50 °C o motor > 80 °C | 2.9 |
| T3 con 1 persona a fondo | Media > 9,0 km/h | Bajar el tope de ERPM ya; 2.8 |
| Inspección de temporada | Picaduras | 3.4 |
