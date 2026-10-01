# 02 — Dimensionamiento (sizing.py)

Todo sale de [`sizing.py`](sizing.py) + [`p1calc/`](p1calc/) leyendo `inputs.yaml`. Las tablas
entre marcadores `AUTO` las regenera `docgen.py` desde `resultados/sizing.json`; los números
de la prosa usan marcadores `<!--V:…-->`. Etiquetas: [VERIFICADO: fuente] · [CALCULADO] ·
[ESTIMADO: base] · [SUPUESTO].

## 1. Resumen de resultados

<!-- AUTO:sizing_main -->
| Magnitud | Valor | Etiqueta |
|---|---|---|
| Masa total de diseño | 293 kg | [CALCULADO] |
| Carga útil vs placa de capacidad | 248 / 160 kg (155 %) | [CALCULADO] |
| Calado / francobordo | 198 / 182 mm | [CALCULADO] |
| Velocidad de casco (Fr_L=0.40) | 6.36 km/h | [CALCULADO] |
| Fr_L a velocidad de crucero | 0.376 | [CALCULADO] |
| R crucero (nominal / diseño) | 135 / 156 N | [CALCULADO] |
| Empuje en el eje en crucero (diseño) | 195 N | [CALCULADO] |
| Hélice | MKP32 — modelo lineal calibrada a B-series, fuera del rango de la serie [ESTIMADO] | [SUPUESTO] |
| rpm hélice / J / η0 crucero (diseño) | 1491 rpm / 0.23 / 0.41 | [CALCULADO] |
| Potencia al eje crucero (diseño) | 698 W | [CALCULADO] |
| Potencia de batería crucero (nominal / diseño) | 736 / 879 W | [CALCULADO] |
| Rendimiento total batería→R·V (diseño) | 30 % | [CALCULADO] |
| Relación de correa | 20T : 48T = 2.40 | [CALCULADO] |
| Batería elegida | 2 × Power Queen 12V 100Ah en serie (BMS 100 A c/u) | [CALCULADO] |
| Energía requerida / usable | 2343 / 2304 Wh | [CALCULADO] |
| Autonomía a crucero (nominal / diseño) | 3.13 / 2.62 h | [CALCULADO] |
| V máx. (diseño, batería baja) | 6.4 km/h — limita: tensión (duty) | [CALCULADO] |
| V máx. (nominal, batería nominal) | 7.1 km/h | [CALCULADO] |
| Bollard pull avante (horizontal) | 287 N (29.3 kgf) — limita: corriente de motor | [CALCULADO] |
| Bollard pull marcha atrás | 91 N | [CALCULADO] |
| Corriente pico de batería / margen ESC | 47 A / 112 % | [CALCULADO] |
| Cable DC / fases | 10 mm² (1.2 %) / 10 mm² (2.1 %) | [CALCULADO] |
| Fusible principal | 60 A | [CALCULADO] |
| Pasador de corte | Ø2.0 mm AISI 316 → corta a 12.4 N·m | [CALCULADO] |
| Velocidad crítica del eje / rpm máx. | 5834 / 1713 rpm | [CALCULADO] |
| Largo de eje / tubo | 1357 / 1171 mm | [CALCULADO] |
<!-- /AUTO:sizing_main -->

Figuras: [R(v)](figuras/R_v.png) · [P(v)](figuras/P_v.png) · [autonomía(v)](figuras/autonomia_v.png) ·
[costo vs autonomía](figuras/costo_autonomia.png) · [velocidad–autonomía–costo](figuras/velocidad_autonomia_costo.png) ·
[sensibilidad](figuras/sensibilidad.png).

## 2. Resistencia al avance R(v)

**Hidrostática.** Volumen ∇ = m/ρ; calado T con costados abocinados: ∇ = L·C_B·(B_f·T + tanφ·T²)
(B_f ancho de fondo, tanφ = (B − B_f)/(2·puntal)). Masa de diseño <!--V:sizing.masses.total_kg:.0f-->293<!--/V--> kg →
calado <!--V:sizing.hydrostatics.draft_m:.3f-->0.198<!--/V--> m, francobordo <!--V:sizing.hydrostatics.freeboard_m:.3f-->0.182<!--/V--> m [CALCULADO].

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

**Bollard pull objetivo:** ≥ 0,85 × predicho; predicho <!--V:sizing.bollard_fwd.T_horiz:.0f-->287<!--/V--> N horizontales
(<!--V:sizing.bollard_fwd.limiter:-->corriente de motor<!--/V--> limita), igual a los fuerabordas eléctricos de 1 kW medidos (290–310 N,
0,28–0,29 N/W; research/R04 §B.2). Los "65 lb a 600 W" de algunos trolling exigen FM > 1:
físicamente imposibles y no se usan como meta. Marcha atrás: <!--V:sizing.bollard_rev.T_horiz:.0f-->91<!--/V--> N (límite de
corriente 50 % por firmware × rendimiento de hélice invertida 0,65 [ESTIMADO]).

### 3.1 Límite legal de velocidad (Sejladsreglement §4: ≤ 5 kn a < 300 m de la costa)

Como P1 opera siempre a < 300 m, la V máx útil es 9,26 km/h [VERIFICADO: research/R07 §1.2]; los
12 km/h del pedido no tienen uso legal y no se dimensiona para ellos. Pero con carga liviana
(1 persona) el modelo supera el límite, así que se fija un **tope de ERPM** en el VESC
(`l_max_erpm`, parámetro de VESC Tool [ESTIMADO: nombre de memoria técnica, confirmar en la
versión instalada]) calculado como las rpm a 5 kn en el caso más rápido (liviano, banda baja,
batería llena). Con 2 personas el bote no llega a 5 kn en ninguna banda (8,7 km/h en la banda baja),
así que sacar el tope con 2 a bordo es legal y recupera ~0,5 km/h; por defecto queda puesto.

<!-- AUTO:legal_speed -->
| Magnitud | Valor | Etiqueta |
|---|---|---|
| Límite legal a < 300 m de la costa | 9.26 km/h (5 kn) | [VERIFICADO: research/R07 §1.2] |
| V máx con carga liviana (161 kg), batería llena, banda baja | 9.5 km/h | [CALCULADO] |
| ¿Cumple sin limitador? | **no → tope de ERPM 'modo costa'** | [CALCULADO] |
| Tope de rpm del motor / ERPM (VESC `l_max_erpm`) | 4309 rpm / 30164 ERPM | [CALCULADO] |
| V máx a plena carga con el tope (banda nominal) | 7.1 km/h | [CALCULADO] |
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
| Hélice | Batería | Poleas | P_bat crucero diseño [W] | E req/nom [Wh] | Autonomía diseño [h] | V máx nom [km/h] | Bollard [N] | Costo hélice+bat [€] | No cumple |
|---|---|---|---|---|---|---|---|---|---|
| MKP32 | LFP12_100x2 | 20:48 | 879 | 2343/2560 | 2.62 | 7.1 | 287 | 643 | vmax |
| MKP32 | LFP12_100x2_LT | 20:48 | 872 | 2325/2560 | 2.64 | 7.1 | 287 | 688 | vmax |
| TOH74x6 | LFP24_50 | 16:40 | 932 | 2485/1280 | 1.24 | 6.5 | 206 | 473 | energy, vmax, prop_seat |
| EO10x8 | LFP24_50 | 20:72 | 774 | 2065/1280 | 1.49 | 6.8 | 247 | 473 | energy, vmax, purchasable |
| MKP32 | LFP24_50 | 16:40 | 831 | 2216/1280 | 1.39 | 6.7 | 261 | 478 | energy, vmax |
| TOH74x6 | LFP12_50x2 | 16:40 | 936 | 2496/1280 | 1.23 | 6.5 | 206 | 480 | energy, vmax, prop_seat |
| EO10x8 | LFP12_50x2 | 20:72 | 778 | 2074/1280 | 1.48 | 6.8 | 247 | 480 | energy, vmax, purchasable |
| MKP32 | LFP12_50x2 | 16:40 | 834 | 2225/1280 | 1.38 | 6.7 | 261 | 485 | energy, vmax |
| TOH74x6 | LFP36_50 | 14:48 | 926 | 2469/1920 | 1.87 | 7.3 | 278 | 593 | energy, vmax, prop_seat |
| EO10x8 | LFP36_50 | 14:72 | 763 | 2034/1920 | 2.27 | 7.7 | 336 | 593 | energy, vmax, purchasable |
| MKP32 | LFP36_50 | 14:48 | 826 | 2204/1920 | 2.09 | 7.5 | 354 | 598 | energy, vmax, prop_seat |
| TOH74x6 | LFP12_100x2 | 16:40 | 984 | 2623/2560 | 2.34 | 6.7 | 265 | 638 | energy, vmax, prop_seat |
| EO10x8 | LFP12_100x2 | 20:72 | 816 | 2176/2560 | 2.82 | 7.5 | 280 | 638 | vmax, purchasable |
| TOH74x6 | LFP12_100x2_LT | 16:40 | 976 | 2602/2560 | 2.36 | 6.7 | 265 | 683 | energy, vmax, prop_seat |
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
<!--V:sizing.esc.I_bat_peak_a:.0f-->47<!--/V--> A → margen del ESC (100 A) <!--V:sizing.esc.margin_frac:.0%-->112%<!--/V--> (requisito ≥ 30 %).
Correa HTD-5M 15 mm: tirón efectivo a corriente máxima <!--V:sizing.mech.belt.Fe_N:.0f-->189<!--/V--> N vs admisible 400 N
[ESTIMADO: catálogo, a verificar] → FS <!--V:sizing.mech.belt.fs_belt:.2f-->2.11<!--/V-->; correa
<!--V:sizing.mech.belt.length_std_mm:.0f-->425<!--/V--> mm.

### 5.1 Tiempo sostenible a velocidad alta ("por ratos")

<!-- AUTO:sizing_sustain -->
| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1285 | 50 | 108 | 14 | 14 |
| 7 | design | no (tensión (duty)) | 1541 | 60 | 90 | 9 | 0 |
| 8 | nominal | no (tensión (duty), corriente de motor) | 2012 | 79 | 69 | 6 | 0 |
| 8 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2420 | 95 | 57 | 4 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2865 | 112 | 48 | 4 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3451 | 135 | 40 | 3 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3783 | 148 | 37 | 2 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4559 | 178 | 30 | 2 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4715 | 184 | 29 | 2 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5682 | 222 | 24 | 1 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5636 | 220 | 25 | 1 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 6787 | 265 | 20 | 1 | 0 |
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
| Requisito de compra (crucero → caja ≤ 50 °C) |  |  | **≤ 0.61** |
| Con ese disipador, a V máx sostenida: 56 °C estacionario (límite ESC 80 °C) |  |  | ∞ |
<!-- /AUTO:thermal_esc -->

## 6. Batería, cables y protecciones

E_req = P_bat,crucero × 2 h × 1,2 / DoD útil (0,90). Requerida <!--V:sizing.battery.E_required_wh:.0f-->2343<!--/V--> Wh;
elegida: <!--V:sizing.selection.battery_desc:-->2 × Power Queen 12V 100Ah en serie (BMS 100 A c/u)<!--/V--> (<!--V:sizing.battery.E_usable_wh:.0f-->2304<!--/V--> Wh usables,
<!--V:sizing.battery.mass_kg:.1f-->22.0<!--/V--> kg, tasa pico <!--V:sizing.battery.C_rate_peak:.2f-->0.47<!--/V--> C).
Química: LiFePO4 (sin runaway en ensayo ARC; research/R06), fija en caja ventilada, alta y
centrada (trimado), nunca en el espejo. Cable DC <!--V:sizing.cables.dc.section_mm2:d-->10<!--/V--> mm²
(caída <!--V:sizing.cables.dc.drop_frac:.1%-->1.2%<!--/V-->), fases <!--V:sizing.cables.phase.section_mm2:d-->10<!--/V--> mm²
(caída <!--V:sizing.cables.phase.drop_frac:.1%-->2.1%<!--/V-->); fusible <!--V:sizing.fuse.rating_a:d-->60<!--/V--> A a ≤ 178 mm del borne
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
| P1-MNT-01 | Apriete (sostenido) | M = F_apriete·brazo = 2083 N·36 mm; Z = b·t²/6 (esquina de la C) | 2.60 | sust | 8.4 | 3.23 | 3.0 | ✔ |
| P1-MNT-01 | LC5 impacto + apriete (corta) | (M_apriete + H_imp·h) / Z; H_imp = 0.5·F_pico = 501 N | 5.04 | short | 24.0 | 4.76 | 3.0 | ✔ |
| P1-MNT-01 | LC1 empuje avante (corta) | (M_apriete + T·h)/Z | 4.00 | short | 24.0 | 6.0 | 3.0 | ✔ |
| P1-MNT-01 | Apriete: apoyo de la placa de reparto (sostenido) | p = F_tornillo / (40×40 mm) | 0.65 | sust | 8.4 | 12.89 | 3.0 | ✔ |
| P1-MNT-02 | Apriete (sostenido, compresión) | p = F / (π·D²/4) | 0.83 | sust | 8.4 | 10.12 | 3.0 | ✔ |
| P1-MNT-03 | LC5 vuelco (corta) | M_vuelco=50.9 N·m → F_perno=605 N; flexión local brazo 20 mm, b=40, t=20.0 | 4.54 | short | 24.0 | 5.28 | 3.0 | ✔ |
| P1-MNT-04 | Tuerca cautiva M6 en mejilla: arranque por corte (corta) | τ = F_perno/(2·t·h), h = 18 mm; admisible 0.5·S | 1.20 | metal | 12.0 | 9.98 | 3.0 | ✔ |
| P1-MNT-04 | LC5 en el plano (corta) | M = (H/2)·h; Z = t·L²/6 (L=64) | 2.66 | short | 24.0 | 9.01 | 3.0 | ✔ |
| P1-MNT-04 | Golpe lateral 200 N (corta) | M=(F/2)·h; Z = L·t²/6 (fuera del plano) | 4.86 | short | 24.0 | 4.94 | 3.0 | ✔ |
| P1-MNT-04 | Apoyo del perno Ø12 (corta) | p = (H/2)/(d·t) | 1.49 | short | 24.0 | 16.08 | 3.0 | ✔ |
| P1-MNT-05 | LC5 dinámico (corta) | p = 6M/(d·L²), M = 0.19·F·L = 215 N·m | 1.74 | short | 24.0 | 13.76 | 3.0 | ✔ |
| P1-MNT-05 | LC5 cola trabada (corta) | p = 6M/(d·L²), M = F_fus·L = 338 N·m | 2.75 | short | 24.0 | 8.73 | 3.0 | ✔ |
| P1-MNT-05/06 | Tope de marcha (sostenido) | F = (T·e + M_grav)/r = 406 N sobre tope Ø25 | 0.83 | sust | 8.4 | 10.14 | 3.0 | ✔ |
| P1-MNT-05/06 | LC6 golpe de ola 3 g en el tope (corta) | F = 1053 N | 2.15 | short | 24.0 | 11.17 | 3.0 | ✔ |
| P1-MNT-05/06 | LC6 ola ±1 g (fatiga ~1e6 ciclos) | F_a = 351 N | 0.71 | lcf | 3.6 | 5.03 | 3.0 | ✔ |
| P1-MNT-05 | LC1 apoyo del buje del pivote (corta) | p = F/(d·w), POM Ø20 × ancho | 0.34 | short | 24.0 | 70.72 | 3.0 | ✔ |
| P1-MNT-05 | LC6 paso de pala ±20 % T lateral (fatiga 1e7–1e8) | p_a = 6M/(d·L²) | 0.36 | fat | 1.4 | 4.04 | 3.0 | ✔ |
| P1-MNT-05 | LC1 tuercas cautivas de la placa motriz: arranque por corte (corta) | τ = (T/4)/(2·12·18) (bolsillo a 18 mm de la cara) | 0.18 | metal | 12.0 | 65.38 | 3.0 | ✔ |
| P1-MNT-05 | LC6 tuercas de placa motriz ±amp·T (fatiga 1e7–1e8) | τ_a = (amp·T_cr/4)/(2·12·18) | 0.02 | metal | 0.7 | 31.92 | 3.0 | ✔ |
| P1-MNT-05 | LC2 marcha atrás: cartucho contra el fondo del rebaje (corta) | p = T_rev/A_anillo | 0.10 | short | 24.0 | 240.24 | 3.0 | ✔ |
| P1-MNT-06 | LC5 cola trabada: apoyo extremo (corta) | p = F_ext/(d·25), F_ext = 3111 N | 3.11 | short | 24.0 | 7.71 | 3.0 | ✔ |
| P1-MNT-06 | LC5: arandela Ø24 de perno pasante (corta) | p = (F_ext/2)/(π(24²−6.4²)/4) | 3.70 | short | 24.0 | 6.48 | 3.0 | ✔ |
| P1-HSG-01 placa Al | LC1 empuje bollard | franja cartucho→pernos: M = (T/2)·11 mm, Z = 30·t²/6 (t=6) | 9.68 | metal | 240.0 | 24.8 | 2.0 | ✔ |
| P1-HSG-01 placa Al | LC6 ±20 % empuje (fatiga) | σ_a = (amp·T/2)·11/Z | 1.19 | metal | 60.0 | 50.44 | 2.0 | ✔ |
| P1-HSG-01 placa Al | LC3 torque de rotor trabado en colisos M4 | p = Q/(4·r·d·t) | 2.09 | metal | 240.0 | 114.61 | 2.0 | ✔ |
| P1-DRV-08 cartucho Al | LC1 empuje en el labio (corte) | τ = T/(π·Ø21·espesor labio) | 0.48 | metal | 138.5 | 288.42 | 2.0 | ✔ |
| P1-HSG-02 | LC3 tracción en el plano (corta) | σ = R_B/(24·t) | 0.95 | short | 24.0 | 25.24 | 3.0 | ✔ |
| P1-HSG-02 | LC4 tirón de correa (corta) | σ = R_B,pin/(24·t) | 1.62 | short | 24.0 | 14.77 | 3.0 | ✔ |
| P1-HSG-04 | LC7 apoyo del tubo en la abrazadera (corta) | M = F·L = 82 N·m → F = M/s = 1500 N; p = F/(d·22) | 2.27 | short | 24.0 | 10.55 | 3.0 | ✔ |
| P1-HSG-04 | LC7 tracción de la abrazadera (2 M6, sección 2×8×22) (corta) | σ = F/(2·8·22) | 4.26 | short | 24.0 | 5.62 | 3.0 | ✔ |
| P1-HSG-07 placa Al | LC7 torsión de la placa | τ = M/(β·b·t²) | 36.95 | metal | 138.5 | 3.75 | 2.0 | ✔ |
| P1-MNT-05 | LC7 apoyo de la placa de caña sobre la cuna (corta) | p = (M/0.06 m)/(20·76) = 1375 N / 1520 mm² | 0.91 | short | 24.0 | 26.5 | 3.0 | ✔ |
| P1-STR-01 | LC5 fusible: apoyo del tubo (corta) | p = 6M/(d·L²), L = 45 mm | 2.45 | short | 24.0 | 9.77 | 3.0 | ✔ |
| P1-STR-01 | LC5 fusible: pernos del patín (corta) | p = (F/2)/(6·2·14) | 0.89 | short | 24.0 | 26.85 | 3.0 | ✔ |
| P1-PRP-02 | LC5 fusible | σ = F_fus·h/Z en la cintura (h=110 mm) | 35.25 | metal | 35.2 | 1.0 | 3.0 | ✔ (justif.) |
| P1-PRP-02 | Arrastre a 9 km/h (sostenido) | F = ½ρV²·Cd·A = 6.4 N | 0.75 | sust | 8.4 | 11.19 | 3.0 | ✔ |
| P1-PRP-02 | Fuerza lateral en giro (corta) | F = ½ρV²·C_L·A = 44 N, brazo 70 mm, eje débil | 5.96 | short | 24.0 | 4.02 | 3.0 | ✔ |
| P1-PRP-01 | Golpe radial 150 N en el anillo (corta) | M = F·L/8 (arco entre uniones) | 1.65 | short | 24.0 | 14.57 | 3.0 | ✔ |
| P1-ELE-01 | Compresión del O-ring en insertos M4 (sostenido) | F_total = 1764 N / 8 insertos vs 1 kN arranque [ESTIMADO] | 1.85 | sust | 8.4 | 4.54 | 3.0 | ✔ |
| P1-SAF-01 | Tirón del cordón 100 N (corta) | placa 7 mm en voladizo 20 mm | 6.80 | short | 24.0 | 3.52 | 3.0 | ✔ |
| P1-STR-02 tubo Al | LC5 cola trabada (fusible) | σ = F_fus·L/Z = 338 N·m / 3003 mm³ | 112.70 | metal | 240.0 | 2.13 | 2.0 | ✔ |
| P1-STR-02 tubo Al | LC5 dinámico | σ = 0.19·F·L/Z | 71.52 | metal | 240.0 | 3.36 | 2.0 | ✔ |
| P1-HSG-06 caña Al | LC7 manipulación | σ = M/Z (Ø30×3) | 52.72 | metal | 240.0 | 4.55 | 2.0 | ✔ |
| P1-MNT-08 perno 316 | LC1+LC5 corte doble | τ = (F/2)/A | 2.28 | metal | 118.3 | 51.93 | 2.0 | ✔ |
| P1-DRV-01 eje 316 | LC3/LC4 torsión+flexión (sizing) | ver 02_calculos.md §7 | — | metal | — | 2.4 | 2.0 | ✔ |
<!-- /AUTO:estructural -->

## 10. Sensibilidad — las 3 entradas que más mueven el resultado

<!-- AUTO:sizing_sens -->
| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | Variación P | 
|---|---|---|---|---|
| Coef. de olas c_w (calibración) | ±30 % | 708 / 1061 | 6.8 / 6.1 | 40 % |
| Pérdida por protector (0–25 %) | 0–0.25 | 768 / 1113 | 6.6 / 6.1 | 39 % |
| Masa por persona | ±20 % | 743 / 1022 | 6.7 / 6.2 | 32 % |
| Eslora de flotación | ±10 % | 1027 / 767 | 6.2 / 6.6 | 30 % |
| Rendimiento de hélice (modelo) | ±10 % | 983 / 795 | 6.4 / 6.5 | 21 % |
| Masa del casco | ±30 % | 832 / 926 | 6.5 / 6.3 | 11 % |
| Ancho de espejo sumergido | ±20 % | 807 / 899 | 6.6 / 6.4 | 10 % |
| Ángulo de eje | ±20 % | 853 / 913 | 6.4 / 6.4 | 7 % |
| Resistencia del motor | ±30 % | 853 / 904 | 6.6 / 6.3 | 6 % |
<!-- /AUTO:sizing_sens -->

## 11. Criterios de éxito de P1 (con números)

| Criterio | Valor | Cómo se mide |
|---|---|---|
| Bollard pull | ≥ <!--V:sizing.success.bollard_pull_min_N:.0f-->244<!--/V--> N | Dinamómetro en el cabo, T2 |
| Crucero con 2 personas | 6,0 km/h con P_bat ≤ <!--V:sizing.success.cruise_P_bat_max_W:.0f-->879<!--/V--> W | GPS + medidor de energía, T3/T4 |
| V máx con 2 personas | ≥ <!--V:sizing.success.vmax_min_kmh:.1f-->6.0<!--/V--> km/h | GPS, T3 |
| Autonomía | ≥ 2 h a 6 km/h con ≥ 20 % de reserva | Wh consumidos/h × capacidad, T4 |
| Estanqueidad | 0 g de agua en la caja ESC tras 30 min a 0,5 m | T1 |
| Térmico | carcasa motor ≤ 80 °C; piezas impresas ≤ 50 °C | IR, T2 |
| Corte de emergencia | < 1 s (10/10) por cordón y por seta | Cronómetro/osciloscopio, T0 |
