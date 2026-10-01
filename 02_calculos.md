# 02 — Dimensionamiento (sizing.py)

Todo sale de [`sizing.py`](sizing.py) + [`p1calc/`](p1calc/) leyendo `inputs.yaml`. Las tablas
entre marcadores `AUTO` las regenera `docgen.py` desde `resultados/sizing.json`; los números
de la prosa usan marcadores `<!--V:…-->`. Etiquetas: [VERIFICADO: fuente] · [CALCULADO] ·
[ESTIMADO: base] · [SUPUESTO].

## 1. Resumen de resultados

<!-- AUTO:sizing_main -->
| Magnitud | Valor | Etiqueta |
|---|---|---|
| Estado del optimizador | sin_vmax_objetivo | [CALCULADO] |
| Motor / controlador / batería | Maytech MTI120116 150 KV (inrunner refrigerado por agua, 10–16S) / Flipsky FSESC 75350 con caja de agua (VESC, filtro de fase, IP65) / 2 × LiTime 36 V 60 Ah Golf Cart en paralelo (12S2P, BMS 2 × 120 A) | [CALCULADO: optimizador] |
| Masa total / LCG desde el espejo | 217 kg / 1.07 m | [CALCULADO] |
| Calado / GM / escora con el piloto 0,1 m a un lado | 285 mm / 15 mm / 70° | [CALCULADO] |
| Eje del impulsor bajo la flotación (cebado) | 170 mm (ceba) | [CALCULADO] |
| Impulsor / cubo / tobera | Ø132 / Ø66 / Ø87 mm | [CALCULADO] |
| Punto de diseño de la bomba | 39.6 km/h, 5073 rpm, φ 0.260, ψ 0.073, Ω_s 5.59 | [CALCULADO] |
| ¿Planea? / margen mínimo en la joroba | sí / 12 % | [CALCULADO] |
| Tiempo de 0 a planeo | 7.7 s | [CALCULADO] |
| V máx. sostenida (potencia continua, banda nominal) | 25.3 km/h (objetivo 30) | [CALCULADO] |
| P de batería a V máx. / a 5 kn | 6723 W / 1678 W | [CALCULADO] |
| Empuje a punto fijo / en reversa | 764 N / 217 N | [CALCULADO] |
| Autonomía a V máx. / a 5 kn | 37 min (15.6 km) / 2.5 h | [CALCULADO] |
| Energía de la misión requerida / nominal | 3360 / 4608 Wh | [CALCULADO] |
| Cavitación S a V máx. (límite) | 3.18 (3.5) | [CALCULADO] |
| Velocidad periférica máx. | 29.0 m/s | [CALCULADO] |
| Corriente pico de batería / límite de fase | 192 A / 292 A | [CALCULADO] |
| Motor a V máx. sostenida (estacionario) | 49 °C (máx. 120) | [CALCULADO] |
| Eje Ø / FS estático / FS fatiga | 20 mm / 4.0 / 10.3 | [CALCULADO] |
| Rodamientos L10 a V máx. / vel. crítica / sello | 966443 h / 3.1× n máx. / 4.4 m/s | [CALCULADO] |
<!-- /AUTO:sizing_main -->

Figuras: [R(v)](figuras/R_v.png) · [P(v)](figuras/P_v.png) · [autonomía(v)](figuras/autonomia_v.png) ·
[costo vs autonomía](figuras/costo_autonomia.png) · [velocidad–autonomía–costo](figuras/velocidad_autonomia_costo.png) ·
[sensibilidad](figuras/sensibilidad.png).

## 2. Resistencia al avance R(v)

**Hidrostática.** Volumen ∇ = m/ρ; calado T con costados abocinados: ∇ = L·C_B·(B_f·T + tanφ·T²)
(B_f ancho de fondo, tanφ = (B − B_f)/(2·puntal)). Masa de diseño <!--V:sizing.masses.total_kg:.0f-->217<!--/V--> kg →
calado <!--V:sizing.hydrostatics.draft_m:.3f-->0.285<!--/V--> m, francobordo <!--V:sizing.hydrostatics.freeboard_m:.3f-->0.182<!--/V--> m [CALCULADO].

**Régimen.** Velocidad de casco 1,34·√LWL[ft] kn ≡ Fr_L ≈ 0,40 → <!--V:sizing.hull_speed.v_hull_kmh:.2f-->6.36<!--/V--> km/h. El crucero
pedido (6 km/h, Fr_L = 0,376) **está en la velocidad de casco**: verificado. Entre 8 y 12 km/h
(Fr_L 0,50–0,75; Fr_∇ ≈ 0,9–1,3) el casco está en la **joroba de transición** (no planea con 2 personas:
research/R04 #9). L/∇^⅓ ≈ 3 — fuera de toda serie sistemática (NPL, Series 62, Holtrop) y de
Savitsky (planeo). Por eso se usa un modelo por componentes con banda de incertidumbre y
calibración por remolque:

| Componente | Ecuación | Fuente / etiqueta |
|---|---|---|
| Fricción | R_F = ½ρV²S·(C_F + ΔC_F)·(1+k), C_F = 0,075/(log₁₀Re − 2)² | ITTC-1957 [VERIFICADO: research/R09]; k = 0,20, ΔC_F = 4·10⁻⁴ [ESTIMADO] |
| Espejo sumergido | R_TR = ½ρV²A_T·c₆, c₆ = 0,2(1 − 0,2F_nT) si F_nT < 5; F_nT = V/√(2gA_T/(B + B·C_WP)) | Holtrop & Mennen 1982 [VERIFICADO: research/R09] |
| Olas + joroba | R_W = W·c_w·Fr⁴/(1 + (Fr/Fr_h)⁴) | Forma semi-empírica [ESTIMADO]: ~Fr⁴ bajo la vel. de casco, meseta en la joroba; c_w = 1,5, Fr_h = 0,55 **a calibrar** |
| Aire | R_air = ½ρ_a C_d A (V + V_viento)² | C_d = 1,0, A = 1,0 m² [ESTIMADO] |

**Banda.** [0,75; 1,15] × nominal, anclada a mediciones de botes de 2,4–2,75 m con 1–2
personas: R(6 km/h) = 95–150 N (research/R04 §C.3). Se dimensiona con el borde alto
("diseño"). Contraste con Gerr (Propeller Handbook) en [P(v)](figuras/P_v.png): Gerr da más
potencia porque su DL ratio (~790) está fuera de rango (solo orden de magnitud).

**Calibración (PENDIENTES P0.3–P0.4):** remolcar el bote cargado con el dinamómetro a 3–4
velocidades (GPS), 3 pasadas por sentido; ajustar `resistance.wave_cw` (y si hace falta
`wave_fr_hump`) para que el modelo nominal pase por los puntos (error ≤ 10 %).

### Barrido de velocidad

<!-- AUTO:sizing_sweep -->
| v [km/h] | Fr_L | R nom [N] | R diseño [N] | P_bat nom [W] | P_bat diseño [W] | rpm hélice | Autonomía nom [h] | Autonomía diseño [h] | Wh/km diseño |
|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.13 | 10 | 11 | 23 | 26 | 435 | 100.67 | 89.09 | 13 |
| 3 | 0.19 | 24 | 27 | 68 | 78 | 669 | 34.13 | 29.46 | 26 |
| 4 | 0.25 | 48 | 55 | 170 | 199 | 924 | 13.59 | 11.56 | 50 |
| 5 | 0.31 | 84 | 97 | 375 | 445 | 1201 | 6.14 | 5.18 | 89 |
| 6 | 0.38 | 135 | 156 | 736 | 879 | 1491 | 3.13 | 2.62 | 146 |
| 7 | 0.44 | 198 | 228 | 1285 | 1541 ✗ | 1781 | 1.79 | 1.49 | 220 |
| 8 | 0.50 | 267 | 307 | 2012 | 2420 ✗ | 2055 | 1.15 | 0.95 | 302 |
| 9 | 0.56 | 335 | 385 | 2865 | 3451 ✗ | 2307 | 0.80 | 0.67 | 383 |
| 10 | 0.63 | 398 | 458 | 3783 | 4559 ✗ | 2533 | 0.61 | 0.51 | 456 |
| 11 | 0.69 | 455 | 523 | 4715 | 5682 ✗ | 2735 | 0.49 | 0.41 | 517 |
| 12 | 0.75 | 505 | 580 | 5636 | 6787 ✗ | 2917 | 0.41 | 0.34 | 566 |
| 13 | 0.82 | 548 | 630 | 6533 | 7861 ✗ | 3085 | 0.35 | 0.29 | 605 |
<!-- /AUTO:sizing_sweep -->

## 3. Empuje requerido y márgenes

Empuje en el eje: T_eje = R / [(1 − t)·cosθ·(1 − pérdida_protector)], con t = 0,02 (hélice
~1 m detrás del espejo), θ = 25°, pérdida del aro protector 6 % [ESTIMADO: aro corto no
perfilado 3–8 %, research/R03]. Avance: V_a = V(1 − w)·cosθ, w = 0,02.

Márgenes de diseño (condición adversa): viento de proa 6 m/s + olas cortas (+25 % de R
hidrodinámica) + corriente 0,5 m/s. En esa condición, la velocidad alcanzable es
<!--V:sizing.adverse.vmax_headwind_waves_kmh:.1f-->5.6<!--/V--> km/h y la velocidad sobre el fondo contra la corriente
<!--V:sizing.adverse.sog_against_current_kmh:.1f-->3.8<!--/V--> km/h (criterio ≥ 3 km/h) [CALCULADO].

**Bollard pull objetivo:** ≥ 0,85 × predicho; predicho <!--V:sizing.bollard_fwd.T_horiz:.0f-->253<!--/V--> N horizontales
(<!--V:sizing.bollard_fwd.limiter:-->corriente de motor<!--/V--> limita), igual a los fuerabordas eléctricos de 1 kW medidos (290–310 N,
0,28–0,29 N/W; research/R04 §B.2). Los "65 lb a 600 W" de algunos trolling exigen FM > 1:
físicamente imposibles y no se usan como meta. Marcha atrás: <!--V:sizing.bollard_rev.T_horiz:.0f-->80<!--/V--> N (límite de
corriente 50 % por firmware × rendimiento de hélice invertida 0,65 [ESTIMADO]).

### 3.1 Límite legal de velocidad (Sejladsreglement §4: ≤ 5 kn a < 300 m de la costa)

Como P1 opera siempre a < 300 m, la V máx útil es 9,26 km/h [VERIFICADO: research/R07 §1.2]; los
12 km/h del pedido no tienen uso legal y no se dimensiona para ellos. Pero con carga liviana
(1 persona) el modelo supera el límite, así que se fija un **tope de ERPM** en el VESC
(`l_max_erpm`, parámetro de VESC Tool [ESTIMADO: nombre de memoria técnica, confirmar en la
versión instalada]) calculado como las rpm a 5 kn en el caso más rápido (liviano, banda baja,
batería llena). Con 2 personas el bote no llega a 5 kn en ninguna banda (<!--V:sizing.legal_speed.vmax_full_load_low_full_bat_kmh:.1f-->8.0<!--/V--> km/h en la banda baja con batería llena [CALCULADO]),
así que sacar el tope con 2 a bordo es legal, pero recupera apenas <!--V:sizing.legal_speed.cap_loss_full_load_low_kmh:.2f-->0.05<!--/V--> km/h [CALCULADO]; por defecto queda puesto.

<!-- AUTO:legal_speed -->
| Magnitud | Valor | Etiqueta |
|---|---|---|
| Límite legal a < 300 m de la costa | 9.26 km/h (5 kn) | [VERIFICADO: research/R07, R13] |
| Potencia de batería a 5 kn (banda de diseño) | 1678 W | [CALCULADO] |
| Autonomía a 5 kn | 2.5 h | [CALCULADO] |
| Tope de rpm 'modo costa' (piloto liviano, 197 kg, banda baja, batería llena) | 1850 rpm / 3700 ERPM | [CALCULADO] → VESC `l_max_erpm` en el perfil de costa |
<!-- /AUTO:legal_speed -->

## 4. Hélice

### 4.1 Selección
Optimizador (sizing.py → `optimize`): recorre hélices × baterías × relaciones de poleas
HTD-5M y elige el **mínimo costo** que cumple las restricciones **duras** (energía 2 h + 20 %
en la banda de diseño, corriente BMS/ESC, margen ESC ≥ 30 %, tensión ≤ 48 V, cavitación de
Keller, calado de punta ≤ 380 mm, **asiento de hélice del eje con FS ≥ 2 en torsión al corte del
pasador** y **hélice con producto concreto identificado**); dentro de +10 % de costo prefiere la
que cumple V máx (restricción blanda, 8 km/h) y luego la más barata entre las que quedan a ≤ 3 %
de la mejor autonomía. La hélice "objetivo"
EO10x8 (3 palas, ~10 × 8 in) daría ~13 % menos energía de crucero, pero no se encontró a la venta
(research/R08b §5): se muestra como referencia y se elige la Minn Kota MKP-32 (decisiones D-06),
cuyas medidas son [ESTIMADO] hasta medirla (PENDIENTES P0.7).

<!-- AUTO:optimization -->
| Motor | Batería | Ø imp | D_t/D | V máx [km/h] | Margen joroba | Costo [€] | Duras OK |
|---|---|---|---|---|---|---|---|
| MTI120116_150 | LT36_60x2 | 132 | 0.66 | 25.3 | 12 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 120 | 0.74 | 25.2 | 12 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 132 | 0.62 | 25.0 | 10 % | 1896 | sí |
| MTI120116_150 | LT36_60x2 | 120 | 0.70 | 25.0 | 11 % | 1896 | sí |
| HPM5000B_48 | LT36_60x1 | 132 | 0.74 | 14.4 | -34 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.74 | 14.3 | -34 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.70 | 14.2 | -34 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.74 | 14.1 | -35 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.70 | 14.1 | -35 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.74 | 14.0 | -35 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.66 | 14.0 | -34 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.70 | 13.9 | -35 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.74 | 13.8 | -35 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 132 | 0.66 | 13.8 | -35 % | 1308 | no |
| HPM5000B_48 | LT36_60x1 | 120 | 0.70 | 13.8 | -35 % | 1308 | no |
<!-- /AUTO:optimization -->

### 4.2 Modelo de hélice
KT(J), KQ(J) de la hélice concreta con los polinomios **Wageningen B-series** (Oosterveld & van
Oossanen; 39 + 47 términos transcritos de Bernitsas, Ray & Kinley 1981 y comparados término a
término; control B3-50, P/D 1,0, J 0,5 → KT 0,2451, KQ 0,03863, η0 0,505 [VERIFICADO: research/R09
§2.1; test `test_bseries_control`]) dentro de su rango (Z 2–7, AE/A0 0,30–1,05, P/D 0,5–1,4).
Fuera de rango —como la hélice de trolling elegida, P/D ≈ 0,4— se usa una aproximación lineal
calibrada contra la serie [ESTIMADO]: KT = KT0(1 − J/J_T0), KQ = KQ0(1 − J/J_Q0), KT0 = 0,40·P/D,
J_T0 = 1,10·P/D, J_Q0 = 1,20·P/D, KQ0 = KT0^1,5/(√(π/2)·2π·FOM_b), FOM_b = 0,72 − 0,18·P/D.
En ambos casos η0 × 0,95 por escala y rugosidad (la hélice opera a Rn 6–8·10⁵ < 2·10⁶;
corrección ITTC-78 de Holtrop: 0,93–0,98, research/R09 §2.2). Contraste con el disco actuador:
η_i = 2/(1 + √(1 + C_T)). η0 de crucero = <!--V:sizing.cruise.design.prop_eta0:.2f-->0.41<!--/V--> a J = <!--V:sizing.cruise.design.prop_J:.2f-->0.23<!--/V--> y
<!--V:sizing.cruise.design.prop_n_rpm:.0f-->1491<!--/V--> rpm (los eléctricos comerciales: 1 200–1 450 rpm a plena potencia).

### 4.3 Cavitación (Keller y Burrill)
Keller: AE/A0 mín = (1,3 + 0,3Z)·T/((p0 + ρgh − pv)·D²) + K, K = 0,2 (un eje; conservador para
flujo casi uniforme) [VERIFICADO: research/R09 §3.3];
Burrill: σ0,7R = (p0 + ρgh − pv)/(½ρV_R²), τc = T/(½ρV_R²·A_P), A_P ≈ A_D(1,067 − 0,229·P/D)
[ESTIMADO: Carlton, no verificado]; límite = **curva de 5 % digitalizada** (interpolación en tabla)
[VERIFICADO: research/R09 §3.2]. El ajuste anterior 0,3σ^0,6 era no conservador para σ > 0,6.
En punto fijo se espera algo de cavitación/ventilación a fondo de acelerador (τc del punto fijo
es propiedad de la hélice); el criterio vale para crucero y V máx.

<!-- AUTO:cavitation -->
| Condición | T [N] | n [rpm] | σ0.7R | τc | τc límite (Burrill aprox.) | AE/A0 mín Keller | AE/A0 |
|---|---|---|---|---|---|---|---|
| bollard | 317 | 1300 | 1.36 | 0.247 | 0.279 | 0.29 | 0.35 |
| cruise | 195 | 1491 | 1.02 | 0.114 | 0.261 | 0.26 | 0.35 |
| vmax | 232 | 1616 | 0.87 | 0.115 | 0.249 | 0.27 | 0.35 |
<!-- /AUTO:cavitation -->

### 4.4 ¿Hélice impresa? No.
Raíz de pala de una hélice de 10–12" a ~1 kW: M ≈ 10 N·m sobre Z ≈ 320 mm³ → σ ≈ 30 MPa.
Admisible PETG en fatiga (≥ 10⁷ ciclos, mojado): < 1,5 MPa (research/R05: f_fatiga ≈ 0,06).
FS ≈ 0,05 → **se compra** (research/R02 E1: hélice PETG fisurada tras una temporada a baja carga).

### 4.5 Efecto del protector
Aro perfilado (espesor 15 %, cuerda 76 mm, holgura 2–3 % D): −10 % de empuje de diseño (rango de sensibilidad 0–25 %), sin ganancia en bollard [ESTIMADO, research/R03; decisiones D-26].
Una tobera Kort 19A daría +20–30 % de bollard pero no entra impresa (Ø > 210 mm) sin
segmentarla con perfil exacto → P2.

## 5. Motor, ESC y correa

Modelo DC del BLDC: Kt = 1/KV_rad; I = Q/Kt + I0; V = ω/KV_rad + I·R; P_bat = V·I/η_ESC;
duty = V/V_bat ≤ 0,95. Motor Flipsky 6374 Battle Hardened 190 KV: 85 A, 3,5 kW, 0,98 kg, eje 8 mm
[VERIFICADO: research/R08a §1]; R = 0,040 Ω [ESTIMADO: Maytech MTO6374 de la misma clase 0,0402 Ω,
VERIFICADO research/R08a; Flipsky no publica]; ESC Flipsky 75100 V2.0: 14–84 V, 100 A continuos,
BEC 5 V 1 A [VERIFICADO: research/R08a §2]; con FW ≥ 5.03 hay que **apagar el filtro de fase**
(advertencia del fabricante, research/R08a). Relación de
poleas elegida <!--V:sizing.selection.z_motor:d-->20<!--/V-->T : <!--V:sizing.selection.z_shaft:d-->48<!--/V-->T. Corriente pico de batería
<!--V:sizing.esc.I_bat_peak_a:.0f-->53<!--/V--> A → margen del ESC (100 A) <!--V:sizing.esc.margin_frac:.0%-->67%<!--/V--> (requisito ≥ 30 %).
Correa HTD-5M 15 mm: tirón efectivo a corriente máxima <!--V:sizing.mech.belt.Fe_N:.0f-->189<!--/V--> N vs admisible 400 N
[ESTIMADO: catálogo, a verificar] → FS <!--V:sizing.mech.belt.fs_belt:.2f-->2.11<!--/V-->; correa
<!--V:sizing.mech.belt.length_std_mm:.0f-->425<!--/V--> mm.

### 5.1 Tiempo sostenible a velocidad alta ("por ratos")

<!-- AUTO:sizing_sustain -->
| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1285 | 50 | 108 | 2 | 2 |
| 7 | design | no (tensión (duty)) | 1541 | 60 | 90 | 1 | 0 |
| 8 | nominal | no (tensión (duty), corriente de motor) | 2012 | 79 | 69 | 1 | 0 |
| 8 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2420 | 95 | 57 | 1 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2865 | 112 | 48 | 0 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3451 | 135 | 40 | 0 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3783 | 148 | 37 | 0 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4559 | 178 | 30 | 0 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4715 | 184 | 29 | 0 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5682 | 222 | 24 | 0 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5636 | 220 | 25 | 0 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 6787 | 265 | 20 | 0 | 0 |
<!-- /AUTO:sizing_sustain -->

### 5.2 Térmico del ESC en caja estanca

La caja impresa (ELE-01) no puede superar la temperatura de servicio del PETG (50 °C). El calor
del ESC sale por la tapa de aluminio (ELE-02) hacia un **disipador de aletas comprado**; el
cálculo da la resistencia térmica máxima que hay que exigir al comprarlo (pérdida del ESC con
η = 0,97, conservador; caja a la sombra, aire a 30 °C):

<!-- AUTO:thermal_esc -->
| Condición | Pérdida ESC [W] | Sol [W] | R disipador máx. [K/W] |
|---|---|---|---|
| esc_cruise | 26 | 0 | 0.61 |
| esc_vmax | 34 | 0 | 0.44 |
| Requisito de compra (crucero → caja ≤ 50 °C) |  |  | **≤ 0.44** |
| Con ese disipador, a V máx sostenida: 50 °C estacionario (límite ESC 80 °C) |  |  | ∞ |
<!-- /AUTO:thermal_esc -->

## 6. Batería, cables y protecciones

E_req = P_bat,crucero × 2 h × 1,2 / DoD útil (0,90). Requerida <!--V:sizing.battery.E_required_wh:.0f-->2343<!--/V--> Wh;
elegida: <!--V:sizing.selection.battery_desc:-->2 × LiTime 36 V 60 Ah Golf Cart en paralelo (12S2P, BMS 2 × 120 A)<!--/V--> (<!--V:sizing.battery.E_usable_wh:.0f-->2304<!--/V--> Wh usables,
<!--V:sizing.battery.mass_kg:.1f-->22.0<!--/V--> kg, tasa pico <!--V:sizing.battery.C_rate_peak:.2f-->0.53<!--/V--> C).
Química: LiFePO4 (sin runaway en ensayo ARC; research/R06), fija en caja ventilada, alta y
centrada (trimado), nunca en el espejo. Cable DC <!--V:sizing.cables.dc.section_mm2:d-->16<!--/V--> mm²
(caída <!--V:sizing.cables.dc.drop_frac:.1%-->0.9%<!--/V-->), fases <!--V:sizing.cables.phase.section_mm2:d-->10<!--/V--> mm²
(caída <!--V:sizing.cables.phase.drop_frac:.1%-->2.1%<!--/V-->); fusible <!--V:sizing.fuse.rating_a:d-->80<!--/V--> A a ≤ 178 mm del borne
(ABYC E-11; research/R06), que protege al cable. Fusible y portafusible MIDI de **58 V**
(IMAXX midiOTO + HMD4-MG1-H): los portafusibles de 32 V de Biltema ANL y Blue Sea AMI/MIDI
quedarían cortos si se pasa a 12S [VERIFICADO: research/R08a §6]. Batería ↔ instalación con
Anderson SB50 (120 A, 16 mm²), el mismo conector de salida del cargador [VERIFICADO: research/R08a §5, §8].
El BMS bloquea la carga bajo 5 °C (Power Queen): cargar en interior [VERIFICADO: research/R08a §4].

## 7. Mecánica del tren

| Ítem | Resultado |
|---|---|
| Eje Ø16 316 — FS estático mín. | <!--V:sizing.mech.shaft.fs_static:.2f-->2.40<!--/V--> |
| Eje — FS fatiga (Goodman) | <!--V:sizing.mech.shaft.fs_fatigue_goodman:.2f-->2.45<!--/V--> |
| Velocidad crítica / rpm máx | <!--V:sizing.mech.shaft.n_crit_rpm:.0f-->5834<!--/V--> / <!--V:sizing.mech.shaft.n_max_rpm:.0f-->1713<!--/V--> rpm |
| Rodamiento A (6202-2RS), L10 a máxima | <!--V:sizing.mech.bearing_max.L10_h:.0f-->12013<!--/V--> h |
| Pasador de corte | Ø<!--V:sizing.mech.shear_pin.d_std_mm:-->2.0<!--/V--> mm AISI 316 → <!--V:sizing.mech.shear_pin.Q_shear_Nm:.1f-->12.4<!--/V--> N·m (calibrar con P1.9) |
| Pasador en crucero: τ medio / FS Goodman en corte | <!--V:sizing.mech.shear_pin.fatigue_cruise.tau_mean_MPa:.0f-->112<!--/V--> MPa / <!--V:sizing.mech.shear_pin.fatigue_cruise.fs_goodman:.2f-->1.46<!--/V--> → vida limitada: **cambiar el pasador cada 10 h de uso o al inicio de cada salida larga** [SUPUESTO]; llevar repuestos (research/R09 §5.3 llega a la misma conclusión) |
| Velocidad crítica: tramo entre bujes ≤ 0,6 m (research/R09 §5.1: 5 100 rpm con 0,6 m; 1 850 rpm con 1,0 m) | ver fila de velocidad crítica |
| Torque de rotor trabado en el eje | <!--V:sizing.mech.Q_lock_shaft_Nm:.1f-->6.8<!--/V--> N·m |

## 8. Basculación (kick-up), impacto y retención en marcha atrás

Momento de gravedad de la unidad (cola pesada) <!--V:sizing.mech.kickup.M_gravity_Nm:.1f-->25.9<!--/V--> N·m; retén
<!--V:sizing.mech.kickup.M_detent_Nm:.0f-->15<!--/V--> N·m; empuje en reversa <!--V:sizing.mech.kickup.M_thrust_rev_Nm:.1f-->5.5<!--/V--> N·m →
FS de retención en reversa <!--V:sizing.mech.kickup.fs_reverse_hold:.1f-->7.4<!--/V-->. En avance, la cola bascula con
<!--V:sizing.mech.kickup.F_release_at_skeg_fwd_N:.0f-->90<!--/V--> N horizontales en el patín.
Impacto a 2,5 m/s: impulso J = I_p·v/r_c (I_p = <!--V:sizing.mech.inertia.I_pivot_kgm2:.2f-->2.57<!--/V--> kg·m²) en 10 ms
→ pico <!--V:sizing.mech.impact.F_peak_N:.0f-->1002<!--/V--> N (semiseno ×2). La hélice sale del agua a ~22° de basculación.

## 9. Estructural — FS por pieza y caso de carga

Propiedades degradadas (research/R05): S_corta = σ_XY·f_agua·f_temp·f_proceso; S_sost = ×f_creep;
S_fatiga = ×f_fatiga. Casos: LC1 empuje avante, LC2 marcha atrás, LC3 rotor trabado, LC4 golpe
de hélice (hasta el corte del pasador), LC5 varada/impacto (pico dinámico y cola trabada con
fusible), LC6 ola y vibración (fatiga a paso de pala), LC7 manipulación.

<!-- AUTO:estructural -->
| Pieza | Caso de carga | Modelo | σ [MPa] | Admisible | S [MPa] | FS | Obj. | OK |
|---|---|---|---|---|---|---|---|---|
| P1-PMP-03 | Álabe en la raíz: par de diseño 15.2 N·m + empuje | voladizo: F_t=T/(Z·r_m)=61 N a span/2 + F_a=153 N/álabe en r̄; M=2.98 N·m; W_mín perfil cubo=80 mm³ (c=53.9, t=4.31) | 37.43 | metal | 205.0 | 5.48 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz, fatiga: par de diseño 15.2 N·m + empuje | σ_a = 0.30·σ_m (paso por 7 álabes del estator, toma); K_f 1.5; S_e 316 | 11.23 | metal | 120.0 | 10.69 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz: par máx. del controlador 18.6 N·m + empuje | voladizo: F_t=T/(Z·r_m)=75 N a span/2 + F_a=153 N/álabe en r̄; M=3.06 N·m; W_mín perfil cubo=80 mm³ (c=53.9, t=4.31) | 38.49 | metal | 205.0 | 5.33 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz, fatiga: par máx. del controlador 18.6 N·m + empuje | σ_a = 0.30·σ_m (paso por 7 álabes del estator, toma); K_f 1.5; S_e 316 | 11.55 | metal | 120.0 | 10.39 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz: par de corte del pasador 33.5 N·m (traba repartida) | voladizo: F_t=T/(Z·r_m)=135 N a span/2 + F_a=153 N/álabe en r̄; M=3.58 N·m; W_mín perfil cubo=80 mm³ (c=53.9, t=4.31) | 45.00 | metal | 205.0 | 4.56 | 2.0 | ✔ |
| P1-PMP-03 | Cubo: aplastamiento del pasador al par de corte | F=837 N por lado sobre 3.5×20 mm (r medio) | 11.96 | metal | 307.5 | 25.72 | 2.0 | ✔ |
| P1-PMP-05 | Par máx. del controlador (margen contra corte intempestivo) | corte doble τ=T/(d_eje·A)=96.5 MPa; τ_u=0,6·S_u=174 MPa; T_corte/T_máx=1.80 (criterio R12 ≥ 1,5) | 96.50 | metal | 174.0 | 1.8 | 2.0 | ✔ (justif.) |
| P1-PMP-05 | Fatiga a par de crucero (Goodman en corte) | τ_m=73.4, τ_a=11.0 MPa (T_top 14.1 N·m, ±15%); S_e,τ=0,577·S_e; índice Goodman 0.62 | 0.62 | metal | 1.0 | 1.61 | 2.0 | ✔ (justif.) |
| P1-PMP-06 | Álabe del estator en la raíz: par de diseño 15.2 N·m | voladizo (conservador, en realidad empotrado en camisa y cubo): F_t=44 N, F_a=38 N, F_r buje=22 N; W_mín=68 mm³ (c=44.4, t=4.44) | 25.04 | metal | 240.0 | 9.58 | 2.0 | ✔ |
| P1-PMP-06 | Álabe del estator, fatiga: par de diseño | σ_a=0.30·σ_m (estelas de 5 álabes); S_e Al anodizado = 0.6·S_e; K_f 1.5 | 7.51 | metal | 38.4 | 5.11 | 2.0 | ✔ |
| P1-PMP-06 | Álabe del estator en la raíz: par máx. del controlador 18.6 N·m | voladizo (conservador, en realidad empotrado en camisa y cubo): F_t=54 N, F_a=38 N, F_r buje=22 N; W_mín=68 mm³ (c=44.4, t=4.44) | 26.93 | metal | 240.0 | 8.91 | 2.0 | ✔ |
| P1-PMP-06 | Álabe del estator, fatiga: par máx. del controlador | σ_a=0.30·σ_m (estelas de 5 álabes); S_e Al anodizado = 0.6·S_e; K_f 1.5 | 8.08 | metal | 38.4 | 4.75 | 2.0 | ✔ |
| P1-PMP-01 | Presión interna 0.20 MPa (R12 §7.2) | aro delgado σ=p·r/t, r=73.9, t=5.0 | 2.96 | metal | 240.0 | 81.2 | 2.0 | ✔ |
| P1-PMP-08 | Presión interna 0.20 MPa (R12 §7.2) | aro delgado σ=p·r/t, r=68.9, t=5.0 | 2.76 | metal | 240.0 | 87.09 | 2.0 | ✔ |
| P1-PMP-01 | Bulones brida toma (8×M6): presión + bucket + momentos | F_ax=2276 N, M=171.3 N·m (boquilla 323 N, bucket 698 N, peso) → F_bulón=804 N sobre A_s=20.1 mm² (sin precarga) | 40.01 | metal | 450.0 | 11.25 | 2.0 | ✔ |
| P1-PMP-08 | Bulones brida carcasa–tobera (8×M6): presión + bucket + momentos | F_ax=2276 N, M=118.6 N·m (boquilla 323 N, bucket 698 N, peso) → F_bulón=633 N sobre A_s=20.1 mm² (sin precarga) | 31.51 | metal | 450.0 | 14.28 | 2.0 | ✔ |
| P1-PMP-01 | Tornillos anti-rotación del estator (2×M5) al corte | F=130 N por tornillo (T_max 18.6 N·m, r=71.4) | 9.16 | metal | 259.6 | 28.35 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: aplastamiento del alojamiento del buje — F lateral de la boquilla 323 N | σ_b=F/(d·t), d=12.0, t=25.5 | 1.05 | metal | 187.5 | 177.87 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: sección neta y desgarro — F lateral de la boquilla 323 N | máx(F/((w−d)·t), F/(2·(e−d/2)·t)·√3), w=24.0, e=12.0 | 1.83 | metal | 125.0 | 68.46 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: flexión en el arranque — F lateral de la boquilla 323 N | M=F·15.0 mm, W=w·t²/6 (eje débil) | 1.86 | metal | 125.0 | 67.3 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: fatiga — F lateral de la boquilla 323 N | σ_a = σ flexión (maniobras, ~1e5–1e6 ciclos); S_e 5083; K_f 1.5 | 1.86 | metal | 73.3 | 39.48 | 2.0 | ✔ |
| P1-PMP-11 | Buje de pivote POM: presión — F lateral de la boquilla 323 N | p=F/(d·L), d=8.0, L=25.5 (un solo buje) | 1.58 | metal | 25.0 | 15.81 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: aplastamiento del alojamiento del buje — F del bucket 698 N | σ_b=F/(d·t), d=12.0, t=25.5 | 2.28 | metal | 187.5 | 82.29 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: sección neta y desgarro — F del bucket 698 N | máx(F/((w−d)·t), F/(2·(e−d/2)·t)·√3), w=24.0, e=12.0 | 3.95 | metal | 125.0 | 31.67 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: flexión en el arranque — F del bucket 698 N | M=F·15.0 mm, W=w·t²/6 (eje débil) | 4.01 | metal | 125.0 | 31.14 | 2.0 | ✔ |
| P1-PMP-09 | Oreja: fatiga — F del bucket 698 N | σ_a = σ flexión (maniobras, ~1e5–1e6 ciclos); S_e 5083; K_f 1.5 | 4.01 | metal | 73.3 | 18.27 | 2.0 | ✔ |
| P1-PMP-11 | Buje de pivote POM: presión — F del bucket 698 N | p=F/(d·L), d=8.0, L=25.5 (un solo buje) | 3.42 | metal | 25.0 | 7.31 | 2.0 | ✔ |
| P1-PMP-09 | Bulones placa–espejo (6×M6): F del bucket 698 N + momento | brazo 36 mm al espejo; F_bulón=207 N sobre A_s=20.1 mm² | 10.30 | metal | 450.0 | 43.67 | 2.0 | ✔ |
| P1-PMP-09 | Cuello: F lateral de la boquilla con el O-ring a tope | voladizo del cuello M=F·L=5.3 N·m, W anillo=116736 mm³ | 0.04 | metal | 125.0 | 2753.99 | 2.0 | ✔ |
| P1-STE-01 | Flexión del tubo por el desvío del chorro (fatiga, sizing) | M = F_s·e = 323 N × 66 mm; Z tubo Ø101.1/Ø91.1 | 0.62 | metal | 90.0 | 145.96 | 2.0 | ✔ |
| P1-STE-01 | Oreja del bucket: flexión en su plano (bucket R12, corta) | F/2 = 704 N a 52 mm de la raíz; sección 8 × 36 | 21.12 | metal | 240.0 | 11.36 | 2.0 | ✔ |
| P1-STE-01 | Oreja del bucket: flexión (reversa sizing, fatiga) | F/2 = 349 N a 52 mm; 8 × 36 | 10.47 | metal | 90.0 | 8.59 | 2.0 | ✔ |
| P1-STE-01 | Oreja de pivote (dentro de la de la bomba): flexión de la raíz | F = √((F_b/2)²+(F_s/2)²) = 727 N a 12 mm; 25 × 30 | 2.33 | metal | 240.0 | 103.14 | 2.0 | ✔ |
| P1-STE-02 | Hombro Ø8 biempotrado: flexión + corte (bucket R12 + dirección, corta) | reacción superior 1490 N en luz 28.5 mm (M = F·L/8); 316 estirado | 111.17 | metal | 310.0 | 2.79 | 2.0 | ✔ |
| P1-STE-02 | Hombro Ø8: flexión por maniobras (fatiga) | F_s/2 = 162 N, M = F·L/8 | 11.46 | metal | 180.0 | 15.7 | 2.0 | ✔ |
| P1-STE-05 | Hombro Ø8 en voladizo: flexión + corte (corta) | reacción inferior 195 N a 14.3 mm | 56.20 | metal | 310.0 | 5.52 | 2.0 | ✔ |
| P1-STE-05 | Hombro Ø8 en voladizo: flexión por maniobras (fatiga) | F_s/2 = 162 N a 14.3 mm | 45.86 | metal | 180.0 | 3.92 | 2.0 | ✔ |
| P1-STE-02 | Presión en el buje POM de la oreja de la bomba (P1-PMP-11) | 1490 N / (Ø8 × 25.5) | 7.29 | metal | 20.0 | 2.74 | 2.0 | ✔ |
| P1-STE-03 | Arandela POM: empuje axial (peso boquilla + bucket + componente vertical) | 60 N [ESTIMADO] / 199 mm² | 0.30 | metal | 10.0 | 33.18 | 2.0 | ✔ |
| P1-STE-06 | Poste Ø22: flexión + torsión (biela M66, M_s con F_s R12) | F_biela = M_s/79 mm = 304 N a 138 mm de la brida | 41.03 | metal | 240.0 | 5.85 | 2.0 | ✔ |
| P1-STE-06 | Poste Ø22: flexión (fatiga, sizing) | F_biela = 269 N | 35.67 | metal | 90.0 | 2.52 | 2.0 | ✔ |
| P1-STE-06 | Brida del poste: 4 × M8 A4-70 en Ø32 (tracción) | F = 4M/(n·BC) = 1313 N; As 36,6 mm² | 35.87 | metal | 450.0 | 12.55 | 2.0 | ✔ |
| P1-STE-04 | Banda de la brida: torsión (momento del poste) + flexión | T = 42.0 N·m en 24 × 20 (α = 0.217); F_biela × 76 mm | 36.92 | metal | 125.0 | 3.39 | 2.0 | ✔ |
| P1-STE-04 | 4 × M8 A4-70 a la torre: tracción por el momento del poste | F = M/(19 mm)/2 = 1105 N por bulón | 30.20 | metal | 450.0 | 14.9 | 2.0 | ✔ |
| P1-STE-08 | Placa de topes 8 mm: flexión en su plano (timón forzado) | F = 2·F_biela = 607 N a 90 mm del ala; sección 32 × 8 | 40.02 | metal | 125.0 | 3.12 | 2.0 | ✔ |
| P1-STE-06 | Poste contra el tope: flexión (timón forzado) | F = 607 N a 111 mm de la brida | 64.69 | metal | 240.0 | 3.71 | 2.0 | ✔ |
| P1-STE-08 | 2 × M6 A4-70 del ala al espejo (tracción por el momento) | M = F × 40 mm / 30 mm entre bulón y borde | 40.27 | metal | 450.0 | 11.18 | 2.0 | ✔ |
| P1-STE-07 | Brazo 10 mm: flexión por la altura de la rótula + tracción | F_biela 304 N; M = F × 12 mm en 24 × 10 | 10.37 | metal | 125.0 | 12.05 | 2.0 | ✔ |
| P1-REV-01 | Chapa de la cuchara: franja empotrada bajo la presión dinámica (corta) | p = 98 kPa, luz 53.5 mm (nervio central), t = 4 | 8.73 | metal | 125.0 | 14.31 | 2.0 | ✔ |
| P1-REV-01 | Chapa de la cuchara: franja (fatiga de soldadura, 1e5) | ídem | 8.73 | metal | 68.0 | 7.79 | 2.0 | ✔ |
| P1-REV-01 | Cuchara como viga entre brazos (bucket R12, corta) | M = F·L/8, L = 107; I_arco = 245e3 mm⁴ | 3.51 | metal | 125.0 | 35.61 | 2.0 | ✔ |
| P1-REV-01 | Brazo lateral: flexión (bucket R12, corta) | F/2 = 704 N a 128 mm; sección 4 × 60 | 37.41 | metal | 125.0 | 3.34 | 2.0 | ✔ |
| P1-REV-01 | Brazo lateral: flexión (reversa sizing, fatiga de soldadura) | F/2 = 349 N | 18.55 | metal | 68.0 | 3.67 | 2.0 | ✔ |
| P1-REV-01 | Agujero de traba: aplastamiento del brazo (émbolo Ø12) | F = M_h/r = 127 N·m / 45 mm = 2817 N | 58.68 | metal | 125.0 | 2.13 | 2.0 | ✔ |
| P1-REV-01 | Pivote: aplastamiento del brazo + refuerzo (buje Ø14 × 8) | F/2 = 704 N | 6.29 | metal | 125.0 | 19.89 | 2.0 | ✔ |
| P1-REV-02 | Perno con hombro Ø10: flexión + corte (bucket R12, corta) | F/2 = 704 N a 5.5 mm | 44.54 | metal | 205.0 | 4.6 | 2.0 | ✔ |
| P1-REV-02 | Perno con hombro Ø10: flexión (fatiga) | F/2 = 349 N | 19.56 | metal | 180.0 | 9.2 | 2.0 | ✔ |
| P1-REV-03 | Buje POM Ø10/Ø14 × 8: presión (bucket R12, corta) | 704 N / (10 × 8) | 8.80 | metal | 20.0 | 2.27 | 2.0 | ✔ |
| P1-REV-03 | Buje POM: presión (reversa sizing, oscilación) | 349 N / (10 × 8) | 4.36 | metal | 10.0 | 2.29 | 2.0 | ✔ |
| P1-REV-04 | Perno del émbolo Ø12: flexión + corte (M_h con bucket R12) | F = 2817 N a 3.5 mm; 316 | 81.76 | metal | 205.0 | 2.51 | 2.0 | ✔ |
| P1-REV-04 | Perno del émbolo: flexión (reversa sizing, fatiga) | F = 1397 N | 28.82 | metal | 180.0 | 6.25 | 2.0 | ✔ |
| P1-REV-06 | Tornillo con hombro Ø8 de la varilla: flexión (palanca forzada) | F = 100 N × 125/46 = 272 N a 6 mm | 32.44 | metal | 205.0 | 6.32 | 2.0 | ✔ |
| P1-REV-09 | Soporte del Bowden 4 mm: placa de tope en voladizo | tiro 60 N [ESTIMADO] a 34 mm; sección 16 × 4 | 47.81 | metal | 125.0 | 2.61 | 2.0 | ✔ |
| P1-CTL-14 | Gatillo 6 mm: flexión por el apriete (100 N a 20 mm del pivote) | sección 10 × 6 | 20.00 | metal | 240.0 | 12.0 | 2.0 | ✔ |
| P1-REV-05 | Soporte del Mach5: placa lateral en voladizo (palanca forzada) | 272 N a 48 mm; 6 × 124 | 0.85 | metal | 125.0 | 147.35 | 2.0 | ✔ |
| P1-CTL-09 | Palanca del acelerador: flexión en el cubo (100 N en el pomo) | M = 100 N × 120 mm; barra 16 × 8 | 35.16 | metal | 240.0 | 6.83 | 2.0 | ✔ |
| P1-CTL-10 | Palanca del bucket: flexión en el escalón (100 N en el pomo) | M = 100 N × 125 mm; 16 × 8 | 36.62 | metal | 240.0 | 6.55 | 2.0 | ✔ |
| P1-CTL-11 | Eje Ø12: torsión (100 N en el pomo del acelerador) | T = 15 N·m | 76.57 | metal | 205.0 | 2.68 | 2.0 | ✔ |
| P1-CTL-11 | Pasador Ø4 A4 palanca–eje: doble corte | F = T/d = 1250 N | 86.14 | metal | 450.0 | 5.22 | 2.0 | ✔ |
| P1-CTL-12 | Perno de enclavamiento Ø6: corte (palanca forzada contra el enclavamiento) | F = 100 N × 125 / 22 = 568 N | 46.41 | metal | 205.0 | 4.42 | 2.0 | ✔ |
| P1-CTL-08 | Placa central: aplastamiento del perno de enclavamiento (6 mm) | 568 N / (6 × 6) | 15.78 | metal | 125.0 | 7.92 | 2.0 | ✔ |
| P1-CTL-08 | Placa central: flexión bajo el eje (100 N en el pomo) | M = 100 N × 190 mm; sección 6 × 56 | 6.06 | metal | 125.0 | 20.63 | 2.0 | ✔ |
| P1-CTL-02 | Tapa PETG 6 mm: mano apoyada 150 N [SUPUESTO] (corta) | franja 50 × 6 apoyada, luz 50: M = F·L/4 | 6.25 | short | 24.0 | 3.84 | 3.0 | ✔ |
| P1-CTL-03 | Cara PETG 10 mm: tirón del cordón 150 N [SUPUESTO] (corta, cruza capas) | franja 50 × 10 empotrada, luz 76: M = F·L/8; ÷ f_Z (cara inclinada 32°) | 4.28 | short | 24.0 | 5.61 | 3.0 | ✔ |
| P1-CTL-03 | Cara PETG 10 mm: golpe sobre la seta 200 N [SUPUESTO] (corta, cruza capas) | ídem | 5.70 | short | 24.0 | 4.21 | 3.0 | ✔ |
| P1-CTL-01 | Placa de refuerzo 6 mm: carga del pasamuros del M66 | placa circular empotrada R 60, carga 304 N en r 10 | 13.40 | metal | 125.0 | 9.33 | 2.0 | ✔ |
| P1-CTL-04 | Pasamuros M66: cuerpo Ø20/Ø9,6 a tracción + flexión | 304 N; momento por 20 mm de voladizo | 9.42 | metal | 205.0 | 21.77 | 2.0 | ✔ |
| P1-INT-01 | Techo plano entre costados, p = máx(p_cierre, p_golpe) | placa larga empotrada: σ = p·b²/(2t²), b = W_open = 158, t = 5.0 | 33.82 | metal | 125.0 | 3.7 | 2.0 | ✔ |
| P1-INT-01 | Costado plano más alto (en el labio), p = máx(p_cierre, p_golpe) | placa empotrada brida–techo: σ = p·h²/(2t²), h = 156 | 32.77 | metal | 125.0 | 3.81 | 2.0 | ✔ |
| P1-INT-01 | Fatiga de la soldadura del costado: Δp = p_ram + p_succión = 42 kPa, 1e+05 ciclos | Δσ = Δp·h²/(2t²) vs FAT 25 (IIW, m = 3) → 68 MPa | 20.41 | metal | 67.9 | 3.32 | 2.0 | ✔ |
| P1-INT-01 | Bulones M6 A4 brida ↔ placa (14): precarga + p·A_abertura + 3 g | σ = (F_v + Φ·F/n)/A_s, F = 4466 N, Φ = 0,25 | 202.97 | metal | 450.0 | 2.22 | 2.0 | ✔ |
| P1-INT-01 | Tubo junto a la brida de la bomba: momento del bucket (sin placa de espejo) | σ = M/(π r² t), M = F_bucket·358 | 3.13 | metal | 125.0 | 39.98 | 2.0 | ✔ |
| P1-INT-01 | Bulones M6 de la brida de la bomba: precarga + momento del bucket | σ = (F_v + Φ·4M/(n·r_bc))/A_s, Φ = 0,25 (VDI 2230) | 217.90 | metal | 450.0 | 2.07 | 2.0 | ✔ |
| P1-INT-01 | Tubo del eje en voladizo (sin contar el alma): caja del sello | σ = F·L/W, L = 74 | 2.35 | metal | 125.0 | 53.27 | 2.0 | ✔ |
| P1-INT-01 | Chimenea de inspección: presión de cierre (aro) | σ = p·r/t | 0.74 | metal | 125.0 | 168.6 | 2.0 | ✔ |
| P1-INT-02 | Paño lateral entre bulones del conducto y del ala: golpe de fondo | σ = p·b²/(2t²), b = 68 | 1.17 | metal | 125.0 | 106.56 | 2.0 | ✔ |
| P1-INT-02 | Tornillos M8 A4-70 del soporte (ISO 10642 desde abajo + tuerca): precarga + vuelco del empuje | σ = (F_v + Φ·F_t)/A_s, F_v = 7000 N, F_t = 451 N, Φ = 0,25 | 194.34 | metal | 450.0 | 2.32 | 2.0 | ✔ |
| P1-INT-02 | Asiento cónico de la cabeza M8 en el 5083 (aplastamiento) | σ_b = F/(π/4·(dk² − d²)) (proyección del cono) | 47.82 | metal | 125.0 | 2.61 | 2.0 | ✔ |
| P1-INT-02 | Arranque de la cabeza M8 a través de la placa (tapón de Ø dk sobre el cono) | τ = F/(π·dk·(t − h_cono)), t − h = 6.0 | 24.10 | metal | 72.2 | 2.99 | 2.0 | ✔ |
| P1-INT-02 | Bulones M6 del ala al casco (26): precarga + golpe de fondo + presión en la abertura | σ = (F_v + Φ·F/n)/A_s, F = 8768 N, Φ = 0,25 | 203.20 | metal | 450.0 | 2.21 | 2.0 | ✔ |
| P1-INT-02 | Aplastamiento del casco (Al 4 mm) por el empuje en los bulones del ala | σ_b = (T/n)/(d·t) | 1.23 | metal | 125.0 | 102.03 | 2.0 | ✔ |
| P1-INT-02 | Arranque de la cabeza avellanada M6 en el casco de 4 mm (corte del labio de 1,2 mm) | τ = (F/n)/(π·d_m·t_labio), d_m = 9 | 9.94 | metal | 72.2 | 7.26 | 2.0 | ✔ |
| P1-INT-03 | Barra con la rejilla tapada (bolsa) a la presión de cierre | viga simplemente apoyada L = 330, w = p·paso, W = 212 mm³ (sección perfilada) | 87.91 | metal | 205.0 | 2.33 | 2.0 | ✔ |
| P1-INT-03 | Barra: golpe de objeto 200 N en el centro | M = P·L/4 | 77.88 | metal | 205.0 | 2.63 | 2.0 | ✔ |
| P1-INT-03 | Apoyo de la barra contra la cuña de la placa (aplastamiento del Al) | σ_b = R/(b·9 mm) | 6.27 | metal | 125.0 | 19.93 | 2.0 | ✔ |
| P1-INT-04 | Tapa: succión/contrapresión de cierre (corta) | σ = 3(3+ν)p a²/(8t²), a = 58, t = 13.0 | 1.72 | short | 24.0 | 13.9 | 3.0 | ✔ |
| P1-INT-04 | Tapa: recuperación de presión a 30 km/h (sostenida) | ídem con p_ram | 0.63 | sust | 8.4 | 13.32 | 3.0 | ✔ |
| P1-INT-04 | Tapa: ciclo marcha ↔ punto fijo Δp = 42 kPa (olas/maniobras) | ídem con Δp | 1.07 | lcf | 3.6 | 3.35 | 3.0 | ✔ |
| P1-INT-04 | Tapa en la purga (r = 32, espesor neto 13.6): ciclo Δp (olas/maniobras) | σ_r = 3(3+ν)p(a² − r²)/(8t²) | 0.69 | lcf | 3.6 | 5.24 | 3.0 | ✔ |
| P1-INT-04 | Tapa: aplastamiento bajo arandela M6 Ø18 (sostenido) | σ = F/(π/4(18² − 6,4²)) | 0.30 | sust | 8.4 | 28.28 | 3.0 | ✔ |
| P1-DRV-01 | Agujero del pasador: par de corte del pasador (traba con piedra) | τ = T_corte/(πd³/16 − d_h·d²/6), T_corte 33.5 N·m, sección neta, K_t = 1 (dúctil, estático) | 25.07 | metal | 118.3 | 4.72 | 2.0 | ✔ |
| P1-DRV-01 | Agujero del pasador: fatiga en V máx. (T_top ± 10 %) | Goodman τ_a/τ_e + τ_m/τ_u, K_ts 2.0 (Peterson), S_e corrosión 180 MPa; σ_eq = τ_a·τ_u/τ_e + τ_m | 27.19 | metal | 297.1 | 10.93 | 2.0 | ✔ |
| P1-DRV-01 | Ranura DIN 471 de empuje: par de corte del pasador + Fa | von Mises √(σ² + 3τ²), τ = T_corte/(π·19³/16), σ = Fa/A_fondo, K_t = 1 (dúctil, estático) | 43.14 | metal | 205.0 | 4.75 | 2.0 | ✔ |
| P1-DRV-01 | Ranura DIN 471 de empuje: fatiga en V máx. | Goodman von Mises σ_a/S_e + σ_m/S_u; K_ts 3.0, K_t ax 4.0; empuje en V máx. ∝ T_top | 70.31 | metal | 515.0 | 7.32 | 2.0 | ✔ |
| P1-DRV-01 | Chaveta 6×6 del acople: aplastamiento a T_max | p = 2T/(d·(h − t1)·(l − b)), l = 22 mm, cubo de acero | 46.42 | metal | 100.0 | 2.15 | 2.0 | ✔ |
| P1-DRV-01 | Rosca M20×1 (KM4): Fa en reversa + par T_max | von Mises en el núcleo (d − 1,083·P), σ = Fa/A, τ = 16T/(π d3³) | 24.35 | metal | 205.0 | 8.42 | 2.0 | ✔ |
| P1-DRV-02 | Presión de diseño 0.20 MPa en la cámara mojada (espigón) | anillo de pared delgada σ = p·r/t (espigón, la sección más delgada) | 1.20 | metal | 205.0 | 170.83 | 2.0 | ✔ |
| P1-DRV-02 | Bulones 4 × M6 A4-70 al buje de la toma: presión + resorte del sello | σ = F/(4·A_s), F = p·π/4·Ø42² + 150 N (sin precarga) | 5.31 | metal | 450.0 | 84.71 | 2.0 | ✔ |
| P1-DRV-02 | Brida de 8 mm: flexión entre espigón y bulones | placa anular como viga por unidad de perímetro: σ = 6·F·e/(π·BC·t²) | 1.42 | metal | 205.0 | 144.76 | 2.0 | ✔ |
| P1-DRV-03 | Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa) | flexión en su plano σ = M/(t·L²/6), M = Fa/2 · 121 mm, L = 150 mm, ZAT soldada | 1.02 | metal | 115.0 | 112.35 | 2.0 | ✔ |
| P1-DRV-03 | Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico | σ = P·L/4/(b t²/6) + Fa·e/(t·b²/6)/2, L = 200, b = 31, e = 35 mm, ZAT | 16.11 | metal | 115.0 | 7.14 | 2.0 | ✔ |
| P1-DRV-03 | Espárragos 4 × ISO 10642 M8 A4-70: vuelco por Fa + corte (servicio) | F_t = Fa·h/Δx/2 + 3g/4, F_s = Fa/4; von Mises sobre A_s (carga de servicio; Δx = 120) | 15.40 | metal | 450.0 | 29.21 | 2.0 | ✔ |
| P1-DRV-03 | Tuerca ISO 4032 A4 sobre espárrago A4: precarga (15 N·m) + F_t | barrido de filetes τ = F/(π·d·m·0,6), m = 6.8, F = T/(K·d) + F_t (K 0.18) vs 0,58·R_p0,2 A4-70 | 106.03 | metal | 261.0 | 2.46 | 2.0 | ✔ |
| P1-DRV-03 | Avellanado de 90° en la placa base de Al (TOMA): precarga + F_t | aplastamiento p = F/A_cono (Ø16→Ø8,4, 90°) vs R_p0,2 5083-H111 125 MPa [ESTIMADO] | 52.79 | metal | 125.0 | 2.37 | 2.0 | ✔ |
| P1-DRV-03 | Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo | corte del resalte τ = Fa/(π·D·t_resalte), σ_eq = √3·τ | 2.99 | metal | 240.0 | 80.29 | 2.0 | ✔ |
| P1-DRV-06 | Tapa: empuje Fa hacia proa entre el aro exterior y los M5 | placa anular por unidad de perímetro σ = 6·Fa·e/(2π r_m t²) | 3.51 | metal | 240.0 | 68.4 | 2.0 | ✔ |
| P1-DRV-06 | Bulones 4 × M5 A4-70 de la tapa: Fa | σ = Fa/(4·A_s) (sin precarga) | 13.46 | metal | 450.0 | 33.43 | 2.0 | ✔ |
| P1-MOT-02 | Placa: 3 g vertical del motor en voladizo (sin cartelas) | σ = W·e/(b t²/6), W = 3 g × 4.4 kg, e = 63 mm, b = 2·95 − Ø64 | 3.88 | metal | 115.0 | 29.6 | 2.0 | ✔ |
| P1-MOT-02 | Placa: par de reacción T_max (en su plano) + 3 g | corte en la sección por el agujero τ = (T/ (2·y_pie) + W/2)/(b·t) , σ_eq = √3·τ | 0.27 | metal | 115.0 | 423.85 | 2.0 | ✔ |
| P1-MOT-02 | Bulones 4 × M6 a la cara del motor: T_max + 3 g (corte) | τ = (T/(n·r) + W/n)/A_s, σ_eq = √3·τ (sin fricción por precarga) | 12.79 | metal | 450.0 | 35.18 | 2.0 | ✔ |
| P1-MOT-02 | Bulones 4 × M8 de los pies al casco: vuelco 3 g + par | F_t = W·e/Δx/2 + T/(2·y_pie) sobre A_s | 7.00 | metal | 450.0 | 64.28 | 2.0 | ✔ |
| P1-ELE-01 | Insertos M5 de la capota: apriete de las tiras de EPDM (sostenido) | arranque τ = F/(π·Ø·L) del inserto, F = máx(EPDM 160 N, 3 g arriba 66 N)/4; cruza capas (×f_Z) | 0.52 | sust | 8.4 | 16.02 | 3.0 | ✔ |
| P1-ELE-01 | Paredes del pedestal: 3 g vertical de ESC + capota (compresión sostenida) | σ = 3 g·m/A_paredes (pandeo despreciable: h/t = 19) | 0.03 | sust | 8.4 | 245.74 | 3.0 | ✔ |
| P1-ELE-01 | Orejas M6 al piso: 2 g lateral (golpe) del conjunto a la altura del CG | vuelco: F_t = m·2g·h_CG/(ancho)/2 sobre el anillo de la oreja (7 mm, cruza capas) | 0.16 | short | 24.0 | 153.03 | 3.0 | ✔ |
| P1-ELE-02 | Techo de la capota: reacción de las tiras de EPDM (sostenida) | voladizo desde la pared por unidad de largo σ = 6·q·b·(b/2 + c)/t² | 1.31 | sust | 8.4 | 6.39 | 3.0 | ✔ |
| P1-DRV eje 316 | Torsión máx. del controlador + fatiga (sizing) | 02_calculos.md §7 | — | metal | — | 4.0 | 2.0 | ✔ |
<!-- /AUTO:estructural -->

## 10. Sensibilidad — las 3 entradas que más mueven el resultado

<!-- AUTO:sizing_sens -->
| Entrada incierta | Rango | V máx. sostenida [km/h] (bajo / alto) | Margen en la joroba (bajo / alto) | ¿Planea en ambos extremos? |
|---|---|---|---|---|
| Potencia continua del motor ±25 % | 4.5e+03 – 7.5e+03 | 17.5 / 28.5 | 12 % / 12 % | sí |
| Masa del piloto 70–110 kg | 70 – 110 | 28.9 / 21.3 | 28 % / 1 % | **NO** |
| Resistencia de planeo ±10 % | 0.9 – 1.1 | 29.0 / 21.6 | 12 % / 12 % | sí |
| Rendimiento de bomba 0,65–0,78 | 0.65 – 0.78 | 21.7 / 28.1 | 2 % / 20 % | sí |
| Posición del piloto (LCG) 1,20–1,55 m | 1.2 – 1.55 | 22.3 / 26.7 | 1 % / 23 % | sí |
| Recuperación en la toma 0,55–0,85 | 0.55 – 0.85 | 23.4 / 28.0 | 9 % / 15 % | sí |
| Astilla muerta 4–14° | 4 – 14 | 26.5 / 23.3 | 15 % / 7 % | sí |
| Manga de planeo ±10 % | 0.54 – 0.66 | 23.7 / 26.6 | 9 % / 15 % | sí |
| R/Δ en la joroba ±25 % | 0.15 – 0.25 | 25.3 / 25.3 | 12 % / 4 % | sí |
| Masa del casco ±30 % | 26.6 – 49.4 | 25.3 / 25.3 | 12 % / 12 % | sí |
<!-- /AUTO:sizing_sens -->

## 11. Criterios de éxito de P1 (con números)

| Criterio | Valor | Cómo se mide |
|---|---|---|
| Bollard pull | ≥ <!--V:sizing.success.bollard_pull_min_N:.0f-->215<!--/V--> N | Dinamómetro en el cabo, T2 |
| Crucero con 2 personas | 6,0 km/h con P_bat ≤ <!--V:sizing.success.cruise_P_bat_max_W:.0f-->879<!--/V--> W | GPS + medidor de energía, T3/T4 |
| V máx con 2 personas | ≥ <!--V:sizing.success.vmax_min_kmh:.1f-->21.5<!--/V--> km/h | GPS, T3 |
| Autonomía | ≥ 2 h a 6 km/h con ≥ 20 % de reserva | Wh consumidos/h × capacidad, T4 |
| Estanqueidad | 0 g de agua en la caja ESC tras 30 min a 0,5 m | T1 |
| Térmico | carcasa motor ≤ 80 °C; piezas impresas ≤ 50 °C | IR, T2 |
| Corte de emergencia | < 1 s (10/10) por cordón y por seta | Cronómetro/osciloscopio, T0 |
