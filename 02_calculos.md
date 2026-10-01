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
| Hélice | EO10x8 — modelo lineal aproximada [ESTIMADO] | [SUPUESTO] |
| rpm hélice / J / η0 crucero (diseño) | 976 rpm / 0.36 / 0.46 | [CALCULADO] |
| Potencia al eje crucero (diseño) | 628 W | [CALCULADO] |
| Potencia de batería crucero (nominal / diseño) | 643 / 774 W | [CALCULADO] |
| Rendimiento total batería→R·V (diseño) | 34 % | [CALCULADO] |
| Relación de correa | 16T : 48T = 3.00 | [CALCULADO] |
| Batería elegida | 2 × LiFePO4 12.8 V 100 Ah en serie (BMS 100 A c/u) | [CALCULADO] |
| Energía requerida / usable | 2064 / 2304 Wh | [CALCULADO] |
| Autonomía a crucero (nominal / diseño) | 3.58 / 2.98 h | [CALCULADO] |
| V máx. (diseño, batería baja) | 7.1 km/h — limita: tensión (duty) | [CALCULADO] |
| V máx. (nominal, batería nominal) | 7.7 km/h | [CALCULADO] |
| Bollard pull avante (horizontal) | 297 N (30.3 kgf) — limita: corriente de motor | [CALCULADO] |
| Bollard pull marcha atrás | 94 N | [CALCULADO] |
| Corriente pico de batería / margen ESC | 66 A / 51 % | [CALCULADO] |
| Cable DC / fases | 16 mm² (1.2 %) / 10 mm² (2.7 %) | [CALCULADO] |
| Fusible principal | 100 A | [CALCULADO] |
| Pasador de corte | Ø3.0 mm Al6061-T6 → corta a 23.4 N·m | [CALCULADO] |
| Velocidad crítica del eje / rpm máx. | 5763 / 1216 rpm | [CALCULADO] |
| Largo de eje / tubo | 1352 / 1178 mm | [CALCULADO] |
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
| 2 | 0.13 | 10 | 11 | 19 | 22 | 279 | 121.30 | 106.02 | 11 |
| 3 | 0.19 | 24 | 27 | 57 | 67 | 430 | 40.32 | 34.40 | 22 |
| 4 | 0.25 | 48 | 55 | 146 | 173 | 598 | 15.82 | 13.32 | 43 |
| 5 | 0.31 | 84 | 97 | 325 | 390 | 782 | 7.08 | 5.91 | 78 |
| 6 | 0.38 | 135 | 156 | 643 | 774 | 976 | 3.58 | 2.98 | 129 |
| 7 | 0.44 | 198 | 228 | 1126 | 1361 | 1170 | 2.05 | 1.69 | 194 |
| 8 | 0.50 | 267 | 307 | 1763 | 2135 ✗ | 1352 | 1.31 | 1.08 | 267 |
| 9 | 0.56 | 335 | 385 | 2504 | 3038 ✗ | 1517 | 0.92 | 0.76 | 338 |
| 10 | 0.63 | 398 | 458 | 3293 | 3997 ✗ | 1662 | 0.70 | 0.58 | 400 |
| 11 | 0.69 | 455 | 523 | 4084 | 4957 ✗ | 1790 | 0.56 | 0.46 | 451 |
| 12 | 0.75 | 505 | 580 | 4854 | 5889 ✗ | 1903 | 0.47 | 0.39 | 491 |
| 13 | 0.82 | 548 | 630 | 5592 | 6781 ✗ | 2005 | 0.41 | 0.34 | 522 |
<!-- /AUTO:sizing_sweep -->

## 3. Empuje requerido y márgenes

Empuje en el eje: T_eje = R / [(1 − t)·cosθ·(1 − pérdida_protector)], con t = 0,02 (hélice
~1 m detrás del espejo), θ = 25°, pérdida del aro protector 6 % [ESTIMADO: aro corto no
perfilado 3–8 %, research/R03]. Avance: V_a = V(1 − w)·cosθ, w = 0,02.

Márgenes de diseño (condición adversa): viento de proa 6 m/s + olas cortas (+25 % de R
hidrodinámica) + corriente 0,5 m/s. En esa condición, la velocidad alcanzable es
<!--V:sizing.adverse.vmax_headwind_waves_kmh:.1f-->6.2<!--/V--> km/h y la velocidad sobre el fondo contra la corriente
<!--V:sizing.adverse.sog_against_current_kmh:.1f-->4.4<!--/V--> km/h (criterio ≥ 3 km/h) [CALCULADO].

**Bollard pull objetivo:** ≥ 0,85 × predicho; predicho <!--V:sizing.bollard_fwd.T_horiz:.0f-->297<!--/V--> N horizontales
(<!--V:sizing.bollard_fwd.limiter:-->corriente de motor<!--/V--> limita), igual a los fuerabordas eléctricos de 1 kW medidos (290–310 N,
0,28–0,29 N/W; research/R04 §B.2). Los "65 lb a 600 W" de algunos trolling exigen FM > 1:
físicamente imposibles y no se usan como meta. Marcha atrás: <!--V:sizing.bollard_rev.T_horiz:.0f-->94<!--/V--> N (límite de
corriente 50 % por firmware × rendimiento de hélice invertida 0,65 [ESTIMADO]).

## 4. Hélice

### 4.1 Selección
Optimizador (sizing.py → `optimize`): recorre hélices × baterías × relaciones de poleas
HTD-5M y elige el **mínimo costo** que cumple las restricciones **duras** (energía 2 h + 20 %
en la banda de diseño, corriente BMS/ESC, margen ESC ≥ 30 %, tensión ≤ 48 V, cavitación de
Keller, calado de punta ≤ 380 mm); dentro de +10 % de costo desempata por V máx (restricción
blanda, 8 km/h) y autonomía.

<!-- AUTO:optimization -->
| Hélice | Batería | Poleas | P_bat crucero diseño [W] | E req/nom [Wh] | Autonomía diseño [h] | V máx nom [km/h] | Bollard [N] | Costo hélice+bat [€] | No cumple |
|---|---|---|---|---|---|---|---|---|---|
| WW10x4 | LFP12_100x2 | 18:36 | 895 | 2386/2560 | 2.57 | 7.4 | 280 | 415 | vmax |
| OB78x6 | LFP12_100x2 | 18:36 | 926 | 2469/2560 | 2.49 | 7.3 | 259 | 425 | vmax |
| EO10x8 | LFP12_100x2 | 16:48 | 774 | 2064/2560 | 2.98 | 7.7 | 297 | 440 | vmax |
| WW10x4 | LFP24_100 | 18:36 | 891 | 2377/2560 | 2.58 | 7.4 | 280 | 595 | vmax |
| OB78x6 | LFP24_100 | 18:36 | 922 | 2458/2560 | 2.50 | 7.3 | 259 | 605 | vmax |
| EO10x8 | LFP24_100 | 16:48 | 771 | 2055/2560 | 2.99 | 7.7 | 297 | 620 | vmax |
| WW10x4 | LFP12_50x2 | 18:44 | 843 | 2248/1280 | 1.37 | 6.6 | 266 | 295 | energy, vmax |
| OB74x55 | LFP12_50x2 | 18:40 | 905 | 2414/1280 | 1.27 | 6.5 | 219 | 300 | energy, vmax |
| OB78x6 | LFP12_50x2 | 18:44 | 868 | 2315/1280 | 1.33 | 6.6 | 227 | 305 | energy, vmax |
| EO10x8 | LFP12_50x2 | 20:72 | 730 | 1945/1280 | 1.58 | 6.9 | 267 | 320 | energy, vmax |
| EO11x8 | LFP12_50x2 | 14:56 | 700 | 1866/1280 | 1.65 | 7.0 | 284 | 335 | energy, vmax, draft |
| WW10x4 | LFP24_50 | 18:36 | 858 | 2288/1280 | 1.34 | 7.5 | 280 | 365 | energy, vmax |
| OB74x55 | LFP24_50 | 22:40 | 923 | 2460/1280 | 1.25 | 7.3 | 252 | 370 | energy, vmax |
| OB78x6 | LFP24_50 | 18:36 | 885 | 2359/1280 | 1.30 | 7.4 | 259 | 375 | energy, vmax |
<!-- /AUTO:optimization -->

### 4.2 Modelo de hélice
KT(J), KQ(J) de la hélice concreta. Mientras no se verifique la tabla de Wageningen B-series
(Oosterveld & van Oossanen 1975; ver research/R09), se usa una aproximación lineal calibrada a
valores típicos B3 [ESTIMADO]: KT = KT0(1 − J/J_T0), KQ = KQ0(1 − J/J_Q0), KT0 = 0,38·P/D,
J_T0 = 1,05·P/D, J_Q0 = 1,15·P/D, KQ0 = KT0^1,5/(√(π/2)·2π·FOM_b) con FOM_b = 0,60. Contraste con
el disco actuador: η_i = 2/(1 + √(1 + C_T)). η0 de crucero = <!--V:sizing.cruise.design.prop_eta0:.2f-->0.46<!--/V--> a J = <!--V:sizing.cruise.design.prop_J:.2f-->0.36<!--/V--> y
<!--V:sizing.cruise.design.prop_n_rpm:.0f-->976<!--/V--> rpm (los eléctricos comerciales: 1 200–1 450 rpm a plena potencia).

### 4.3 Cavitación (Keller y Burrill)
Keller: AE/A0 mín = (1,3 + 0,3Z)·T/((p0 + ρgh − pv)·D²) + K, K = 0,2 [VERIFICADO: research/R09];
Burrill: σ0,7R = (p0 + ρgh − pv)/(½ρV_R²), τc = T/(½ρV_R²·A_P), A_P ≈ A_D(1,067 − 0,229·P/D);
límite τc ≈ 0,3·σ^0,6 [ESTIMADO: ajuste aproximado del diagrama de 2,5 % — a verificar].

<!-- AUTO:cavitation -->
| Condición | T [N] | n [rpm] | σ0.7R | τc | τc límite (Burrill aprox.) | AE/A0 mín Keller | AE/A0 |
|---|---|---|---|---|---|---|---|
| bollard | 328 | 960 | 2.51 | 0.362 | 0.521 | 0.31 | 0.50 |
| cruise | 195 | 976 | 2.36 | 0.202 | 0.502 | 0.27 | 0.50 |
| vmax | 298 | 1195 | 1.58 | 0.207 | 0.394 | 0.30 | 0.50 |
<!-- /AUTO:cavitation -->

### 4.4 ¿Hélice impresa? No.
Raíz de pala de una hélice de 10–12" a ~1 kW: M ≈ 10 N·m sobre Z ≈ 320 mm³ → σ ≈ 30 MPa.
Admisible PETG en fatiga (≥ 10⁷ ciclos, mojado): < 1,5 MPa (research/R05: f_fatiga ≈ 0,06).
FS ≈ 0,05 → **se compra** (research/R02 E1: hélice PETG fisurada tras una temporada a baja carga).

### 4.5 Efecto del protector
Aro corto no perfilado: −6 % de empuje en marcha, sin ganancia en bollard [ESTIMADO, research/R03].
Una tobera Kort 19A daría +20–30 % de bollard pero no entra impresa (Ø > 210 mm) sin
segmentarla con perfil exacto → P2.

## 5. Motor, ESC y correa

Modelo DC del BLDC: Kt = 1/KV_rad; I = Q/Kt + I0; V = ω/KV_rad + I·R; P_bat = V·I/η_ESC;
duty = V/V_bat ≤ 0,95. Motor 6374 190 KV [ESTIMADO: datos típicos de catálogo]. Relación de
poleas elegida <!--V:sizing.selection.z_motor:d-->16<!--/V-->T : <!--V:sizing.selection.z_shaft:d-->48<!--/V-->T. Corriente pico de batería
<!--V:sizing.esc.I_bat_peak_a:.0f-->66<!--/V--> A → margen del ESC (100 A) <!--V:sizing.esc.margin_frac:.0%-->51%<!--/V--> (requisito ≥ 30 %).
Correa HTD-5M 15 mm: tirón efectivo a corriente máxima <!--V:sizing.mech.belt.Fe_N:.0f-->276<!--/V--> N vs admisible 400 N
[ESTIMADO: catálogo, a verificar] → FS <!--V:sizing.mech.belt.fs_belt:.2f-->1.45<!--/V-->; correa
<!--V:sizing.mech.belt.length_std_mm:.0f-->415<!--/V--> mm.

### 5.1 Tiempo sostenible a velocidad alta ("por ratos")

<!-- AUTO:sizing_sustain -->
| v [km/h] | Banda | Factible | P_bat [W] | I_bat [A] | t energía [min] | t térmico [min] | Sostenible [min] |
|---|---|---|---|---|---|---|---|
| 7 | nominal | sí | 1126 | 44 | 123 | ∞ | 123 |
| 7 | design | sí | 1361 | 53 | 102 | ∞ | 102 |
| 8 | nominal | no (corriente de motor) | 1763 | 69 | 78 | 43 | 0 |
| 8 | design | no (corriente de motor, corriente de batería/ESC) | 2135 | 83 | 65 | 15 | 0 |
| 9 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 2504 | 98 | 55 | 11 | 0 |
| 9 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3038 | 119 | 46 | 7 | 0 |
| 10 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC) | 3293 | 129 | 42 | 6 | 0 |
| 10 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 3997 | 156 | 35 | 5 | 0 |
| 11 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4084 | 160 | 34 | 5 | 0 |
| 11 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4957 | 194 | 28 | 3 | 0 |
| 12 | nominal | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 4854 | 190 | 28 | 4 | 0 |
| 12 | design | no (tensión (duty), corriente de motor, corriente de batería/ESC, potencia del motor) | 5889 | 230 | 23 | 3 | 0 |
<!-- /AUTO:sizing_sustain -->

## 6. Batería, cables y protecciones

E_req = P_bat,crucero × 2 h × 1,2 / DoD útil (0,90). Requerida <!--V:sizing.battery.E_required_wh:.0f-->2064<!--/V--> Wh;
elegida: <!--V:sizing.selection.battery_desc:-->2 × LiFePO4 12.8 V 100 Ah en serie (BMS 100 A c/u)<!--/V--> (<!--V:sizing.battery.E_usable_wh:.0f-->2304<!--/V--> Wh usables,
<!--V:sizing.battery.mass_kg:.1f-->22.0<!--/V--> kg, tasa pico <!--V:sizing.battery.C_rate_peak:.2f-->0.66<!--/V--> C).
Química: LiFePO4 (sin runaway en ensayo ARC; research/R06), fija en caja ventilada, alta y
centrada (trimado), nunca en el espejo. Cable DC <!--V:sizing.cables.dc.section_mm2:d-->16<!--/V--> mm²
(caída <!--V:sizing.cables.dc.drop_frac:.1%-->1.2%<!--/V-->), fases <!--V:sizing.cables.phase.section_mm2:d-->10<!--/V--> mm²
(caída <!--V:sizing.cables.phase.drop_frac:.1%-->2.7%<!--/V-->); fusible <!--V:sizing.fuse.rating_a:d-->100<!--/V--> A a ≤ 178 mm del borne
(ABYC E-11; research/R06), que protege al cable.

## 7. Mecánica del tren

| Ítem | Resultado |
|---|---|
| Eje Ø16 316 — FS estático mín. | <!--V:sizing.mech.shaft.fs_static:.2f-->2.54<!--/V--> |
| Eje — FS fatiga (Goodman) | <!--V:sizing.mech.shaft.fs_fatigue_goodman:.2f-->4.02<!--/V--> |
| Velocidad crítica / rpm máx | <!--V:sizing.mech.shaft.n_crit_rpm:.0f-->5763<!--/V--> / <!--V:sizing.mech.shaft.n_max_rpm:.0f-->1216<!--/V--> rpm |
| Rodamiento A (6002 inox), L10 a máxima | <!--V:sizing.mech.bearing_max.L10_h:.0f-->2859<!--/V--> h |
| Pasador de corte | Ø<!--V:sizing.mech.shear_pin.d_std_mm:-->3.0<!--/V--> mm Al 6061 → <!--V:sizing.mech.shear_pin.Q_shear_Nm:.1f-->23.4<!--/V--> N·m |
| Torque de rotor trabado en el eje | <!--V:sizing.mech.Q_lock_shaft_Nm:.1f-->9.9<!--/V--> N·m |

## 8. Basculación (kick-up), impacto y retención en marcha atrás

Momento de gravedad de la unidad (cola pesada) <!--V:sizing.mech.kickup.M_gravity_Nm:.1f-->28.9<!--/V--> N·m; retén
<!--V:sizing.mech.kickup.M_detent_Nm:.0f-->15<!--/V--> N·m; empuje en reversa <!--V:sizing.mech.kickup.M_thrust_rev_Nm:.1f-->5.7<!--/V--> N·m →
FS de retención en reversa <!--V:sizing.mech.kickup.fs_reverse_hold:.1f-->7.7<!--/V-->. En avance, la cola bascula con
<!--V:sizing.mech.kickup.F_release_at_skeg_fwd_N:.0f-->95<!--/V--> N horizontales en el patín.
Impacto a 2,5 m/s: impulso J = I_p·v/r_c (I_p = <!--V:sizing.mech.inertia.I_pivot_kgm2:.2f-->2.98<!--/V--> kg·m²) en 10 ms
→ pico <!--V:sizing.mech.impact.F_peak_N:.0f-->1162<!--/V--> N (semiseno ×2). La hélice sale del agua a ~22° de basculación.

## 9. Estructural — FS por pieza y caso de carga

Propiedades degradadas (research/R05): S_corta = σ_XY·f_agua·f_temp·f_proceso; S_sost = ×f_creep;
S_fatiga = ×f_fatiga. Casos: LC1 empuje avante, LC2 marcha atrás, LC3 rotor trabado, LC4 golpe
de hélice (hasta el corte del pasador), LC5 varada/impacto (pico dinámico y cola trabada con
fusible), LC6 ola y vibración (fatiga a paso de pala), LC7 manipulación.

<!-- AUTO:estructural -->
| Pieza | Caso de carga | Modelo | σ [MPa] | Admisible | S [MPa] | FS | Obj. | OK |
|---|---|---|---|---|---|---|---|---|
| P1-MNT-01 | Apriete (sostenido) | M = F_apriete·brazo = 2083 N·36 mm; Z = b·t²/6 (esquina de la C) | 2.60 | sust | 8.4 | 3.23 | 3.0 | ✔ |
| P1-MNT-01 | LC5 impacto + apriete (corta) | (M_apriete + H_imp·h) / Z; H_imp = 0.5·F_pico = 581 N | 5.43 | short | 24.0 | 4.41 | 3.0 | ✔ |
| P1-MNT-01 | LC1 empuje avante (corta) | (M_apriete + T·h)/Z | 4.04 | short | 24.0 | 5.93 | 3.0 | ✔ |
| P1-MNT-01 | Apriete: apoyo de la placa de reparto (sostenido) | p = F_tornillo / (40×40 mm) | 0.65 | sust | 8.4 | 12.89 | 3.0 | ✔ |
| P1-MNT-02 | Apriete (sostenido, compresión) | p = F / (π·D²/4) | 0.83 | sust | 8.4 | 10.12 | 3.0 | ✔ |
| P1-MNT-03 | LC5 vuelco (corta) | M_vuelco=59.0 N·m → F_perno=702 N; flexión local brazo 20 mm, b=40, t=20.0 | 5.26 | short | 24.0 | 4.55 | 3.0 | ✔ |
| P1-MNT-04 | Tuerca cautiva M6 en mejilla: arranque por corte (corta) | τ = F_perno/(2·t·h), h = 18 mm; admisible 0.5·S | 1.39 | metal | 12.0 | 8.6 | 3.0 | ✔ |
| P1-MNT-04 | LC5 en el plano (corta) | M = (H/2)·h; Z = t·L²/6 (L=64) | 3.08 | short | 24.0 | 7.77 | 3.0 | ✔ |
| P1-MNT-04 | Golpe lateral 200 N (corta) | M=(F/2)·h; Z = L·t²/6 (fuera del plano) | 4.86 | short | 24.0 | 4.94 | 3.0 | ✔ |
| P1-MNT-04 | Apoyo del perno Ø12 (corta) | p = (H/2)/(d·t) | 1.73 | short | 24.0 | 13.86 | 3.0 | ✔ |
| P1-MNT-05 | LC5 dinámico (corta) | p = 6M/(d·L²), M = 0.19·F·L = 249 N·m | 4.61 | short | 24.0 | 5.2 | 3.0 | ✔ |
| P1-MNT-05 | LC5 cola trabada (corta) | p = 6M/(d·L²), M = F_fus·L = 338 N·m | 6.27 | short | 24.0 | 3.82 | 3.0 | ✔ |
| P1-MNT-05/06 | Tope de marcha (sostenido) | F = (T·e + M_grav)/r = 440 N sobre tope Ø25 | 0.90 | sust | 8.4 | 9.36 | 3.0 | ✔ |
| P1-MNT-05/06 | LC6 golpe de ola 3 g en el tope (corta) | F = 1088 N | 2.22 | short | 24.0 | 10.81 | 3.0 | ✔ |
| P1-MNT-05/06 | LC6 ola ±1 g (fatiga ~1e6 ciclos) | F_a = 363 N | 0.74 | lcf | 3.6 | 4.87 | 3.0 | ✔ |
| P1-MNT-05 | LC1 apoyo del buje del pivote (corta) | p = F/(d·w), POM Ø20 × ancho | 0.36 | short | 24.0 | 66.42 | 3.0 | ✔ |
| P1-MNT-05 | LC6 paso de pala ±10 % T lateral (fatiga 1e7–1e8) | p_a = 6M/(d·L²) | 0.41 | fat | 1.4 | 3.54 | 3.0 | ✔ |
| P1-MNT-05 | LC1 tuercas cautivas de la placa motriz: arranque por corte (corta) | τ = (T/4)/(2·12·18) (bolsillo a 18 mm de la cara) | 0.19 | metal | 12.0 | 63.17 | 3.0 | ✔ |
| P1-MNT-05 | LC6 tuercas de placa motriz ±amp·T (fatiga 1e7–1e8) | τ_a = (amp·T_cr/4)/(2·12·18) | 0.01 | metal | 0.7 | 63.84 | 3.0 | ✔ |
| P1-MNT-05 | LC2 marcha atrás: cartucho contra el fondo del rebaje (corta) | p = T_rev/A_anillo | 0.12 | short | 24.0 | 201.61 | 3.0 | ✔ |
| P1-MNT-06 | LC5 cola trabada: apoyo extremo (corta) | p = F_ext/(d·25), F_ext = 4701 N | 4.70 | short | 24.0 | 5.1 | 3.0 | ✔ |
| P1-MNT-06 | LC5: arandela Ø24 de perno pasante (corta) | p = (F_ext/2)/(π(24²−6.4²)/4) | 5.59 | short | 24.0 | 4.29 | 3.0 | ✔ |
| P1-HSG-01 placa Al | LC1 empuje bollard | franja cartucho→pernos: M = (T/2)·11 mm, Z = 30·t²/6 (t=6) | 10.02 | metal | 240.0 | 23.96 | 2.0 | ✔ |
| P1-HSG-01 placa Al | LC6 ±10 % empuje (fatiga) | σ_a = (amp·T/2)·11/Z | 0.59 | metal | 60.0 | 100.89 | 2.0 | ✔ |
| P1-HSG-01 placa Al | LC3 torque de rotor trabado en colisos M4 | p = Q/(4·r·d·t) | 2.44 | metal | 240.0 | 98.23 | 2.0 | ✔ |
| P1-DRV-08 cartucho Al | LC1 empuje en el labio (corte) | τ = T/(π·Ø21·espesor labio) | 0.50 | metal | 138.5 | 278.68 | 2.0 | ✔ |
| P1-HSG-02 | LC3 tracción en el plano (corta) | σ = R_B/(24·t) | 1.39 | short | 24.0 | 17.21 | 3.0 | ✔ |
| P1-HSG-02 | LC4 tirón de correa (corta) | σ = R_B,pin/(24·t) | 3.09 | short | 24.0 | 7.76 | 3.0 | ✔ |
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
| P1-ELE-01 | Compresión del O-ring en insertos M4 (sostenido) | F_total = 1404 N / 8 insertos vs 1 kN arranque [ESTIMADO] | 1.47 | sust | 8.4 | 5.7 | 3.0 | ✔ |
| P1-SAF-01 | Tirón del cordón 100 N (corta) | placa 7 mm en voladizo 20 mm | 6.80 | short | 24.0 | 3.52 | 3.0 | ✔ |
| P1-STR-02 tubo Al | LC5 cola trabada (fusible) | σ = F_fus·L/Z = 338 N·m / 3003 mm³ | 112.70 | metal | 240.0 | 2.13 | 2.0 | ✔ |
| P1-STR-02 tubo Al | LC5 dinámico | σ = 0.19·F·L/Z | 82.93 | metal | 240.0 | 2.89 | 2.0 | ✔ |
| P1-HSG-06 caña Al | LC7 manipulación | σ = M/Z (Ø30×3) | 52.72 | metal | 240.0 | 4.55 | 2.0 | ✔ |
| P1-MNT-08 perno 316 | LC1+LC5 corte doble | τ = (F/2)/A | 2.57 | metal | 118.3 | 46.05 | 2.0 | ✔ |
| P1-DRV-01 eje 316 | LC3/LC4 torsión+flexión (sizing) | ver 02_calculos.md §7 | — | metal | — | 2.54 | 2.0 | ✔ |
<!-- /AUTO:estructural -->

## 10. Sensibilidad — las 3 entradas que más mueven el resultado

<!-- AUTO:sizing_sens -->
| Entrada | ±Δ | P_bat crucero (−/+) [W] | V máx (−/+) [km/h] | Variación P | 
|---|---|---|---|---|
| Coef. de olas c_w (calibración) | ±30 % | 617 / 942 | 7.6 / 6.8 | 42 % |
| Pérdida por protector (0–25 %) | 0–0.25 | 673 / 990 | 7.4 / 6.7 | 41 % |
| Masa por persona | ±20 % | 650 / 906 | 7.5 / 6.9 | 33 % |
| Eslora de flotación | ±10 % | 911 / 671 | 6.9 / 7.4 | 31 % |
| Rendimiento de hélice (modelo) | ±10 % | 864 / 701 | 6.9 / 7.2 | 21 % |
| Masa del casco | ±30 % | 731 / 818 | 7.2 / 7.0 | 11 % |
| Ancho de espejo sumergido | ±20 % | 708 / 793 | 7.3 / 7.1 | 11 % |
| Ángulo de eje | ±20 % | 747 / 811 | 7.2 / 7.1 | 8 % |
| Resistencia del motor | ±30 % | 755 / 793 | 7.2 / 7.0 | 5 % |
<!-- /AUTO:sizing_sens -->

## 11. Criterios de éxito de P1 (con números)

| Criterio | Valor | Cómo se mide |
|---|---|---|
| Bollard pull | ≥ <!--V:sizing.success.bollard_pull_min_N:.0f-->253<!--/V--> N | Dinamómetro en el cabo, T2 |
| Crucero con 2 personas | 6,0 km/h con P_bat ≤ <!--V:sizing.success.cruise_P_bat_max_W:.0f-->774<!--/V--> W | GPS + medidor de energía, T3/T4 |
| V máx con 2 personas | ≥ <!--V:sizing.success.vmax_min_kmh:.1f-->6.7<!--/V--> km/h | GPS, T3 |
| Autonomía | ≥ 2 h a 6 km/h con ≥ 20 % de reserva | Wh consumidos/h × capacidad, T4 |
| Estanqueidad | 0 g de agua en la caja ESC tras 30 min a 0,5 m | T1 |
| Térmico | carcasa motor ≤ 80 °C; piezas impresas ≤ 50 °C | IR, T2 |
| Corte de emergencia | < 1 s (10/10) por cordón y por seta | Cronómetro/osciloscopio, T0 |
