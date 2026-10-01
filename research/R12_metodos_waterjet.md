# R12 — Métodos para dimensionar el waterjet inboard (impulsor, estator, tobera, toma, cavitación, planeo, cargas)

**Fecha:** 2026-10-01.

**Proyecto (nuevo alcance):** waterjet inboard eléctrico para un jet boat de 2,30 × 0,80 m, 1 piloto, Δ = 150–230 kg, 5 kW continuos / 7,2 kW máx., impulsor axial Ø108 a ~4500 rpm, tobera Ø72, objetivo ≥ 30 km/h y mucho uso a 5 kn (9,26 km/h). Se va a dimensionar con Python y modelar en build123d.

**Qué NO repite este informe** (ya verificado; se cita):
- `research/R03_proyectos_jet_ducted_efoil.md`: jets impresos (J1–J4, PRO-JET), propulsor vs jet, holgura de jets impresos, ~30 cm de luz bajo el jet.
- `research/R09_metodos.md`: Savitsky 1964 (ecuaciones), regímenes de Savitsky 2003, ITTC-57, pasador de corte (fórmula y τ_u), fatiga, velocidad crítica de eje.
- `research/R10a_toma_waterjet.md`: geometría de toma enrasada (θ ≈ 25–30°, labio, 2,9 D × 1,2 D, ITTC 23rd), IVR, NPSH_A (Bulten ec. 2.64), n_ωs = 3,5–4,0, cebado, rejilla, pruebas.
- `research/R10b_auditoria_plano_jorge.md` §4.4–4.7: openplaning para 18 cascos, empuje por cantidad de movimiento, Ω_s 4,1–4,8, σ en la punta, eje Ø20, empuje axial de referencia.

**Etiquetas:**
- [VERIFICADO: Tn, pág./ec.] = leído en la fuente Tn de la §11, abierta en esta sesión.
- [VERIFICADO: R0x …] = verificado en otro informe del repo (no reabierto).
- [CALCULADO] = salida del script `r12_calc.py` (§12, ejecutado; la salida está copiada).
- [ESTIMADO: base] = memoria técnica o deducción, **no** verificado.

**Constantes del script** (de `inputs.yaml`): ρ = 1013 kg/m³, ν = 1,35·10⁻⁶ m²/s, p_v = 2984 Pa (24 °C, peor caso), p_atm = 101 325 Pa, g = 9,81 m/s².

---

## 0. Resumen ejecutivo (lo que cambia el diseño)

1. **Relación de cubo: subir de 0,40 a 0,45–0,50.** Con torbellino libre y ν = 0,40, el cubo queda sobrecargado: giro de 31°, w₂/w₁ = 0,62 y factor de difusión D_f = 0,60, o sea solidez necesaria de 4,3 en el cubo para D_f ≤ 0,45 [CALCULADO]. Con ν = 0,50: giro de 16°, w₂/w₁ = 0,71 y s_cubo ≥ 1,2 [CALCULADO]. Alternativa: mantener 0,40 con torbellino forzado (menos trabajo en el cubo) [VERIFICADO como práctica: T2 p.54, "most of the designs are of the forced vortex type"].
2. **El punto de diseño es un axial "de alta Ω_s": Ω_s ≈ 5,0** (φ_B = 0,089, ψ_B = 0,023 a 30 km/h) [CALCULADO]. Bulten: axiales > 2,4, waterjets típicos 2–3 [VERIFICADO: T1 p.23–24]. Funciona, pero el η esperable es menor: η_máx ≈ **0,76** por la correlación de Bulten (Q = 0,053 m³/s, Ω_s = 5) [CALCULADO con T1 ec. 2.26]; con holgura y rugosidad reales, **0,65–0,75** [ESTIMADO].
3. **Cavitación: el límite real es S ≈ 3,5 (diseño) a 4,0 (comercial).** A punto fijo, 4500 rpm (≈ 4,3 kW al eje) da S = 3,3. La potencia al eje admisible es **≈ 4,8 kW con S ≤ 3,5 y ≈ 6,3 kW con S ≤ 4,0 hasta ~10 km/h**, y sube a 6,2 / 8,2 kW a 30 km/h [CALCULADO, §5]. → **7,2 kW eléctricos a punto fijo están en S ≈ 4,0: al borde de la ruptura**. Ley de control: limitar potencia (o rpm) en función de la velocidad (tabla §5.4).
4. **Rejilla:** la pérdida por barras (Kirschmer) es chica en la toma corregida (11–46 mm de columna a punto fijo, contra NPSH_A ≈ 10 m) [CALCULADO]. Lo que importa es **dónde** va: en el plano del fondo, cubriendo toda la abertura **a proa del impulsor** (de ~1 D a ~3,8 D por delante de su cara). Respuesta a Jorge en §4.4.
5. **Resistencia:** openplaning (Savitsky 1964) da **R = 327 N, τ = 6,37°** para Δ 200 kg, b 0,6 m, β 10°, LCG 1,0 m a 8,33 m/s [CALCULADO, ejecutado, §6.2]. Para la joroba y los 5 kn hay una regresión aplicable: **Mercier–Savitsky 1973** (Fn∇ 1–2, L/∇^⅓ 2–12) [VERIFICADO rangos: T9]; coeficientes tomados de una transcripción secundaria [VERIFICADO: T10]. Da **R/Δ ≈ 0,12–0,17 en la joroba (12–14 km/h)** y **0,04–0,10 a 5 kn** según el casco [CALCULADO]. A 5 kn el jet de diseño necesitaría **0,55–1,55 kW eléctricos** (autonomía 1,9–5,5 h con 3 kWh útiles) [CALCULADO].
6. **Piedras:** la energía cinética del rotor a 4500 rpm (~490 J [CALCULADO con J ESTIMADO]) produce pares de 300–2800 N·m si el impulsor se traba en 90–10°: **el límite de corriente del ESC no protege**; hace falta un fusible mecánico (pasador o limitador de par) en el cubo, de ~25–45 N·m (§7.6).
7. **Datos de referencia muy cercanos:** Lampuga Air (jetboard eléctrico de **2,30 × 0,75 m**, ≤ 10 kW, 50,4 V, 3,6 kWh, hasta 50 km/h, ~55 kg de equipo) [VERIFICADO: T12] y Mokai ES-Kape (jet de 7 hp, 75 kg, 3,4 m, 32 km/h) [VERIFICADO: T14]. Ver §8.

---

## 1. Tabla para implementar (fórmula → coeficiente → fuente)

| # | Magnitud | Fórmula / valor | Validez | Etiqueta |
|---|---|---|---|---|
| 1 | Coef. de caudal (Bulten) | φ_B = Q/(ΩD³) | Ω en rad/s | [VERIFICADO: T1 ec. 2.15] |
| 2 | Coef. de altura (Bulten) | ψ_B = gH/(ΩD)² | — | [VERIFICADO: T1 ec. 2.16] |
| 3 | Coefs. de Brennen | ψ = gH/(Ω²R_T²) = 4ψ_B; φ₁ = Q/(A₁R_TΩ) | A₁ anular | [VERIFICADO: T2 ec. 2.16–2.17] |
| 4 | Velocidad específica | Ω_s = ΩQ^½/(gH)^¾ = φ_B^½/ψ_B^¾; N_US = 2734,6·Ω_s; n_q (rpm, m³/s, m) = 52,9·Ω_s | — | [VERIFICADO: T1 ec. 2.18–2.19; T2 p.25–26 (2734,6)]; 52,9 [CALCULADO: 60/(2π)·g^¾] |
| 5 | Tipo por Ω_s | axial > 2,4; radial < 1,0; waterjets "around 2.0–3.0" | — | [VERIFICADO: T1 p.23–24] |
| 6 | Potencia específica | P* = P/(ρΩ³D⁵) = φψ/η | — | [VERIFICADO: T1 ec. 2.21–2.22] |
| 7 | η máx. esperado | η = 0,95 − 0,05/∛(Q/1 m³/s) − 0,125·[log₁₀ Ω_s]² | Bombas convencionales; Q 0,1–10 m³/s en la figura | Ecuación [VERIFICADO: T1 ec. 2.26]; lectura ∛ y log₁₀ [ESTIMADO: coherente con la Fig. 2.4 de T1] |
| 8 | Altura del sistema | H_R = (1+φ_n)V_j²/2g − (1−ε)V_in²/2g + h_j | — | [VERIFICADO: T1 ec. 2.56; R10a] |
| 9 | Pérdidas | φ_n (tobera) = 0,02; ε (toma) = 0,10–0,30 (0,20 típico) | — | [VERIFICADO: T1 p.38, Fig. 2.10–2.12] |
| 10 | η propulsivo | η_d = [(1−t)/(1−w)]·η_p·2μ(1−μ)/[(1+φ_n) − μ²(1−ε)], μ = V/V_j | óptimo μ = 0,65–0,75 | [VERIFICADO: T1 ec. 2.62, p.38] |
| 11 | Velocidad esp. de succión | S = ΩQ^½/(g·NPSH)^¾ | diseño waterjet 3,5; comercial ~4,0 | [VERIFICADO: T1 ec. 2.29; T2 ec. 5.8] |
| 12 | NPSH disponible | NPSH_A = (p_atm − p_v)/ρg + (1−ε)V_in²/2g − h_j | — | [VERIFICADO: T1 ec. 2.64; R10a] |
| 13 | Cavitación (número) | σ = (p₁ − p_v)/(½ρU_T²); S ↔ σ: S = [πφ₁(1−ν²)]^½ / [½(σ+φ₁²)]^¾ | U_T = ΩR_T; ν = R_H1/R_T1 | [VERIFICADO: T2 ec. 5.4, 5.9] |
| 14 | Incidencia, triángulos | α = β_b1 − β₁; β₁ = atan(c_m/Ωr) (desde la tangencial) | sin pre-giro | [VERIFICADO: T2 ec. 2.1, 2.18] |
| 15 | Paso constante | β_b(r) = atan(R_T·tan β_bT/r) | hélice de paso cte. | [VERIFICADO: T2 ec. 2.7] |
| 16 | Solidez | s = c/h = Z c/(2πr) | — | [VERIFICADO: T2 ec. 2.10] |
| 17 | Desviación (Constant) | δ = 0,26·θ_c/s^½ | regla temprana | [VERIFICADO: T2 ec. 3.19] |
| 18 | Factor de difusión (Lieblein) | D_f = 1 − w₂/w₁ + (c_u2 − c_u1)/(2 s w₁) | — | [VERIFICADO: T2 ec. 3.20] ; límite D_f ≤ 0,45 [ESTIMADO] |
| 19 | Torbellino libre / forzado | libre: r·c_u = cte (c_m uniforme); forzado: c_u ∝ r (c_m decrece con r) | equilibrio radial | [VERIFICADO: T2 ec. 4.2, p.54] |
| 20 | Rejilla (Kirschmer) | Δh = β·(t/e)^(4/3)·sin α·v₁²/2g; β = 2,42 (rect.), 1,83 (semicírc. aguas arriba), 1,79 (circular), 1,67 (semicírc. ambos lados) | flujo normal; Δh = diferencia de nivel, no pérdida de energía | [VERIFICADO: T7 ec. 8; T8] |
| 21 | Preplaneo | Mercier–Savitsky: R_T/Δ = Σ a_j(Fn∇)·término_j(X,U,Z,W) | Fn∇ 1–2; iE 10–55°; L/∇^⅓ 2–12; L/B 2–14 | Rangos [VERIFICADO: T9]; coeficientes [VERIFICADO: T10, transcripción secundaria] |
| 22 | Planeo | Savitsky 1964 vía openplaning | C_V 0,6–13; τ 2–15°; λ ≤ 4 | [VERIFICADO: T11 líneas 504–519] |
| 23 | Reversa | hasta 60 % del empuje avante (HamiltonJet) | jets grandes | [VERIFICADO: T15] |
| 24 | Afinidad | Q ∝ nD³; H ∝ n²D²; P ∝ n³D⁵ | geometría y Re similares | [VERIFICADO: T1 ec. 2.15–2.22; T2 §1.4] |

---

## 2. Impulsor axial

### 2.1 Punto de diseño y velocidad específica

Hipótesis del punto de diseño (30 km/h): P_eje = 4,3 kW (5 kW × 0,91 motor × 0,97 ESC × 0,98 mec., como R10b), η_p = 0,75, φ_n = 0,02, ε = 0,20, w = 0,05, tobera Ø72, D = 108 mm, 4500 rpm [ESTIMADO: η_p y w; resto VERIFICADO en T1/R10b].

| Magnitud | Valor [CALCULADO] |
|---|---|
| V_j / Q / H / T | 12,95 m/s / 52,7 L/s / 6,16 m / 269 N |
| μ = V/V_j | 0,644 (óptimo de Bulten 0,65–0,75 [VERIFICADO: T1 p.38]) |
| η_d/η_p (ec. 2.62, η_hull = 1) | 0,666 → η_d = 0,50 |
| φ_B / ψ_B | 0,0888 / 0,0233 |
| ψ (Brennen) / φ₁ (ν 0,40 / 0,50) | 0,093 / 0,269 / 0,301 |
| Q* = Q/(nD³) (n en rev/s, convención AxWJ-2) | 0,558 |
| **Ω_s** / n_q / N_US | **4,99** / 264 / 13 655 |
| U_T | 25,4 m/s |
| P/D² | 369 kW/m² (Bulten grafica 3000, 5000 y 7000 kW/m² para jets de un ferry rápido, y la densidad admisible crece con la velocidad [VERIFICADO: T1 Fig. 2.13–2.14, p.42–44]) |

**Bombas de referencia de escala parecida** (abiertas en esta sesión):

| Bomba | D | rpm | Z rotor / estator | Holgura | Ω_s | φ_B | ψ_B | Dato | Fuente |
|---|---|---|---|---|---|---|---|---|---|
| Modelo de Chen et al. 2025 | 180 mm | 1450 | 5 / 9 | 1 mm (0,56 % D) | 4,24 | 0,124 | 0,036 | H 2,76 m; η_p 0,819 (CFD); T 304 N; tobera Ø100 | [VERIFICADO: T3]; Ω_s, φ, ψ [CALCULADO] |
| Bomba axial de waterjet (PMC11516003) | 300 mm | 1450 | 6 / 11 | 0,001 D | 2,76 | 0,112 | 0,060 | Q 0,46 m³/s; H 12,7 m; NPSH_R(3 %) entre 6,27 y 8,18 m → **S = 3,8–4,7** | [VERIFICADO: T4]; Ω_s, S [CALCULADO] |
| ONR AxWJ-2 (modelo 12") | 305 mm | 2000 | 6 / 8 | — | — | Q* diseño 0,85 (φ_B = 0,135) | — | sin estator la bomba da ~20 % menos presión | [VERIFICADO: T5] |
| Bomba Peerless (Brennen Fig. 7.3) | 203 mm | ~1500 | 3 | — | — | φ₂ = 0,171 | — | η máx ≈ 85 %; ν = 0,45; s_punta = 0,344; β_bT = 11,9° | [VERIFICADO: T2 p.117–118] |
| Axial de Oshima (Brennen Fig. 7.4) | — | — | 4 | — | — | — | — | ν = 0,483; s = 0,68; β_bT ≈ 18° | [VERIFICADO: T2 p.119] |
| R10b (este jet, 0–30 km/h) | 108 mm | 4500 | — | 0,5–0,8 mm | 4,1–4,8 | — | — | — | [VERIFICADO: R10b §4.6] |

**Lectura.** El Ω_s ≈ 5 de este jet está en el extremo axial. Para bajar Ω_s (más η y mejor succión) habría que bajar rpm o subir H (tobera más chica, peor η_jet). Con la tobera Ø72 el μ ya está en el óptimo de Bulten, así que **mantener Ø72 / 4500 rpm** y aceptar η_p ≈ 0,70–0,75 [ESTIMADO].

### 2.2 Rendimiento esperado y escala (Ø ~100 mm)

- Bulten ec. 2.26 con Q = 0,053 m³/s y Ω_s = 5,0 → **η_máx = 0,756** [CALCULADO]. La misma fórmula da 0,90 para Q = 1 m³/s y Ω_s = 1 ("Achievable pump efficiencies around 90% for large pumps") [VERIFICADO: T1 p.25].
- Reynolds: Brennen (Balje) corrige η a Re = 2ΩR_T²/ν = 10⁸ [VERIFICADO: T2 Fig. 2.8–2.9, p.28]. Este jet: Re = 2·471·0,054²/1,35·10⁻⁶ = **2,0·10⁶** [CALCULADO], 50 veces menos: hay pérdida adicional por Reynolds que la figura cuantifica pero el texto no [la curva no es legible como texto → no verificado].
- Escala tipo Moody, (1 − η₂)/(1 − η₁) = (D₁/D₂)^0,2 [ESTIMADO: memoria técnica]: de AxWJ-2 (η modelo 0,90 en 305 mm, dato del resumen del buscador, no abierto) a 108 mm → 0,88. Es optimista: no incluye holgura relativa mayor ni rugosidad de fabricación casera.
- Modelo de 180 mm con holgura de 1 mm: η_p = **0,819** por CFD [VERIFICADO: T3, Tabla 6].
- **Rango para `sizing`: η_p = 0,65 (fabricación casera, holgura 0,8 mm) – 0,75 (impulsor mecanizado, holgura ≤ 0,4 mm) – 0,80 (techo)** [ESTIMADO con las anclas anteriores].

### 2.3 Relación de cubo (hub/tip)

Torbellino libre (U·c_u2 = gH/η_h constante), η_h = 0,85, Q y H del punto de diseño [CALCULADO: `r12_hub.py`]:

| ν = d/D | c_m m/s | Cubo: β₁→β₂ (giro) | w₂/w₁ cubo | s_mín cubo (D_f ≤ 0,45) | s_mín medio | s_mín punta |
|---|---|---|---|---|---|---|
| 0,35 | 6,56 | 36,4 → 82,0 (45,6°) | 0,60 | 7,4 | 0,46 | 0,15 |
| 0,40 | 6,85 | 33,9 → 65,0 (31,1°) | 0,62 | 4,3 | 0,40 | 0,15 |
| 0,45 | 7,21 | 32,2 → 54,0 (21,8°) | 0,66 | 2,1 | 0,36 | 0,15 |
| **0,50** | 7,67 | 31,1 → 47,1 (16,0°) | **0,71** | **1,2** | 0,32 | 0,15 |
| 0,55 | 8,25 | 30,5 → 42,8 (12,3°) | 0,75 | 0,8 | 0,28 | 0,15 |

- Criterios: D_f ≤ 0,45 y w₂/w₁ ≥ 0,70 (de Haller) [ESTIMADO: límites usuales de cascadas; la definición de D_f sí está VERIFICADA en T2 ec. 3.20].
- **Recomendación: ν = 0,50 (cubo Ø54)** [ESTIMADO con el cálculo]. También deja lugar para eje Ø20, chaveta/pasador y tuerca. La referencia Peerless usa 0,45 y la de Oshima 0,483 [VERIFICADO: T2 p.117–119].
- Con ν = 0,50 la sección anular es 68,7 cm² y A_tobera/A_anular = 0,59 [CALCULADO].

### 2.4 Número de álabes y solidez

| Referencia | Z rotor | Solidez | Fuente |
|---|---|---|---|
| Waterjets de modelo | 5 (Chen), 6 (AxWJ-2, PMC11516003, Bulten) | — | [VERIFICADO: T3, T4, T5, T1 p.144] |
| Axial Peerless | 3 | 0,344 en la punta | [VERIFICADO: T2 p.118] |
| Axial Oshima | 4 | 0,68 | [VERIFICADO: T2 p.119] |
| Inductores cavitantes | 3–4 | óptimo ≈ 1,5; con s < 1 cae la succión | [VERIFICADO: T2 p.128–129] |
| Flujo potencial | — | con s > ~1 la salida sigue al álabe (ψ₀ → 1) | [VERIFICADO: T2 p.41] |

**Recomendado para Ø108:**
- **Z = 5** (4 si se fabrica a mano; 6 si se quiere más solidez sin cuerdas largas) [ESTIMADO].
- Solidez: **cubo 1,2–1,4; medio 0,9–1,0; punta 0,6–0,8** [ESTIMADO, chequeado con D_f del §2.3].
- Con Z = 5 y ν = 0,50: paso 33,9 / 50,9 / 67,9 mm (cubo/medio/punta) → **cuerdas 44 / 48 / 48 mm** con s = 1,3 / 0,95 / 0,70 [CALCULADO].
- Re de cuerda en la punta ≈ 0,9·10⁶ [CALCULADO]: régimen de transición; la rugosidad de pala importa.

### 2.5 Triángulos de velocidad y ángulos de pala (ν = 0,50, Z = 5, sin pre-giro, incidencia 3°)

Convención de Brennen: β medido **desde el plano perpendicular al eje (dirección tangencial)** [VERIFICADO: T2 p.18–19]. En CAD: ángulo de calado desde el eje = 90° − β.

| Sección | r mm | U m/s | c_u2 m/s | β₁ flujo | β₂ flujo | **β_b1 pala** | **β_b2 pala** | δ (Constant) | D_f | Ángulo de entrada al estator α₃ (desde la tangencial) |
|---|---|---|---|---|---|---|---|---|---|---|
| Cubo | 27,0 | 12,7 | 5,58 | 31,1° | 47,1° | **34,1°** | **50,9°** | 3,8° | 0,44 | 53,9° |
| Medio | 40,5 | 19,1 | 3,72 | 21,9° | 26,5° | **24,9°** | **27,1°** | 0,6° | 0,26 | 64,1° |
| Punta | 54,0 | 25,4 | 2,79 | 16,8° | 18,7° | **19,8°** | **18,2°** | −0,5° | 0,18 | 70,0° |

[CALCULADO: `r12_calc_nu50.py` = `r12_calc.py` con ν = 0,50 y s = 1,30/0,95/0,70.]

Notas de diseño:
- **Incidencia de 2–4°**, no cero: en inductores "designed to function at an incidence angle of a few degrees… to ensure suction surface cavitation" [VERIFICADO: T2 p.124]. Con 3°, β_b2 < β_b1 en la punta (la punta casi no gira el flujo: perfil de poca curvatura con calado).
- Desviación por la regla de Constant (δ = 0,26 θ_c/√s) [VERIFICADO: T2 ec. 3.19], iterada. Es una regla vieja; Brennen dice que la superaron las correlaciones de Lieblein [VERIFICADO: T2 p.42]. Usar como primera aproximación y corregir con ensayo o CFD.
- **Ley de torbellino:** el cálculo es de torbellino libre (H uniforme en el radio). Brennen: en bombas "most of the designs are of the forced vortex type" y un vórtice forzado con c_m uniforme implica palas helicoidales de paso constante (ec. 2.7) [VERIFICADO: T2 p.54]. Para fabricar: **paso constante en la entrada** (fácil de mecanizar) y torcer la salida según la tabla [ESTIMADO].
- **Borde de ataque:** "the sharper the leading edge the better the hydraulic performance under both cavitating and non-cavitating conditions… very thin leading edges may flutter" [VERIFICADO: T2 p.132].

### 2.6 Espesor de pala

- Carga: par 9,1 N·m (diseño) a 13,5 N·m (7,2 kW eléctricos) [CALCULADO]. Fuerza tangencial media por pala F_t = τ/(Z·r_m) = **45 N** (Z = 5, r_m = 40,5 mm) a 4,3 kW [CALCULADO].
- Raíz como placa en voladizo (M = F_t·h/2, W = c·t²/6): **t_mín estático ≈ 1,0–1,2 mm** en 316 o Al 6061-T6 [CALCULADO; σ_adm 60–90 MPa ESTIMADO].
- **Espesor de uso** (fatiga por paso de álabes, golpes, erosión por cavitación, mecanizado): **t/c ≈ 8–10 % en el cubo (3,5–4,5 mm) y 4–6 % en la punta (2–3 mm)**, borde de ataque de radio ~0,3–0,5 mm [ESTIMADO: memoria técnica].
- R10b ya mostró que una pala de PETG no cierra (7,2 MPa contra 2,7 MPa admisibles) [VERIFICADO: R10b §4.6].

### 2.7 Holgura de punta

Lo verificado:
- Bulten: "The distance between the impeller tip and the seatring is therefore very small, about 1-2% of the diameter" [VERIFICADO: T1 p.66, texto literal tras pdftotext; 1–2 % de D = 1,1–2,2 mm aquí, que parece alto: posible pérdida del signo ‰ en la extracción].
- Modelos de waterjet: 1 mm en Ø180 (0,56 % D) [VERIFICADO: T3]; 0,001 D [VERIFICADO: T4]; un estudio CFD barrió 0,1–0,7 % D y concluyó que la holgura "has a great impact on the performance" [VERIFICADO: T16, resumen].
- Brennen (inductores): el rendimiento no cavitante "is relatively insensitive to the clearance unless the latter is increased above 2% of the chord"; óptimo de cavitación ≈ 1 % de la cuerda (o de la altura de pala) [VERIFICADO: T2 p.95–96, p.129–131].
- Rotores carenados (aire): de 0,3 a 2,0 % D, −20 % de empuje estático [VERIFICADO: R09 §4, S24].

**Pérdida de η por holgura** (no encontré el dato cuantitativo para bombas en fuente abierta): **Δη ≈ 1,5–3 puntos por cada 1 % de la altura de pala** por encima de ~0,5 % [ESTIMADO: memoria técnica de turbomáquinas axiales]. Con altura de pala h = 27 mm (ν = 0,50):

| Holgura | % D | % h | Δη estimado |
|---|---|---|---|
| 0,3 mm | 0,28 % | 1,1 % | 1–2 puntos |
| 0,5 mm | 0,46 % | 1,9 % | 2–4 puntos |
| 0,8 mm | 0,74 % | 3,0 % | 4–7 puntos |
| 1,5 mm | 1,4 % | 5,6 % | 8–15 puntos |

[CALCULADO % D y % h; Δη ESTIMADO]. → Objetivo: **0,3–0,4 mm diametral/2 con anillo de desgaste torneado**, revisar con galgas; reemplazar el anillo si pasa de 0,8 mm.

### 2.8 Ley de afinidad (para barridos de rpm)

Q₂/Q₁ = n₂/n₁; H₂/H₁ = (n₂/n₁)²; P₂/P₁ = (n₂/n₁)³ (misma bomba) [VERIFICADO: T1 ec. 2.15–2.22]. Brennen: la densidad de potencia escala como ρD²Ω³ y σ ∝ 1/(ΩD)²: achicar la bomba sube la velocidad de punta y la cavitación [VERIFICADO: T2 p.15]. Viscosidad: "Since hydraulic losses do scale differently, additional empirical relations are used" [VERIFICADO: T1 p.23] → no extrapolar η más de ×2 en rpm sin corregir.

---

## 3. Estator (difusor) y tobera

### 3.1 Número de álabes del estator

- Waterjets abiertos en esta sesión: 5/9 [T3], 6/7 [T1], 6/8 [T5], 6/11 [T4] (rotor/estator) [VERIFICADO].
- Bulten: con 6/7 la fuerza de interacción "counter rotating at the blade passing frequency… can possibly lead to backward whirling" [VERIFICADO: T1 p.144]. Brennen: con Z_S = Z_R + 1 siempre aparece una perturbación a −Z_RΩ; las máquinas se diseñan cuidando los factores comunes de Z_R y Z_S para evitar subarmónicos [VERIFICADO: T2 p.181–184].
- **Recomendado: Z_R = 5, Z_S = 7** (coprimos, Z_S − Z_R = 2) o 5/9 como el modelo de Chen [ESTIMADO; regla "evitar |ν_S·Z_S − ν_R·Z_R| ≤ 1 en los primeros armónicos" = memoria técnica (Gülich), no verificada].

### 3.2 Ángulos y solidez del estator

- Ángulo de entrada (desde la tangencial) = α₃ = atan(c_m/c_u2) + incidencia ≈ **54° (cubo) / 64° (medio) / 70° (punta)** con ν = 0,50 [CALCULADO, §2.5]; incidencia 0–3° [ESTIMADO].
- Salida: axial (90°) **más** la desviación: sobre-girar 3–8° para que el flujo salga axial [ESTIMADO con la regla de Constant aplicada al estator].
- El estator suele ir en un cono convergente hacia la tobera (el cubo se afina a cero) [VERIFICADO como geometría en T3: "The hub diameter tapers to zero in the nozzle"].
- Solidez 1,0–1,5 [ESTIMADO]. Importancia: en AxWJ-2, quitar el estator baja ~20 % la presión entregada [VERIFICADO: T5].
- Luz rotor-estator: PRO-JET tuvo que llevarla a 3 mm por roces de piezas impresas [VERIFICADO: R03 S4]; recomiendo ≥ 0,1·D = 10–15 mm para bajar la excitación de paso de álabes [ESTIMADO].

### 3.3 Tobera

- Pérdida: **φ_n = 0,02** (Bulten) [VERIFICADO: T1]; R10b usó K_n = 0,03 [ESTIMADO allí]. Usar 0,02–0,04.
- El diámetro de tobera fija el punto de operación (la curva del sistema corta la curva de la bomba): "the main role of a nozzle is to act as a valve and ensure that the impeller working under the best efficiency point" [VERIFICADO: T6 p.51].
- Contracción: D_n/D = 0,667 aquí (A_n/A_anular = 0,59 con ν 0,5) [CALCULADO]; modelo de Chen 100/180 = 0,556 [VERIFICADO: T3].
- **Vena contracta:** ITTC pide estimar "the contraction coefficient to be applied to the calculated nozzle velocity" y su ubicación [VERIFICADO: T17 p.12]; Scherer et al. encontraron poca variación de presión estática en la vena contracta [VERIFICADO: T18 p.396]. No encontré un valor numérico de C_c para toberas de waterjet → **C_c = 0,97–1,00** con tramo final cilíndrico de 0,3–0,5 D_n [ESTIMADO].
- Ángulo de cono 8–12° (semiángulo) y largo 1–1,5 D desde el estator [ESTIMADO].
- **Prohibido:** expansión después de la tobera (el plano de Jorge pierde ~50 % de la altura dinámica) [VERIFICADO: R10b H3].

---

## 4. Toma (complementa R10a)

### 4.1 Lo que ya está en R10a (no se repite)
Rampa 25–30°, curvatura continua, labio redondeado, abertura 2,5–2,9 D × 1,2 D, ancho de captación 1,5–1,9 ×, IVR (ITTC) y sus límites (< 0,65 separación en el techo; > 1,4 riesgo en el labio), 2 m sin apéndices (escalado 0,5–1 m), escalones ≤ 2 mm, altura del eje ≤ calado − 20 mm.

### 4.2 Pérdida de la toma en función de IVR (modelo para el script)

- Bulten usa ε constante (0,10/0,20/0,30) [VERIFICADO: T1 Fig. 2.10].
- Chen et al.: el coeficiente de recuperación de presión total "exhibits an initial rise followed by a decline" al subir IVR; con IVR ≤ 0,7 hay separación (que los generadores de vórtice corrigen) [VERIFICADO: T3].
- Jiao 2019 (solo el resumen del buscador, **no abierto**): óptimo de 35°, largo 6,38 D₀, IVR óptimo 0,69–0,87.
- **Modelo propuesto** [ESTIMADO]: ε(IVR) = ε₀ + k_s·max(0, 0,7 − IVR)² + k_l·max(0, IVR − 1,1)², con ε₀ = 0,15–0,20, k_s ≈ 1, k_l ≈ 0,2. A punto fijo (V = 0) usar en su lugar una pérdida de conducto K_d·V_garganta²/2g con K_d = 0,2 (como R10a).

### 4.3 Rejilla: pérdida por barras

Kirschmer: Δh = β·(t/e)^(4/3)·sin α·v₁²/2g [VERIFICADO: T7 ec. 8]. Ojo: Kirschmer da la **diferencia de nivel**, no la pérdida de energía; con variación de velocidad apreciable sobreestima [VERIFICADO: T7 p.10]. Otras correlaciones con relación de bloqueo p: Raynal (β = 2,89 rectangular, 1,70 hidrodinámico), Tsikata (β_T = 3,4 / 2,23 / 1,93) [VERIFICADO: T7 Tabla 1].

Aplicado a la toma corregida (abertura bruta 0,0368 m², flujo de punto fijo 46,7 L/s → v_n = 1,27 m/s normal al plano de la rejilla, α = 90°) [CALCULADO]:

| Barras | t / e (mm) | K | Δh |
|---|---|---|---|
| Rectangular (β 2,42) | 4 / 12 | 0,56 | 46 mm |
| Rectangular | 4 / 18 | 0,33 | 27 mm |
| Semicircular aguas arriba (1,83) | 4 / 18 | 0,25 | 20 mm |
| Circular (1,79) | 3 / 20 | 0,14 | 12 mm |
| Semicircular ambos lados (1,67) | 3 / 20 | 0,13 | 11 mm |
| Semicircular ambos lados | 5 / 25 | 0,20 | 16 mm |

- Contra NPSH_A ≈ 10 m, la rejilla corregida resta **0,1–0,5 %**: no limita la cavitación [CALCULADO]. Con la rejilla de 120 × 90 del plano (v ≈ 5,2 m/s) la pérdida era 16 veces mayor (R10a).
- **Luz recomendada 15–20 mm, barras de 3–4 mm perfiladas** (nariz redonda, cola afinada; Luo 2021: la rejilla perfilada es mejor [VERIFICADO: R10a S10]). Luz < paso mínimo entre álabes en la punta del rotor menos la holgura: entre palas hay ~68 mm de paso en la punta y ~34 mm en el cubo con Z = 5 [CALCULADO], así que 20 mm detiene lo que trabaría el rotor contra el estator [ESTIMADO]. Para dedos (seguridad) ver R10a §0.
- A velocidad, las barras son un apéndice dentro de la capa límite: arrastre chico frente a 270 N [ESTIMADO, no calculado].

### 4.4 Dónde va la rejilla respecto del impulsor (respuesta a Jorge)

1. **En el plano del fondo, enrasada (escalón ≤ 2 mm), cubriendo toda la abertura de la toma** [VERIFICADO: R10a S5/S6].
2. **Toda la abertura está a proa de la cara del impulsor**: con la geometría de R10a, de **96 mm (labio) a 407 mm (tangencia de la rampa) por delante de la cara**, o sea **~0,9 D a ~3,8 D** [VERIFICADO: R10a §5.2 (CALCULADO allí)].
3. Barras **longitudinales** (proa-popa), para que las algas resbalen hacia el labio y se puedan limpiar con rastrillo desde el espejo [VERIFICADO como práctica: R10a S6 p.162; orientación ESTIMADA].
4. Distancia rejilla → cara del impulsor medida por el conducto ≥ ~1 D, para que las estelas de las barras se mezclen antes del rotor (excitación de paso de barras) [ESTIMADO].
5. **Detrás del impulsor (como en el plano) la rejilla queda del lado de descarga: no hay succión ahí.** Jorge tiene razón [VERIFICADO: R10a §1].

### 4.5 Transición rectangular → circular
- Área de la sección del conducto **monótonamente decreciente** desde la abertura hasta la garganta (R10a usa 1,15 → 1,0) y desde la garganta hasta el impulsor, sin escalones [ESTIMADO, coherente con R10a].
- En build123d: `loft` entre un rectángulo de esquinas redondeadas (r ≥ 0,15 × ancho) en la abertura y el círculo de la garganta, con guías tangentes a la curva del techo (polinomio de 5.º grado de la ITTC [VERIFICADO: R10a S3]).
- El eje cruza el techo del conducto: carenar el paso del eje con un "shaft fairing" de sección perfilada [ESTIMADO].

---

## 5. Cavitación, ruptura de empuje y límite de potencia a baja velocidad

### 5.1 Definiciones (no repetidas de R10a)
- NPSH_A (ec. 2.64 de Bulten) y S = ΩQ^½/(g·NPSH)^¾ [VERIFICADO: T1; R10a].
- Tres niveles: inicio σ_i, pérdida de 2–5 % de altura σ_a, ruptura σ_b; "σ_i can be an order of magnitude larger than σ_a or σ_b" [VERIFICADO: T2 p.80–81].
- S_a/S_b de bombas típicas: S_b = 1,6–4,7 (Tabla 5.1, McNulty & Pearsall) [VERIFICADO: T2 p.82]. La línea del Hydraulic Institute corresponde a S = 3,0, y "is more like S_a" (no garantiza ausencia de cavitación) [VERIFICADO: T2 p.82].
- Waterjet: diseño n_ωs = 3,5; comercial ≈ 4,0 [VERIFICADO: T1 p.26]. Bomba de waterjet de 300 mm: S(NPSH_R 3 %) = 3,8–4,7 [CALCULADO con T4].
- Ruptura de empuje: "Thrust breakdown occurs when the mass flow through the system collapses due to extreme cavitation"; banda entre la línea de 1 % de cavitación y la de ruptura; un jet chico (alta P/D²) queda sin margen en la joroba [VERIFICADO: T1 p.43–44, Fig. 2.14].
- Pérdida de altura empírica: ΔH = P(S)·NPSH [VERIFICADO: T2 ec. 7.21] (la curva P(S) es una figura, no texto).

### 5.2 σ en la punta
σ_T = (p₁ − p_v)/(½ρU_T²) con p₁ estática en la entrada [VERIFICADO: T2 ec. 5.4]. Este jet: σ_T = 0,24–0,30 entre 0 y 30 km/h a 4500 rpm [CALCULADO], dentro del rango de ruptura de bombas centrífugas citado por Brennen (0,1–0,4) [VERIFICADO: T2 p.117] → margen chico, coherente con R10b (0,28–0,35 con otra p_v).

### 5.3 Modelo usado (script §D)
- Curva de la bomba lineal ψ(φ) = ψ_d·[a − (a−1)φ/φ_d] con **a = ψ₀/ψ_d = 2,0** (sensibilidad con 2,6) [ESTIMADO] y η(φ) = η_d·[1 − (φ/φ_d − 1)²] [ESTIMADO].
- Sistema: ec. 2.56 con h_j = +0,05 m (punta del impulsor sobre la superficie en planeo y en reposo, peor caso de R10a) [ESTIMADO].
- Advertencia: con a = 2 la potencia a rpm fija queda casi constante en φ (máximo de φ·ψ en φ_d); una bomba axial real **sube la potencia al bajar el caudal**. Con a = 2,6 los límites cambian < 4 % [CALCULADO].

### 5.4 Resultado: potencia y empuje admisibles por cavitación [CALCULADO]

| V km/h | S a 4,3 kW eje | σ_T | **P_eje máx. (S = 3,5)** | T con ese límite | P_eje máx. (S = 4,0) | T | I_bat a 44 V con S = 3,5 (η_m·η_ESC 0,88) |
|---|---|---|---|---|---|---|---|
| 0 | 3,31 | 0,24 | **4,82 kW** (4673 rpm) | 586 N | 6,29 kW (5109 rpm) | 701 N | 124 A |
| 5 | 3,30 | 0,24 | 4,85 | 528 | 6,34 | 637 | 125 |
| 9,26 | 3,27 | 0,25 | 4,94 | 488 | 6,46 | 593 | 128 |
| 12 | 3,24 | 0,25 | 5,02 | 465 | 6,58 | 570 | 130 |
| 15 | 3,21 | 0,26 | 5,14 | 444 | 6,75 | 547 | 133 |
| 20 | 3,13 | 0,27 | 5,40 | 415 | 7,11 | 517 | 140 |
| 25 | 3,05 | 0,28 | 5,75 | 392 | 7,60 | 495 | 148 |
| 30 | 2,95 | 0,30 | 6,18 | 374 | 8,20 | 479 | 160 |

**Ley de control recomendada** (para el ESC/VESC):
1. Medir la velocidad (GPS o pitot) y limitar **P_eje ≤ P_lim(V)** de la tabla con S = 3,5 (≈ 4,8 kW hasta 10 km/h, rampa lineal a 6,2 kW a 30 km/h). Equivalente en rpm: n ≤ 4670 rpm a 0–10 km/h → 5080 rpm a 30 km/h [CALCULADO].
2. Respaldo sin sensor de velocidad: **límite de rpm** (la cavitación se ve como rpm que sube sin empuje [VERIFICADO: R10a S4 p.29]) + detección de "unloading": d(rpm)/dt alta con corriente cayendo → bajar el duty.
3. A punto fijo, **no pasar de ~5,5 kW eléctricos** sostenidos (S = 3,5) y ~7,2 kW solo en transitorios (S ≈ 4,0) [CALCULADO].
4. Hamilton lo dice cualitativamente: "Full power cannot be used at low vessel speeds" [VERIFICADO: R10a S4 p.28].

Fórmula cerrada útil (afinidad a lo largo de una misma curva de sistema, Q ∝ n): **P_máx/P_ref = (S_lím/S_ref)²** y n_máx/n_ref = (S_lím/S_ref)^(2/3) [CALCULADO: de S ∝ n·√Q ∝ n^1,5 y P ∝ n³]. Ej.: S_ref = 3,31 a 4,3 kW → P(S = 3,5) = 4,3·(3,5/3,31)² = 4,81 kW, igual que la tabla.

---

## 6. Resistencia de planeo (cascos de 2–2,5 m, 150–250 kg)

### 6.1 openplaning 0.4.9: API verificada en el código instalado [VERIFICADO: T11]

Archivo: `/usr/local/lib/python3.11/dist-packages/openplaning/openplaning.py` (1118 líneas; depende de `ndmath`, `scipy`).

```python
from openplaning import PlaningBoat
b = PlaningBoat(speed, weight, beam, lcg, vcg, r_g, beta, epsilon, vT, lT,
                loa=None, H_sig=None, ahr=150e-6, LD_change=None, Lf=0, sigma=0, delta=0,
                l_air=0, h_air=0, b_air=0, C_shape=0, C_D=0.7, z_wl=0, tau=5,
                rho=1025.87, nu=1.19e-6, rho_air=1.225, g=9.8066,
                wetted_lengths_type=1, z_max_type=1, roughness_penalty_type=1, seaway_drag_type=1)
b.get_steady_trim(x0=[0, 3], tauLims=[0.5, 35], tolF=1e-6, maxiter=50)  # resuelve z_wl y tau
b.get_forces()            # recalcula fuerzas con el trimado hallado (y emite avisos de validez)
R = -b.thrust_force[0]    # N: empuje horizontal requerido = resistencia total
```

| Argumento | Unidad | Significado (docstring) |
|---|---|---|
| `speed` | m/s | velocidad |
| `weight` | **N** (no kg) | peso |
| `beam` | m | manga de pantoque (chine) |
| `lcg` | m | CG desde el **espejo** |
| `vcg` | m | CG sobre la quilla |
| `r_g` | m | radio de giro (solo para dinámica/porpoising) |
| `beta` | ° | astilla muerta |
| `epsilon` | ° | ángulo del empuje respecto de la quilla (CCW) |
| `vT`, `lT` | m | línea de empuje: sobre la quilla / a proa del espejo |
| `ahr` | m | rugosidad media (150 µm) |
| `l_air, h_air, b_air, C_shape, C_D` | m, –, – | arrastre aerodinámico (si `C_shape = 0` o `b_air = 0`, no hay) |
| `Lf, sigma, delta` | m, –, ° | flap (Savitsky & Brown 1976) |
| `wetted_lengths_type` | 1/2/3 | 1 = Faltinsen 2005 (subida de ola), 2 = Savitsky 64, 3 = Savitsky 76 |
| `roughness_penalty_type` | 1/2 | 1 = Mosaad 1986, 2 = Townsin 1984 |

Salidas (atributos tras `get_forces`): `tau` (°), `z_wl` (m, CG sobre la flotación en calma), `L_K`, `L_C`, `lambda_W`, `T` (calado del espejo), `wetted_bottom_area`, `bottom_fluid_speed`, `C_f`, `deltaC_f`, `lcp`, y vectores **[F_x (+ a popa), F_z (+ arriba), M_cg (+ proa arriba)]**: `hydrodynamic_force`, `skin_friction`, `air_resistance`, `flap_force`, `thrust_force`, `net_force`. Ojo: `net_force[0]` **no** es un residuo: el empuje solo se suma a F_z y M (líneas 706–719), así que `net_force[0]` = R. `thrust_force[0]` = −ΣF_x (componente horizontal); el módulo del empuje es R/cos(ε+τ).

Ecuaciones en el código: C_L0 = τ^1,1(0,012λ^½ + 0,0055λ^2,5/C_V²) (l. 504), C_Lβ = C_L0 − 0,0065βC_L0^0,6 (l. 507), l_p = λb(0,75 − 1/(5,21(C_V/λ)² + 2,39)) (l. 519), V_m (l. 559), C_f ITTC-57 (l. 565), ΔC_f Mosaad (l. 570), L_K de Faltinsen ec. 9.50 (l. 308). Avisos de validez: C_V 0,60–13, λ ≤ 4, τ 2–15° (sustentación, l. 497–501), C_V ≥ 1 (velocidad media de fondo, l. 556), β 4–40° (tabla de Faltinsen, l. 319) y pantoques secos L_C = 0 (l. 339) [VERIFICADO: T11]. **`get_steady_trim` silencia los avisos** (`warnings.filterwarnings("ignore")`, l. 754): llamar `get_forces()` después para verlos. `check_porpoising()` devuelve `[[inestable_por_autovalores, t_asentamiento], [porpoising_por_Savitsky, τ_crítico]]` (l. 910–972); `print_description()` imprime todo.

### 6.2 Ejemplo ejecutado: Δ = 200 kg, b = 0,6 m, β = 10°, LCG = 1,0 m, V = 8,33 m/s

Entradas adicionales [ESTIMADO]: vcg 0,33 m, r_g 0,5 m, ε 0°, vT 0,10 m, lT 0, ρ 1013, ν 1,35·10⁻⁶. Script `op_ejemplo.py` (§12). Salida copiada:

```
--- caso base ---
tau = 6.367 deg  z_wl = 0.2604 m
L_K = 1.609 m  L_C = 1.303 m  lambda = 2.427  T_espejo = 0.1785 m
S mojada = 0.887 m2  V_m = 8.115 m/s  C_f = 0.00307 dC_f = 0.00050
hydrodynamic_force [Fx,Fz,M] = [ 216.17 1937.2   -41.74]
skin_friction      [Fx,Fz,M] = [110.56 -12.34 -33.87]
air_resistance     [Fx,Fz,M] = [0 0 0]
thrust_force       [Fx,Fz,M] = [-326.73   36.46   75.61]
net_force (debe ~0)          = [326.7271   0.       0.    ]
R total = 326.7 N  R/Delta = 0.167  P_E = 2.722 kW  lcp = 0.979 m  Fn_B = 3.434
porpoising [[eig, t_settle],[Savitsky, tau_crit]] = [[True, -8.481040618728525], [False, 8.658865971800111]]
--- caso aire --- (l_air 0.8, h_air 0.6, b_air 0.8, C_shape 1, C_D 0.9)
tau = 6.374 deg  ... R total = 342.1 N  R/Delta = 0.174  P_E = 2.849 kW
```

- Coincide con R10b (343 N con aire) [VERIFICADO: R10b §4.4].
- Porpoising: el criterio de Savitsky dice **no** (τ 6,4° < τ_crít 8,7°), pero el análisis de autovalores da una raíz con parte real positiva (t_asentamiento negativo) → **contradicción: verificar en el agua** con el LCG real; no confiar en el autovalor de un casco tan chico extrapolado [ESTIMADO].
- Barrido (mismo casco): 12 km/h 291 N (τ 7,8°, λ 3,81); 15 → 338; 17 → 357; **20 → 361 (máximo)**; 25 → 343; 30 → 327; 35 → 324 N [CALCULADO]. Por debajo de ~20 km/h Savitsky está fuera de sus hipótesis aunque no avise (R09 §1.6).

### 6.3 Joroba y preplaneo: Mercier–Savitsky 1973

- Método: regresión de R_T/Δ para un buque de referencia de **100 000 lb**, con 4 parámetros: X = ∇^⅓/L, U = √(2·i_E) (i_E = semiángulo de entrada de la flotación, en grados), Z = ∇/b³, W = A_T/A_X (espejo sumergido / sección máxima), y 14 términos [1, X, U, W, XZ, XU, XW, ZU, ZW, W², XW², ZX², UW², WU²] con coeficientes tabulados para Fn∇ = 1,0; 1,1; …; 2,0 [VERIFICADO: T10, "Table VI", transcripción de DTIC AD-764958 en código C++; **no** la contrasté con el original, que respondió con bloqueo].
- **Rango** (manual PIAS): Fn∇ 1–2; i_E 10–55°; **L/∇^⅓ 2–12**; A_T/A_X 0–1; L/B 2–14 [VERIFICADO: T9]. → R09 suponía "L/∇^⅓ ≳ 4" de memoria: **queda corregido**; este casco (L/∇^⅓ = 3,4–4,0 con 200 kg [CALCULADO]) entra.
- Escala a nuestro tamaño (fricción): R_T/Δ = (R_T/Δ)_ref + [C_F(Re) − C_F(Re_ref)]·(S/∇^⅔)·Fn∇²/2, con S/∇^⅔ = 2,262·√(L/∇^⅓)·(1 + 0,046 B/T + 0,00287 (B/T)²) [VERIFICADO: T10 (forma de la corrección y fórmula de superficie mojada, transcriptas); derivación de R_F/Δ = C_F(S/∇^⅔)Fn∇²/2: CALCULADO].
- Coeficientes (filas = términos, columnas Fn∇ 1,0…2,0): en el script `r12_calc.py` (§12), copiados de T10.

**Resultados para 200 kg** (∇ = 0,1974 m³, ∇^⅓ = 0,582 m) [CALCULADO; geometrías ESTIMADAS porque el casco no está medido]:

| Casco (L, b, i_E, A_T/A_X, B/T) | Fn∇ 1,0 (8,6 km/h) | 1,2 (10,3) | 1,4 (12,0) | 1,6 (13,8) | 1,8 (15,5) | 2,0 (17,2) |
|---|---|---|---|---|---|---|
| 2,0 / 0,60 / 20° / 0,9 / 4,0 | 0,035 (69 N) | 0,109 (215) | 0,150 (294) | **0,159 (312)** | 0,154 (303) | 0,145 (284) |
| 2,0 / 0,70 / 30° / 0,9 / 5,0 | 0,064 (126) | 0,142 (279) | **0,165 (324)** | 0,162 (317) | 0,158 (311) | 0,152 (298) |
| 2,2 / 0,75 / 25° / 1,0 / 5,5 | 0,026 (52) | 0,080 (156) | **0,120 (235)** | 0,116 (227) | 0,117 (229) | 0,108 (211) |

- La joroba (R/Δ 0,12–0,17 a 12–14 km/h) empalma con openplaning a 17–20 km/h (357–361 N con b 0,6) y con la banda de R10b (0,10–0,20) [VERIFICADO: R10b §4.4].
- **Empuje disponible en la joroba** con el límite S = 3,5: 444–465 N a 12–15 km/h [CALCULADO §5.4] contra 235–324 N → margen de 1,4–2,0. Con 230 kg el margen baja proporcionalmente.
- **Blount–Fox (1976)** y **Savitsky–Brown (1976)** para la joroba: no encontré fuente abierta (buscar: "Blount Fox 1976 Small craft power prediction Marine Technology"). PIAS menciona que su Savitsky aplica correcciones de Blount y Fox [VERIFICADO: T9], sin fórmulas.

### 6.4 A 5 kn (uso principal)

Fn∇ = 1,076 (borde inferior del rango de Mercier–Savitsky) [CALCULADO]:

| Casco | R/Δ | R | rpm del jet | P_eje | P_el | η total | Autonomía 3 kWh |
|---|---|---|---|---|---|---|---|
| 2,0 / 0,60 / 20° | 0,055 | 108 N | 2436 | 682 W | 775 W | 0,36 | 3,9 h |
| 2,0 / 0,70 / 30° | 0,095 | 185 N | 3068 | 1362 W | 1548 W | 0,31 | 1,9 h |
| 2,2 / 0,75 / 25° | 0,042 | 82 N | 2173 | 484 W | 550 W | 0,38 | 5,5 h |

[CALCULADO, η_p constante 0,75 fuera de diseño: optimista a 2200–3000 rpm por Reynolds.] La dispersión (×2,8) viene de i_E y b: **medir el casco** (L_wl, b de pantoque, i_E, A_T/A_X, calado) es lo que más reduce la incertidumbre. R10b daba 0,65–3,9 kW con una banda R/Δ ESTIMADA; esto la acota a ~0,55–1,6 kW.

### 6.5 Datos medidos para calibrar (ver §8)
Mokai (3,4 m, ~165 kg con piloto, 7 hp, 32 km/h) y Lampuga Air (2,30 × 0,75 m, ~135 kg con piloto, ≤ 10 kW, ≤ 50 km/h); R04: RIB de 2,75 m planea a 14,8–17,6 km/h con 2,5 hp [VERIFICADO: R04 C.1, citado en R10b].

---

## 7. Cargas estructurales del jet

Valores [CALCULADO] con el modelo §5.3 (ν 0,40 salvo indicación).

### 7.1 Empuje axial y su camino
- Empuje neto del jet: 269 N (30 km/h, 4,3 kW) a **~700 N** (punto fijo, 7,2 kW el.) = ρQV_j [CALCULADO].
- Fuerza axial sobre el rotor ≈ Δp_estática·A_anular = **370–410 N** a 4,3 kW (Δp ≈ 53–54 kPa) [CALCULADO; aproximación de disco]. A 7,2 kW punto fijo, escalar con H: ~550–600 N [CALCULADO por afinidad].
- Camino: rotor → eje → **rodamiento axial fijo en la caja de la bomba** (par de contacto angular) → carcasa → bloque de toma/espejo → casco. El motor no debe recibir empuje (acople con juego axial) [VERIFICADO como criterio: R10b H16]. El resto del empuje del jet llega al casco como presión sobre conducto, estator y tobera.

### 7.2 Presión interna (carcasa, estator, tobera)
- Presión estática en la entrada de la tobera: p ≈ (1+φ_n)·½ρ(V_j² − V_entrada²) = **51 kPa** (5 kW, punto fijo) / **64 kPa** (7,2 kW) [CALCULADO].
- Presión de cierre (tobera tapada, ψ₀ = 2ψ_d): **≈ 122 kPa** a 4500 rpm, **≈ 158 kPa** a 5120 rpm [CALCULADO; ψ₀/ψ_d ESTIMADO].
- Diseño de carcasa/tobera/bridas: **p_diseño = 0,2 MPa** (≈ 1,3 × cierre a 5120 rpm) y prueba hidrostática a 0,3 MPa [ESTIMADO: criterio].
- Además, depresión en la entrada (succión): hasta −90 kPa locales en cavitación → paredes del conducto y del anillo sin pandeo a 1 bar externo [ESTIMADO].

### 7.3 Álabes del estator
- El estator recibe el par de reacción del giro: F_θ ≈ τ/(Z_S·r_m) = **32–34 N por álabe** a 4,3 kW, ~50 N a 7,2 kW [CALCULADO]. Los álabes del estator **sostienen el cubo del estator** (y a veces el cojinete trasero): verificar también la carga radial del rotor (desbalance + interacción rotor-estator [VERIFICADO: T1 p.144]).

### 7.4 Boquilla direccional
- Momento del chorro J = ρQV_j = 552 N (5 kW) / 704 N (7,2 kW) a punto fijo [CALCULADO].
- Desviar el chorro δ: fuerza lateral J·sin δ y fuerza sobre la boquilla |F| = 2J·sin(δ/2) → **189–286 N (δ 20–30°, 5 kW)**, **241–364 N (7,2 kW)** [CALCULADO: balance de cantidad de movimiento].
- Momento en el pivote: |F|·e, con e = distancia del pivote al centro de giro del chorro (≈ 0,3–0,5 del largo de la boquilla) [ESTIMADO]. Con pivote centrado y boquilla de 100 mm: 10–18 N·m. Topes mecánicos a ±25–30°.

### 7.5 Bucket de reversa
- Fuerza sobre el bucket ≈ J·(1 + k_r), k_r = fracción reversada (Hamilton: hasta 60 % [VERIFICADO: T15]) → **880–1100 N (5 kW)**, **1130–1410 N (7,2 kW)** [CALCULADO].
- Momento en la bisagra con brazo de 60 mm: **53–85 N·m** [CALCULADO; brazo ESTIMADO].
- R10b pedía bisagra para ≥ 2 × 760 N [VERIFICADO: R10b H10]: coherente con 1,4 kN. Bajar el bucket solo a ralentí ("damage to the plate and brackets can occur" [VERIFICADO: R10b, CG Aux]) y limitar potencia en reversa (p. ej. ≤ 50 % P) por firmware [ESTIMADO].

### 7.6 Piedras: fusible mecánico vs límite de corriente
- Energía cinética rotor + impulsor a 4500 rpm: ½Jω² ≈ **490 J** con J ≈ 0,0044 kg·m² [CALCULADO; J ESTIMADO (rotor de motor de 5 kW)].
- Si el impulsor se traba en 90° / 30° / 10° de giro: par medio **311 / 933 / 2799 N·m** [CALCULADO]. El ESC limita solo el par electromagnético (k_t·I): **no protege contra la inercia**.
- Capacidades: eje Ø20 316 con chavetero ≈ 74 N·m a fluencia (τ_y 118 MPa, K_t 2,5 de R10b) [CALCULADO con valores de R10b ESTIMADOS allí].
- **Criterio:** τ_fusible ≥ 1,5·τ_máx(ESC) y ≤ 0,6·τ_fluencia(eje con chavetero, pala, cubo).
  - Con límite de corriente equivalente a 15 N·m: τ_fusible = 23–44 N·m → **pasador 6061-T6 Ø3–4 mm en eje Ø20: 25 / 44 N·m** (corte doble, τ_u = 0,6·UTS 290 MPa) [CALCULADO con R09 §5.3].
  - Si el ESC deja pasar el par pico del motor (≈ 45 N·m según R10b, no verificado), el pasador corta en cada arranque: **limitar la corriente de fase** a ≤ 15 N·m equivalentes.
- Alternativa: acople limitador de par por fricción en el lado seco (reutilizable) [ESTIMADO].
- Firmware: detectar bloqueo (rpm → 0 con corriente al límite > 0,3 s) y cortar [ESTIMADO].

---

## 8. Datos de jets chicos para calibrar

| Caso | Casco / masa | Potencia | Velocidad / empuje | Derivado | Fuente |
|---|---|---|---|---|---|
| **Lampuga Air** (jetboard eléctrico) | 2,30 × 0,75 × 0,25 m; batería 27 kg + powerbox 20 kg + casco 8 kg ≈ 55 kg (+ piloto) | motor BLDC refrigerado por agua "up to 10kW"; 50,4 V; 3,6 kWh | "Up to 50 km/h"; "Up to 45 min" | ~74 W/kg con 80 kg de piloto; 3,6 kWh/45 min = 4,8 kW medios [CALCULADO] | [VERIFICADO: T12] |
| Lampuga Air (2016) | tabla de 2 m, 32 kg | "15-hp" | 47 km/h; 40 min | — | [VERIFICADO: T13] |
| Lampuga Air 4: 7,5 / 10,2 kW → 73 / 96 kg de empuje, 48 / 53 km/h | — | — | — | — | **No verificado** (resumen del buscador; la página no abrió) |
| **Mokai ES-Kape** (kayak con jet a nafta) | 3,4 m, 75 kg, casco planeador escalonado, 1 adulto + niño | 7 hp (≈ 5,2 kW, potencia del motor) | "up to 20 mph (32 km/h)" | ~32 W/kg con 90 kg de piloto; L/∇^⅓ ≈ 6,2 [CALCULADO] | [VERIFICADO: T14] |
| Modelo de laboratorio (Chen 2025) | — | H 2,76 m, η_p 0,82 | T = 304 N a 1450 rpm, D 180 | — | [VERIFICADO: T3] |
| Jets impresos J1–J4, PRO-JET, FluxJet | kayak / SUP / tabla | 0,27–5 kW | 4 kgf a 270 W; 11,5 km/h a 1,1 kW | — | [VERIFICADO: R03 §1–2] |

**Lectura para este proyecto** [CALCULADO/ESTIMADO]:
- Este bote: 5 kW / 200 kg = **25 W/kg**; 7,2 kW / 200 kg = 36 W/kg.
- Mokai llega a 32 km/h con ~32 W/kg, pero con un casco **mucho más esbelto** (L/∇^⅓ ≈ 6,2 contra 3,4–4,0 aquí).
- Lampuga usa ~74 W/kg en un casco del mismo tamaño en planta (2,30 × 0,75) para 40–50 km/h.
- → Con 25 W/kg y L/∇^⅓ ≈ 3,5–4, **30 km/h es posible pero marginal** (coherente con R10b: 20–34 km/h según casco); con 36 W/kg es razonable.

---

## 9. Qué no pude verificar (y cómo buscarlo)

| Tema | Estado | Buscar |
|---|---|---|
| Allison 1993 (SNAME Trans. 101, pp. 275–335) | Existe; solo hallé copias en sitios de dudosa licencia, **no usadas** | Biblioteca SNAME / institucional |
| Kim & Chun 2007 (holgura de punta en waterjet axial, Ocean Eng. 34) | Solo título (abstract elidido por el editor) | "Kim Chun 2007 Ocean Engineering tip clearance waterjet" |
| Δη por 1 % de holgura en bombas axiales | [ESTIMADO] 1,5–3 puntos por 1 % de altura de pala | Gülich, *Centrifugal Pumps*, cap. "axial pumps", "tip clearance losses" |
| Mercier–Savitsky original (DTIC AD-764958) | Bloqueado; coeficientes de transcripción secundaria (T10) | Contrastar la Tabla VI con el PDF original antes de usar en decisiones finales |
| Blount–Fox 1976, Savitsky–Brown 1976 | No abiertos | "Blount Fox 1976 small craft power prediction" |
| Coeficiente de contracción de toberas de waterjet | Solo cualitativo (ITTC) | "waterjet nozzle discharge coefficient vena contracta" |
| Curva de recuperación de la toma vs IVR (números) | Solo tendencia (T3) | Van Terwisga 1996 (TU Delft), Jiao 2019 |
| Límites D_f ≤ 0,45 y de Haller ≥ 0,7 | [ESTIMADO] | Lieblein 1953; Dixon & Hall, *Fluid Mechanics and Thermodynamics of Turbomachinery* |
| Reglas de Z_R/Z_S (Gülich) | [ESTIMADO] | Gülich §10 "rotor-stator interaction" |
| ψ₀/ψ_d de bombas axiales (cierre) | [ESTIMADO 2–2,6] | Stepanoff, curvas de bombas axiales |
| β = 0,76 (barra perfilada) en Kirschmer | Solo resumen del buscador | Kirschmer 1926; Idelchik, "screens" |
| Empuje de Lampuga 73/96 kg | Página no abrió | ficha del fabricante |
| Inercia del rotor del motor de 5 kW | [ESTIMADO 0,004 kg·m²] | ficha del motor elegido |

---

## 10. Cómo usar esto en el código (orden sugerido)

1. `pump_design(D, n, Dn, nu_h, P_shaft, V_design)` → V_j, Q, H, φ_B, ψ_B, Ω_s, S, σ_T (fórmulas 1–13).
2. `blade_sections(nu_h, Z, s[], inc, vortex="free"|"forced")` → tabla de β_b1, β_b2, cuerdas, D_f, α₃ (fórmulas 14–19) → entrada a build123d.
3. `pump_curve(a=2..2.6)` + `system_curve(V)` → punto de operación a cualquier V y n.
4. `cav_limit(V, S_lim=3.5)` → P_lim(V), n_lim(V) → tabla para el ESC.
5. `hull_resistance(V)`: Mercier–Savitsky para Fn∇ 1–2, openplaning para C_V ≥ ~2,3 (≥ 20 km/h con b = 0,6), interpolar en el medio; calibrar con prueba de remolque o de potencia (R10a §8).
6. `loads()` → empuje axial, presiones, bucket, boquilla, fusible.

---

## 11. Fuentes abiertas en esta sesión

| Id | Fuente | Qué se leyó |
|---|---|---|
| T1 | Bulten, N. W. H. (2006), *Numerical analysis of a waterjet propulsion system*, tesis, TU Eindhoven. https://pure.tue.nl/ws/files/2277312/200612081.pdf (pdftotext) | ec. 2.15–2.29 (p.22–26), 2.56 (p.35), 2.59–2.63 y Fig. 2.10 (p.37–39), 2.67 y Fig. 2.11–2.14 (p.40–44), §4.1.5 holgura (p.66), §6.3.3 rotor 6 / estator 7 (p.144) |
| T2 | Brennen, C. E., *Hydrodynamics of Pumps*, Concepts NREC / Oxford UP. http://brennen.caltech.edu/INTPump/pumbook.pdf | §2.1–2.5 (p.17–29), §3.2–3.4 (p.36–45), §4 vórtice libre/forzado (p.54), §5.2–5.5 y Tabla 5.1 (p.73–82), holgura (p.94–96), bombas axiales (p.117–119), Tabla 7.1 e incidencia (p.124), §7.5 solidez y holgura (p.128–131), ec. 7.21 (p.157), §8.8 rotor-estator (p.181–184) |
| T3 | Chen et al. (2025), "Influences of micro ramp vortex generators on the performance of flush waterjet propulsor", *Sci Rep* 15:31278. https://pmc.ncbi.nlm.nih.gov/articles/PMC12379258/ | Modelo D 180 mm, 5 álabes, 9 directrices, holgura 1 mm, 1450 rpm, tobera Ø100, cubo que se afina a cero; Tabla 6 (H 2,76 m, η_p 0,8187, T 303,78 N); tendencia de la recuperación con IVR |
| T4 | "Experimental and numerical study on cavitation pulsating pressure of water-jet propulsion axial-flow pump" (2024). https://pmc.ncbi.nlm.nih.gov/articles/PMC11516003/ | D 0,3 m, 6 álabes / 11 directrices, holgura 0,001 D, 1450 rpm, Q 0,46 m³/s; NPSH_R(3 %) entre 6,27 y 8,18 m; Tabla 2 (H) |
| T5 | Monroe, S. E., "Parallel URANS Studies of the Performance of ONR Waterjet AxWJ-2", Clarkson Univ. https://par.nsf.gov/servlets/purl/10414214 | Rotor 6 / estator 8, modelo 12", Q* = 0,85 a 2000 rpm, sin estator −20 % |
| T6 | Ni, Liu, Shen, Pan (2017), "Thrust Characteristics and Nozzle Role of Water Jet Propulsion", *IJFMS* 10(1):47. https://www.jstage.jst.go.jp/article/ijfms/10/1/10_47/_pdf | La tobera fija el punto de operación ("act as a valve") |
| T7 | Baselt & Malcherek (2022), "Determining the Flow Resistance of Racks…", *Water* 14:2469. https://athene-forschung.unibw.de/doc/142476/142476.pdf | Kirschmer ec. 8, β = 2,42 (barra cuadrada), Tabla 1 (Raynal, Tsikata, Clark, Wahl…), Δh ≠ h_V |
| T8 | Apuntes "Screen chamber" (https://shahidarshad.wordpress.com/wp-content/uploads/2018/01/l-11-screen-chamber.pdf) y "Screening" (http://ceuom.weebly.com/uploads/1/0/8/9/1089833/4._ww_screening.pdf) | β de Kirschmer 2,42 / 1,83 / 1,79 / 1,67 (fuente secundaria docente) |
| T9 | SARC, *PIAS Manual: Resistance*. https://www.sarc.nl/images/manuals/pias/htmlEN/resistance.html | Rangos de Savitsky, Mercier–Savitsky, Robinson, Delft |
| T10 | GitHub fesbda/GenericMichell, `src/resistance.h` (commit 70be695). https://raw.githubusercontent.com/fesbda/GenericMichell/HEAD/src/resistance.h | Tabla VI de Mercier–Savitsky (14 × 11), términos X, U, Z, W, corrección de fricción y S/∇^⅔ (transcripción secundaria) |
| T11 | openplaning 0.4.9 instalado: `/usr/local/lib/python3.11/dist-packages/openplaning/openplaning.py` | Clase `PlaningBoat`, argumentos, unidades, métodos, ecuaciones (líneas citadas) |
| T12 | Lampuga, *Contractual products / Technical Details Lampuga Air*. https://lampuga.com/fileadmin/Documents/AIR_3/Lampuga_Air_Datenblatt_375f781508__1_.pdf | 2,30 × 0,75 × 0,25 m; ≤ 10 kW; 50,4 V; 3,6 kWh; ≤ 50 km/h; masas |
| T13 | New Atlas, "Modular inflatable electric surfboard jets to 29 mph". https://newatlas.com/lampuga-air-inflatable-e-surfboard/44381/ | 15 hp, 47 km/h, 32 kg, 40 min |
| T14 | New Atlas, "Mokai jet-drive boat breaks down into three nesting pieces". https://newatlas.com/mokai-three-piece-nesting-jet-drive-kayak/31417/ | 3,4 m, 75 kg, 7 hp, 32 km/h, casco planeador escalonado |
| T15 | HamiltonJet, "HJ Series". https://www.hamiltonjet.com/waterjets/hj-series | "split duct reverse deflector provides up to 60% of forward thrust" |
| T17 | ITTC, *Specialist Committee on Waterjets – Final Report, 22nd ITTC*. https://ittc.info/media/1518/specialist-committee-on-waterjets.pdf | p.12: estimar el coeficiente de contracción y la ubicación de la vena contracta |
| T18 | ITTC, *Specialist Committee on Validation of Waterjet Test Procedures, 23rd ITTC*. https://ittc.info/media/1467/waterjet.pdf | p.396–397: Scherer et al., poca variación de presión estática en la vena contracta |
| T16 | Crossref / Semantic Scholar (metadatos): Li 2022, doi 10.3233/atde220403 (resumen: holgura 0,1–0,7 % D); Kim & Chun 2007, doi 10.1016/j.oceaneng.2005.12.011 (solo título); Bai et al. 2026, doi 10.3390/w18030437 (resumen: más holgura → menos H y η pico) | Solo resúmenes |

Del repositorio: R03 (§1–2), R04 (C.1, vía R10b), R09 (§1.6, §4, §5.3), R10a (§0–§9, fuentes S1–S12), R10b (§4.4–4.7, H3, H10, H16).

No abiertos o bloqueados: Allison 1993; DTIC AD-764958 (Mercier–Savitsky) y AD0710246 (Garcia 1970, "Waterjet pump performance determinations"); Jiao 2019 (403); MDPI (403); Lampuga shop (certificado); tesis DiVA "Methods to Predict Hull Resistance" (conexión cortada).

---

## 12. Scripts ejecutados y salida

Ejecutados con Python 3.11, numpy, openplaning 0.4.9, en el directorio temporal de la sesión (fuera del repo). Las variantes `r12_calc_nu50.py` (ν = 0,50; s = 1,30/0,95/0,70) y `r12_calc_a26.py` (a = 2,6) son el mismo script con esas líneas cambiadas. `r12_hub.py` es el barrido de la §2.3.

<details><summary>r12_calc.py (cálculos de las §2, §4, §5, §6, §7)</summary>

```python
"""R12 - calculos de metodo para el waterjet inboard (D=108 mm, 4500 rpm, tobera 72 mm).
Todas las formulas citadas en research/R12_metodos_waterjet.md. Ejecutar: python r12_calc.py
"""
import math, warnings
import numpy as np

rho, nu, g = 1013.0, 1.35e-6, 9.81          # inputs.yaml
p_atm, p_v = 101325.0, 2984.0                # inputs.yaml (p_v a 24 C, peor caso)
D, n_rpm, Dn = 0.108, 4500.0, 0.072
nu_h = 0.40                                  # relacion cubo/punta (R10b)
Om = 2*math.pi*n_rpm/60
An = math.pi/4*Dn**2
Aann = math.pi/4*D**2*(1-nu_h**2)
phi_n, eps, w = 0.02, 0.20, 0.05             # Bulten: phi (tobera) 0.02, eps 0.10-0.30 ; w ESTIMADO

def section(title):
    print("\n" + "="*8 + " " + title + " " + "="*8)

# ---------------------------------------------------------------- A. punto de diseno
section("A. Punto de diseno 30 km/h, P_eje 4.3 kW, eta_p 0.75")
V = 30/3.6; P_sh = 4300.0; eta_p = 0.75
Vin = (1-w)*V
# eta_p*P = rho*Q*[(1+phi)Vj^2/2 - (1-eps)Vin^2/2], Q=An*Vj  -> resolver Vj
f = lambda Vj: rho*An*Vj*((1+phi_n)*Vj**2/2 - (1-eps)*Vin**2/2) - eta_p*P_sh
lo, hi = Vin, 60.0
for _ in range(200):
    mid = (lo+hi)/2
    lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
Vj = (lo+hi)/2; Q = An*Vj
H = ((1+phi_n)*Vj**2 - (1-eps)*Vin**2)/(2*g)
T = rho*Q*(Vj - Vin)
mu = V/Vj
eta_jet_B = 2*mu*(1-mu)/((1+phi_n) - mu**2*(1-eps))     # Bulten ec. 2.62 sin (1-t)/(1-w)
print(f"Vj={Vj:.2f} m/s Q={Q*1000:.1f} L/s H={H:.2f} m T={T:.0f} N mu=V/Vj={mu:.3f} "
      f"eta_d/eta_p (Bulten 2.62, hull=1)={eta_jet_B:.3f} -> eta_d={eta_jet_B*eta_p:.3f}")
phiB = Q/(Om*D**3); psiB = g*H/(Om*D)**2
Ns = Om*math.sqrt(Q)/(g*H)**0.75
nq = n_rpm*math.sqrt(Q)/H**0.75
U = Om*D/2; cm = Q/Aann
print(f"phi_B=Q/(Om D^3)={phiB:.4f} psi_B=gH/(Om D)^2={psiB:.4f} | Brennen psi=gH/(Om R)^2={4*psiB:.3f} "
      f"phi1=Q/(A1 R Om)={Q/(Aann*U):.3f} | Om_s={Ns:.2f} nq(rpm,m3/s,m)={nq:.0f} N_US={Ns*2734.6:.0f}")
print(f"U_tip={U:.1f} m/s c_m={cm:.2f} m/s (A_anular {Aann*1e4:.1f} cm2) Q*=Q/(nD^3)={Q/(n_rpm/60*D**3):.3f}")
eta_B = 0.95 - 0.05/(Q)**(1/3) - 0.125*math.log10(Ns)**2
print(f"Bulten ec.2.26 (cbrt, log10): eta_max={eta_B:.3f}  | P/D^2={P_sh/1000/D**2:.0f} kW/m2")
for nm, Dx, nx, Qx, Hx in [("Chen2025 D180", 0.18, 1450, 0.110, 2.76), ("PMC11516003 D300", 0.30, 1450, 0.46, 12.73)]:
    Ox = 2*math.pi*nx/60
    print(f"  ref {nm}: Om_s={Ox*math.sqrt(Qx)/(g*Hx)**0.75:.2f} phi_B={Qx/(Ox*Dx**3):.3f} psi_B={g*Hx/(Ox*Dx)**2:.4f} "
          f"U_tip={Ox*Dx/2:.1f}")
Ox = 2*math.pi*1450/60
for npsh in (6.27, 7.2, 8.18):
    print(f"  ref PMC11516003 S con NPSH_R={npsh}: {Ox*math.sqrt(0.46)/(g*npsh)**0.75:.2f}")

# ---------------------------------------------------------------- B. triangulos
section("B. Triangulos de velocidad (torbellino libre, sin pre-giro)")
eta_h = 0.85                                   # ESTIMADO
gHth = g*H/eta_h
Zr = 5
s_sel = {"cubo": 1.30, "medio": 1.00, "punta": 0.80}   # ESTIMADO (ver texto)
inc = 3.0                                      # incidencia, grados (Brennen: "a few degrees")
rows = []
for name, r in [("cubo", nu_h*D/2), ("medio", (1+nu_h)/2*D/2), ("punta", D/2)]:
    Ur = Om*r
    cu2 = gHth/Ur                              # torbellino libre: U*cu2 = const
    b1 = math.degrees(math.atan2(cm, Ur))      # desde la direccion tangencial (Brennen)
    b2 = math.degrees(math.atan2(cm, Ur-cu2))
    w1 = math.hypot(cm, Ur); w2 = math.hypot(cm, Ur-cu2)
    s = s_sel[name]
    # Lieblein (Brennen 3.20): Df = 1 - w2/w1 + (cu2-cu1)/(2 s w1)
    Df = 1 - w2/w1 + cu2/(2*s*w1)
    # desviacion Constant (Brennen 3.19): delta = 0.26*theta_c/sqrt(s); iterar
    bb1 = b1 + inc; bb2 = b2
    for _ in range(50):
        th = bb2 - bb1
        delta = 0.26*th/math.sqrt(s)
        bb2 = b2 + delta
    pitch = 2*math.pi*r/Zr; c = s*pitch
    alpha3 = math.degrees(math.atan2(cm, cu2))   # angulo absoluto a la salida (desde tangencial)
    rows.append((name, r, Ur, cu2, b1, b2, bb1, bb2, delta, w2/w1, Df, pitch, c, alpha3))
    print(f"{name:5s} r={r*1000:5.1f} mm U={Ur:5.1f} cu2={cu2:5.2f} beta1={b1:5.1f} beta2={b2:5.1f} | "
          f"blade b1={bb1:5.1f} b2={bb2:5.1f} (desv {delta:4.1f}) w2/w1={w2/w1:.2f} Df={Df:.2f} s={s} "
          f"paso={pitch*1000:.1f} cuerda={c*1000:.1f} mm | alpha3(estator in)={alpha3:5.1f}")
print("Re cuerda punta =", f"{math.hypot(cm,U)*rows[2][12]/nu:.2e}")

# ---------------------------------------------------------------- C. estator y cargas de alabe
section("C. Estator, par, cargas de alabe")
tau = P_sh/Om
print(f"Par eje = {tau:.2f} N m (diseno). Con 7.2 kW el/0.88: {7200*0.88/Om:.2f} N m")
Zs = 7; rm = (1+nu_h)/2*D/2
Ft_rotor = tau/(Zr*rm); Ft_stat = tau/(Zs*rm)
print(f"Fuerza tangencial media por alabe: rotor Z={Zr}: {Ft_rotor:.0f} N ; estator Z={Zs}: {Ft_stat:.0f} N (r_m={rm*1000:.1f} mm)")
span = (1-nu_h)*D/2
for mat, sadm in [("Al 6061-T6", 60e6), ("316 fundido/mecanizado", 80e6), ("bronce NiAl", 90e6)]:
    # pala como viga en voladizo, carga uniforme -> M = F*span/2 ; seccion ~ placa c x t: W = c t^2/6 (conservador)
    c_h = rows[0][12]
    t_req = math.sqrt(6*Ft_rotor*span/2/(c_h*sadm))
    print(f"  {mat}: t_raiz minima (sigma_adm {sadm/1e6:.0f} MPa, cuerda cubo {c_h*1000:.0f} mm) = {t_req*1000:.2f} mm")
# carga axial del rotor ~ aumento de presion estatica x area anular
cu2m = rows[1][3]
dp_stat = rho*g*H - 0.5*rho*cu2m**2
print(f"Empuje axial sobre el rotor ~ dp_estatica*A_anular = {dp_stat*Aann:.0f} N (dp={dp_stat/1000:.1f} kPa); "
      f"empuje neto del jet a 30 km/h = {T:.0f} N")

# ---------------------------------------------------------------- D. modelo bomba + sistema, limites
section("D. Bomba (curva lineal) + sistema; limites por cavitacion vs velocidad")
psi_d, phi_d = psiB, phiB
a_shut = 2.0          # psi(0)/psi_d  ESTIMADO
def psi_of(phi): return psi_d*(a_shut - (a_shut-1)*phi/phi_d)
def eta_of(phi): return max(0.05, eta_p*(1 - 1.0*(phi/phi_d-1)**2))
def operate(n, Vb, h_j=0.0, extra_loss_K=0.0):
    Omx = 2*math.pi*n/60; Vinx = (1-w)*Vb
    # resolver phi: psi(phi)(Om D)^2 = sys(Q)
    def F(phi):
        Qx = phi*Omx*D**3; Vjx = Qx/An
        sysH = (1+phi_n)*Vjx**2/2 - (1-eps)*Vinx**2/2 + extra_loss_K*(Qx/0.0113)**2/2
        return psi_of(phi)*(Omx*D)**2 - sysH
    lo, hi = 1e-4, phi_d*a_shut/(a_shut-1)
    for _ in range(200):
        m = (lo+hi)/2
        lo, hi = (m, hi) if F(m) > 0 else (lo, m)
    phi = (lo+hi)/2; Qx = phi*Omx*D**3; Hx = psi_of(phi)*(Omx*D)**2/g
    Px = rho*g*Qx*Hx/eta_of(phi); Vjx = Qx/An
    Tx = rho*Qx*(Vjx - Vinx)
    NPSHa = (p_atm-p_v)/(rho*g) + (1-eps)*Vinx**2/(2*g) - h_j - extra_loss_K*(Qx/0.0113)**2/(2*g)
    S = Omx*math.sqrt(Qx)/(g*NPSHa)**0.75
    sig = (NPSHa*g - (Qx/Aann)**2/2)/(0.5*(Omx*D/2)**2)   # sigma punta ~ (p1-pv)/(0.5 rho U^2)
    return dict(phi=phi, Q=Qx, H=Hx, P=Px, T=Tx, Vj=Vjx, S=S, NPSHa=NPSHa, sig=sig, eta=eta_of(phi))
o = operate(n_rpm, V)
print(f"chequeo 4500 rpm 30 km/h: Q={o['Q']*1000:.1f} L/s H={o['H']:.2f} P={o['P']:.0f} W T={o['T']:.0f} N S={o['S']:.2f}")
hj = 0.05   # punta superior del impulsor sobre la sup. libre en planeo (ESTIMADO)
print("V km/h | n@P=4.3kW  P  T  S  sigma | n_max(S=3.5) P_lim T_lim | n_max(S=4.0) P T | I_bat@44V(S=3.5, eta_m*esc 0.88)")
for Vk in (0, 5, 9.26, 12, 15, 20, 25, 30):
    Vb = Vk/3.6
    # potencia 4.3 kW eje
    lo, hi = 500, 9000
    for _ in range(100):
        m = (lo+hi)/2
        lo, hi = (m, hi) if operate(m, Vb, hj)['P'] < 4300 else (lo, m)
    oP = operate((lo+hi)/2, Vb, hj); nP = (lo+hi)/2
    res = []
    for Slim in (3.5, 4.0):
        lo, hi = 300, 9000
        for _ in range(100):
            m = (lo+hi)/2
            lo, hi = (m, hi) if operate(m, Vb, hj)['S'] < Slim else (lo, m)
        res.append(((lo+hi)/2, operate((lo+hi)/2, Vb, hj)))
    I = res[0][1]['P']/0.88/44
    print(f"{Vk:6.2f} | {nP:5.0f} {oP['P']:5.0f} {oP['T']:4.0f} {oP['S']:4.2f} {oP['sig']:4.2f} | "
          f"{res[0][0]:5.0f} {res[0][1]['P']:5.0f} {res[0][1]['T']:4.0f} | {res[1][0]:5.0f} {res[1][1]['P']:5.0f} {res[1][1]['T']:4.0f} | {I:5.0f} A")

# ---------------------------------------------------------------- E. rejilla
section("E. Rejilla (Kirschmer, flujo normal al plano de la rejilla)")
A_open = 0.0368     # area bruta abertura R10a (m2)
for nm, beta in [("rectangular 2.42", 2.42), ("semicirc. aguas arriba 1.83", 1.83), ("circular 1.79", 1.79), ("ambos semicirc. 1.67", 1.67)]:
    for t, e in [(0.004, 0.012), (0.004, 0.018), (0.003, 0.020), (0.005, 0.025)]:
        Qb = operate(n_rpm, 0.0, 0.0)['Q']
        vn = Qb/A_open
        K = beta*(t/e)**(4/3)
        print(f"  {nm:30s} t={t*1000:.0f} e={e*1000:.0f}: K={K:.3f} v_n(punto fijo)={vn:.2f} m/s dh={K*vn**2/2/g*1000:.1f} mm")

# ---------------------------------------------------------------- F. cargas
section("F. Cargas: presiones, boquilla, bucket, piedra")
ob = operate(n_rpm, 0.0, 0.0)
print(f"Punto fijo 4500 rpm: Q={ob['Q']*1000:.1f} L/s H={ob['H']:.2f} m P={ob['P']:.0f} W T={ob['T']:.0f} N Vj={ob['Vj']:.1f}")
p_shut = rho*g*psi_d*a_shut*(Om*D)**2/g
print(f"Presion estatica max. en carcasa (cierre, psi0=2 psi_d) ~ {p_shut/1000:.0f} kPa manometrica + p_atm; "
      f"presion dinamica chorro 1/2 rho Vj^2 (punto fijo) = {0.5*rho*ob['Vj']**2/1000:.0f} kPa")
for Pel in (5000, 7200):
    lo, hi = 500, 9000
    for _ in range(100):
        m = (lo+hi)/2
        lo, hi = (m, hi) if operate(m, 0.0)['P'] < Pel*0.88 else (lo, m)
    oo = operate((lo+hi)/2, 0.0)
    J = rho*oo['Q']*oo['Vj']
    print(f"P_el {Pel}: n={(lo+hi)/2:.0f} rpm, momento del chorro rho Q Vj = {J:.0f} N; p_estatica entrada tobera "
          f"~ {0.5*rho*(oo['Vj']**2-(oo['Q']/(math.pi/4*0.100**2))**2)*(1+phi_n)/1000:.0f} kPa")
    for k_r in (0.6, 1.0):
        F_b = J*(1+k_r)
        print(f"   bucket (reversa k_r={k_r}): F ~ {F_b:.0f} N; M_bisagra con brazo 60 mm = {F_b*0.06:.1f} N m")
    for dlt in (20, 30):
        F_lat = J*math.sin(math.radians(dlt)); F_res = 2*J*math.sin(math.radians(dlt)/2)
        print(f"   boquilla delta={dlt}: F_lateral={F_lat:.0f} N, |F| sobre boquilla={F_res:.0f} N")
J_rot = 0.004 + 0.0004   # kg m2 rotor motor 5 kW + impulsor (ESTIMADO)
E = 0.5*J_rot*Om**2
for ang in (90, 30, 10):
    print(f"Piedra: E_cin rotor = {E:.0f} J ; parada en {ang} grados -> par medio {E/math.radians(ang):.0f} N m")
for d_p in (3, 4, 5):
    Ds = 0.020
    tq = 0.6*290e6*math.pi*(d_p/1000)**2/4*Ds
    print(f"Pasador 6061-T6 d={d_p} mm en eje 20 mm (corte doble, tau_u=0.6 UTS): {tq:.0f} N m")

# ---------------------------------------------------------------- G. resistencia
section("G. openplaning (Savitsky 1964) y Mercier-Savitsky (preplaneo)")
from openplaning import PlaningBoat
def op(Vb, m=200, b=0.6, beta=10, lcg=1.0):
    pb = PlaningBoat(speed=Vb, weight=m*9.8066, beam=b, lcg=lcg, vcg=0.33, r_g=0.5, beta=beta,
                     epsilon=0, vT=0.10, lT=0.0, rho=rho, nu=nu)
    pb.get_steady_trim(); pb.get_forces()
    return pb
pb = op(8.33)
print(f"EJEMPLO Delta=200 kg b=0.6 beta=10 LCG=1.0 V=8.33: tau={pb.tau:.3f} deg z_wl={pb.z_wl:.4f} m "
      f"R={-pb.thrust_force[0]:.1f} N (presion {pb.hydrodynamic_force[0]:.1f} + friccion {pb.skin_friction[0]:.1f}) "
      f"L_K={pb.L_K:.3f} L_C={pb.L_C:.3f} lambda={pb.lambda_W:.3f} S={pb.wetted_bottom_area:.3f} m2 T_espejo={pb.T:.4f}")
MS_A = [
 [0.06473,0.10776,0.09483,0.03475,0.03013,0.03163,0.03194,0.04343,0.05036,0.05612,0.05967],
 [-0.48630,-0.88787,-0.63720,0,0,0,0,0,0,0,0],
 [-0.01030,-0.01634,-0.01540,-0.00978,-0.00664,0,0,0,0,0,0],
 [-0.06490,-0.13444,-0.13580,-0.05097,-0.05540,-0.10543,-0.08599,-0.13289,-0.15597,-0.18661,-0.19758],
 [0,0,-0.16046,-0.21880,-0.19359,-0.20540,-0.19442,-0.18062,-0.17813,-0.18288,-0.20152],
 [0.10628,0.18186,0.16803,0.10434,0.09612,0.06007,0.06191,0.05487,0.05099,0.04744,0.04645],
 [0.97310,1.83080,1.55972,0.43510,0.51820,0.58230,0.52349,0.78195,0.92859,1.18569,1.30026],
 [-0.00272,-0.00389,-0.00309,-0.00198,-0.00215,-0.00372,-0.00360,-0.00332,-0.00308,-0.00244,-0.00212],
 [0.01089,0.01467,0.03481,0.04113,0.03901,0.04794,0.04436,0.04187,0.04111,0.04124,0.04343],
 [0,0,0,0,0,0.08317,0.07366,0.12147,0.14928,0.18090,0.19769],
 [-1.40962,-2.46696,-2.15556,-0.92663,-0.95276,-0.70895,-0.72057,-0.95929,-1.12178,-1.38644,-1.55127],
 [0.29136,0.47305,1.02992,1.06392,0.97757,1.19737,1.18119,1.01562,0.93144,0.78414,0.78282],
 [0.02971,0.05877,0.05198,0.02209,0.02413,0,0,0,0,0,0],
 [-0.00150,-0.00356,-0.00303,-0.00105,-0.00140,0,0,0,0,0,0]]
def ms(Fnv, vol, L, b, ie_deg, W, BT):
    X = vol**(1/3)/L; U_ = math.sqrt(2*ie_deg); Z = vol/b**3
    terms = [1, X, U_, W, X*Z, X*U_, X*W, Z*U_, Z*W, W*W, X*W*W, Z*X*X, U_*W*W, W*U_*U_]
    fc = min(2.0, max(1.0, Fnv)); i0 = min(9, int((fc-1.0)/0.1 + 1e-9)); fr = (fc-(1+0.1*i0))/0.1
    r0 = sum(MS_A[j][i0]*terms[j] for j in range(14)); r1 = sum(MS_A[j][i0+1]*terms[j] for j in range(14))
    RT_ref = (1-fr)*r0 + fr*r1      # R_T/Delta del buque de 100 000 lb
    Sv = 2.262*math.sqrt(L/vol**(1/3))*(1 + 0.046*BT + 0.00287*BT**2)
    Rn_ref = Fnv*(L/vol**(1/3))*math.sqrt(32.2*100000/64)/1.2817e-5
    V_ = Fnv*math.sqrt(g*vol**(1/3)); Rn = V_*L/nu
    cf = lambda R: 0.075/(math.log10(R)-2)**2
    RT = RT_ref + (cf(Rn) - cf(Rn_ref))*Sv*Fnv**2/2
    return RT, RT_ref, X, Z, U_
m = 200; vol = m/rho
print(f"vol={vol:.4f} m3 vol^1/3={vol**(1/3):.4f}")
for (L, b, ie, W, BT) in [(2.0, 0.60, 20, 0.9, 4.0), (2.0, 0.70, 30, 0.9, 5.0), (2.2, 0.75, 25, 1.0, 5.5)]:
    print(f" casco L={L} b={b} iE={ie} AT/AX={W} B/T={BT}:")
    for Fnv in (1.0, 1.2, 1.4, 1.6, 1.8, 2.0):
        RT, RTr, X, Z, U_ = ms(Fnv, vol, L, b, ie, W, BT)
        Vb = Fnv*math.sqrt(g*vol**(1/3))
        print(f"   Fnv={Fnv:.1f} V={Vb*3.6:5.1f} km/h X={X:.3f} Z={Z:.3f} U={U_:.2f} R/Delta_ref={RTr:.4f} "
              f"R/Delta(escala)={RT:.4f} R={RT*m*g:.0f} N")
print("openplaning barrido (200 kg, b 0.6, beta 10, LCG 1.0):")
for Vk in (12, 15, 17, 20, 25, 30, 35):
    with warnings.catch_warnings(record=True) as wl:
        warnings.simplefilter("always")
        p = op(Vk/3.6)
    print(f"   {Vk} km/h: R={-p.thrust_force[0]:.0f} N tau={p.tau:.2f} lambda={p.lambda_W:.2f} Fn_B={Vk/3.6/math.sqrt(g*0.6):.2f} avisos={len(wl)}")

section("H. 5 kn (9,26 km/h): R Mercier-Savitsky -> rpm, potencia y autonomia con el jet de diseno")
Vb = 9.26/3.6; Fnv = Vb/math.sqrt(g*vol**(1/3))
print(f"Fn_vol a 5 kn = {Fnv:.3f}")
for (L, b, ie, W, BT) in [(2.0, 0.60, 20, 0.9, 4.0), (2.0, 0.70, 30, 0.9, 5.0), (2.2, 0.75, 25, 1.0, 5.5)]:
    RT, *_ = ms(Fnv, vol, L, b, ie, W, BT); R = RT*m*g
    lo, hi = 300, 9000
    for _ in range(100):
        mm = (lo+hi)/2
        lo, hi = (mm, hi) if operate(mm, Vb)['T'] < R else (lo, mm)
    oo = operate((lo+hi)/2, Vb)
    Pel = oo['P']/0.88
    print(f"  L={L} b={b} iE={ie}: R/Delta={RT:.3f} R={R:.0f} N -> n={(lo+hi)/2:.0f} rpm P_eje={oo['P']:.0f} W "
          f"P_el={Pel:.0f} W eta_total={R*Vb/Pel:.3f} | 3 kWh utiles: {3000/Pel:.2f} h")
```

</details>

<details><summary>Salida de r12_calc.py (ν = 0,40, a = 2,0)</summary>

```

======== A. Punto de diseno 30 km/h, P_eje 4.3 kW, eta_p 0.75 ========
Vj=12.95 m/s Q=52.7 L/s H=6.16 m T=269 N mu=V/Vj=0.644 eta_d/eta_p (Bulten 2.62, hull=1)=0.666 -> eta_d=0.500
phi_B=Q/(Om D^3)=0.0888 psi_B=gH/(Om D)^2=0.0233 | Brennen psi=gH/(Om R)^2=0.093 phi1=Q/(A1 R Om)=0.269 | Om_s=4.99 nq(rpm,m3/s,m)=264 N_US=13655
U_tip=25.4 m/s c_m=6.85 m/s (A_anular 77.0 cm2) Q*=Q/(nD^3)=0.558
Bulten ec.2.26 (cbrt, log10): eta_max=0.756  | P/D^2=369 kW/m2
  ref Chen2025 D180: Om_s=4.24 phi_B=0.124 psi_B=0.0362 U_tip=13.7
  ref PMC11516003 D300: Om_s=2.76 phi_B=0.112 psi_B=0.0602 U_tip=22.8
  ref PMC11516003 S con NPSH_R=6.27: 4.69
  ref PMC11516003 S con NPSH_R=7.2: 4.23
  ref PMC11516003 S con NPSH_R=8.18: 3.84

======== B. Triangulos de velocidad (torbellino libre, sin pre-giro) ========
cubo  r= 21.6 mm U= 10.2 cu2= 6.98 beta1= 33.9 beta2= 65.0 | blade b1= 36.9 b2= 73.3 (desv  8.3) w2/w1=0.62 Df=0.60 s=1.3 paso=27.1 cuerda=35.3 mm | alpha3(estator in)= 44.5
medio r= 37.8 mm U= 17.8 cu2= 3.99 beta1= 21.0 beta2= 26.4 | blade b1= 24.0 b2= 27.2 (desv  0.8) w2/w1=0.81 Df=0.30 s=1.0 paso=47.5 cuerda=47.5 mm | alpha3(estator in)= 59.8
punta r= 54.0 mm U= 25.4 cu2= 2.79 beta1= 15.1 beta2= 16.8 | blade b1= 18.1 b2= 16.3 (desv -0.5) w2/w1=0.90 Df=0.17 s=0.8 paso=67.9 cuerda=54.3 mm | alpha3(estator in)= 67.8
Re cuerda punta = 1.06e+06

======== C. Estator, par, cargas de alabe ========
Par eje = 9.12 N m (diseno). Con 7.2 kW el/0.88: 13.45 N m
Fuerza tangencial media por alabe: rotor Z=5: 48 N ; estator Z=7: 34 N (r_m=37.8 mm)
  Al 6061-T6: t_raiz minima (sigma_adm 60 MPa, cuerda cubo 35 mm) = 1.49 mm
  316 fundido/mecanizado: t_raiz minima (sigma_adm 80 MPa, cuerda cubo 35 mm) = 1.29 mm
  bronce NiAl: t_raiz minima (sigma_adm 90 MPa, cuerda cubo 35 mm) = 1.22 mm
Empuje axial sobre el rotor ~ dp_estatica*A_anular = 409 N (dp=53.1 kPa); empuje neto del jet a 30 km/h = 269 N

======== D. Bomba (curva lineal) + sistema; limites por cavitacion vs velocidad ========
chequeo 4500 rpm 30 km/h: Q=52.7 L/s H=6.16 P=4300 W T=269 N S=2.94
V km/h | n@P=4.3kW  P  T  S  sigma | n_max(S=3.5) P_lim T_lim | n_max(S=4.0) P T | I_bat@44V(S=3.5, eta_m*esc 0.88)
  0.00 |  4500  4300  544 3.31 0.24 |  4673  4817  586 |  5109  6291  701 |   124 A
  5.00 |  4500  4300  485 3.30 0.24 |  4685  4852  528 |  5122  6341  637 |   125 A
  9.26 |  4500  4300  440 3.27 0.25 |  4713  4940  488 |  5155  6464  593 |   128 A
 12.00 |  4500  4300  414 3.24 0.25 |  4740  5024  465 |  5186  6582  570 |   130 A
 15.00 |  4500  4300  387 3.21 0.26 |  4777  5143  444 |  5229  6748  547 |   133 A
 20.00 |  4500  4300  344 3.13 0.27 |  4856  5404  415 |  5322  7114  517 |   140 A
 25.00 |  4500  4300  305 3.05 0.28 |  4957  5749  392 |  5440  7596  495 |   148 A
 30.00 |  4500  4300  269 2.95 0.30 |  5079  6184  374 |  5581  8203  479 |   160 A

======== E. Rejilla (Kirschmer, flujo normal al plano de la rejilla) ========
  rectangular 2.42               t=4 e=12: K=0.559 v_n(punto fijo)=1.27 m/s dh=46.0 mm
  rectangular 2.42               t=4 e=18: K=0.326 v_n(punto fijo)=1.27 m/s dh=26.8 mm
  rectangular 2.42               t=3 e=20: K=0.193 v_n(punto fijo)=1.27 m/s dh=15.9 mm
  rectangular 2.42               t=5 e=25: K=0.283 v_n(punto fijo)=1.27 m/s dh=23.3 mm
  semicirc. aguas arriba 1.83    t=4 e=12: K=0.423 v_n(punto fijo)=1.27 m/s dh=34.8 mm
  semicirc. aguas arriba 1.83    t=4 e=18: K=0.246 v_n(punto fijo)=1.27 m/s dh=20.3 mm
  semicirc. aguas arriba 1.83    t=3 e=20: K=0.146 v_n(punto fijo)=1.27 m/s dh=12.0 mm
  semicirc. aguas arriba 1.83    t=5 e=25: K=0.214 v_n(punto fijo)=1.27 m/s dh=17.6 mm
  circular 1.79                  t=4 e=12: K=0.414 v_n(punto fijo)=1.27 m/s dh=34.0 mm
  circular 1.79                  t=4 e=18: K=0.241 v_n(punto fijo)=1.27 m/s dh=19.8 mm
  circular 1.79                  t=3 e=20: K=0.143 v_n(punto fijo)=1.27 m/s dh=11.7 mm
  circular 1.79                  t=5 e=25: K=0.209 v_n(punto fijo)=1.27 m/s dh=17.2 mm
  ambos semicirc. 1.67           t=4 e=12: K=0.386 v_n(punto fijo)=1.27 m/s dh=31.7 mm
  ambos semicirc. 1.67           t=4 e=18: K=0.225 v_n(punto fijo)=1.27 m/s dh=18.5 mm
  ambos semicirc. 1.67           t=3 e=20: K=0.133 v_n(punto fijo)=1.27 m/s dh=10.9 mm
  ambos semicirc. 1.67           t=5 e=25: K=0.195 v_n(punto fijo)=1.27 m/s dh=16.1 mm

======== F. Cargas: presiones, boquilla, bucket, piedra ========
Punto fijo 4500 rpm: Q=46.7 L/s H=6.85 m P=4300 W T=544 N Vj=11.5
Presion estatica max. en carcasa (cierre, psi0=2 psi_d) ~ 122 kPa manometrica + p_atm; presion dinamica chorro 1/2 rho Vj^2 (punto fijo) = 67 kPa
P_el 5000: n=4535 rpm, momento del chorro rho Q Vj = 552 N; p_estatica entrada tobera ~ 51 kPa
   bucket (reversa k_r=0.6): F ~ 883 N; M_bisagra con brazo 60 mm = 53.0 N m
   bucket (reversa k_r=1.0): F ~ 1104 N; M_bisagra con brazo 60 mm = 66.3 N m
   boquilla delta=20: F_lateral=189 N, |F| sobre boquilla=192 N
   boquilla delta=30: F_lateral=276 N, |F| sobre boquilla=286 N
P_el 7200: n=5121 rpm, momento del chorro rho Q Vj = 704 N; p_estatica entrada tobera ~ 64 kPa
   bucket (reversa k_r=0.6): F ~ 1126 N; M_bisagra con brazo 60 mm = 67.6 N m
   bucket (reversa k_r=1.0): F ~ 1408 N; M_bisagra con brazo 60 mm = 84.5 N m
   boquilla delta=20: F_lateral=241 N, |F| sobre boquilla=245 N
   boquilla delta=30: F_lateral=352 N, |F| sobre boquilla=364 N
Piedra: E_cin rotor = 489 J ; parada en 90 grados -> par medio 311 N m
Piedra: E_cin rotor = 489 J ; parada en 30 grados -> par medio 933 N m
Piedra: E_cin rotor = 489 J ; parada en 10 grados -> par medio 2799 N m
Pasador 6061-T6 d=3 mm en eje 20 mm (corte doble, tau_u=0.6 UTS): 25 N m
Pasador 6061-T6 d=4 mm en eje 20 mm (corte doble, tau_u=0.6 UTS): 44 N m
Pasador 6061-T6 d=5 mm en eje 20 mm (corte doble, tau_u=0.6 UTS): 68 N m

======== G. openplaning (Savitsky 1964) y Mercier-Savitsky (preplaneo) ========
EJEMPLO Delta=200 kg b=0.6 beta=10 LCG=1.0 V=8.33: tau=6.367 deg z_wl=0.2604 m R=326.7 N (presion 216.2 + friccion 110.6) L_K=1.609 L_C=1.303 lambda=2.427 S=0.887 m2 T_espejo=0.1785
vol=0.1974 m3 vol^1/3=0.5823
 casco L=2.0 b=0.6 iE=20 AT/AX=0.9 B/T=4.0:
   Fnv=1.0 V=  8.6 km/h X=0.291 Z=0.914 U=6.32 R/Delta_ref=0.0319 R/Delta(escala)=0.0354 R=69 N
   Fnv=1.2 V= 10.3 km/h X=0.291 Z=0.914 U=6.32 R/Delta_ref=0.1045 R/Delta(escala)=0.1094 R=215 N
   Fnv=1.4 V= 12.0 km/h X=0.291 Z=0.914 U=6.32 R/Delta_ref=0.1435 R/Delta(escala)=0.1499 R=294 N
   Fnv=1.6 V= 13.8 km/h X=0.291 Z=0.914 U=6.32 R/Delta_ref=0.1509 R/Delta(escala)=0.1590 R=312 N
   Fnv=1.8 V= 15.5 km/h X=0.291 Z=0.914 U=6.32 R/Delta_ref=0.1443 R/Delta(escala)=0.1543 R=303 N
   Fnv=2.0 V= 17.2 km/h X=0.291 Z=0.914 U=6.32 R/Delta_ref=0.1329 R/Delta(escala)=0.1448 R=284 N
 casco L=2.0 b=0.7 iE=30 AT/AX=0.9 B/T=5.0:
   Fnv=1.0 V=  8.6 km/h X=0.291 Z=0.576 U=7.75 R/Delta_ref=0.0603 R/Delta(escala)=0.0641 R=126 N
   Fnv=1.2 V= 10.3 km/h X=0.291 Z=0.576 U=7.75 R/Delta_ref=0.1372 R/Delta(escala)=0.1424 R=279 N
   Fnv=1.4 V= 12.0 km/h X=0.291 Z=0.576 U=7.75 R/Delta_ref=0.1584 R/Delta(escala)=0.1651 R=324 N
   Fnv=1.6 V= 13.8 km/h X=0.291 Z=0.576 U=7.75 R/Delta_ref=0.1531 R/Delta(escala)=0.1616 R=317 N
   Fnv=1.8 V= 15.5 km/h X=0.291 Z=0.576 U=7.75 R/Delta_ref=0.1478 R/Delta(escala)=0.1583 R=311 N
   Fnv=2.0 V= 17.2 km/h X=0.291 Z=0.576 U=7.75 R/Delta_ref=0.1391 R/Delta(escala)=0.1517 R=298 N
 casco L=2.2 b=0.75 iE=25 AT/AX=1.0 B/T=5.5:
   Fnv=1.0 V=  8.6 km/h X=0.265 Z=0.468 U=7.07 R/Delta_ref=0.0224 R/Delta(escala)=0.0263 R=52 N
   Fnv=1.2 V= 10.3 km/h X=0.265 Z=0.468 U=7.07 R/Delta_ref=0.0743 R/Delta(escala)=0.0797 R=156 N
   Fnv=1.4 V= 12.0 km/h X=0.265 Z=0.468 U=7.07 R/Delta_ref=0.1125 R/Delta(escala)=0.1196 R=235 N
   Fnv=1.6 V= 13.8 km/h X=0.265 Z=0.468 U=7.07 R/Delta_ref=0.1068 R/Delta(escala)=0.1158 R=227 N
   Fnv=1.8 V= 15.5 km/h X=0.265 Z=0.468 U=7.07 R/Delta_ref=0.1055 R/Delta(escala)=0.1166 R=229 N
   Fnv=2.0 V= 17.2 km/h X=0.265 Z=0.468 U=7.07 R/Delta_ref=0.0943 R/Delta(escala)=0.1076 R=211 N
openplaning barrido (200 kg, b 0.6, beta 10, LCG 1.0):
   12 km/h: R=291 N tau=7.80 lambda=3.81 Fn_B=1.37 avisos=0
   15 km/h: R=338 N tau=8.94 lambda=3.31 Fn_B=1.72 avisos=0
   17 km/h: R=357 N tau=9.29 lambda=3.03 Fn_B=1.95 avisos=0
   20 km/h: R=361 N tau=9.07 lambda=2.76 Fn_B=2.29 avisos=0
   25 km/h: R=343 N tau=7.76 lambda=2.53 Fn_B=2.86 avisos=0
   30 km/h: R=327 N tau=6.36 lambda=2.43 Fn_B=3.43 avisos=0
   35 km/h: R=324 N tau=5.22 lambda=2.37 Fn_B=4.01 avisos=0

======== H. 5 kn (9,26 km/h): R Mercier-Savitsky -> rpm, potencia y autonomia con el jet de diseno ========
Fn_vol a 5 kn = 1.076
  L=2.0 b=0.6 iE=20: R/Delta=0.055 R=108 N -> n=2436 rpm P_eje=682 W P_el=775 W eta_total=0.358 | 3 kWh utiles: 3.87 h
  L=2.0 b=0.7 iE=30: R/Delta=0.095 R=185 N -> n=3068 rpm P_eje=1362 W P_el=1548 W eta_total=0.308 | 3 kWh utiles: 1.94 h
  L=2.2 b=0.75 iE=25: R/Delta=0.042 R=82 N -> n=2173 rpm P_eje=484 W P_el=550 W eta_total=0.383 | 3 kWh utiles: 5.45 h
```

</details>

<details><summary>Salida de r12_calc_nu50.py, secciones B–C (ν = 0,50)</summary>

```
======== B. Triangulos de velocidad (torbellino libre, sin pre-giro) ========
cubo  r= 27.0 mm U= 12.7 cu2= 5.58 beta1= 31.1 beta2= 47.1 | blade b1= 34.1 b2= 50.9 (desv  3.8) w2/w1=0.71 Df=0.44 s=1.3 paso=33.9 cuerda=44.1 mm | alpha3(estator in)= 53.9
medio r= 40.5 mm U= 19.1 cu2= 3.72 beta1= 21.9 beta2= 26.5 | blade b1= 24.9 b2= 27.1 (desv  0.6) w2/w1=0.83 Df=0.26 s=0.95 paso=50.9 cuerda=48.3 mm | alpha3(estator in)= 64.1
punta r= 54.0 mm U= 25.4 cu2= 2.79 beta1= 16.8 beta2= 18.7 | blade b1= 19.8 b2= 18.2 (desv -0.5) w2/w1=0.90 Df=0.18 s=0.7 paso=67.9 cuerda=47.5 mm | alpha3(estator in)= 70.0
Re cuerda punta = 9.35e+05

======== C. Estator, par, cargas de alabe ========
Par eje = 9.12 N m (diseno). Con 7.2 kW el/0.88: 13.45 N m
Fuerza tangencial media por alabe: rotor Z=5: 45 N ; estator Z=7: 32 N (r_m=40.5 mm)
  Al 6061-T6: t_raiz minima (sigma_adm 60 MPa, cuerda cubo 44 mm) = 1.17 mm
  316 fundido/mecanizado: t_raiz minima (sigma_adm 80 MPa, cuerda cubo 44 mm) = 1.02 mm
  bronce NiAl: t_raiz minima (sigma_adm 90 MPa, cuerda cubo 44 mm) = 0.96 mm
Empuje axial sobre el rotor ~ dp_estatica*A_anular = 372 N (dp=54.2 kPa); empuje neto del jet a 30 km/h = 269 N

```

</details>

<details><summary>r12_hub.py y salida</summary>

```python
import math
rho,g=1013.0,9.81; D=0.108; Om=2*math.pi*4500/60; Q=0.0527; H=6.16; eta_h=0.85
gHth=g*H/eta_h; Dflim=0.45
print("nu_h | c_m | seccion: beta1 beta2 turn  w2/w1  s_min(Df<=0.45)  | U_tip | H_hub/H (si torbellino libre ok)")
for nu in (0.35,0.40,0.45,0.50,0.55):
    A=math.pi/4*D**2*(1-nu**2); cm=Q/A
    out=[]
    for name,r in (("cubo",nu*D/2),("medio",(1+nu)/2*D/2),("punta",D/2)):
        U=Om*r; cu2=gHth/U
        if cu2>=U: out.append(f"{name}: IMPOSIBLE (cu2>U)"); continue
        b1=math.degrees(math.atan2(cm,U)); b2=math.degrees(math.atan2(cm,U-cu2))
        w1=math.hypot(cm,U); w2=math.hypot(cm,U-cu2)
        smin=cu2/(2*w1*(Dflim-1+w2/w1)) if (Dflim-1+w2/w1)>0 else float('inf')
        out.append(f"{name}: {b1:4.1f} {b2:4.1f} {b2-b1:4.1f} {w2/w1:.2f} {smin:5.2f}")
    print(f"{nu:.2f} | {cm:4.2f} | "+" | ".join(out))
# de Haller w2/w1 >= 0.7 (ESTIMADO) -> indica limite
```

```
nu_h | c_m | seccion: beta1 beta2 turn  w2/w1  s_min(Df<=0.45)  | U_tip | H_hub/H (si torbellino libre ok)
0.35 | 6.56 | cubo: 36.4 82.0 45.6 0.60  7.42 | medio: 20.9 26.7  5.8 0.79  0.46 | punta: 14.4 16.1  1.7 0.90  0.15
0.40 | 6.85 | cubo: 33.9 65.0 31.1 0.62  4.32 | medio: 21.0 26.4  5.3 0.81  0.40 | punta: 15.1 16.8  1.8 0.90  0.15
0.45 | 7.21 | cubo: 32.2 54.0 21.8 0.66  2.11 | medio: 21.4 26.3  4.9 0.82  0.36 | punta: 15.8 17.7  1.8 0.90  0.15
0.50 | 7.67 | cubo: 31.1 47.1 16.0 0.71  1.21 | medio: 21.9 26.5  4.6 0.83  0.32 | punta: 16.8 18.7  1.9 0.90  0.15
0.55 | 8.25 | cubo: 30.5 42.8 12.3 0.75  0.79 | medio: 22.7 27.1  4.4 0.85  0.28 | punta: 18.0 20.0  2.0 0.90  0.15
```

</details>

<details><summary>op_ejemplo.py (openplaning, §6.2) y salida completa</summary>

```python
import warnings, numpy as np
from openplaning import PlaningBoat
g = 9.8066
casos = dict(base=dict(), aire=dict(l_air=0.8, h_air=0.6, b_air=0.8, C_shape=1.0, C_D=0.9))
for nombre, extra in casos.items():
    b = PlaningBoat(speed=8.33, weight=200*g, beam=0.6, lcg=1.0, vcg=0.33, r_g=0.5,
                    beta=10, epsilon=0, vT=0.10, lT=0.0, loa=2.3,
                    rho=1013, nu=1.35e-6, **extra)
    b.get_steady_trim()          # resuelve z_wl y tau (equilibrio Fz y M)
    b.get_forces()               # vuelve a calcular con el trimado hallado (emite warnings de validez)
    R = -b.thrust_force[0]       # N, empuje efectivo requerido (horizontal)
    print(f"--- caso {nombre} ---")
    print(f"tau = {b.tau:.3f} deg  z_wl = {b.z_wl:.4f} m")
    print(f"L_K = {b.L_K:.3f} m  L_C = {b.L_C:.3f} m  lambda = {b.lambda_W:.3f}  T_espejo = {b.T:.4f} m")
    print(f"S mojada = {b.wetted_bottom_area:.3f} m2  V_m = {b.bottom_fluid_speed:.3f} m/s  C_f = {b.C_f:.5f} dC_f = {b.deltaC_f:.5f}")
    print("hydrodynamic_force [Fx,Fz,M] =", np.round(b.hydrodynamic_force,2))
    print("skin_friction      [Fx,Fz,M] =", np.round(b.skin_friction,2))
    print("air_resistance     [Fx,Fz,M] =", np.round(b.air_resistance,2))
    print("thrust_force       [Fx,Fz,M] =", np.round(b.thrust_force,2))
    print("net_force (debe ~0)          =", np.round(b.net_force,4))
    print(f"R total = {R:.1f} N  R/Delta = {R/(200*g):.3f}  P_E = {R*8.33/1000:.3f} kW  lcp = {b.lcp:.3f} m  Fn_B = {8.33/np.sqrt(g*0.6):.3f}")
    b.check_porpoising()
    print("porpoising [[eig, t_settle],[Savitsky, tau_crit]] =", b.porpoising)
```

```
--- caso base ---
tau = 6.367 deg  z_wl = 0.2604 m
L_K = 1.609 m  L_C = 1.303 m  lambda = 2.427  T_espejo = 0.1785 m
S mojada = 0.887 m2  V_m = 8.115 m/s  C_f = 0.00307 dC_f = 0.00050
hydrodynamic_force [Fx,Fz,M] = [ 216.17 1937.2   -41.74]
skin_friction      [Fx,Fz,M] = [110.56 -12.34 -33.87]
air_resistance     [Fx,Fz,M] = [0 0 0]
thrust_force       [Fx,Fz,M] = [-326.73   36.46   75.61]
net_force (debe ~0)          = [326.7271   0.       0.    ]
R total = 326.7 N  R/Delta = 0.167  P_E = 2.722 kW  lcp = 0.979 m  Fn_B = 3.434
porpoising [[eig, t_settle],[Savitsky, tau_crit]] = [[True, -8.481040618728525], [False, 8.658865971800111]]
--- caso aire ---
tau = 6.374 deg  z_wl = 0.2607 m
L_K = 1.606 m  L_C = 1.300 m  lambda = 2.422  T_espejo = 0.1783 m
S mojada = 0.885 m2  V_m = 8.114 m/s  C_f = 0.00307 dC_f = 0.00050
hydrodynamic_force [Fx,Fz,M] = [ 216.2  1935.44  -45.24]
skin_friction      [Fx,Fz,M] = [110.35 -12.33 -33.81]
air_resistance     [Fx,Fz,M] = [15.51  0.   -0.11]
thrust_force       [Fx,Fz,M] = [-342.06   38.21   79.16]
net_force (debe ~0)          = [342.0584   0.       0.    ]
R total = 342.1 N  R/Delta = 0.174  P_E = 2.849 kW  lcp = 0.977 m  Fn_B = 3.434
porpoising [[eig, t_settle],[Savitsky, tau_crit]] = [[True, -8.28453672555269], [False, 8.658865971800111]]
```

</details>
