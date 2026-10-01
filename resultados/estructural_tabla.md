<!-- generado por 04_diseno/structural.py -->
| Pieza | Caso de carga | Modelo | σ [MPa] | Admisible | S [MPa] | FS | Obj. | OK |
|---|---|---|---|---|---|---|---|---|
| P1-PMP-03 | Álabe en la raíz: par de diseño 14.6 N·m + empuje | voladizo: F_t=T/(Z·r_m)=59 N a span/2 + F_a=150 N/álabe en r̄; M=2.91 N·m; W_mín perfil cubo=77 mm³ (c=53.9, t=4.31) | 37.91 | metal | 205.0 | 5.41 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz, fatiga: par de diseño 14.6 N·m + empuje | σ_a = 0.30·σ_m (paso por 7 álabes del estator, toma); K_f 1.5; S_e 316 | 11.37 | metal | 120.0 | 10.55 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz: par máx. del controlador 18.6 N·m + empuje | voladizo: F_t=T/(Z·r_m)=75 N a span/2 + F_a=150 N/álabe en r̄; M=3.01 N·m; W_mín perfil cubo=77 mm³ (c=53.9, t=4.31) | 39.18 | metal | 205.0 | 5.23 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz, fatiga: par máx. del controlador 18.6 N·m + empuje | σ_a = 0.30·σ_m (paso por 7 álabes del estator, toma); K_f 1.5; S_e 316 | 11.76 | metal | 120.0 | 10.21 | 2.0 | ✔ |
| P1-PMP-03 | Álabe en la raíz: par de corte del pasador 33.5 N·m (traba repartida) | voladizo: F_t=T/(Z·r_m)=135 N a span/2 + F_a=150 N/álabe en r̄; M=3.54 N·m; W_mín perfil cubo=77 mm³ (c=53.9, t=4.31) | 46.03 | metal | 205.0 | 4.45 | 2.0 | ✔ |
| P1-PMP-03 | Cubo: aplastamiento del pasador al par de corte | F=837 N por lado sobre 3.5×20 mm (r medio) | 11.96 | metal | 307.5 | 25.72 | 2.0 | ✔ |
| P1-PMP-05 | Par máx. del controlador (margen contra corte intempestivo) | corte doble τ=T/(d_eje·A)=96.5 MPa; τ_u=0,6·S_u=174 MPa; T_corte/T_máx=1.80 (criterio R12 ≥ 1,5) | 96.50 | metal | 174.0 | 1.8 | 2.0 | ✔ (justif.) |
| P1-PMP-05 | Fatiga a par de crucero (Goodman en corte) | τ_m=65.7, τ_a=9.9 MPa (T_top 12.6 N·m, ±15%); S_e,τ=0,577·S_e; índice Goodman 0.56 | 0.56 | metal | 1.0 | 1.8 | 2.0 | ✔ (justif.) |
| P1-PMP-06 | Álabe del estator en la raíz: par de diseño 14.6 N·m | voladizo (conservador, en realidad empotrado en camisa y cubo): F_t=42 N, F_a=29 N, F_r buje=20 N; W_mín=66 mm³ (c=44.4, t=4.44) | 23.18 | metal | 240.0 | 10.35 | 2.0 | ✔ |
| P1-PMP-06 | Álabe del estator, fatiga: par de diseño | σ_a=0.30·σ_m (estelas de 5 álabes); S_e Al anodizado = 0.6·S_e; K_f 1.5 | 6.96 | metal | 38.4 | 5.52 | 2.0 | ✔ |
| P1-PMP-06 | Álabe del estator en la raíz: par máx. del controlador 18.6 N·m | voladizo (conservador, en realidad empotrado en camisa y cubo): F_t=54 N, F_a=29 N, F_r buje=20 N; W_mín=66 mm³ (c=44.4, t=4.44) | 25.68 | metal | 240.0 | 9.35 | 2.0 | ✔ |
| P1-PMP-06 | Álabe del estator, fatiga: par máx. del controlador | σ_a=0.30·σ_m (estelas de 5 álabes); S_e Al anodizado = 0.6·S_e; K_f 1.5 | 7.70 | metal | 38.4 | 4.99 | 2.0 | ✔ |
| P1-PMP-01 | Presión interna 0.20 MPa (R12 §7.2) | aro delgado σ=p·r/t, r=74.2, t=5.0 | 2.97 | metal | 240.0 | 80.91 | 2.0 | ✔ |
| P1-PMP-08 | Presión interna 0.20 MPa (R12 §7.2) | aro delgado σ=p·r/t, r=69.2, t=5.0 | 2.77 | metal | 240.0 | 86.76 | 2.0 | ✔ |
| P1-PMP-01 | Bulones brida toma (8×M6): presión + bucket + momentos | F_ax=2347 N, M=150.6 N·m (boquilla 281 N, bucket 607 N, peso) → F_bulón=749 N sobre A_s=20.1 mm² (sin precarga) | 37.25 | metal | 450.0 | 12.08 | 2.0 | ✔ |
| P1-PMP-08 | Bulones brida carcasa–tobera (8×M6): presión + bucket + momentos | F_ax=2347 N, M=104.8 N·m (boquilla 281 N, bucket 607 N, peso) → F_bulón=602 N sobre A_s=20.1 mm² (sin precarga) | 29.93 | metal | 450.0 | 15.04 | 2.0 | ✔ |
| P1-PMP-01 | Tornillos anti-rotación del estator (2×M5) al corte | F=130 N por tornillo (T_max 18.6 N·m, r=71.7) | 9.12 | metal | 259.6 | 28.46 | 2.0 | ✔ |
| P1-PMP-08 | Oreja: aplastamiento — F lateral de la boquilla 281 N | σ_b=F/(d·t), d=8.0, t=12.0 | 2.92 | metal | 360.0 | 123.09 | 2.0 | ✔ |
| P1-PMP-08 | Oreja: sección neta y desgarro — F lateral de la boquilla 281 N | máx(F/((w−d)·t), F/(2·(e−d/2)·t)·√3), w=24.0, e=12.0 | 2.56 | metal | 240.0 | 93.57 | 2.0 | ✔ |
| P1-PMP-08 | Oreja: flexión en el arranque — F lateral de la boquilla 281 N | M=F·15.0 mm, W=w·t²/6 (eje débil) | 7.31 | metal | 240.0 | 32.83 | 2.0 | ✔ |
| P1-PMP-08 | Oreja: fatiga — F lateral de la boquilla 281 N | σ_a = σ flexión (maniobras, ~1e5–1e6 ciclos); S_e Al anodizado 0.6·S_e; K_f 1.5 | 7.31 | metal | 38.4 | 5.25 | 2.0 | ✔ |
| P1-PMP-08 | Oreja: aplastamiento — F del bucket 607 N | σ_b=F/(d·t), d=8.0, t=12.0 | 6.32 | metal | 360.0 | 56.95 | 2.0 | ✔ |
| P1-PMP-08 | Oreja: sección neta y desgarro — F del bucket 607 N | máx(F/((w−d)·t), F/(2·(e−d/2)·t)·√3), w=24.0, e=12.0 | 5.54 | metal | 240.0 | 43.29 | 2.0 | ✔ |
| P1-PMP-08 | Oreja: flexión en el arranque — F del bucket 607 N | M=F·15.0 mm, W=w·t²/6 (eje débil) | 15.80 | metal | 240.0 | 15.19 | 2.0 | ✔ |
| P1-PMP-08 | Oreja: fatiga — F del bucket 607 N | σ_a = σ flexión (maniobras, ~1e5–1e6 ciclos); S_e Al anodizado 0.6·S_e; K_f 1.5 | 15.80 | metal | 38.4 | 2.43 | 2.0 | ✔ |
| P1-PMP-09 | Cuello: F lateral de la boquilla con el O-ring a tope | voladizo del cuello M=F·L=4.6 N·m, W anillo=108957 mm³ | 0.04 | metal | 125.0 | 2957.92 | 2.0 | ✔ |
| P1-INT-01 | Techo plano entre costados, p = máx(p_cierre, p_golpe) | placa larga empotrada: σ = p·b²/(2t²), b = W_open = 158, t = 5.0 | 35.67 | metal | 125.0 | 3.5 | 2.0 | ✔ |
| P1-INT-01 | Costado plano más alto (en el labio), p = máx(p_cierre, p_golpe) | placa empotrada brida–techo: σ = p·h²/(2t²), h = 156 | 34.67 | metal | 125.0 | 3.61 | 2.0 | ✔ |
| P1-INT-01 | Fatiga de la soldadura del costado: Δp = p_ram + p_succión = 40 kPa, 1e+05 ciclos | Δσ = Δp·h²/(2t²) vs FAT 25 (IIW, m = 3) → 68 MPa | 19.40 | metal | 67.9 | 3.5 | 2.0 | ✔ |
| P1-INT-01 | Bulones M6 A4 brida ↔ placa (14): precarga + p·A_abertura + 3 g | σ = (F_v + Φ·F/n)/A_s, F = 4689 N, Φ = 0,25 | 203.17 | metal | 450.0 | 2.21 | 2.0 | ✔ |
| P1-INT-01 | Tubo junto a la brida de la bomba: momento del bucket (sin placa de espejo) | σ = M/(π r² t), M = F_bucket·358 | 2.70 | metal | 125.0 | 46.35 | 2.0 | ✔ |
| P1-INT-01 | Bulones M6 de la brida de la bomba: precarga + momento del bucket | σ = (F_v + Φ·4M/(n·r_bc))/A_s, Φ = 0,25 (VDI 2230) | 215.37 | metal | 450.0 | 2.09 | 2.0 | ✔ |
| P1-INT-01 | Tubo del eje en voladizo (sin contar el alma): caja del sello | σ = F·L/W, L = 74 | 2.41 | metal | 125.0 | 51.94 | 2.0 | ✔ |
| P1-INT-01 | Chimenea de inspección: presión de cierre (aro) | σ = p·r/t | 0.78 | metal | 125.0 | 159.84 | 2.0 | ✔ |
| P1-INT-02 | Paño lateral entre bulones del conducto y del ala: golpe de fondo | σ = p·b²/(2t²), b = 68 | 1.17 | metal | 125.0 | 106.56 | 2.0 | ✔ |
| P1-INT-02 | Roscas M8 ciegas del soporte (7,5 mm en 5083): precarga + vuelco del empuje | τ = F/(0,5·π·d·L_e), F_v = 3000 N, F_t = 395 N | 36.02 | metal | 72.2 | 2.0 | 2.0 | ✔ |
| P1-INT-02 | Bulones M6 del ala al casco (26): precarga + golpe de fondo + presión en la abertura | σ = (F_v + Φ·F/n)/A_s, F = 8990 N, Φ = 0,25 | 203.31 | metal | 450.0 | 2.21 | 2.0 | ✔ |
| P1-INT-02 | Aplastamiento del casco (Al 4 mm) por el empuje en los bulones del ala | σ_b = (T/n)/(d·t) | 1.06 | metal | 125.0 | 117.41 | 2.0 | ✔ |
| P1-INT-02 | Arranque de la cabeza avellanada M6 en el casco de 4 mm (corte del labio de 1,2 mm) | τ = (F/n)/(π·d_m·t_labio), d_m = 9 | 10.19 | metal | 72.2 | 7.08 | 2.0 | ✔ |
| P1-INT-03 | Barra con la rejilla tapada (bolsa) a la presión de cierre | viga simplemente apoyada L = 330, w = p·paso, W = 212 mm³ (sección perfilada) | 92.94 | metal | 205.0 | 2.21 | 2.0 | ✔ |
| P1-INT-03 | Barra: golpe de objeto 200 N en el centro | M = P·L/4 | 77.97 | metal | 205.0 | 2.63 | 2.0 | ✔ |
| P1-INT-03 | Apoyo de la barra contra la cuña de la placa (aplastamiento del Al) | σ_b = R/(b·9 mm) | 6.62 | metal | 125.0 | 18.88 | 2.0 | ✔ |
| P1-INT-04 | Tapa: succión/contrapresión de cierre (corta) | σ = 3(3+ν)p a²/(8t²), a = 58, t = 13.0 | 1.82 | short | 24.0 | 13.18 | 3.0 | ✔ |
| P1-INT-04 | Tapa: recuperación de presión a 30 km/h (sostenida) | ídem con p_ram | 0.63 | sust | 8.4 | 13.32 | 3.0 | ✔ |
| P1-INT-04 | Tapa: ciclo marcha ↔ punto fijo Δp = 40 kPa (olas/maniobras) | ídem con Δp | 1.02 | lcf | 3.6 | 3.53 | 3.0 | ✔ |
| P1-INT-04 | Tapa: aplastamiento bajo arandela M6 Ø18 (sostenido) | σ = F/(π/4(18² − 6,4²)) | 0.30 | sust | 8.4 | 28.28 | 3.0 | ✔ |
| P1-DRV-01 | Agujero del pasador: par de corte del pasador (traba con piedra) | τ = T_corte/(πd³/16 − d_h·d²/6), T_corte 33.5 N·m, sección neta, K_t = 1 (dúctil, estático) | 25.07 | metal | 118.3 | 4.72 | 2.0 | ✔ |
| P1-DRV-01 | Agujero del pasador: fatiga en V máx. (T_top ± 10 %) | Goodman τ_a/τ_e + τ_m/τ_u, K_ts 2.0 (Peterson), S_e corrosión 180 MPa; σ_eq = τ_a·τ_u/τ_e + τ_m | 24.34 | metal | 297.1 | 12.21 | 2.0 | ✔ |
| P1-DRV-01 | Ranura DIN 471 de empuje: par de corte del pasador + Fa | von Mises √(σ² + 3τ²), τ = T_corte/(π·19³/16), σ = Fa/A_fondo, K_t = 1 (dúctil, estático) | 43.12 | metal | 205.0 | 4.75 | 2.0 | ✔ |
| P1-DRV-01 | Ranura DIN 471 de empuje: fatiga en V máx. | Goodman von Mises σ_a/S_e + σ_m/S_u; K_ts 3.0, K_t ax 4.0; empuje en V máx. ∝ T_top | 62.95 | metal | 515.0 | 8.18 | 2.0 | ✔ |
| P1-DRV-01 | Chaveta 6×6 del acople: aplastamiento a T_max | p = 2T/(d·(h − t1)·(l − b)), l = 22 mm, cubo de acero | 46.42 | metal | 100.0 | 2.15 | 2.0 | ✔ |
| P1-DRV-01 | Rosca M20×1 (KM4): Fa en reversa + par T_max | von Mises en el núcleo (d − 1,083·P), σ = Fa/A, τ = 16T/(π d3³) | 24.31 | metal | 205.0 | 8.43 | 2.0 | ✔ |
| P1-DRV-02 | Presión de diseño 0.20 MPa en la cámara mojada (espigón) | anillo de pared delgada σ = p·r/t (espigón, la sección más delgada) | 1.20 | metal | 205.0 | 170.83 | 2.0 | ✔ |
| P1-DRV-02 | Bulones 4 × M6 A4-70 al buje de la toma: presión + resorte del sello | σ = F/(4·A_s), F = p·π/4·Ø42² + 150 N (sin precarga) | 5.31 | metal | 450.0 | 84.71 | 2.0 | ✔ |
| P1-DRV-02 | Brida de 8 mm: flexión entre espigón y bulones | placa anular como viga por unidad de perímetro: σ = 6·F·e/(π·BC·t²) | 1.42 | metal | 205.0 | 144.76 | 2.0 | ✔ |
| P1-DRV-03 | Mejillas: empuje Fa a punto fijo en la base (cada una ½ Fa) | flexión en su plano σ = M/(t·L²/6), M = Fa/2 · 121 mm, L = 150 mm, ZAT soldada | 0.89 | metal | 115.0 | 129.28 | 2.0 | ✔ |
| P1-DRV-03 | Tablero: 3 g vertical del tren + Fr (biapoyado entre mejillas) + Fa excéntrico | σ = P·L/4/(b t²/6) + Fa·e/(t·b²/6)/2, L = 200, b = 31, e = 35 mm, ZAT | 14.86 | metal | 115.0 | 7.74 | 2.0 | ✔ |
| P1-DRV-03 | Bulones 4 × M8 A4-70 a la placa base: vuelco por Fa + corte | F_t = Fa·h/Δx/2 + 3g/4, F_s = Fa/4; von Mises sobre A_s (sin precarga; Δx = 120) | 13.46 | metal | 450.0 | 33.44 | 2.0 | ✔ |
| P1-DRV-03 | Rosca M8 en la placa base de Al (TOMA), 8 mm de filete | τ = F_t/(π·d·L_e·0,6) contra τ_adm = 0,58·R_p0,2 de 5083-H111 (125 MPa [ESTIMADO]) | 3.31 | metal | 72.5 | 21.89 | 2.0 | ✔ |
| P1-DRV-03 | Alojamiento Ø47: Fa sobre el resalte trasero (reversa) / anillo | corte del resalte τ = Fa/(π·D·t_resalte), σ_eq = √3·τ | 2.60 | metal | 240.0 | 92.39 | 2.0 | ✔ |
| P1-DRV-06 | Tapa: empuje Fa hacia proa entre el aro exterior y los M5 | placa anular por unidad de perímetro σ = 6·Fa·e/(2π r_m t²) | 3.05 | metal | 240.0 | 78.71 | 2.0 | ✔ |
| P1-DRV-06 | Bulones 4 × M5 A4-70 de la tapa: Fa | σ = Fa/(4·A_s) (sin precarga) | 11.70 | metal | 450.0 | 38.47 | 2.0 | ✔ |
| P1-MOT-02 | Placa: 3 g vertical del motor en voladizo (sin cartelas) | σ = W·e/(b t²/6), W = 3 g × 4.4 kg, e = 63 mm, b = 2·95 − Ø64 | 3.88 | metal | 115.0 | 29.6 | 2.0 | ✔ |
| P1-MOT-02 | Placa: par de reacción T_max (en su plano) + 3 g | corte en la sección por el agujero τ = (T/ (2·y_pie) + W/2)/(b·t) , σ_eq = √3·τ | 0.27 | metal | 115.0 | 423.85 | 2.0 | ✔ |
| P1-MOT-02 | Bulones 4 × M6 a la cara del motor: T_max + 3 g (corte) | τ = (T/(n·r) + W/n)/A_s, σ_eq = √3·τ (sin fricción por precarga) | 12.79 | metal | 450.0 | 35.18 | 2.0 | ✔ |
| P1-MOT-02 | Bulones 4 × M8 de los pies al casco: vuelco 3 g + par | F_t = W·e/Δx/2 + T/(2·y_pie) sobre A_s | 7.00 | metal | 450.0 | 64.28 | 2.0 | ✔ |
| P1-ELE-01 | Insertos M5 de la capota: apriete de las tiras de EPDM (sostenido) | arranque τ = F/(π·Ø·L) del inserto, F = máx(EPDM 160 N, 3 g arriba 66 N)/4; cruza capas (×f_Z) | 0.52 | sust | 8.4 | 16.02 | 3.0 | ✔ |
| P1-ELE-01 | Paredes del pedestal: 3 g vertical de ESC + capota (compresión sostenida) | σ = 3 g·m/A_paredes (pandeo despreciable: h/t = 19) | 0.03 | sust | 8.4 | 245.74 | 3.0 | ✔ |
| P1-ELE-01 | Orejas M6 al piso: 2 g lateral (golpe) del conjunto a la altura del CG | vuelco: F_t = m·2g·h_CG/(ancho)/2 sobre el anillo de la oreja (7 mm, cruza capas) | 0.16 | short | 24.0 | 153.03 | 3.0 | ✔ |
| P1-ELE-02 | Techo de la capota: reacción de las tiras de EPDM (sostenida) | voladizo desde la pared por unidad de largo σ = 6·q·b·(b/2 + c)/t² | 1.31 | sust | 8.4 | 6.39 | 3.0 | ✔ |
| P1-DRV eje 316 | Torsión máx. del controlador + fatiga (sizing) | 02_calculos.md §7 | — | metal | — | 4.0 | 2.0 | ✔ |
