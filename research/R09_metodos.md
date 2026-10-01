# R09 — Métodos de cálculo para `sizing.py`: resistencia de casco plano, hélice B-series, cavitación, toberas, ejes y térmico

Fecha de consulta: 2026-10-01. Alcance: fórmulas exactas, rango de validez y fuente abierta de cada método que usa (o debería usar) `sizing.py` / `p1calc/`. Los números del proyecto (LWL 2,0 m, Δ ≈ 290 kg, hélice EO10x8, eje Ø16 AISI 316 a 25°) salen de `inputs.yaml` y `resultados/sizing.json`. Cada cálculo propio está hecho con las fórmulas citadas.

**Etiquetas:** [VERIFICADO: Sx] = leído en la fuente Sx de la tabla §8, abierta en esta sesión. [CALCULADO] = cuenta propia con fórmulas verificadas. [ESTIMADO: base]. [SUPUESTO].

**Limitación:** el cupo de WebSearch de la sesión estaba agotado desde el principio. Por eso todo se buscó con URLs directas: Wikipedia en texto crudo, el sitio de la ITTC, repositorios de GitHub y PDFs abiertos. Lo que no se pudo abrir figura como "buscar: …".

---

## 0. Resumen de métodos

| # | Método | Ecuación (resumen) | Validez | Estado |
|---|---|---|---|---|
| 1 | Fricción ITTC-1957 | C_F = 0,075/(log₁₀Re − 2)² | Línea de correlación modelo-buque | **VERIFICADO** S18 |
| 2 | Rugosidad ΔC_F y C_A de la ITTC-78 | ΔC_F = 0,044[(k_S/L)^⅓ − 10·Re^−⅓] + 0,000125; C_A = (5,68 − 0,6 log Re)·10⁻³ | Buques. **Da ΔC_F < 0 con L = 2 m** | **VERIFICADO** S20; no aplicable |
| 3 | Factor de forma, Holtrop 1984 | 1+k₁ = 0,93 + 0,487118·c₁₄·(B/L)^1,06806·… ; c₁₄ = 1 + 0,011·C_stern ("pram with gondola" = −25) | Buques; da ≈1,47 extrapolado | c₁₄ VERIFICADO S16; exponentes con OCR parcial |
| 4 | Factor de forma en HSMV (ITTC) | (1+k) = 1,0 en cascos con espejo | Lancha rápida con espejo | **VERIFICADO** S19 |
| 5 | Prohaska | C_TM/C_FM contra Fr⁴/C_FM, 0,1 < Fr < 0,2 | **No usar si el espejo va mojado** | **VERIFICADO** S18 |
| 6 | Espejo sumergido, Holtrop-Mennen 1982 | R_TR = ½ρV²A_T·c₆; c₆ = 0,2(1 − 0,2F_nT) si F_nT < 5, si no 0; F_nT = V/√(2gA_T/(B + B·C_WP)) | Buques con espejo; datos "escasos" (Holtrop 1984) | **VERIFICADO** S15, S16. Coincide con `hydro.py` |
| 7 | Olas, Holtrop 1982/84 | R_W = c₁c₂c₅∇ρg·exp{m₁Fn^d + m₂cos(λFn⁻²)} para Fn ≤ 0,40; interpolación para 0,40–0,55; fórmula de alta velocidad para Fn > 0,55 | Buques: Fn 0,15–0,45 y Cp 0,55–0,85 (fuente secundaria) | Estructura VERIFICADA S16; rango VERIFICADO S31 |
| 8 | Planeo, Savitsky 1964 | C_L0 = τ^1,1(0,0120λ^½ + 0,0055λ^2,5/C_V²) | 0,60 ≤ C_V ≤ 13; 2° ≤ τ ≤ 15°; λ ≤ 4 | ESTIMADO (memoria) |
| 9 | Regímenes de Savitsky 2003 | Desplazamiento SLR < 1,34; semidesplazamiento 1,34–3; planeo > 3. Curva R/Δ típica | Cualitativo | **VERIFICADO** S21 |
| 10 | Pre-planeo (Mercier-Savitsky 1973; Savitsky-Brown 1976) | Regresión de R/Δ en Fn∇ 1,0–2,0 | L/∇^⅓ ≳ 4 (memoria) | **No accesible** |
| 11 | Gerr, SLR máximo | SLR_máx = 8,26/DL^0,311, nunca menor que 1,34 | Desplazamiento y semidesplazamiento | **VERIFICADO** S22 |
| 12 | Gerr, potencia | SLR = 10,665/(LB/SHP)^⅓ | Ídem | ESTIMADO (memoria) |
| 13 | Wageningen B-series KT/KQ | KT, KQ = ΣC·J^s(P/D)^t(AE/A0)^u Z^v; 39 + 47 términos | 2 ≤ Z ≤ 7; 0,30 ≤ AE/A0 ≤ 1,05; 0,5 ≤ P/D ≤ 1,4; Rn = 2·10⁶ | **VERIFICADO** S13, S14 (85/86 idénticos al escaneo; 1 difiere en 4·10⁻⁵) |
| 14 | Corrección de Reynolds de la B-series | ΔKT, ΔKQ en función de (log Rn − 0,301) | Solo Rn > 2·10⁶ | **VERIFICADO** S14, S17 |
| 15 | Escala y rugosidad de la hélice (ITTC-78 según Holtrop) | KT_s = KT_B + ΔC_D·0,3(P/D)(cZ/D); KQ_s = KQ_B − ΔC_D·0,25(cZ/D) | k_p = 30 µm | **VERIFICADO** S15 |
| 16 | Disco actuador | P = √(T³/2ρA); η_i = 2/(1 + √(1 + C_T)) | Ideal | P VERIFICADO S2; η_i derivado |
| 17 | Rotor carenado ideal | P_i = T^1,5/√(4σ_dρA) | Ideal, punto fijo | **VERIFICADO** S24 |
| 18 | Burrill | σ₀,₇R = (p₀ + ρgh − p_v)/(½ρV²₀,₇R); τ_c = T/(½ρV²₀,₇R·A_P); curvas de 5 % y 10 % digitalizadas | Diseño en avance, no punto fijo | Curvas VERIFICADAS (código S17); A_P ESTIMADO |
| 19 | Keller | AE/A0 = (1,3 + 0,3Z)T/((p₀ + ρgh − p_v)D²) + K; K = 0,2 (1 eje), 0–0,1 (2 ejes) | Preliminar | **VERIFICADO** S15, S13, S30 |
| 20 | Velocidad crítica de eje | Viga biapoyada ω₁ = (π/L)²√(EI/μ); voladizo 3,516/L²·√(EI/μ); Rayleigh y Dunkerley | Euler-Bernoulli | Forma general VERIFICADA S7, S1 |
| 21 | Fatiga | Goodman σ_a/σ_w + σ_m/σ_u = 1/n; Soderberg con σ_y; Gerber parabólica | Vida infinita | **VERIFICADO** S3 |
| 22 | Pasador de corte | Q = τ_u·(πd_p²/4)·D_s (corte doble); τ_u ≈ 0,65·UTS (Al), 0,75·UTS (acero) | Orientativo | Relaciones VERIFICADAS S6, S8; ecuación derivada |
| 23 | Eje inclinado | T_horiz = T·cos ψ; T_vert = T·sin ψ; flujo cruzado V·sin ψ | Datos hasta 12° | **VERIFICADO** S23 |
| 24 | Pérdidas en MOSFET | P_cond = R_DS(on)·I_RMS²; P_sw = V_in·I_out·f_sw·Q_sw/I_g | Medio puente | **VERIFICADO** S28 |
| 25 | Cobre con la temperatura | R(T) = R₂₀[1 + 0,00393(T − 20)] (cobre recocido) | ±50 K | **VERIFICADO** S9 |

---

## 1. Resistencia de casco plano chico

### 1.1 Números adimensionales del bote (Δ = 290 kg, LWL = 2,0 m, b_chine = 0,95 m) [CALCULADO]

| v (km/h) | Fn_L | SLR (kn/√ft) | Fn∇ = V/√(g∇^⅓) | C_V = V/√(gb) | Re_L | Frh, h = 1,0 m | Frh, h = 0,6 m |
|---|---|---|---|---|---|---|---|
| 6 | 0,376 | 1,26 | 0,655 | 0,546 | 2,5·10⁶ | 0,53 | 0,69 |
| 8 | 0,502 | 1,69 | 0,874 | 0,728 | 3,3·10⁶ | 0,71 | 0,92 |
| 12 | 0,753 | 2,53 | 1,311 | 1,092 | 4,9·10⁶ | 1,06 | 1,37 |

- L/∇^⅓ = 3,02 y L/B_WL = 1,85. Están **fuera de toda serie sistemática** conocida, porque las series de lanchas arrancan cerca de L/∇^⅓ ≈ 4 [ESTIMADO: memoria técnica, no verificado].
- Con SLR = 1,26, la ola de proa mide ≈ 0,88·LWL, según la relación Lw/LWL = SLR²/1,80 (tabla: SLR 1,34 → 1,00; SLR 1,90 → 2,00) [VERIFICADO: S21].
- La carga útil del proyecto es 1,55 veces la placa de capacidad, con calado 0,196 m [CALCULADO: `resultados/sizing.json`]. Esa inmersión del espejo es la que agranda R_TR (§1.4).

### 1.2 Fricción: ITTC-1957 y correcciones de la ITTC-78

- C_F = 0,075/(log₁₀Re − 2)². Equivale a (1 + 0,1194)·0,067/(log₁₀Re − 2)², es decir, a la línea de Hughes más ~12 % de factor de forma incorporado. La ITTC aclara que "the ITTC-1957 correlation line already contains a form factor correction" [VERIFICADO: S18].
- Rugosidad (ITTC-78, rev. 2017): ΔC_F = 0,044[(k_S/L_WL)^⅓ − 10·Re^−⅓] + 0,000125, con k_S = 150 µm si no hay dato medido. Correlación: C_A = (5,68 − 0,6·log Re)·10⁻³ [VERIFICADO: S20].
- **Con L = 2 m estas fórmulas no sirven** [CALCULADO]:

| v km/h | Re | C_F (ITTC-57) | ΔC_F ITTC-78 (k_S = 150 µm) | C_A ITTC-78 |
|---|---|---|---|---|
| 3 | 1,2·10⁶ | 0,00448 | **−0,00212** | 0,00203 |
| 6 | 2,5·10⁶ | 0,00389 | **−0,00127** | 0,00184 |
| 12 | 4,9·10⁶ | 0,00340 | **−0,00060** | 0,00166 |

  ΔC_F da negativo y C_A vale ~47 % de C_F. Ambas son correlaciones de buques. → En `sizing.py` conviene dejar `delta_cf` (hoy 0,0004 [SUPUESTO]) como **parámetro de calibración** y no derivarlo de la ITTC-78.

### 1.3 Factor de forma (1 + k)

- **Holtrop 1984:** 1+k₁ = 0,93 + 0,487118·c₁₄·(B/L)^1,06806·(T/L)^0,46106·(L/L_R)^0,121563·(L³/∇)^0,36486·(1 − Cp)^−0,604247, con L_R = L(1 − Cp + 0,06·Cp·lcb/(4Cp − 1)) y **c₁₄ = 1 + 0,011·C_stern**. La tabla de C_stern incluye **"Pram with gondola −25"**, V −10, normal 0 y U con popa Hogner +10 [VERIFICADO: S16, que confirma c₁₄, la tabla de C_stern, 0,93, 0,487118 y L_R; el OCR de los demás exponentes está dañado, los tomé de ESTIMADO: memoria técnica].
- Con Cp = 0,72, lcb entre 0 y −4 % y C_stern = −25, sale **1+k = 1,46–1,49**. Con C_stern = 0 sale 1,66–1,70 [CALCULADO, extrapolado: L/B = 1,85 queda muy por debajo de los buques de la base].
- **ITTC, lanchas rápidas (HSMV):** "for HSMVs with transom sterns continue to be assumed (1+k) = 1.0", porque a baja velocidad el flujo detrás del espejo es confuso y la superficie mojada cambia con la velocidad [VERIFICADO: S19].
- **Prohaska** (C_TM/C_FM contra Fr⁴/C_FM con 0,1 < Fr < 0,2): "should not be used for any vessel with substantial transom sterns for which the transom runs wet at the speed range for the Prohaska test" [VERIFICADO: S18]. El jon boat tiene el espejo mojado a 1,6–3,2 km/h, así que **Prohaska no vale para el ensayo de remolque del proyecto**.
- → `form_factor_k = 0,2` (1+k = 1,2) queda dentro de la banda 1,0 (ITTC) – 1,5 (Holtrop extrapolado). No se puede separar de R_TR ni de R_W con un ensayo en el mar. Hay que calibrar **R(v) total**.

### 1.4 Espejo sumergido (Holtrop & Mennen 1982): fórmula verificada

Texto del paper (OCR, S15): "the additional pressure resistance due to the immersed transom … R_TR = 0.5ρV²A_T·c₆. The coefficient c₆ has been related to the Froude number based on the transom immersion: c₆ = 0.2(1 − 0.2F_nT) when F_nT < 5, or c₆ = 0 when F_nT ≥ 5. F_nT = V/√(2gA_T/(B + B·C_WP)), C_WP waterplane area coefficient." A_T es "the immersed part of the transverse area of the transom at zero speed", incluyendo cuñas en el pantoque. El mismo A_T entra en c₅ = 1 − 0,8A_T/(B·T·C_M), que reduce R_W [VERIFICADO: S15].
**`hydro.py` implementa la fórmula exacta.** No usa c₅, lo cual es aceptable porque R_W se calibra.

Holtrop 1984: "No attempts were made to derive new formulations for the transom pressure resistance … The available material to develop such formulae is rather scarce" [VERIFICADO: S16].

Con A_T = 0,189 m², B_WL = 1,079 m y C_WP = 0,85 [CALCULADO]:

| v km/h | 3 | 4 | 5 | 6 | 7 | 8 | 10 | 12 |
|---|---|---|---|---|---|---|---|---|
| F_nT | 0,61 | 0,82 | 1,02 | 1,22 | 1,43 | 1,63 | 2,04 | 2,45 |
| c₆ | 0,176 | 0,167 | 0,159 | 0,151 | 0,143 | 0,135 | 0,118 | 0,102 |
| R_TR (N) | 11,7 | 19,8 | 29,4 | **40,2** | 51,7 | 63,7 | 87,5 | 108,7 |

- F_nT recién llega a 5 a **24,5 km/h**. Según la fórmula, el espejo nunca se ventila en el rango del proyecto.
- A 6 km/h, R_TR es **30 % de R nominal (134 N)** y es el término con menos base empírica.
- R_TR ∝ A_T·c₆(A_T). Bajar el calado de popa es la palanca más barata: carga hacia proa y no sobrecargar el bote.

### 1.5 Olas y joroba

- Holtrop 1984 [VERIFICADO: S16]:
  - Para Fn ≤ 0,40 recomienda la fórmula de 1982 con m₂ = c₁₅·0,4·exp(−0,034Fn^−3,29) (el exponente −3,29 está borroso en el OCR [ESTIMADO]).
  - Para Fn > 0,55 da una fórmula de alta velocidad aparte: c₁₇, m₃ y m₄.
  - Para 0,40 < Fn < 0,55: "use the more or less arbitrary interpolation formula" entre R_W(0,40) y R_W(0,55). La forma es R_W = R_W,A(0,40) + (10Fn − 4)(R_W,B(0,55) − R_W,A(0,40))/1,5 [ESTIMADO: OCR dañado + memoria].
  - c₇ = 0,5 − 0,0625·L/B cuando B/L > 0,25, que es el caso del bote (B/L = 0,54).
- Rango de Holtrop, según la documentación de un repositorio (fuente secundaria): Fn 0,15–0,45, Cp 0,55–0,85, precisión ±5–10 % [VERIFICADO: S31]. El crucero (Fn 0,376) cae dentro, pero 8–12 km/h (Fn 0,50–0,75) quedan **en la zona de interpolación arbitraria o fuera de rango**. La geometría queda fuera en L/B y en L/∇^⅓.
- → La forma semiempírica de `hydro.py` (R_W = W·c_w·Fr⁴/(1 + (Fr/Fr_h)⁴)) es razonable como modelo para calibrar. No hay un método publicado validado para este casco.

### 1.6 Planeo (Savitsky 1964) y regímenes (Savitsky 2003)

- **Savitsky 2003 (abierto)** [VERIFICADO: S21]:
  - Desplazamiento hasta SLR ≈ 1,3, con "wall of resistance" a SLR 1,34. Semidesplazamiento 1,3–3,0. Planeo de pantoque duro "recommended when operating at SLR > 3.0".
  - "The planing hull has somewhat larger resistance than the displacement or semi-displacement hulls up to a SLR of approximately 3 (pre-planing speed)", por los pantoques vivos y el espejo ancho sumergido.
  - Curva R/Δ típica (Fig. 4, leída a ojo ±0,01): **≈0,02–0,025 a SLR 1,3; ≈0,05–0,06 a SLR 1,7; ≈0,08 a SLR 2; ≈0,10 a SLR 3**. Es una curva "típica"; el ejemplo de potencia del mismo texto usa L/∇^⅓ = 6,9.
- **Contraste [CALCULADO]:** `hydro.py` da R/W = 0,047 (6 km/h, SLR 1,26), 0,093 (8 km/h) y 0,176 (12 km/h), o sea **~2 veces la curva típica de Savitsky**. Los datos medidos en botes reales de 2,4–2,75 m (R04: 95–150 N a 6 km/h) respaldan el nivel del proyecto. → **No usar curvas R/Δ "típicas" para este casco rechoncho**: subestiman la resistencia a la mitad.
- **Savitsky 1964** [ESTIMADO: memoria técnica, no verificado; buscar: "Savitsky 1964 Hydrodynamic design of planing hulls Marine Technology pdf"]:
  - C_Lβ = Δ/(½ρV²b²) = C_L0 − 0,0065β·C_L0^0,6
  - C_L0 = τ^1,1(0,0120λ^½ + 0,0055λ^2,5/C_V²)
  - l_p/(λb) = 0,75 − 1/(5,21C_V²/λ² + 2,39)
  - D = Δ·tan τ + ½ρV₁²λb²C_f/(cos β·cos τ)
  - Validez: 0,60 ≤ C_V ≤ 13; 2° ≤ τ ≤ 15°; λ ≤ 4.
  - **No aplica:** a 12 km/h, C_V = 1,09 está formalmente en rango, pero Fn∇ = 1,31 es pre-planeo. Las hipótesis de Savitsky (espejo seco, pantoques secos, sustentación dominante) no se cumplen.
- **Pre-planeo** (Mercier & Savitsky 1973, Davidson Lab; Savitsky & Brown 1976): regresión de R/Δ en Fn∇ = 1,0–2,0 con variables ∇^⅓/L, ángulo de entrada, A_T/A_X y B/T [ESTIMADO: memoria]. **No encontré los coeficientes en fuente abierta.** El límite inferior de L/∇^⅓ (≈4 según la memoria) excluye este casco (3,0). → buscar: "Mercier Savitsky 1973 resistance of transom-stern craft in the pre-planing regime coefficients"; "Savitsky Brown 1976 procedures hydrodynamic evaluation planing hulls".
- **Series 62 (Clement & Blount 1963):** no encontré fuente abierta con R/Δ en la joroba. → buscar: "Clement Blount 1963 Series 62 resistance tests systematic series planing hull forms DTMB".

### 1.7 Gerr (Propeller Handbook y artículos de Gerr Marine)

- **Verificado** [S22]: "Max Hull SL Ratio = 8.26/(DL ratio)^0.311, but never less than 1.34. This gives the maximum speed-length ratio a hull can be driven without planing". DL = Disp[t largas]/(0,01·WL[ft])³. SLR < 1,34 es desplazamiento, > 3 es planeo pleno y en medio está el semidesplazamiento. La muestra del artículo tiene DL de 79 a 334.
- No verificado: SLR = 10,665/(LB/SHP)^⅓ [ESTIMADO: memoria técnica; `hydro.gerr_power_w` usa esta fórmula; buscar: "Gerr Propeller Handbook 10.665 LB/SHP"].
- **Proyecto [CALCULADO]:** DL = **1010**, unas 3 veces la muestra de Gerr. 8,26/1010^0,311 = 0,96 → se aplica el piso de 1,34 → velocidad máxima sin planear **≈ 6,4 km/h**. El crucero de 6 km/h ya está al 94 %.
  - Potencia de Gerr al eje: 460 W (5 km/h), **795 W (6 km/h)**, 1885 W (8 km/h), 6,4 kW (12 km/h).
  - Con la B-series y R del proyecto, P_D = 507–545 W a 6 km/h (§2.3).
  - En campo, un inflable de 8 ft necesitó ≈500 W *eléctricos* a 6,1–6,7 km/h (R04).
  - → **Gerr sobreestima 1,5–2 veces**. Usarlo solo como techo.

### 1.8 Agua poco profunda

ITTC (Schuster): ΔV/V = m/(1 − m − Frh²) + (1 − R_V/R_T)·(2/3)·Frh¹⁰. El segundo término es "finite depth influence on wave making resistance … within the range 0 < Frh < 0.7" [VERIFICADO: S18].

En aguas abiertas m ≈ 0 [ESTIMADO: extrapolación de una corrección para tanque]:
- Con h = 1 m: Frh = 0,53 a 6 km/h → efecto despreciable (Frh¹⁰ = 0,002).
- **Con h = 0,6 m a 8 km/h, Frh = 0,92**: fuera de la validez y cerca del crítico (Frh = 1), con un aumento fuerte de resistencia que la fórmula no cuantifica.
- → En los bajos de arena (< 1 m), ir a ≤ 6 km/h.
- → El ensayo de remolque necesita **h ≥ 1,5 m** (Frh ≤ 0,58 a 8 km/h).

### 1.9 Datos experimentales de botes planos

No encontré ensayos abiertos de remolque de jon boats, punts ni barcazas chicas. Lo más cercano es la Fig. 4 de S21, que no es representativa (§1.6), y los datos de campo de R04. → buscar: "jon boat towing tank resistance test", "flat bottom punt resistance model test", "garvey hull resistance".

**Protocolo derivado (§1.2–1.8):**
- Remolque con dinamómetro a 2, 3, 4, 5, 6, 7 y 8 km/h (GPS), con h ≥ 1,5 m, sin viento o con viento promediado ida y vuelta, y con la carga y el trimado reales.
- Ajustar **una sola** curva R(v) y no separar (1+k), R_TR y R_W.
- Ajustar c_w y Fr_h con `form_factor_k` y `delta_cf` fijos.

---

## 2. Hélice: Wageningen B-series

### 2.1 Fuente pública verificada y coeficientes

- **Repositorio:** GijsB/propy (MIT), archivo `src/propy/wageningen_b.py`. Implementa KT y KQ como polinomios en J con coeficientes en (P/D, AE/A0, Z). Límites del código: Z 2–7, AE/A0 0,3–1,05, P/D 0,5–1,4 [VERIFICADO: S13].
- **Fuente primaria (en el mismo repositorio):** Bernitsas, Ray & Kinley, *KT, KQ and Efficiency Curves for the Wageningen B-Series Propellers*, Univ. of Michigan, Dept. NA&ME, Report No. 237, mayo de 1981. Es un PDF escaneado de 111 páginas.
  - Tabla 1, "Reproduced from [1] = Oosterveld & van Oossanen 1974/75": KT = ΣC^T_{s,t,u,v}·J^s(P/D)^t(AE/A0)^u Z^v, con 39 términos para KT y 47 para KQ, a **Rn = 2·10⁶**.
  - Tabla 2: corrección de Reynolds ΔKT y ΔKQ "above Rn = 2×10⁶", con términos en (log Rn − 0,301).
  - Validez: "2 ≤ Z ≤ 7, 0.30 ≤ AE/A0 ≤ 1.05, 0.5 ≤ P/D ≤ 1.40 … at the extremes … not fully reliable (KT local maximum for low J, high Z, low AE/A0 and high P/D)" [VERIFICADO: S14].
- **Control término a término:** transcribí la Tabla 1 del escaneo y la comparé término a término con propy. Coinciden los 39 de KT y 46 de 47 de KQ. El restante, el término (s,t,u,v) = (1,3,1,0) de KQ, es 0,00318086 en el escaneo y 0,003180986 en propy: diferencia relativa de 4·10⁻⁵, despreciable [CALCULADO]. En el bloque de abajo va el valor del escaneo.
- **Valores de control** (evaluados con los polinomios) [CALCULADO]. La Fig. 21 de S14 (3 palas, AE/A0 = 0,50), revisada a ojo, coincide: η máx ≈ 0,72 cerca de J ≈ 0,87 y KT = 0 en J ≈ 1,09 para P/D = 1,0.

| Hélice | J | KT | KQ | η₀ | Otros |
|---|---|---|---|---|---|
| **B3-50, P/D 1,0** | **0,5** | **0,2451** | **0,03863** | **0,505** | KT0 = 0,4057; KQ0 = 0,05964; η_máx 0,723 en J = 0,869; KT = 0 en J = 1,087 |
| B3-50, P/D 0,8 | 0,5 | 0,1579 | 0,02148 | 0,585 | KT0 = 0,3217; η_máx 0,681 en J = 0,68; KT = 0 en J = 0,881 |
| B3-50, P/D 1,2 | 0,5 | 0,3280 | 0,06000 | 0,435 | KT0 = 0,4809; η_máx 0,745 en J = 1,055 |
| B4-55, P/D 1,0 | 0,5 | 0,2652 | 0,04178 | 0,505 | — |

- **Contraste con el modelo lineal de `prop.py`** [CALCULADO]:

| Parámetro | `prop.py` hoy | B-series |
|---|---|---|
| KT0/(P/D) | 0,38 | 0,40 (B3-50, P/D 0,6–1,2: 0,389–0,406); 0,37 (B3-35); 0,44 (B3-65) |
| J_T0 | 1,05·P/D | 1,10·P/D (P/D 0,8); 1,09 (1,0); 1,08 (1,2); 1,125 (0,6) |
| FOM en punto fijo, T^1,5/(√(2ρA)·2πnQ) | 0,60 | 0,63 (P/D 0,6); 0,60 (0,8); 0,55 (1,0); 0,50 (1,2) |

- Otra implementación con la misma tabla y además la corrección de Reynolds de la Tabla 2: `msunderland78/NAVALARCHITECTURE-POP`, `pop_core/wageningen.py` [VERIFICADO: S17].
- **Cuatro cuadrantes (marcha atrás):** propy dice "this is not currently implemented … a simple function fit is used to get a very rough approximation" [VERIFICADO: S13]. No hay datos abiertos de B-series en cuatro cuadrantes. → buscar: "Wageningen B-series four quadrant Fourier coefficients MARIN". Empuje atrás ≈ 50–70 % del empuje adelante a igual rpm [ESTIMADO: memoria técnica].
- **Gawn-Burrill** (secciones segmentales, más parecidas a una hélice de fueraborda): propy lo implementa según Radojčić, con P/D 0,8–1,8, AE/A0 ≈ 0,5–1,2 y J ≥ AE/A0/2 [VERIFICADO: S13, código]. No lo validé numéricamente.

**Bloque listo para `p1calc/bseries_coeffs.json`.** El formato coincide con `_poly()` de `prop.py`: [C, s(J), t(P/D), u(AE/A0), v(Z)].

```json
{"source": "Bernitsas, Ray & Kinley 1981 (UMich NAME Rep. 237) Tabla 1; transcripcion GijsB/propy wageningen_b.py",
 "Rn": 2.0e6,
 "format": "[C, s(J), t(P/D), u(AE/A0), v(Z)]",
 "KT": [
  [0.00880496, 0, 0, 0, 0], [0.0144043, 0, 0, 0, 1], [-0.000606848, 0, 0, 0, 2], [-0.0125894, 0, 0, 1, 1],
  [0.000690904, 0, 0, 1, 2], [-0.0507214, 0, 0, 2, 0], [0.166351, 0, 1, 0, 0], [0.0143481, 0, 1, 0, 1],
  [0.158114, 0, 2, 0, 0], [0.415437, 0, 2, 1, 0], [-0.00410798, 0, 2, 2, 1], [-0.133698, 0, 3, 0, 0],
  [-0.00841728, 0, 3, 0, 1], [-0.0317791, 0, 3, 1, 1], [0.00421749, 0, 3, 1, 2], [-0.00146564, 0, 3, 2, 2],
  [0.00638407, 0, 6, 0, 0], [-0.204554, 1, 0, 0, 0], [-0.0049819, 1, 0, 0, 2], [0.0109689, 1, 0, 1, 1],
  [0.018604, 1, 0, 2, 1], [0.0606826, 1, 1, 0, 1], [-0.481497, 1, 1, 1, 0], [-0.00163652, 1, 2, 0, 2],
  [0.0168424, 1, 3, 0, 1], [-0.000328787, 1, 6, 0, 2], [0.010465, 1, 6, 2, 0], [-0.0530054, 2, 0, 0, 1],
  [0.0025983, 2, 0, 0, 2], [-0.147581, 2, 0, 1, 0], [0.0854559, 2, 0, 2, 0], [-0.00132718, 2, 6, 0, 0],
  [0.000116502, 2, 6, 0, 2], [-0.00648272, 2, 6, 2, 0], [-0.000560528, 3, 0, 0, 2], [0.168496, 3, 0, 1, 0],
  [-0.0504475, 3, 0, 2, 0], [-0.00102296, 3, 3, 0, 1], [5.65229e-05, 3, 6, 1, 2]
 ],
 "KQ": [
  [0.00379368, 0, 0, 0, 0], [0.015896, 0, 0, 2, 0], [-0.0001843, 0, 0, 2, 2], [0.00513696, 0, 1, 0, 1],
  [-0.0408811, 0, 1, 1, 0], [-0.0502782, 0, 1, 2, 0], [0.00344778, 0, 2, 0, 0], [0.188561, 0, 2, 1, 0],
  [-0.0269403, 0, 2, 1, 1], [0.00155334, 0, 2, 1, 2], [0.0126803, 0, 2, 2, 1], [0.0161886, 0, 3, 1, 0],
  [-0.0397722, 0, 3, 2, 0], [-0.000425399, 0, 3, 2, 2], [-0.000313912, 0, 6, 0, 1], [-0.00142121, 0, 6, 1, 1],
  [0.000302683, 0, 6, 1, 2], [-0.00350024, 0, 6, 2, 0], [0.00334268, 0, 6, 2, 1], [-0.0004659, 0, 6, 2, 2],
  [-0.00370871, 1, 0, 0, 1], [0.000269551, 1, 0, 1, 2], [0.0471729, 1, 0, 2, 0], [-0.00383637, 1, 0, 2, 1],
  [-0.032241, 1, 1, 0, 0], [0.0209449, 1, 1, 0, 1], [-0.00183491, 1, 1, 0, 2], [-0.108009, 1, 1, 1, 0],
  [0.00438388, 1, 1, 1, 1], [0.00318086, 1, 3, 1, 0], [5.54194e-05, 1, 6, 2, 2], [0.00886523, 2, 0, 0, 0],
  [-0.00723408, 2, 0, 1, 1], [0.00083265, 2, 0, 1, 2], [0.00474319, 2, 1, 0, 1], [-0.0885381, 2, 1, 1, 0],
  [0.0417122, 2, 2, 2, 0], [-0.00318278, 2, 3, 2, 1], [-0.0106854, 3, 0, 0, 1], [0.0558082, 3, 0, 1, 0],
  [0.0035985, 3, 0, 1, 1], [0.0196283, 3, 0, 2, 0], [0.000112451, 3, 2, 0, 2], [0.00110903, 3, 3, 0, 1],
  [8.69243e-05, 3, 3, 2, 2], [-2.97228e-05, 3, 6, 0, 2], [-0.030055, 3, 1, 2, 0]
 ]}
```

Prueba unitaria sugerida: B3-50, P/D = 1,0, J = 0,5 → KT = 0,2451 ± 0,0001, KQ = 0,03863 ± 0,00001, η₀ = 0,505 ± 0,001.

### 2.2 Escala y rugosidad: la hélice chica opera por debajo de Rn = 2·10⁶

- **Holtrop 1982 (método ITTC-78)** [VERIFICADO: S15]. Los polinomios "are valid, however, for a Reynolds number of 2·10⁶ and need to be corrected for the specific Reynolds number and the roughness":
  - KT_buque = KT_B + ΔC_D·0,3·(P/D)·(c₀,₇₅Z/D)
  - KQ_buque = KQ_B − ΔC_D·0,25·(c₀,₇₅Z/D)
  - ΔC_D = (2 + 4(t/c)₀,₇₅)·{0,003605 − (1,89 + 1,62·log(c₀,₇₅/k_p))^−2,5}
  - k_p = 0,00003 m para hélice nueva
  - c₀,₇₅ = 2,073·(AE/A0)·D/Z
  - (t/c)₀,₇₅ = (0,0185 − 0,00125Z)·D/c₀,₇₅
- **EO10x8** (D = 0,254 m, P/D 0,8, Z = 3, AE/A0 0,5) [CALCULADO]: c₀,₇₅ = 87,8 mm; t/c = 0,043; ΔC_D = −0,00624; ΔKT = −0,00155; ΔKQ = +0,00162 → **η₀ baja ~7 %** en crucero (0,494 → 0,459) y P_D sube de 507 a 545 W.
- Rn₀,₇₅ real = (5,7–7,7)·10⁵ [CALCULADO], por debajo de los 2·10⁶ de la regresión. La Tabla 2 solo corrige hacia arriba.
- → Banda para `efficiency_factor`: **0,93–0,98**. Con 0,98 se cubre solo el efecto Re de una hélice lisa; con 0,93, la rugosidad de 30 µm de la ITTC-78 [ESTIMADO].

### 2.3 Hélices candidatas en crucero

Condiciones: T = 169,2 N a lo largo del eje, V = 6 km/h, w = 0,02, Va axial = V(1 − w)·cos 25° = 1,48 m/s, ρ = 1013. B-series de 3 palas sin corrección de escala [CALCULADO].

| Hélice | D m | P/D | rpm | J | η₀ | P_D W |
|---|---|---|---|---|---|---|
| OB78x6 (7,8″ fueraborda) | 0,198 | 0,77 | 1369 | 0,328 | **0,420** | 596 |
| OB74x55 | 0,188 | 0,74 | 1536 | 0,307 | 0,406 | 616 |
| **EO10x8 (elegida)** | 0,254 | 0,80 | 863 | 0,405 | **0,494** | 507 |
| EO11x8 | 0,279 | 0,73 | 782 | 0,406 | **0,523** | 479 |
| Óptimo de la cuadrícula B3-50 | 0,32 | 0,8 | 585 | — | 0,562 | 445 |
| Óptimo de la cuadrícula B3-50 | 0,34 | 0,8 | 530 | — | 0,579 | 432 |

- WW10x4 (P/D 0,4) queda **fuera del rango B-series** (P/D ≥ 0,5). No se puede evaluar con estos polinomios.
- `sizing.json` hoy da η₀ = 0,480 para la EO10x8 con el modelo lineal, contra 0,494 de la B-series. La diferencia es chica, pero con la corrección del §2.2 queda en 0,459.

### 2.4 Disco actuador (límite ideal)

- Potencia ideal en punto fijo: P = √(T³/(2ρA)) [VERIFICADO: S2]. En avance, η_i = 2/(1 + √(1 + C_T)), con C_T = T/(½ρVa²A) [ESTIMADO: derivación estándar de la misma teoría de momento].
- Crucero, T = 169 N, Va = 1,48 m/s [CALCULADO]:

| D | 0,198 | 0,254 | 0,279 | 0,30 | 0,34 |
|---|---|---|---|---|---|
| C_T | 4,95 | 3,01 | 2,49 | 2,16 | 1,68 |
| η_i | 0,581 | 0,666 | 0,698 | 0,720 | 0,758 |

  La relación η₀/η_i de la B-series da 0,72–0,76. Es coherente.
- Punto fijo con T = 328 N: P_ideal = 586 W con D = 0,254 m. La B-series necesita 981 W (FOM 0,60) [CALCULADO].

---

## 3. Cavitación

### 3.1 Definiciones (verificadas en el código de S17)

- σ₀,₇R = (p_atm + ρgh)/(½ρ(Va² + (0,7πnD)²)). POP no resta p_v. `prop.py` sí lo resta, lo que es más conservador.
- POP calcula la carga de Burrill con **A_E y la velocidad a 0,75R**: T/(½ρV²₀,₇₅·A0·AE/A0) [VERIFICADO: S17]. Esa definición **no es la clásica**.
- La definición clásica, que usa `prop.py`, es τ_c = T/(½ρV²₀,₇R·A_P), con A_P ≈ A_E(1,067 − 0,229·P/D) [ESTIMADO: memoria técnica (Carlton), no verificado; buscar: "projected area ratio 1.067 0.229 P/D Burrill"].

### 3.2 Curva de Burrill digitalizada (5 % y 10 % de cavitación en la cara de succión)

Fuente: "Burrill back-cavitation chart digitised from Carlton (2012) Figure 9.21" [VERIFICADO: README y `solver.py` de S17]:

| σ₀,₇R | 0,10 | 0,20 | 0,30 | 0,40 | 0,50 | 0,60 | 0,80 | 1,00 | 1,50 | 2,00 | 3,00 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| τ_c, 5 % | 0,066 | 0,118 | 0,155 | 0,181 | 0,201 | 0,218 | 0,243 | 0,260 | 0,286 | 0,301 | 0,320 |
| τ_c, 10 % | 0,086 | 0,148 | 0,188 | 0,219 | 0,242 | 0,260 | 0,287 | 0,306 | 0,336 | 0,354 | 0,380 |
| `prop.py`: 0,3σ^0,6 | 0,075 | 0,114 | 0,146 | 0,173 | 0,198 | 0,221 | 0,262 | **0,300** | **0,383** | **0,455** | **0,580** |

- El ajuste de `prop.py`, rotulado "2,5 %", **sigue la curva de 5 % solo hasta σ ≈ 0,6**. Por encima se vuelve no conservador: +15 % en σ = 1, +51 % en σ = 2 y +81 % en σ = 3 [CALCULADO].
- → Reemplazarlo por `np.interp(σ, tabla 5 %)`. La curva de 2,5 % (no disponible) queda **por debajo** de la de 5 %.

### 3.3 Keller

AE/A0_mín = (1,3 + 0,3Z)·T/(D²(p₀ + ρgh − p_v)) + K. "K = 0 to 0.1 for twin-screw ships, K = 0.2 for single-screw ships. For sea water of 15 °C, p₀ − p_v = 99047 N/m²" [VERIFICADO: S15]. La misma fórmula aparece en propy (`cavitation_margin`, K = 0,2) y en propy_opt (K = 0,2 con un eje, 0,1 con dos) [VERIFICADO: S13, S30]. Una hélice de cola larga en flujo casi uniforme se parece más al caso K = 0,1 [ESTIMADO].

### 3.4 Resultados para la EO10x8

Con eje a 0,9D = 0,229 m de profundidad (punta a 0,4D) [CALCULADO]:

| Caso | T eje N | rpm | σ₀,₇R | τ_c | Límite 5 % | τ_c/límite | AE/A0 mín Keller (K = 0,2) |
|---|---|---|---|---|---|---|---|
| Crucero nominal | 169 | 863 | 3,00 | 0,224 | 0,320 | 0,70 | 0,26 |
| Crucero diseño | 195 | 908 | 2,71 | 0,233 | 0,315 | 0,74 | 0,27 |
| 8 km/h | 309 | 1162 | 1,65 | 0,225 | 0,291 | 0,77 | 0,30 |
| **Punto fijo** | 328 | 933 | 2,65 | **0,383** | 0,313 | **1,22** (también > 10 %: 0,371) | 0,31 |

- En punto fijo, τ_c = KT0/(½(0,7π)²·A_P/D²) **no depende del empuje**: es propiedad de la hélice. Da 0,38 para cualquier B3-50 con P/D 0,8. La OB78x6 da 0,40 y la EO11x8 0,34 [CALCULADO].
- Burrill es un criterio para el punto de diseño en avance. En punto fijo se espera algo de cavitación o ventilación en la cara de succión a fondo de acelerador, sobre todo con la punta a solo 0,10 m de la superficie [ESTIMADO].
- En crucero y a 8 km/h, el margen es suficiente con AE/A0 = 0,5.

---

## 4. Toberas (Kort 19A) y aro protector

- **Kort o tobera acelerante** [VERIFICADO: S5]:
  - Ventaja "at lower speeds (<10 knots)", y "lose their advantage over propellers at about ten knots".
  - "Bollard pull can increase up to 30% with ducts".
  - Perfiles habituales: MARIN 19A y 37. Desventajas: arrastre, objetos que se atascan entre hélice y tobera ("more difficult to clear"), más cavitación y peor gobierno marcha atrás.
- **Teoría de momento con carenado** [VERIFICADO: S24, ec. 1.2 y 1.5]: P_i = T^1,5/√(4σ_dρA), con σ_d = A_salida/A_disco. La fracción de empuje del rotor es T_rotor/T_total = 1/(2σ_d). Con σ_d = 1 y la misma potencia, el empuje ideal crece (4/2)^⅓ = **1,26 veces, +26 %** [CALCULADO]. Coincide con el "+30 %" de S5.
- **La holgura de punta manda** [VERIFICADO: S24]:
  - Mort, X-22A: pasar de 0,3 % a 2,0 %D de holgura bajó ≈20 % el coeficiente de empuje estático.
  - Rotores de MAV: con 0,5 %D, FM fue 7 % mayor que el rotor libre; con 2,0 %D, **25 % menor**.
  - Hubbard: de 0,2 % a 4,4 %D, "approximately an 84% reduction in total thrust".
  - Los ensayos son aerodinámicos y a bajo Re; los tomo como análogos [ESTIMADO].
  - Wikipedia: "Good efficiency requires very small clearances between the blade tips and the duct" [VERIFICADO: S12].
- **Aro protector del proyecto:** holgura de 6 mm en 254 mm = **2,4 %D**, perfil de 76 mm. Según los datos anteriores **no da ganancia en punto fijo y puede restar**. `guard.thrust_loss_frac = 0,10` y `bollard_gain_frac = 0` son coherentes. Una banda de 0,10–0,20 para análisis de sensibilidad es razonable [ESTIMADO]. El arrastre de fricción del aro es ≈1–3 N a 6 km/h [CALCULADO con C_f ≈ 0,0056 sobre 0,127 m² mojados]. La pérdida principal es por bloqueo y por la estela, no por fricción.
- **Datos de usuarios (eFoil)** [VERIFICADO: S25, S26, S27]:
  - Un aro que gira con la hélice, impreso en 3D: "38A @ 20 km/h" sin aro contra "100A @ 20 km/h" con aro.
  - Un protector impreso de 550 g: "It is only good for protection. Nothing else is positive about it. It works as an effective brake."
  - Con tobera: "a big drop in efficiency above 12mph" (sin medición).
- → Una tobera 19A real necesitaría holgura ≤ 0,5 %D (≈1,3 mm), concentricidad y rigidez que no son viables en PETG con arena y golpes. **El aro es solo protección.**

---

## 5. Mecánica

### 5.1 Velocidad crítica (whirling)

- Rayleigh: ω₁ ≈ √(g·Σwᵢyᵢ/Σwᵢyᵢ²). Con un solo tramo, ω₁ ≈ √(g/y_máx), que subestima. Se combinan cargas o se aplica Dunkerley. "Many practical applications suggest … maximum operating speed should not exceed 75% of the critical speed" (Wikipedia marca falta de cita) [VERIFICADO: S1].
- Euler-Bernoulli: ω = β²√(EI/μ). Voladizo: ω₁ = 3,5160/L²·√(EI/μ). Libre-libre: 22,3733/L²·√(EI/μ) [VERIFICADO: S7]. Viga biapoyada: βL = π → **ω₁ = (π/L)²√(EI/μ)** [ESTIMADO: derivación estándar de la misma ecuación]. Es lo que usa `mech.py`.
- **Ø16 AISI 316** (E = 193 GPa, ρ = 8000): EI = 621 N·m², μ = 1,608 kg/m [CALCULADO]:

| Tramo biapoyado L | 0,3 m | 0,4 m | 0,5 m | 0,6 m | 0,8 m | 1,0 m |
|---|---|---|---|---|---|---|
| n_crít (rpm) | 20 574 | 11 573 | 7 407 | 5 144 | 2 893 | 1 852 |

- Hélice en voladizo (0,65 kg, eje rígido sin su masa, k = 3EI/a³): con a = 60 mm, 34 800 rpm; con a = 100 mm, 16 200 rpm; con a = 150 mm y 0,8 kg, 7 900 rpm [CALCULADO].
- Máximo de la hélice ≈1 230 rpm, con un primer orden de pala de 3× ≈ 3 700 ciclos/min. → **Tramo entre bujes ≤ 0,6 m** (n_crít/n_máx > 4). No conviene un tramo libre de 1 m. Los bujes de POM lubricados por agua con holgura no son apoyos perfectos [ESTIMADO]. Aplicar Dunkerley: 1/ω² = Σ 1/ωᵢ².

### 5.2 Fatiga

- Gerber: (nσ_m/σ_b)² + nσ_a/σ_w = 1. **Goodman: σ_m/σ_b + σ_a/σ_w = 1/n. Soderberg: σ_m/σ_y + σ_a/σ_w = 1/n.** El orden de conservadurismo es Soderberg > Goodman > Gerber [VERIFICADO: S3].
- `mech.py` usa 1/n = σ_a/S_e + √3·τ_m/S_u: Goodman con von Mises, flexión alternante y torsión media. Es la forma DE-Goodman de Shigley con M_m = T_a = 0 [ESTIMADO: memoria técnica (Shigley)]. Agregar la componente alternante de torsión por el primer orden de pala: T_a ≈ 0,10–0,20·T_m (§5.4).
- En agua de mar, el acero inoxidable **no tiene límite de fatiga verdadero** (fatiga con corrosión) [ESTIMADO: memoria técnica; ver R05]. `se_mpa = 120` (contra 150 en seco) es la decisión correcta.

### 5.3 Pasador de corte

- Corte doble a través del eje Ø D_s: Q_corte = τ_u·(πd_p²/4)·D_s [ESTIMADO: equilibrio estático estándar, con las dos fuerzas de corte separadas D_s].
- τ_u ≈ 0,65·UTS en aluminios, ≈ 0,75·UTS en aceros (como guía "muy aproximada"). En general se estima en 60 % de la UTS [VERIFICADO: S6]. 6061-T6: UTS ≥ 42 ksi (290 MPa), fluencia ≥ 35 ksi (241 MPa), fatiga 14 ksi (96,5 MPa) a 5·10⁸ ciclos invertidos [VERIFICADO: S8].
- Par de corte con D_s = 16 mm [CALCULADO]:

| d_p | 2,0 mm | 2,5 mm | **3,0 mm** | 3,5 mm | 4,0 mm |
|---|---|---|---|---|---|
| 6061-T6 (τ_u = 0,65·290 = 189 MPa) | 9,5 N·m | 14,8 | **21,3** | 29,0 | 37,9 |
| 6061-T6 (τ_u = 207 MPa, `inputs.yaml`) | 10,4 | 16,3 | **23,4** | 31,9 | 41,6 |
| AISI 316 recocido (0,75·515 = 386 MPa) [UTS: `inputs.yaml`] | **19,4** | 30,3 | 43,7 | 59,5 | 77,7 |

- Par máximo en la hélice ≈ 9,7–10 N·m (punto fijo, `sizing.json`). → **Pasador de 6061-T6 de Ø3 mm** (21–23 N·m ≈ 2,2 veces Q_máx), o de 316 de Ø2 mm. No usar latón: se descinca (R06).
- En crucero (6 N·m), el pasador de Al de 3 mm trabaja a τ = 53 MPa. El límite de fatiga en corte es ≈ 0,577·96,5 = 56 MPa [ESTIMADO]. Con Goodman (τ_m dominante, τ_a = 10 %), n = 1,6 en punto fijo [CALCULADO]. → Llevar repuestos y revisar cada salida.
- Pasadores de fábrica de fueraborda de 2–3,5 hp: no encontré fuente abierta. → buscar: "Tohatsu 3.5 hp shear pin diameter material", "Mercury 2.5 shear pin dimensions". En R02 hay un caso DIY con ranura para pasador de 3,5 mm en eje de 10 mm.

### 5.4 Eje inclinado (cola larga)

- **Tesis abierta sobre la hélice de long-tail tailandés** [VERIFICADO: S23]:
  - "The actual inclined shaft angle of Long-Tail Boat is operated about 12° from horizontal axis. The shaft length is 4.5 m."
  - "The component of flow Va·sin ψ perpendicular to the propeller shaft gives rise to an eccentricity of the propeller thrust … significant fluctuation in blade loading as the blade rotates. The thrust T can be resolved into a horizontal thrust T·cos ψ and a vertical force T·sin ψ … trim angle should be added to the shaft inclination."
  - Ensayo N4990 con 4,8° y 8,8°: "the inclined shaft showed higher efficiency than straight shaft by … approximately 1–7 %"; KT similar, KQ algo menor.
  - CFD a 12° de la hélice de long-tail: η +2,8 % (original) y +3,5 % (mejorada) en J = 1,1. Sin efecto entre J = 0,5 y 1,0.
- **Aplicado al proyecto (ψ = 25°, más allá de los datos)** [CALCULADO]:
  - Empuje horizontal = 0,906·T (**−9,4 %**).
  - Fuerza vertical = 0,42·T: 72 N en crucero y 139 N en punto fijo. Levanta la popa.
  - Va axial = 0,906·V.
  - Velocidad transversal relativa V·sin ψ/(0,7πnD) = 0,086 → variación de ±8,6 % en la velocidad de la sección y de ≈ ±17 % en la presión dinámica, una vez por vuelta [ESTIMADO].
  - Con 15° el empuje horizontal sería 0,966·T, un **6,6 % más** que con 25°.
- Existen ensayos con 10°, 20° y 30° (Boswell, DTMB 4661, citados en S23), pero no los abrí. → buscar: "Boswell DTMB 4661 oblique flow 20 30 degrees single blade loads".

---

## 6. Térmico

### 6.1 Outrunner refrigerado por aire

- Pérdidas: P_cu = I²·R(T) ("Copper Loss ∝ I²·R") [VERIFICADO: S9 y Wikipedia "Copper loss"]. R(T) = R₂₀[1 + α(T − 20)], con **α = 3,93·10⁻³ K⁻¹ para cobre recocido** (4,04·10⁻³ para cobre puro) [VERIFICADO: S9]. → R(80 °C)/R(20 °C) = **1,236**: a la misma corriente, la pérdida en cobre sube 24 % en caliente [CALCULADO].
- Pérdidas en hierro y mecánicas ≈ I₀·V_bemf [ESTIMADO: modelo DC de motor de hobby].
- Temperatura: T_w(t) = T_amb + P_pérd·R_th·(1 − e^(−t/τ)). Los valores `rth_k_w = 0,45` y `tau_th_s = 600` de `inputs.yaml` **no están verificados** [SUPUESTO]. → buscar: "outrunner 63xx thermal resistance K/W measurement".
- **Medición propuesta (método de resistencia):** T = T₀ + (R/R₀ − 1)/α, con R medida a 4 hilos usando una fuente de 5 A y el multímetro, o con la detección de motor del VESC en frío y en caliente. Correr 20 min a la corriente de crucero.
- VESC por defecto [VERIFICADO: S29]: limitación por motor desde 85 °C y corte a 100 °C (`MCCONF_L_LIM_TEMP_MOTOR_START/END`). Sensor NTC 10 k con β = 3380. → El `t_winding_max_c = 120` de `inputs.yaml` es más alto que lo que el VESC permite por defecto.

### 6.2 Pérdidas del ESC (MOSFET)

- P_cond = R_DS(on)·I_RMS². P_sw = V_IN·I_OUT·f_sw·Q_sw/I_g, con I_g = (V_driver − V_PL)/(R_g + R_driver) [VERIFICADO: S28, medio puente síncrono]. Inversor trifásico con FOC: P_cond ≈ 3·I_fase,rms²·R_DS(on)(T_j) y P_sw ≈ 3·V_bat·(2/π)·I_pico·f_sw·t_sw [ESTIMADO: adaptación].
- VESC por defecto: f_zv (FOC) = **25 kHz**; limitación por MOSFET desde 85 °C y corte a 100 °C [VERIFICADO: S29].
- Ejemplo de crucero con I_fase,rms = 40 A, V = 44 V, R_DS(on) caliente = 2 mΩ [SUPUESTO] y t_sw = 50 ns [SUPUESTO]: P_cond ≈ 9,6 W y P_sw ≈ 5,9 W → **≈ 15 W**. `sizing.json` da 19 W (η 0,97 fija). Es coherente y algo conservador [CALCULADO].

---

## 7. No encontrado (buscar)

| Tema | Términos de búsqueda |
|---|---|
| Coeficientes de Mercier-Savitsky 1973 y Savitsky-Brown 1976 | "Mercier Savitsky 1973 transom-stern craft pre-planing regime Davidson Laboratory report 1667" |
| Savitsky 1964 (texto original) | "Savitsky 1964 Hydrodynamic Design of Planing Hulls Marine Technology pdf" |
| Series 62 en la joroba | "Clement Blount 1963 Series 62 resistance systematic planing" |
| Gerr, SLR = 10,665/(LB/SHP)^⅓ | "Gerr Propeller Handbook 10.665 LB/SHP" |
| A_P/A_E = 1,067 − 0,229·P/D y curva de Burrill de 2,5 % | "Burrill diagram 2.5 percent back cavitation formula" |
| Tobera 19A con Ka4-70 (polinomios abiertos) | "Ka 4-70 nozzle 19A KT KQ polynomial open" |
| Datos de fábrica de protectores de hélice | "propeller guard thrust loss test data outboard" |
| Ensayos de jon boats o punts | "jon boat resistance towing test", "flat bottom punt drag" |
| R_th de outrunner 63xx | "outrunner thermal resistance K/W 6374" |
| Pasadores de corte de fueraborda | "Tohatsu MFS3.5 shear pin size" |

---

## 8. Fuentes abiertas en esta sesión

| ID | URL | Qué respalda |
|---|---|---|
| S1 | https://en.wikipedia.org/w/index.php?title=Critical_speed&action=raw | Rayleigh, √(g/y_máx), regla del 75 % |
| S2 | https://en.wikipedia.org/w/index.php?title=Momentum_theory&action=raw | P = √(T³/2ρA) |
| S3 | https://en.wikipedia.org/w/index.php?title=Goodman_relation&action=raw | Gerber, Goodman, Soderberg |
| S4 | https://en.wikipedia.org/w/index.php?title=Hull_speed&action=raw | 1,34√L_WL; constantes 1,34–1,51 |
| S5 | https://en.wikipedia.org/w/index.php?title=Ducted_propeller&action=raw | Kort 19A/37, +30 % en punto fijo, < 10 kn |
| S6 | https://en.wikipedia.org/w/index.php?title=Shear_strength&action=raw | USS ≈ 0,65 UTS (Al), 0,75 (acero), 60 % en general |
| S7 | https://en.wikipedia.org/w/index.php?title=Euler%E2%80%93Bernoulli_beam_theory&action=raw | ω = β²√(EI/μ), voladizo 3,516 |
| S8 | https://en.wikipedia.org/w/index.php?title=6061_aluminium_alloy&action=raw | 6061-T6: 290/241 MPa; fatiga 96,5 MPa |
| S9 | https://en.wikipedia.org/w/index.php?title=Electrical_resistivity_and_conductivity&action=raw | α del Cu = 3,93·10⁻³ (recocido) |
| S10 | https://en.wikipedia.org/w/index.php?title=P-factor&action=raw | Carga asimétrica de las palas con disco inclinado |
| S11 | https://en.wikipedia.org/w/index.php?title=Long-tail_boat&action=raw | Referencia a la tesis S23 |
| S12 | https://en.wikipedia.org/w/index.php?title=Ducted_fan&action=raw | La holgura de punta tiene que ser mínima |
| S13 | https://github.com/GijsB/propy · https://raw.githubusercontent.com/GijsB/propy/main/src/propy/wageningen_b.py · …/propeller.py · …/gawn_burrill.py · …/README.md | Polinomios B-series, Keller, Gawn-Burrill, nota sobre 4 cuadrantes |
| S14 | https://raw.githubusercontent.com/GijsB/propy/main/literature/Kt,%20Kq%20and%20efficiency%20curves%20for%20the%20wageningen%20b-series%20propellers.pdf | Bernitsas et al. 1981: Tablas 1 y 2, validez, Fig. 21 |
| S15 | https://raw.githubusercontent.com/msunderland78/NAVALARCHITECTURE-PPP/main/PPP-NEW/Paper/Holtrop_Approximate_1982_OCR.md | Holtrop & Mennen 1982: R_TR, c₆, F_nT, c₅, Keller, corrección ITTC-78 de la hélice |
| S16 | https://raw.githubusercontent.com/msunderland78/NAVALARCHITECTURE-PPP/main/PPP-NEW/Paper/Holtrop_Resistance_and_Propulsion_1984_OCR.md | Holtrop 1984: 1+k₁, C_stern, R_W por tramos, espejo |
| S17 | https://github.com/msunderland78/NAVALARCHITECTURE-POP · https://raw.githubusercontent.com/msunderland78/NAVALARCHITECTURE-POP/main/POP-NEW/app/backend/pop_core/solver.py · …/core.py · …/wageningen.py | Burrill de 5 % y 10 % digitalizado, σ, corrección de Re |
| S18 | https://www.ittc.info/media/11780/75-02-02-01.pdf | ITTC-57, Hughes, Prohaska y su exclusión, Schuster |
| S19 | https://www.ittc.info/media/11846/75-02-05-01.pdf | HSMV: (1+k) = 1,0 con espejo |
| S20 | https://www.ittc.info/media/8017/75-02-03-014.pdf | ITTC-78: ΔC_F, C_A |
| S21 | http://oa.upm.es/14340/2/Documentacion/3_Formas/Savitskyreport_conSemidesplazamiento.pdf | Savitsky 2003: regímenes, Fig. 4 R/Δ, Lw/LWL |
| S22 | https://www.gerrmarine.com/Articles/efficientpowerboat01.pdf | Gerr: SLR_máx = 8,26/DL^0,311, DL, regímenes |
| S23 | https://catalog.lib.kyushu-u.ac.jp/opac_download_md/1560381/eng2512.pdf | Kaewkhiaw 2015: eje inclinado, long-tail a 12° |
| S24 | http://drum.lib.umd.edu/bitstream/1903/8752/1/umi-umd-5771.pdf | Pereira 2008: P_i del rotor carenado, efecto de la holgura de punta |
| S25 | https://foil.zone/t/propellers-and-ducts/38 | Tobera en eFoil (cualitativo) |
| S26 | https://foil.zone/t/any-prop-guard-duct-options-for-a-6384-motor/17461 | Aro impreso "effective brake"; 38 → 100 A |
| S27 | https://foil.zone/t/propeller-with-the-duct-integrated-vs-propeller-a-duct/3137 | 38 A contra 100 A a 20 km/h |
| S28 | https://www.ti.com/lit/an/slpa009a/slpa009a.pdf | P_cond y P_sw de MOSFET |
| S29 | https://raw.githubusercontent.com/vedderb/bldc/master/motor/mcconf_default.h | f_zv = 25 kHz; límites de 85/100 °C; NTC |
| S30 | https://raw.githubusercontent.com/nantonelli94/propy_opt/main/app.py | Keller con K = 0,2 (1 eje) y 0,1 (2 ejes) |
| S31 | https://github.com/nantonelli94/propulse | Rango de Holtrop: Fn 0,15–0,45, Cp 0,55–0,85 (secundaria) |

---

## Hallazgos que cambian el diseño

- **Cambiar el modelo lineal de hélice por los polinomios verificados.** El bloque JSON del §2.1 tiene los 86 términos; 85 son idénticos al escaneo y el restante quedó con el valor del escaneo. Corrige KT0/(P/D) de 0,38 a **0,40**, J_T0 de 1,05·P/D a **1,09–1,10·P/D** y FOM de 0,60 a **0,55 con P/D 1,0**. Prueba: B3-50, P/D 1,0, J 0,5 → KT 0,2451, KQ 0,03863, η₀ 0,505.
- **La hélice de fueraborda de 7,8″ es mala para crucerear a 6 km/h.** Da η₀ = 0,42 a 1370 rpm. La 10x8 da 0,49 y la 11x8 da 0,52 (−6 % de energía contra la 10x8 y −20 % contra la 7,8″). Si el calado lo permite (punta ≤ 380 mm), una B3-50 de 0,30–0,34 m con P/D 0,8 a 530–585 rpm da **η₀ 0,56–0,58 (+15 %)**, con reducción ≈ 5:1.
- **Aplicar la corrección de escala y rugosidad ITTC-78 de Holtrop:** η₀ −7 % en la 10x8 (P_D en crucero 507 → 545 W). La hélice trabaja a Rn = 5,7–7,7·10⁵, por debajo de los 2·10⁶ de la serie. → `efficiency_factor` entre 0,93 y 0,98 en lugar de 1,0.
- **Corregir `burrill_tau_limit`.** El ajuste 0,3σ^0,6 sobreestima el τ_c admisible en +15 % (σ = 1), +51 % (σ = 2) y +81 % (σ = 3) frente a la curva de 5 %. Usar `np.interp` sobre la tabla del §3.2.
  - En crucero y a 8 km/h, la 10x8 queda en 0,70–0,77 del límite: bien.
  - En punto fijo, τ_c = 0,38 supera incluso la curva de 10 % (0,37) en cualquier B3-50 con P/D 0,8. Es esperable algo de cavitación o ventilación arrancando a fondo. Keller no pone objeción (AE/A0 mín 0,26–0,31 < 0,5).
- **El ensayo de remolque tiene que medir R(v) total.** Prohaska no vale porque el espejo va mojado (ITTC). La ΔC_F de la ITTC-78 da **negativa** con L = 2 m. (1+k) puede estar en cualquier punto entre 1,0 (ITTC, lanchas) y ≈1,47 (Holtrop "pram", extrapolado). Ensayar a 2–8 km/h con **profundidad ≥ 1,5 m**.
- **El espejo sumergido aporta 40 N de los 134 N a 6 km/h (30 %).** Según la fórmula, no se ventila por debajo de 24,5 km/h, y Holtrop reconoce que hay pocos datos. Bajar la inmersión del espejo (carga hacia proa; hoy el bote va a 1,55 veces la placa de capacidad, con calado de 0,196 m) es la reducción de R más barata. A_T −25 % → R_TR −20 % aproximadamente.
- **Gerr confirma que el casco está en el muro de resistencia.** Con DL = 1010, SLR_máx sale 0,96 y se aplica el piso de 1,34: **6,4 km/h** sin planear. El crucero está al 94 %. Su fórmula de potencia (795 W al eje a 6 km/h) sobreestima 1,5–2 veces: usarla solo como techo.
- **Savitsky (planeo) no aplica.** Con Fn∇ ≤ 1,31 y C_V ≤ 1,09 a 12 km/h, y según Savitsky 2003 un casco de planeo tiene *más* resistencia hasta SLR 3, mientras que 12 km/h es SLR 2,53. Además, las curvas R/Δ típicas de Savitsky subestiman este casco a la mitad. Esto respalda bajar la meta de "8–12 km/h" a **8–9 km/h**.
- **Agua poco profunda:** con h = 0,6 m a 8 km/h, Frh = 0,92, cerca del crítico. Con h = 1 m es 0,71, en el límite de validez. En los bajos (< 1 m), ir a ≤ 6 km/h (Frh ≤ 0,69 con h = 0,6 m).
- **Eje a 25°:** el empuje horizontal baja 9,4 % y aparecen 72 N verticales en crucero. La carga de las palas fluctúa ≈ ±17 % una vez por vuelta. Los únicos datos llegan a 12°, donde no hay pérdida de η. → Subir `blade_rate_amplitude_frac` de 0,10 a **0,15–0,20** para fatiga, y estudiar ψ = 15–20° (con 15°, +6,6 % de empuje horizontal) si el calado lo permite.
- **Velocidad crítica:** con eje de Ø16 de 316, el tramo biapoyado da 7 400 rpm con 0,5 m, 5 100 rpm con 0,6 m, 2 900 rpm con 0,8 m y **1 850 rpm con 1,0 m**. La hélice gira a ≤ 1 230 rpm. → **Tramo entre bujes ≤ 0,6 m.** El voladizo de la hélice (≤ 100 mm) no limita (> 16 000 rpm).
- **Pasador de corte:** 6061-T6 de **Ø3 mm** en eje de 16 mm corta a 21–23 N·m, unas 2,2 veces el par en punto fijo (9,7–10 N·m). La alternativa es 316 de Ø2 mm (19 N·m). No usar latón. En crucero trabaja a 53 MPa, casi en el límite estimado de fatiga en corte (56 MPa), así que hacen falta repuestos.
- **El aro protector (holgura 2,4 %D) no es una tobera.** Los datos de holgura muestran −20 % de empuje (de 0,3 a 2,0 %D) y FM −25 % con 2 %D. Dejar `bollard_gain_frac = 0` y usar `thrust_loss_frac` de 0,10–0,20. Una 19A útil (+26–30 % en punto fijo) pediría holgura ≤ 1,3 mm, inviable con arena.
- **Térmico:** la resistencia del cobre sube 23,6 % a 80 °C. Recalcular las pérdidas del motor con R(T_caliente). El VESC limita por defecto desde 85 °C (motor y MOSFET), por debajo de los 120 °C de `inputs.yaml`. R_th = 0,45 K/W no está verificado: medirlo con el método de resistencia. El ESC pierde ≈ 15 W en crucero contra 19 W en `sizing`: está bien.
